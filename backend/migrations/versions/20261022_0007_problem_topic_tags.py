"""add reusable topic tags to problems

Revision ID: 20261022_0007
Revises: 20261016_0006
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20261022_0007"
down_revision = "20261016_0006"
branch_labels = None
depends_on = None


def upgrade():
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("problems")}
    if "topic_tags" not in columns:
        op.add_column("problems", sa.Column("topic_tags", sa.JSON(), nullable=True))


def downgrade():
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("problems")}
    if "topic_tags" in columns:
        op.drop_column("problems", "topic_tags")
