from pathlib import Path

import pytest

from tests.architecture.import_rules import find_violations


def write_module(root: Path, relative_path: str, source: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def test_app_import_boundaries() -> None:
    package_root = Path(__file__).resolve().parents[2] / "app"
    violations = find_violations(package_root)
    assert not violations, "\n" + "\n".join(str(violation) for violation in violations)


def test_finds_exact_violations_including_type_checking(tmp_path: Path) -> None:
    root = tmp_path / "app"
    write_module(root, "__init__.py", "")
    write_module(root, "api/bad.py", "import app.repositories\nimport httpx\n")
    write_module(
        root,
        "api/typed.py",
        "from typing import TYPE_CHECKING\n"
        "if TYPE_CHECKING:\n"
        "    from app.repositories.jobs import Repository\n",
    )
    write_module(
        root,
        "services/ok.py",
        "from app.repositories import jobs\n"
        "from app.adapters import client\n"
        "from app.domain import Posting\n"
        "from sqlalchemy.ext.asyncio import AsyncSession\n",
    )

    violations = find_violations(root)

    assert [(v.file.as_posix(), v.line, v.layer, v.target) for v in violations] == [
        ("app/api/bad.py", 1, "app.api", "app.repositories"),
        ("app/api/bad.py", 2, "app.api", "httpx"),
        ("app/api/typed.py", 3, "app.api", "app.repositories.jobs.Repository"),
    ]
    assert str(violations[0]) == (
        "app/api/bad.py:1 — app.api는 app.repositories를 import할 수 없다. "
        "서비스 함수를 거쳐라(AGENTS.md 아키텍처 경계)"
    )


@pytest.mark.parametrize(
    ("layer", "targets"),
    [
        ("api", "app.repositories app.adapters sqlalchemy httpx psycopg"),
        ("services", "app.api fastapi starlette httpx psycopg sqlalchemy sqlalchemy.orm"),
        ("repositories", "app.api app.services app.adapters fastapi starlette httpx"),
        ("adapters", "app.api app.services app.repositories app.db sqlalchemy fastapi starlette"),
        (
            "domain",
            "app.api app.services app.repositories app.adapters app.db fastapi starlette "
            "sqlalchemy httpx psycopg",
        ),
    ],
)
def test_forbidden_prefixes_include_submodules(tmp_path: Path, layer: str, targets: str) -> None:
    root = tmp_path / "app"
    imports = [f"{target}.nested" for target in targets.split()]
    write_module(root, f"{layer}/nested/bad.py", "\n".join(f"import {t}" for t in imports))
    assert [v.target for v in find_violations(root)] == imports


def test_relative_and_from_imports_cannot_bypass_rules(tmp_path: Path) -> None:
    root = tmp_path / "app"
    write_module(
        root,
        "api/nested/bad.py",
        "from ... import repositories\n"
        "from ...repositories import jobs\n"
        "from app import adapters\n"
        "from httpx import Client as HttpClient\n"
        "import app.repositories as repository, psycopg as pg\n",
    )
    write_module(root, "api/__init__.py", "from ..repositories import *\n")
    assert [(v.file.as_posix(), v.line, v.target) for v in find_violations(root)] == [
        ("app/api/__init__.py", 1, "app.repositories"),
        ("app/api/nested/bad.py", 1, "app.repositories"),
        ("app/api/nested/bad.py", 2, "app.repositories.jobs"),
        ("app/api/nested/bad.py", 3, "app.adapters"),
        ("app/api/nested/bad.py", 4, "httpx.Client"),
        ("app/api/nested/bad.py", 5, "app.repositories"),
        ("app/api/nested/bad.py", 5, "psycopg"),
    ]


def test_allowed_imports_and_composition_roots(tmp_path: Path) -> None:
    root = tmp_path / "app"
    write_module(
        root,
        "api/ok.py",
        "import app.services, app.domain, app.config, app.db\n"
        "from fastapi import APIRouter\n"
        "from . import health\n"
        "import httpx_extra\n",
    )
    write_module(
        root,
        "services/ok.py",
        "import app.repositories_extra\n"
        "from sqlalchemy.ext import asyncio\n"
        "import sqlalchemy.ext.asyncio\n"
        "from sqlalchemy.ext.asyncio import AsyncSession\n",
    )
    for module in ("main.py", "config.py", "db/__init__.py", "db/session.py"):
        write_module(root, module, "import app.api, app.repositories, httpx, sqlalchemy\n")
    assert find_violations(root) == []


def test_api_internal_imports_require_an_allowed_layer(tmp_path: Path) -> None:
    root = tmp_path / "app"
    write_module(root, "api/bad.py", "import app.utilities\n")
    assert [v.target for v in find_violations(root)] == ["app.utilities"]
