import os
from collections.abc import Iterator

import pytest
from sqlalchemy import Connection, create_engine, text


@pytest.fixture
def db_connection() -> Iterator[Connection]:
    # No fallback to DATABASE_URL and no skip: missing/unreachable test DB is a failure.
    engine = create_engine(os.environ["TEST_DATABASE_URL"], connect_args={"connect_timeout": 5})
    try:
        with engine.connect() as connection, connection.begin():
            connection.execute(text("SELECT 1"))
            yield connection
    finally:
        engine.dispose()
