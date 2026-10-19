"""add assignment revision policy

Revision ID: 20261016_0006
Revises: 20261015_0005
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20261016_0006"
down_revision = "20261015_0005"
branch_labels = None
depends_on = None


def upgrade():
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("assignments")}
    if "revision_policy" not in columns:
        op.add_column("assignments", sa.Column("revision_policy", sa.String(length=32), nullable=False, server_default="VERIFIED_REFERENCE"))


def downgrade():
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("assignments")}
    if "revision_policy" in columns:
        op.drop_column("assignments", "revision_policy")
