"""Keep instructor-created questions out of general practice by default."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision = "20261011_0004"
down_revision = "20261004_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns("problems")}
    if "is_public_practice" not in columns:
        op.add_column("problems", sa.Column("is_public_practice", sa.Boolean(), nullable=False, server_default=sa.true()))
        op.create_index("ix_problems_is_public_practice", "problems", ["is_public_practice"])
    # Existing questions attached to assignments are course material. Master
    # problems can still be deliberately reused by setting this flag true.
    bind.execute(text(
        "UPDATE problems SET is_public_practice = false "
        "WHERE id IN (SELECT problem_id FROM assignment_problems) "
        "AND id LIKE 'instructor-%'"
    ))


def downgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns("problems")}
    if "is_public_practice" in columns:
        op.drop_index("ix_problems_is_public_practice", table_name="problems")
        op.drop_column("problems", "is_public_practice")
