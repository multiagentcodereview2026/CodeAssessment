"""Persist the student-facing score audit trail."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20261015_0005"
down_revision = "20261011_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("submissions")}
    if "score_breakdown" not in columns:
        op.add_column("submissions", sa.Column("score_breakdown", sa.JSON(), nullable=True))


def downgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("submissions")}
    if "score_breakdown" in columns:
        op.drop_column("submissions", "score_breakdown")
