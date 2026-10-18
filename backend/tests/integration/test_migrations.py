import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

pytestmark = pytest.mark.db

TABLES = {
    "profile",
    "criteria",
    "explore_keyword",
    "collection_run",
    "collection_query",
    "raw_posting",
    "query_hit",
    "query_watermark",
    "api_usage",
    "posting",
    "posting_source",
    "filter_result",
    "evaluation",
    "user_mark",
    "excluded_company",
    "tool_call_log",
}


def migration_config():
    config = Config(str(Path(__file__).parents[2] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).parents[2] / "migrations"))
    return config


def test_upgrade_downgrade_upgrade(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    config = migration_config()
    engine = create_engine(os.environ["TEST_DATABASE_URL"])
    try:
        command.upgrade(config, "head")
        assert set(inspect(engine).get_table_names()) >= TABLES
        command.downgrade(config, "base")
        assert not TABLES & set(inspect(engine).get_table_names())
        command.upgrade(config, "head")
        assert set(inspect(engine).get_table_names()) >= TABLES
    finally:
        engine.dispose()


def test_enabled_sources_migration_roundtrip_preserves_existing_run(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    config = migration_config()
    engine = create_engine(os.environ["TEST_DATABASE_URL"])
    try:
        command.upgrade(config, "head")
        command.downgrade(config, "e98f227b8d6e")
        assert "enabled_sources" not in {
            c["name"] for c in inspect(engine).get_columns("collection_run")
        }
        with engine.begin() as connection:
            profile = connection.scalar(
                text("INSERT INTO profile (raw_text) VALUES ('test') RETURNING id")
            )
            criteria = connection.scalar(
                text(
                    "INSERT INTO criteria (profile_id, version) VALUES (:profile, 1) RETURNING id"
                ),
                {"profile": profile},
            )
            run = connection.scalar(
                text(
                    "INSERT INTO collection_run (criteria_id, trigger) "
                    "VALUES (:criteria, 'manual') RETURNING id"
                ),
                {"criteria": criteria},
            )
        command.upgrade(config, "head")
        columns = {c["name"]: c for c in inspect(engine).get_columns("collection_run")}
        assert columns["enabled_sources"]["nullable"] is False
        assert columns["enabled_sources"]["type"].item_type.python_type is str
        with engine.begin() as connection:
            assert (
                connection.scalar(
                    text("SELECT enabled_sources FROM collection_run WHERE id = :run"), {"run": run}
                )
                == []
            )
            connection.execute(text("DELETE FROM collection_run WHERE id = :run"), {"run": run})
            connection.execute(
                text("DELETE FROM criteria WHERE id = :criteria"), {"criteria": criteria}
            )
            connection.execute(
                text("DELETE FROM profile WHERE id = :profile"), {"profile": profile}
            )
    finally:
        command.upgrade(config, "head")
        engine.dispose()
