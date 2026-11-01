"""Operator-only aggregate report: python -m revision_job_report. Never prints code or tests."""
import json
from collections import Counter
from datetime import timedelta

from database import SessionLocal
from models import RevisionJob
from revision_jobs import utcnow


def report(db):
    jobs = db.query(RevisionJob).filter(RevisionJob.created_at >= utcnow() - timedelta(days=1)).all()
    statuses = Counter(job.status for job in jobs)
    failures = Counter(job.failure_type for job in jobs if job.failure_type)
    latencies, tokens, cache_resumes = [], 0, 0
    for job in jobs:
        history = (job.private_snapshot or {}).get("attempt_history") or []
        for item in history:
            metrics = item.get("metrics") or (item.get("alignment") or {}).get("request_metrics") or {}
            if isinstance(metrics.get("latency_ms"), (float, int)):
                latencies.append(metrics["latency_ms"])
            tokens += int((metrics.get("token_usage") or {}).get("total_tokens") or 0)
        cache_resumes += sum(item.get("phase") == "cache_reuse" for item in history)
    return {"window_hours": 24, "jobs": len(jobs), "statuses": dict(statuses), "failure_types": dict(failures),
        "verified_pass_rate": round(statuses.get("passed", 0) / len(jobs), 3) if jobs else None,
        "candidate_attempts": sum(job.candidate_attempts for job in jobs),
        "generation_requests": sum(job.generation_requests for job in jobs),
        "infrastructure_retries": sum(job.infrastructure_retries for job in jobs),
        "cached_candidate_reuses": cache_resumes, "reported_tokens": tokens,
        "average_ai_latency_ms": round(sum(latencies) / len(latencies)) if latencies else None}


if __name__ == "__main__":
    with SessionLocal() as session:
        print(json.dumps(report(session), indent=2))
