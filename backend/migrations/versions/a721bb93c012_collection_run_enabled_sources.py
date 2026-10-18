"""Record sources enabled for each collection run.

Revision ID: a721bb93c012
Revises: e98f227b8d6e
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "a721bb93c012"
down_revision = "e98f227b8d6e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "collection_run",
        sa.Column(
            "enabled_sources",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::text[]"),
        ),
    )


def downgrade() -> None:
    op.drop_column("collection_run", "enabled_sources")
