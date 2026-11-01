"""Durable revision queue, private cache and independent retry counters."""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone
from uuid import uuid4

revision = "20261101_0012"
down_revision = "20261029_0011"
branch_labels = None
depends_on = None


def upgrade():
    if "revision_jobs" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table("revision_jobs",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("submission_id", sa.String(100), nullable=False),
        sa.Column("student_id", sa.String(100), nullable=False),
        sa.Column("problem_id", sa.String(100), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("phase", sa.String(30)),
        sa.Column("candidate_attempts", sa.Integer(), nullable=False),
        sa.Column("generation_requests", sa.Integer(), nullable=False),
        sa.Column("infrastructure_retries", sa.Integer(), nullable=False),
        sa.Column("failure_type", sa.String(60)),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.Column("current_score", sa.Float()), sa.Column("projected_score", sa.Float()),
        sa.Column("cache_key", sa.JSON()), sa.Column("revision_snapshot", sa.JSON()),
        sa.Column("private_snapshot", sa.JSON()),
        sa.Column("retry_available_at", sa.DateTime()), sa.Column("lease_until", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False))
    for name in ("submission_id", "student_id", "status", "retry_available_at"):
        op.create_index("ix_revision_jobs_" + name, "revision_jobs", [name])
    connection = op.get_bind()
    metadata = sa.MetaData()
    submissions = sa.Table("submissions", metadata, autoload_with=connection)
    jobs = sa.Table("revision_jobs", metadata, autoload_with=connection)
    seen_ids = set()
    for row in connection.execute(sa.select(submissions.c.submission_id, submissions.c.student_id,
            submissions.c.problem_id, submissions.c.overall_score, submissions.c.improved_code,
            submissions.c.private_projection, submissions.c.created_at).where(submissions.c.improved_code.is_not(None))).mappings():
        guide = row["improved_code"]
        if not isinstance(guide, dict) or not guide.get("projection_request_id"):
            continue
        private = row["private_projection"]
        if guide["projection_request_id"] in seen_ids or len(str(guide["projection_request_id"])) > 40:
            # Older submission copies can share a request ID. Preserve each
            # private snapshot under a fresh ID rather than dropping data or
            # letting one learner's job overwrite another learner's job.
            old_id = guide["projection_request_id"]
            guide = {**guide, "projection_request_id": uuid4().hex}
            if isinstance(private, dict) and private.get("request_id") == old_id:
                private = {**private, "request_id": guide["projection_request_id"]}
            connection.execute(submissions.update().where(submissions.c.submission_id == row["submission_id"]).values(
                improved_code=guide, private_projection=private))
        seen_ids.add(guide["projection_request_id"])
        projection = guide.get("score_projection") or {}
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        def timestamp(value):
            return datetime.fromisoformat(value).astimezone(timezone.utc).replace(tzinfo=None) if value else None
        connection.execute(jobs.insert().values(id=guide["projection_request_id"], submission_id=row["submission_id"],
            student_id=row["student_id"], problem_id=row["problem_id"], status=projection.get("job_status", "unavailable"),
            phase=projection.get("phase"), candidate_attempts=int(projection.get("attempts") or 0),
            generation_requests=0, infrastructure_retries=0, verified=projection.get("verified") is True,
            current_score=row["overall_score"], projected_score=projection.get("projected_score"),
            revision_snapshot=guide, private_snapshot=private,
            retry_available_at=timestamp(projection.get("next_retry_at")), lease_until=timestamp(guide.get("worker_lease_until")),
            created_at=row["created_at"] or now, updated_at=now))


def downgrade():
    op.drop_table("revision_jobs")
