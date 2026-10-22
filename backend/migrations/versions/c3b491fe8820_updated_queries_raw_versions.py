"""Separate incremental modes and preserve raw payload versions.

Revision ID: c3b491fe8820
Revises: a721bb93c012
"""

import hashlib
import json
from contextlib import suppress
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "c3b491fe8820"
down_revision = "a721bb93c012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("collection_query", "query_watermark"):
        op.add_column(
            table, sa.Column("mode", sa.Text(), nullable=False, server_default="published")
        )
    op.create_check_constraint(
        "ck_query_mode", "collection_query", "mode IN ('published', 'updated')"
    )
    op.create_check_constraint(
        "ck_watermark_mode", "query_watermark", "mode IN ('published', 'updated')"
    )
    op.drop_constraint("query_watermark_pkey", "query_watermark", type_="primary")
    op.create_primary_key(
        "query_watermark_pkey", "query_watermark", ["source", "keyword", "region", "mode"]
    )
    op.add_column("raw_posting", sa.Column("content_hash", sa.Text(), nullable=True))
    versions = op.create_table(
        "raw_posting_version",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "raw_posting_id", sa.BigInteger(), sa.ForeignKey("raw_posting.id"), nullable=False
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("source_modified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("run_id", sa.BigInteger(), sa.ForeignKey("collection_run.id"), nullable=False),
        sa.UniqueConstraint("raw_posting_id", "version"),
        sa.CheckConstraint("version >= 1", name="ck_raw_version_positive"),
    )
    bind = op.get_bind()
    raw = sa.table(
        "raw_posting",
        sa.column("id", sa.BigInteger()),
        sa.column("source", sa.Text()),
        sa.column("payload", postgresql.JSONB()),
        sa.column("content_hash", sa.Text()),
        sa.column("fetched_at", sa.DateTime(timezone=True)),
        sa.column("run_id", sa.BigInteger()),
    )
    # Freeze canonicalization here: future application changes must not alter backfill.
    # Official Saramin fields=count: read-cnt/views and apply-cnt/applicants are activity.
    for row in bind.execute(sa.select(raw)).mappings():
        ignored = {"read-cnt", "apply-cnt"} if row["source"] == "saramin" else set()
        payload = row["payload"]
        canonical = json.dumps(
            {k: v for k, v in payload.items() if k not in ignored},
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        modified = None
        value = payload.get("modification-timestamp") if row["source"] == "saramin" else None
        if value is not None and not isinstance(value, bool):
            with suppress(ValueError, TypeError, OverflowError, OSError):
                modified = datetime.fromtimestamp(int(value), UTC)
        bind.execute(raw.update().where(raw.c.id == row["id"]).values(content_hash=digest))
        bind.execute(
            versions.insert().values(
                raw_posting_id=row["id"],
                version=1,
                payload=payload,
                content_hash=digest,
                source_modified_at=modified,
                fetched_at=row["fetched_at"],
                run_id=row["run_id"],
            )
        )
    op.alter_column("raw_posting", "content_hash", nullable=False)


def downgrade() -> None:
    op.drop_table("raw_posting_version")
    op.drop_column("raw_posting", "content_hash")
    # Old schema has no edit-mode identity; retain published watermarks verbatim.
    op.execute("DELETE FROM query_watermark WHERE mode = 'updated'")
    op.drop_constraint("query_watermark_pkey", "query_watermark", type_="primary")
    op.create_primary_key(
        "query_watermark_pkey", "query_watermark", ["source", "keyword", "region"]
    )
    op.drop_constraint("ck_watermark_mode", "query_watermark", type_="check")
    op.drop_constraint("ck_query_mode", "collection_query", type_="check")
    op.drop_column("query_watermark", "mode")
    op.drop_column("collection_query", "mode")
