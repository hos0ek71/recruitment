from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.adapters.base import SourceName


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str
    SARAMIN_ACCESS_KEY: str | None = None
    WORK24_AUTH_KEY: str | None = None
    ENABLED_SOURCES: str | None = None
    LLM_API_KEY: str | None = None
    # 일일 호출 예산(KST 하루). 사람인 공식 한도는 500회이고, 100회는 추가 탐색용으로 남긴다.
    SARAMIN_DAILY_BUDGET: int = 400
    # 고용24 공식 일일 한도는 확인되지 않았다(docs/research/03). 키를 받은 뒤 조정한다.
    WORK24_DAILY_BUDGET: int = 1000
    TZ: str = "Asia/Seoul"


def resolve_enabled_sources(settings: Settings) -> tuple[SourceName, ...]:
    keys: dict[SourceName, tuple[str, str | None]] = {
        "saramin": ("SARAMIN_ACCESS_KEY", settings.SARAMIN_ACCESS_KEY),
        "work24": ("WORK24_AUTH_KEY", settings.WORK24_AUTH_KEY),
    }
    if not settings.ENABLED_SOURCES or not settings.ENABLED_SOURCES.strip():
        return tuple(source for source, (_, key) in keys.items() if key)
    requested: list[SourceName] = []
    for name in settings.ENABLED_SOURCES.split(","):
        name = name.strip()
        if name == "saramin":
            source: SourceName = "saramin"
        elif name == "work24":
            source = "work24"
        else:
            raise ValueError(f"알 수 없는 소스: {name}")
        key_name, key = keys[source]
        if not key:
            raise ValueError(f"ENABLED_SOURCES에 {source}이 있지만 {key_name}가 없다")
        if source not in requested:
            requested.append(source)
    return tuple(requested)
