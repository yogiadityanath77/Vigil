"""medical_fact.last_confirmed_at — per-fact freshness signal (Slice 8)

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-28 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default=now() backfills existing rows; the app sets it explicitly
    # on insert. Keep the default so out-of-band inserts are never null.
    op.add_column(
        "medical_fact",
        sa.Column(
            "last_confirmed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_column("medical_fact", "last_confirmed_at")
