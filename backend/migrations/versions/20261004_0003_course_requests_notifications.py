"""Persist course join requests and in-app notifications."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20261004_0003"
down_revision = "20261003_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = set(inspect(bind).get_table_names())
    if "enrollment_requests" not in existing:
        op.create_table(
            "enrollment_requests",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("student_id", sa.String(length=100), sa.ForeignKey("students.student_id"), nullable=False),
            sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
            sa.Column("requested_at", sa.DateTime(), nullable=False),
            sa.Column("responded_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_enrollment_requests_id", "enrollment_requests", ["id"])
        op.create_index("ix_enrollment_requests_student_id", "enrollment_requests", ["student_id"])
        op.create_index("ix_enrollment_requests_course_id", "enrollment_requests", ["course_id"])
        op.create_index("ix_enrollment_requests_status", "enrollment_requests", ["status"])
    if "notifications" not in existing:
        op.create_table(
            "notifications",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("recipient_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("event_type", sa.String(length=50), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("target_url", sa.String(length=500), nullable=True),
            sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_notifications_id", "notifications", ["id"])
        op.create_index("ix_notifications_recipient_user_id", "notifications", ["recipient_user_id"])
        op.create_index("ix_notifications_event_type", "notifications", ["event_type"])
        op.create_index("ix_notifications_is_read", "notifications", ["is_read"])


def downgrade() -> None:
    bind = op.get_bind()
    existing = set(inspect(bind).get_table_names())
    if "notifications" in existing:
        op.drop_table("notifications")
    if "enrollment_requests" in existing:
        op.drop_table("enrollment_requests")
