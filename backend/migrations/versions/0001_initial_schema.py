"""Create the initial SmartAttend database schema.

Revision ID: 0001_initial_schema
Revises:
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("university_id", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("university_id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_university_id", "users", ["university_id"], unique=False)
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    op.create_index("ix_users_role", "users", ["role"], unique=False)

    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("lecturer_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["lecturer_id"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_courses_code", "courses", ["code"], unique=False)
    op.create_index("ix_courses_lecturer_id", "courses", ["lecturer_id"], unique=False)

    op.create_table(
        "course_enrolments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("course_id", "student_id", name="uq_course_enrolment"),
    )
    op.create_index("ix_course_enrolments_student_id", "course_enrolments", ["student_id"], unique=False)

    op.create_table(
        "attendance_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("lecturer_id", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lecturer_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_attendance_sessions_course_id", "attendance_sessions", ["course_id"], unique=False)
    op.create_index("ix_attendance_sessions_lecturer_id", "attendance_sessions", ["lecturer_id"], unique=False)

    op.create_table(
        "attendance_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verification_method", sa.String(length=32), nullable=False, server_default="rotating_code"),
        sa.ForeignKeyConstraint(["session_id"], ["attendance_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("session_id", "student_id", name="uq_attendance_session_student"),
    )
    op.create_index("ix_attendance_records_student_id", "attendance_records", ["student_id"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"], unique=False)
    op.create_index("ix_audit_logs_event_type", "audit_logs", ["event_type"], unique=False)
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_event_type", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_attendance_records_student_id", table_name="attendance_records")
    op.drop_table("attendance_records")
    op.drop_index("ix_attendance_sessions_lecturer_id", table_name="attendance_sessions")
    op.drop_index("ix_attendance_sessions_course_id", table_name="attendance_sessions")
    op.drop_table("attendance_sessions")
    op.drop_index("ix_course_enrolments_student_id", table_name="course_enrolments")
    op.drop_table("course_enrolments")
    op.drop_index("ix_courses_lecturer_id", table_name="courses")
    op.drop_index("ix_courses_code", table_name="courses")
    op.drop_table("courses")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_university_id", table_name="users")
    op.drop_table("users")
