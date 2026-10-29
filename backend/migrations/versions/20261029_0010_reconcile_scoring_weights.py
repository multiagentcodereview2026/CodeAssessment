"""Reconcile databases already stamped 0009 without the optional weight columns."""
from alembic import op
import sqlalchemy as sa

revision = "20261029_0010"
down_revision = "20261029_0009"
branch_labels = None
depends_on = None


def upgrade():
    for table in ("problems", "assignment_problems"):
        if "scoring_weights" not in {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table)}:
            op.add_column(table, sa.Column("scoring_weights", sa.JSON(), nullable=True))


def downgrade():
    # A compatibility repair must not remove columns owned by revision 0009.
    pass
