"""Reset only a local database explicitly named with a _test suffix."""

import os
import sys

import psycopg
from psycopg import sql
from sqlalchemy.engine import URL, make_url


def validate_test_url(value: str) -> URL:
    url = make_url(value)
    if (
        url.drivername != "postgresql+psycopg"
        or url.host not in {"localhost", "127.0.0.1"}
        or not url.database
        or not url.database.endswith("_test")
        or url.query
    ):
        raise ValueError("refusing reset: require a local _test PostgreSQL URL without query")
    return url


def reset_test_database(value: str) -> None:
    url = validate_test_url(value)
    # Explicit connection parameters prevent PGHOST/PGDATABASE from overriding the validated target.
    connection_args = {
        "host": url.host,
        "port": url.port or 5432,
        "user": url.username,
        "password": url.password,
        "connect_timeout": 5,
    }
    with psycopg.connect(dbname="postgres", autocommit=True, **connection_args) as connection:
        connection.execute(
            sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(url.database))
        )
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(url.database)))
    with psycopg.connect(dbname=url.database, autocommit=True, **connection_args) as connection:
        connection.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    print(f"Reset test database: {url.database}")


def main() -> int:
    try:
        reset_test_database(os.environ["TEST_DATABASE_URL"])
    except KeyError, ValueError:
        print(
            "Refusing reset: TEST_DATABASE_URL must target localhost/127.0.0.1 and a _test DB.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
