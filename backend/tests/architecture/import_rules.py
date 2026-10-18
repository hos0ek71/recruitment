"""Static import boundaries from AGENTS.md; importing app code is unnecessary."""

import ast
from collections.abc import Iterator
from dataclasses import dataclass
from importlib.util import resolve_name
from pathlib import Path


@dataclass(frozen=True)
class ImportRule:
    forbidden: tuple[str, ...]
    remedy: str
    allowed_internal: tuple[str, ...] | None = None
    exceptions: tuple[str, ...] = ()


RULES: dict[str, ImportRule] = {
    "app.api": ImportRule(
        forbidden=("app.repositories", "app.adapters", "sqlalchemy", "httpx", "psycopg"),
        allowed_internal=("app.api", "app.services", "app.domain", "app.config", "app.db"),
        remedy="서비스 함수를 거쳐라",
    ),
    "app.services": ImportRule(
        forbidden=("app.api", "fastapi", "starlette", "httpx", "psycopg", "sqlalchemy"),
        exceptions=("sqlalchemy.ext.asyncio",),
        remedy="HTTP 객체 의존을 없애고 외부 호출은 어댑터, SQL은 저장소를 거쳐라",
    ),
    "app.repositories": ImportRule(
        forbidden=("app.api", "app.services", "app.adapters", "fastapi", "starlette", "httpx"),
        remedy="저장소에서 상위 레이어와 외부 API에 의존하지 마라",
    ),
    "app.adapters": ImportRule(
        forbidden=(
            "app.api",
            "app.services",
            "app.repositories",
            "app.db",
            "sqlalchemy",
            "fastapi",
            "starlette",
        ),
        remedy="외부 호출을 어댑터 안에 격리하고 도메인 계약을 사용하라",
    ),
    "app.domain": ImportRule(
        forbidden=(
            "app.api",
            "app.services",
            "app.repositories",
            "app.adapters",
            "app.db",
            "fastapi",
            "starlette",
            "sqlalchemy",
            "httpx",
            "psycopg",
        ),
        remedy="도메인에서 인프라와 상위 레이어 의존을 제거하라",
    ),
}


@dataclass(frozen=True)
class Violation:
    file: Path
    line: int
    layer: str
    target: str
    message: str

    def __str__(self) -> str:
        return (
            f"{self.file.as_posix()}:{self.line} — "
            f"{self.layer}는 {self.target}를 import할 수 없다. {self.message}"
        )


def _matches(module: str, prefix: str) -> bool:
    return module == prefix or module.startswith(prefix + ".")


def _forbidden(target: str, rule: ImportRule) -> bool:
    if any(_matches(target, prefix) for prefix in rule.exceptions):
        return False
    if any(_matches(target, prefix) for prefix in rule.forbidden):
        return True
    return (
        rule.allowed_internal is not None
        and _matches(target, "app")
        and not any(_matches(target, prefix) for prefix in rule.allowed_internal)
    )


def _imports(tree: ast.AST, package: str) -> Iterator[tuple[int, str]]:
    # ast.walk includes TYPE_CHECKING guards and imports nested in functions/classes.
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node.lineno, alias.name
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                module = resolve_name("." * node.level + module, package)
            for alias in node.names:
                target = module if alias.name == "*" else f"{module}.{alias.name}"
                yield node.lineno, target


def find_violations(package_root: Path) -> list[Violation]:
    """Return deterministic diagnostics for every forbidden static import in app/."""
    violations: list[Violation] = []
    for file in sorted(package_root.rglob("*.py")):
        relative = file.relative_to(package_root)
        parts = relative.with_suffix("").parts
        module = ".".join(("app", *parts))
        layer = next((name for name in RULES if _matches(module, name)), None)
        if layer is None:
            continue  # main, config, db and app/__init__.py are composition roots.
        package = (
            module.removesuffix(".__init__")
            if file.stem == "__init__"
            else module.rsplit(".", 1)[0]
        )
        tree = ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
        rule = RULES[layer]
        for line, target in sorted(_imports(tree, package)):
            if _forbidden(target, rule):
                violations.append(
                    Violation(
                        file=Path("app") / relative,
                        line=line,
                        layer=layer,
                        target=target,
                        message=f"{rule.remedy}(AGENTS.md 아키텍처 경계)",
                    )
                )
    return violations
