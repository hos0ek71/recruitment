"""initial_schema"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "e98f227b8d6e"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_table(
        "api_usage",
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("calls", sa.Integer(), server_default=sa.text("'0'"), nullable=False),
        sa.CheckConstraint("source IN ('saramin', 'work24')", name="ck_usage_source"),
        sa.PrimaryKeyConstraint("usage_date", "source"),
    )
    op.create_table(
        "excluded_company",
        sa.Column("company_name_norm", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "reason IN ('referral', 'applied', 'other')", name="ck_excluded_company_reason"
        ),
        sa.PrimaryKeyConstraint("company_name_norm"),
    )
    op.create_table(
        "posting",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("company_name", sa.Text(), nullable=True),
        sa.Column("company_name_norm", sa.Text(), nullable=True),
        sa.Column("company_biz_no", sa.Text(), nullable=True),
        sa.Column("employee_count", sa.Integer(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("location_text", sa.Text(), nullable=True),
        sa.Column(
            "region_codes",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column("employment_type", sa.Text(), nullable=True),
        sa.Column("career_type", sa.Text(), nullable=True),
        sa.Column("career_min", sa.Integer(), nullable=True),
        sa.Column("career_max", sa.Integer(), nullable=True),
        sa.Column("education_min", sa.Text(), nullable=True),
        sa.Column("salary_text", sa.Text(), nullable=True),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("close_type", sa.Text(), nullable=True),
        sa.Column(
            "keywords",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column(
            "job_codes",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column("provider", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("'true'"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_posting_company_name_norm", "posting", ["company_name_norm"], unique=False)
    op.create_index("ix_posting_first_seen_at", "posting", ["first_seen_at"], unique=False)
    op.create_index(
        "ix_posting_title_trgm",
        "posting",
        ["title"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"title": "gin_trgm_ops"},
    )
    op.create_table(
        "profile",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "query_watermark",
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("keyword", sa.Text(), nullable=False),
        sa.Column("region", sa.Text(), nullable=False),
        sa.Column(
            "last_completed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("source IN ('saramin', 'work24')", name="ck_watermark_source"),
        sa.PrimaryKeyConstraint("source", "keyword", "region"),
    )
    op.create_table(
        "criteria",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("profile_id", sa.BigInteger(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "keywords",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column(
            "regions",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column(
            "hard_filters",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "recommend_threshold", sa.Integer(), server_default=sa.text("'60'"), nullable=False
        ),
        sa.Column("status", sa.Text(), server_default=sa.text("'draft'"), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'approved', 'superseded')", name="ck_criteria_status"
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["profile.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "version"),
    )
    op.create_table(
        "user_mark",
        sa.Column("posting_id", sa.BigInteger(), nullable=False),
        sa.Column("mark", sa.Text(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("mark IN ('interested', 'applied', 'excluded')", name="ck_user_mark"),
        sa.ForeignKeyConstraint(
            ["posting_id"],
            ["posting.id"],
        ),
        sa.PrimaryKeyConstraint("posting_id"),
    )
    op.create_table(
        "collection_run",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("criteria_id", sa.BigInteger(), nullable=False),
        sa.Column("trigger", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'running'"), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("api_calls_used", sa.Integer(), server_default=sa.text("'0'"), nullable=False),
        sa.CheckConstraint(
            "status IN ('running', 'succeeded', 'partial', 'failed')", name="ck_run_status"
        ),
        sa.CheckConstraint("trigger IN ('schedule', 'manual', 'ai')", name="ck_run_trigger"),
        sa.ForeignKeyConstraint(
            ["criteria_id"],
            ["criteria.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "evaluation",
        sa.Column("posting_id", sa.BigInteger(), nullable=False),
        sa.Column("criteria_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column(
            "match_reasons",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column(
            "missing",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column(
            "needs_check",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column("model", sa.Text(), nullable=True),
        sa.Column("prompt_version", sa.Text(), nullable=True),
        sa.Column("attempts", sa.Integer(), server_default=sa.text("'0'"), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'succeeded', 'failed')", name="ck_evaluation_status"
        ),
        sa.CheckConstraint("score BETWEEN 0 AND 100", name="ck_evaluation_score"),
        sa.ForeignKeyConstraint(
            ["criteria_id"],
            ["criteria.id"],
        ),
        sa.ForeignKeyConstraint(
            ["posting_id"],
            ["posting.id"],
        ),
        sa.PrimaryKeyConstraint("posting_id", "criteria_id"),
    )
    op.create_table(
        "explore_keyword",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("criteria_id", sa.BigInteger(), nullable=False),
        sa.Column("keyword", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'proposed'"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('proposed', 'approved', 'rejected')", name="ck_explore_keyword_status"
        ),
        sa.ForeignKeyConstraint(
            ["criteria_id"],
            ["criteria.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "filter_result",
        sa.Column("posting_id", sa.BigInteger(), nullable=False),
        sa.Column("criteria_id", sa.BigInteger(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column(
            "reason_codes",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column(
            "needs_check_codes",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column("rules_version", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["criteria_id"],
            ["criteria.id"],
        ),
        sa.ForeignKeyConstraint(
            ["posting_id"],
            ["posting.id"],
        ),
        sa.PrimaryKeyConstraint("posting_id", "criteria_id"),
    )
    op.create_table(
        "collection_query",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("run_id", sa.BigInteger(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("keyword", sa.Text(), nullable=False),
        sa.Column("region", sa.Text(), nullable=False),
        sa.Column("published_since", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.Text(), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("pages_fetched", sa.Integer(), server_default=sa.text("'0'"), nullable=False),
        sa.Column("total_reported", sa.Integer(), nullable=True),
        sa.Column("items_received", sa.Integer(), server_default=sa.text("'0'"), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.CheckConstraint("source IN ('saramin', 'work24')", name="ck_query_source"),
        sa.CheckConstraint(
            "status IN ('pending', 'completed', 'partial', 'deferred', 'error')",
            name="ck_query_status",
        ),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["collection_run.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "raw_posting",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("source_posting_id", sa.Text(), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("run_id", sa.BigInteger(), nullable=False),
        sa.CheckConstraint("source IN ('saramin', 'work24')", name="ck_raw_source"),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["collection_run.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "source_posting_id"),
    )
    op.create_index("ix_raw_posting_run_id", "raw_posting", ["run_id"], unique=False)
    op.create_table(
        "tool_call_log",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("run_id", sa.BigInteger(), nullable=True),
        sa.Column("tool", sa.Text(), nullable=False),
        sa.Column(
            "input",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "output",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["collection_run.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "posting_source",
        sa.Column("posting_id", sa.BigInteger(), nullable=False),
        sa.Column("raw_posting_id", sa.BigInteger(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.CheckConstraint("source IN ('saramin', 'work24')", name="ck_posting_source"),
        sa.ForeignKeyConstraint(
            ["posting_id"],
            ["posting.id"],
        ),
        sa.ForeignKeyConstraint(
            ["raw_posting_id"],
            ["raw_posting.id"],
        ),
        sa.PrimaryKeyConstraint("posting_id", "raw_posting_id"),
    )
    op.create_table(
        "query_hit",
        sa.Column("collection_query_id", sa.BigInteger(), nullable=False),
        sa.Column("raw_posting_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["collection_query_id"],
            ["collection_query.id"],
        ),
        sa.ForeignKeyConstraint(
            ["raw_posting_id"],
            ["raw_posting.id"],
        ),
        sa.PrimaryKeyConstraint("collection_query_id", "raw_posting_id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("query_hit")
    op.drop_table("posting_source")
    op.drop_table("tool_call_log")
    op.drop_index("ix_raw_posting_run_id", table_name="raw_posting")
    op.drop_table("raw_posting")
    op.drop_table("collection_query")
    op.drop_table("filter_result")
    op.drop_table("explore_keyword")
    op.drop_table("evaluation")
    op.drop_table("collection_run")
    op.drop_table("user_mark")
    op.drop_table("criteria")
    op.drop_table("query_watermark")
    op.drop_table("profile")
    op.drop_index(
        "ix_posting_title_trgm",
        table_name="posting",
        postgresql_using="gin",
        postgresql_ops={"title": "gin_trgm_ops"},
    )
    op.drop_index("ix_posting_first_seen_at", table_name="posting")
    op.drop_index("ix_posting_company_name_norm", table_name="posting")
    op.drop_table("posting")
    op.drop_table("excluded_company")
    op.drop_table("api_usage")
    # ### end Alembic commands ###
