"""Allow complete Big-O expressions in problem benchmark fields.

Revision ID: 20261003_0002
Revises: 20260929_0001
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision = "20261003_0002"
down_revision = "20260929_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    columns = {column["name"]: column for column in inspect(bind).get_columns("problems")}
    for name in ("target_time_complexity", "target_space_complexity"):
        column = columns.get(name)
        if column is None:
            continue
        length = getattr(column["type"], "length", None)
        if length is not None and length < 200:
            op.alter_column(
                "problems",
                name,
                existing_type=sa.String(length),
                type_=sa.String(200),
                existing_nullable=True,
            )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    too_long = bind.execute(text(
        "SELECT 1 FROM problems WHERE "
        "length(target_time_complexity) > 20 OR length(target_space_complexity) > 20 LIMIT 1"
    )).first()
    if too_long:
        raise RuntimeError("Cannot shrink complexity targets: stored expressions exceed 20 characters")
    for name in ("target_time_complexity", "target_space_complexity"):
        op.alter_column(
            "problems",
            name,
            existing_type=sa.String(200),
            type_=sa.String(20),
            existing_nullable=True,
        )
