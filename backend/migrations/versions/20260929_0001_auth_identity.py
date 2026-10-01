"""Bootstrap missing tables and add safe user/student auth linkage.

Existing records are preserved. Legacy student records are linked only when a
student-role user already has the exact same username as the student ID.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision = "20260929_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    from database import Base
    import models  # noqa: F401

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, checkfirst=True)
    inspector = inspect(bind)

    problem_columns = {column["name"] for column in inspector.get_columns("problems")}
    for name, column_type in (
        ("target_time_complexity", sa.String(20)),
        ("target_space_complexity", sa.String(20)),
        ("complexity_source", sa.String(50)),
        ("complexity_confidence", sa.Float()),
        ("complexity_reasoning", sa.Text()),
    ):
        if name not in problem_columns:
            op.add_column("problems", sa.Column(name, column_type, nullable=True))

    submission_columns = {column["name"] for column in inspect(bind).get_columns("submissions")}
    for name in ("complexity_details", "assessment_flags"):
        if name not in submission_columns:
            op.add_column("submissions", sa.Column(name, sa.JSON(), nullable=True))

    if "assignment_id" not in submission_columns:
        with op.batch_alter_table("submissions") as batch:
            batch.add_column(sa.Column("assignment_id", sa.Integer(), nullable=True))
            batch.create_foreign_key(
                "fk_submissions_assignment_id_assignments",
                "assignments",
                ["assignment_id"],
                ["id"],
            )
            batch.create_index("ix_submissions_assignment_id", ["assignment_id"])

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "token_version" not in user_columns:
        op.add_column(
            "users",
            sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"),
        )

    student_columns = {column["name"] for column in inspect(bind).get_columns("students")}
    if "user_id" not in student_columns:
        with op.batch_alter_table("students") as batch:
            batch.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
            batch.create_foreign_key(
                "fk_students_user_id_users", "users", ["user_id"], ["id"]
            )
            batch.create_index("ix_students_user_id", ["user_id"], unique=True)
    else:
        foreign_keys = inspect(bind).get_foreign_keys("students")
        if not any(
            key.get("referred_table") == "users" and key.get("constrained_columns") == ["user_id"]
            for key in foreign_keys
        ):
            with op.batch_alter_table("students") as batch:
                batch.create_foreign_key(
                    "fk_students_user_id_users", "users", ["user_id"], ["id"]
                )

        indexes = inspect(bind).get_indexes("students")
        if not any(index.get("column_names") == ["user_id"] and index.get("unique") for index in indexes):
            with op.batch_alter_table("students") as batch:
                batch.create_index("ix_students_user_id", ["user_id"], unique=True)

    bind.execute(text(
        "UPDATE students AS s SET user_id = u.id "
        "FROM users AS u "
        "WHERE s.user_id IS NULL AND u.role = 'student' "
        "AND lower(u.username) = lower(s.student_id)"
    ))


def downgrade() -> None:
    bind = op.get_bind()
    student_columns = {column["name"] for column in inspect(bind).get_columns("students")}
    if "user_id" in student_columns:
        with op.batch_alter_table("students") as batch:
            batch.drop_index("ix_students_user_id")
            batch.drop_constraint("fk_students_user_id_users", type_="foreignkey")
            batch.drop_column("user_id")

    user_columns = {column["name"] for column in inspect(bind).get_columns("users")}
    if "token_version" in user_columns:
        op.drop_column("users", "token_version")
