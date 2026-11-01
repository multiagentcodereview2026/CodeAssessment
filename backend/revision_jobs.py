"""Durable revision outbox and bounded failure policy. No learner code is public here."""
import copy
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from uuid import uuid4

from sqlalchemy import event
from sqlalchemy.orm import Session

import models


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def day_start(now=None):
    local = (now or datetime.now(timezone.utc)).astimezone(ZoneInfo("Asia/Kolkata"))
    return local.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc).replace(tzinfo=None)


def safe_unverified_guide(guide):
    """Guide validity is independent of whether its private candidate passed."""
    return bool(guide.get("guide_validated") and guide.get("steps")
                and guide.get("guidance_supported") is not False)


def remember_supported_guide(current, previous=None):
    if safe_unverified_guide(current) and current.get("guidance_supported") is True:
        return copy.deepcopy({key: value for key, value in current.items() if key not in {
            "score_projection", "projection_request_id", "worker_lease_until", "last_candidate_result"}})
    return previous


def retained_revision_guide(current, previous):
    """A bad second draft must not erase supported guidance from the first."""
    if (not safe_unverified_guide(current) or current.get("guidance_supported") is not True) and safe_unverified_guide(previous or {}):
        return {**copy.deepcopy(previous), "last_candidate_result": current.get("last_candidate_result")}
    return current


def failure_policy(kind, candidate_attempts, infrastructure_retries, quota_scope=None):
    """Candidate budget is independent of API and sandbox availability."""
    if kind == "rate_limit":
        return "cooldown" if quota_scope == "minute" else "unavailable"
    if kind in {"judge_unavailable", "provider_timeout", "provider_unavailable", "unavailable"}:
        return "retry_infrastructure" if infrastructure_retries < 1 else "unavailable"
    if kind in {"bad_request", "authentication", "daily_limit", "baseline_outdated", "context_changed"}:
        return "unavailable"
    return "retry_candidate" if candidate_attempts < 2 else "failed"


@event.listens_for(Session, "before_flush")
def persist_revision_outbox(session, flush_context, instances):
    """Persist snapshots in the same transaction as the submission compatibility fields.

    The outbox survives worker crashes and also preserves previous job IDs. Only
    public_guided_revision may serialize a snapshot to a learner.
    """
    for submission in list(session.new) + list(session.dirty):
        if not isinstance(submission, models.Submission):
            continue
        revision = submission.improved_code
        if not isinstance(revision, dict) or not revision.get("projection_request_id"):
            continue
        job_id = revision["projection_request_id"]
        job = next((item for item in session.new if isinstance(item, models.RevisionJob) and item.id == job_id), None)
        job = job or session.get(models.RevisionJob, job_id)
        if job is not None and (job.submission_id != submission.submission_id or job.student_id != submission.student_id):
            job_id = uuid4().hex
            revision = {**revision, "projection_request_id": job_id}
            submission.improved_code = revision
            private = submission.private_projection
            if isinstance(private, dict) and private.get("request_id"):
                submission.private_projection = {**private, "request_id": job_id}
            job = None
        if job is None:
            job = models.RevisionJob(id=job_id, submission_id=submission.submission_id,
                student_id=submission.student_id, problem_id=submission.problem_id, created_at=utcnow())
            session.add(job)
        projection = revision.get("score_projection") or {}
        private = submission.private_projection or {}
        job.status = projection.get("job_status", "unavailable")
        job.phase = projection.get("phase")
        job.candidate_attempts = int(projection.get("attempts") or 0)
        job.generation_requests = int(projection.get("generation_requests") or 0)
        job.infrastructure_retries = int(projection.get("infrastructure_retries") or 0)
        job.failure_type = projection.get("failure_type") or projection.get("status")
        job.verified = projection.get("verified") is True
        job.current_score, job.projected_score = submission.overall_score, projection.get("projected_score")
        job.revision_snapshot = copy.deepcopy(revision)
        job.private_snapshot = copy.deepcopy(private)
        job.cache_key = private.get("job_context")
        job.updated_at = utcnow()
        retry_at = projection.get("next_retry_at")
        job.retry_available_at = datetime.fromisoformat(retry_at).astimezone(timezone.utc).replace(tzinfo=None) if retry_at else None
        lease = revision.get("worker_lease_until")
        job.lease_until = datetime.fromisoformat(lease).astimezone(timezone.utc).replace(tzinfo=None) if lease else None
