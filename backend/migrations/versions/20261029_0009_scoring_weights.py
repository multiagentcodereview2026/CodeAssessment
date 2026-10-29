"""Optional question and assignment-question scoring weights; preserve all data."""
from alembic import op
import sqlalchemy as sa
revision = "20261029_0009"
down_revision = "20261022_0008"
branch_labels = None
depends_on = None


def upgrade():
    for table in ("problems", "assignment_problems"):
        if "scoring_weights" not in {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}:
            op.add_column(table, sa.Column("scoring_weights", sa.JSON(), nullable=True))


def downgrade():
    for table in ("assignment_problems", "problems"):
        op.drop_column(table, "scoring_weights")
