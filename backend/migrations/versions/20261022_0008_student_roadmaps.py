"""add optional student DSA roadmap enrollment

Revision ID: 20261022_0008
Revises: 20261022_0007
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20261022_0008"
down_revision = "20261022_0007"
branch_labels = None
depends_on = None


def upgrade():
    tables = set(inspect(op.get_bind()).get_table_names())
    if "student_roadmaps" not in tables:
        op.create_table(
            "student_roadmaps",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("student_id", sa.String(length=100), sa.ForeignKey("students.student_id"), nullable=False, unique=True),
            sa.Column("is_enrolled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_student_roadmaps_student_id", "student_roadmaps", ["student_id"])


def downgrade():
    if "student_roadmaps" in set(inspect(op.get_bind()).get_table_names()):
        op.drop_table("student_roadmaps")
