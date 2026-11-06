"""add ticket status history

Revision ID: c1b2d3e4f5a6
Revises: e592d3d5403a
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c1b2d3e4f5a6"
down_revision: Union[str, None] = "e592d3d5403a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ticket_status_history",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ticket_id", sa.UUID(), nullable=False),
        sa.Column("from_status", postgresql.ENUM(
            "OPEN", "ASSIGNED", "IN_PROGRESS", "PENDING", "RESOLVED", "CLOSED", "REJECTED",
            name="ticket_status",
            create_type=False,
        ), nullable=True),
        sa.Column("to_status", postgresql.ENUM(
            "OPEN", "ASSIGNED", "IN_PROGRESS", "PENDING", "RESOLVED", "CLOSED", "REJECTED",
            name="ticket_status",
            create_type=False,
        ), nullable=False),
        sa.Column("changed_by", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"]),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("ticket_status_history")
