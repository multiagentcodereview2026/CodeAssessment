"""add assignment revision policy

Revision ID: 20261016_0006
Revises: 20261015_0005
"""
from alembic import op
import sqlalchemy as sa

revision = "20261016_0006"
down_revision = "20261015_0005"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("assignments", sa.Column("revision_policy", sa.String(length=32), nullable=False, server_default="VERIFIED_REFERENCE"))


def downgrade():
    op.drop_column("assignments", "revision_policy")
