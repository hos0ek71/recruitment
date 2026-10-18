import pytest

from app.config import Settings, resolve_enabled_sources


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


@pytest.mark.parametrize(
    ("enabled", "saramin", "work24", "expected"),
    [
        (None, None, None, ()),
        (None, "fake", None, ("saramin",)),
        (None, None, "fake", ("work24",)),
        (None, "fake", "fake", ("saramin", "work24")),
        ("", "fake", None, ("saramin",)),
        ("   ", "fake", None, ("saramin",)),
        ("saramin", "fake", "fake", ("saramin",)),
        (" work24, saramin,work24 ", "fake", "fake", ("work24", "saramin")),
    ],
)
def test_resolve_enabled_sources(enabled, saramin, work24, expected):
    settings = Settings(
        _env_file=None,
        DATABASE_URL="postgresql://localhost/test",
        ENABLED_SOURCES=enabled,
        SARAMIN_ACCESS_KEY=saramin,
        WORK24_AUTH_KEY=work24,
    )
    assert resolve_enabled_sources(settings) == expected


@pytest.mark.parametrize(
    ("enabled", "message"),
    [
        ("saramin", "ENABLED_SOURCES에 saramin이 있지만 SARAMIN_ACCESS_KEY가 없다"),
        ("work24", "ENABLED_SOURCES에 work24이 있지만 WORK24_AUTH_KEY가 없다"),
        ("unknown", "알 수 없는 소스: unknown"),
    ],
)
def test_resolve_enabled_sources_rejects_invalid_configuration(enabled, message):
    settings = Settings(
        _env_file=None,
        DATABASE_URL="postgresql://localhost/test",
        ENABLED_SOURCES=enabled,
        SARAMIN_ACCESS_KEY=None,
        WORK24_AUTH_KEY=None,
    )
    with pytest.raises(ValueError, match=message):
        resolve_enabled_sources(settings)


async def test_lifespan_rejects_invalid_sources_before_startup(monkeypatch):
    from app.main import create_app

    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
    monkeypatch.setenv("ENABLED_SOURCES", "unknown")
    app = create_app()
    with pytest.raises(ValueError, match="알 수 없는 소스: unknown"):
        async with app.router.lifespan_context(app):
            pytest.fail("invalid source configuration reached startup")


@pytest.mark.parametrize("enabled", ["saramin", "work24", "saramin,work24"])
async def test_lifespan_builds_only_explicitly_enabled_adapters(monkeypatch, enabled):
    from app.main import create_app

    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost/test")
    monkeypatch.setenv("ENABLED_SOURCES", enabled)
    monkeypatch.setenv("SARAMIN_ACCESS_KEY", "fake-saramin")
    monkeypatch.setenv("WORK24_AUTH_KEY", "fake-work24")
    app = create_app()
    async with app.router.lifespan_context(app):
        controller = app.state.collection_controller_factory()
        assert list(controller.adapters) == enabled.split(",")
