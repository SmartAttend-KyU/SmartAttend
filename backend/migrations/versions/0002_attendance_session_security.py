"""Add attendance-session expiry controls and verification-window settings.

Revision ID: 0002_attendance_session_security
Revises: 0001_initial_schema
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_attendance_session_security"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "attendance_sessions",
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "attendance_sessions",
        sa.Column(
            "refresh_interval_seconds",
            sa.Integer(),
            nullable=False,
            server_default="10",
        ),
    )
    op.alter_column(
        "attendance_records",
        "verification_method",
        server_default=sa.text("'qr_totp'"),
    )


def downgrade() -> None:
    op.alter_column(
        "attendance_records",
        "verification_method",
        server_default=sa.text("'rotating_code'"),
    )
    op.drop_column("attendance_sessions", "refresh_interval_seconds")
    op.drop_column("attendance_sessions", "ended_at")
