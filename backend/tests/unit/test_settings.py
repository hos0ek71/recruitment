from app.config import Settings


def test_settings_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost/dev")
    for key in ("SARAMIN_ACCESS_KEY", "WORK24_AUTH_KEY", "LLM_API_KEY", "TZ"):
        monkeypatch.delenv(key, raising=False)
    settings = Settings(_env_file=None)
    assert settings.DATABASE_URL == "postgresql+psycopg://user:pass@localhost/dev"
    assert settings.SARAMIN_ACCESS_KEY is None
    assert settings.WORK24_AUTH_KEY is None
    assert settings.LLM_API_KEY is None
    assert settings.TZ == "Asia/Seoul"


def test_settings_reads_dotenv(tmp_path, monkeypatch) -> None:
    for key in ("DATABASE_URL", "SARAMIN_ACCESS_KEY", "WORK24_AUTH_KEY", "LLM_API_KEY", "TZ"):
        monkeypatch.delenv(key, raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("DATABASE_URL=postgresql://localhost/dev\nSARAMIN_ACCESS_KEY=fake\n")
    settings = Settings(_env_file=env_file)
    assert settings.DATABASE_URL == "postgresql://localhost/dev"
    assert settings.SARAMIN_ACCESS_KEY == "fake"
