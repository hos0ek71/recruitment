import pytest
from sqlalchemy import Connection, text

pytestmark = pytest.mark.db


def test_database_and_pg_trgm(db_connection: Connection) -> None:
    assert db_connection.execute(text("SELECT 1")).scalar_one() == 1
    assert (
        db_connection.execute(
            text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm')")
        ).scalar_one()
        is True
    )
