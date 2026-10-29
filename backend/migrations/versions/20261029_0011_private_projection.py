"""Persist private projection evidence through the versioned migration path."""
from alembic import op
import sqlalchemy as sa

revision = "20261029_0011"
down_revision = "20261029_0010"
branch_labels = None
depends_on = None


def upgrade():
    if "private_projection" not in {column["name"] for column in sa.inspect(op.get_bind()).get_columns("submissions")}:
        op.add_column("submissions", sa.Column("private_projection", sa.JSON(), nullable=True))


def downgrade():
    op.drop_column("submissions", "private_projection")
