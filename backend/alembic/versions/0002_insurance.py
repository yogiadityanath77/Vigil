"""insurance table — one-to-one logistics tier per person (Slice 5)

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-28 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "insurance",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        # unique person_id enforces one-to-one (one insurance row per person).
        sa.Column(
            "person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("person.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("provider", sa.Text, nullable=False),
        sa.Column("policy_number", sa.Text, nullable=False),
        sa.Column("hospital_preference", sa.Text, nullable=True),
        sa.Column("cashless", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("insurance")
