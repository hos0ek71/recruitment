import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

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
