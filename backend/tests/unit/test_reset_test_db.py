import pytest

from scripts.reset_test_db import validate_test_url


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+psycopg://x:y@example.com:5432/recruitment_test",
        "postgresql+psycopg://x:y@127.0.0.1:5433/recruitment",
        "postgresql+psycopg://x:y@localhost:5433/",
        "sqlite:///recruitment_test",
        "postgresql+psycopg://x:y@localhost/recruitment_test?host=example.com",
        "postgresql+psycopg://x:y@localhost/recruitment_test?service=production",
    ],
)
def test_rejects_unsafe_reset_targets(url: str) -> None:
    with pytest.raises(ValueError):
        validate_test_url(url)


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1"])
def test_accepts_local_test_database(host: str) -> None:
    url = validate_test_url(f"postgresql+psycopg://x:y@{host}:5433/recruitment_test")
    assert url.database == "recruitment_test"
