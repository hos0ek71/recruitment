from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str
    SARAMIN_ACCESS_KEY: str | None = None
    WORK24_AUTH_KEY: str | None = None
    LLM_API_KEY: str | None = None
    # 일일 호출 예산(KST 하루). 사람인 공식 한도는 500회이고, 100회는 추가 탐색용으로 남긴다.
    SARAMIN_DAILY_BUDGET: int = 400
    # 고용24 공식 일일 한도는 확인되지 않았다(docs/research/03). 키를 받은 뒤 조정한다.
    WORK24_DAILY_BUDGET: int = 1000
    TZ: str = "Asia/Seoul"
