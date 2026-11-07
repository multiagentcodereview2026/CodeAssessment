import asyncio
from datetime import datetime, timezone

import pytest

import main as app
import models
from revision_jobs import day_start, failure_policy, safe_unverified_guide
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from database import Base
from scoring.rubric import student_rubric_score


@pytest.fixture
def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_failure_budgets_and_local_day_boundary():
    assert failure_policy("rate_limit", 2, 1, "minute") == "cooldown"
    assert failure_policy("rate_limit", 0, 0, "daily") == "unavailable"
    assert failure_policy("rate_limit", 0, 0, "unknown") == "unavailable"
    assert failure_policy("judge_unavailable", 0, 0) == "retry_infrastructure"
    assert failure_policy("judge_unavailable", 0, 1) == "unavailable"
    assert failure_policy("no_improvement", 1, 1) == "retry_candidate"
    assert failure_policy("no_improvement", 2, 0) == "failed"


def test_three_guides_each_and_five_distinct_problems_daily(db_session):
    from revision_jobs import guide_request_limit_reason, utcnow
    from agents.revision_contract import CONTRACT_VERSION
    for problem in range(5):
        for attempt in range(2):
            db_session.add(models.RevisionJob(
                id=f"quota-{problem}-{attempt}", submission_id=f"submission-{problem}",
                student_id="learner", problem_id=f"problem-{problem}", status="passed",
                revision_snapshot={"guidance_version": CONTRACT_VERSION}, created_at=utcnow(),
            ))
    db_session.commit()
    check = lambda problem: guide_request_limit_reason(db_session, "learner", problem, CONTRACT_VERSION)
    assert check("problem-0") is None  # Third request remains available.
    assert "5 different problems" in check("problem-5")
    db_session.add(models.RevisionJob(
        id="third", submission_id="submission-0", student_id="learner",
        problem_id="problem-0", status="passed",
        revision_snapshot={"guidance_version": CONTRACT_VERSION}, created_at=utcnow(),
    ))
    db_session.commit()
    assert "3 guide requests" in check("problem-0")
    assert guide_request_limit_reason(db_session, "another-learner", "problem-5", CONTRACT_VERSION) is None


def test_usage_reset_preserves_history_and_counts_new_jobs(db_session):
    from revision_jobs import guide_request_limit_reason, utcnow
    from agents.revision_contract import CONTRACT_VERSION
    for number in range(3):
        db_session.add(models.RevisionJob(
            id=f"old-{number}", submission_id="old", student_id="learner",
            problem_id="problem", status="passed",
            revision_snapshot={"guidance_version": CONTRACT_VERSION, "usage_reset_at": utcnow().isoformat()},
            created_at=utcnow(),
        ))
    db_session.commit()
    assert guide_request_limit_reason(db_session, "learner", "problem", CONTRACT_VERSION) is None
    for number in range(3):
        db_session.add(models.RevisionJob(
            id=f"new-{number}", submission_id="new", student_id="learner",
            problem_id="problem", status="passed",
            revision_snapshot={"guidance_version": CONTRACT_VERSION}, created_at=utcnow(),
        ))
    db_session.commit()
    assert "3 guide requests" in guide_request_limit_reason(db_session, "learner", "problem", CONTRACT_VERSION)
    assert db_session.query(models.RevisionJob).count() == 6
    assert day_start(datetime(2026, 11, 1, 19, tzinfo=timezone.utc)) == datetime(2026, 11, 1, 18, 30)


def test_only_jobs_blocked_by_retired_gate_offer_corrected_recheck(monkeypatch):
    monkeypatch.setattr(app.settings, "SCORE_PROJECTION_ENABLED", True)
    monkeypatch.setattr(app.settings, "SCORE_PROJECTION_STYLE_TOLERANCE", 1.0)
    guide = {"revision_policy": "GUIDED_STEPS", "guidance_version": app.CONTRACT_VERSION,
        "guide_validated": True, "guidance_supported": True, "steps": [{"id": "one"}], "guided_steps": ["Saved action"],
        "score_projection": {"job_status": "failed", "pending": False, "failure_type": "component_regression",
            "retry_allowed": False, "projected_score": None}}
    public = app.public_guided_revision(guide)
    assert public["score_projection"]["retry_allowed"] is True
    assert public["score_projection"]["policy_update_available"] is True
    assert public["score_projection"]["projected_score"] is None
    assert guide["score_projection"]["retry_allowed"] is False  # serialization cannot mutate saved state
    current = {**guide, "score_projection": {**guide["score_projection"], "release_policy": {"version": app.RELEASE_POLICY_VERSION}}}
    assert app.public_guided_revision(current)["score_projection"]["retry_allowed"] is False


@pytest.mark.parametrize("failure", ["minute", "daily", "judge"])
def test_infrastructure_failure_preserves_budget_and_resumes_cached_stage(db_session, monkeypatch, failure):
    x, baseline = student_rubric_score(100, {"time_score": 12.5, "space_score": 25}, 90)
    y, candidate = student_rubric_score(100, {"time_score": 25, "space_score": 25}, 90)
    student = models.Student(student_id="infra-learner", name="Learner")
    problem = models.Problem(id="infra-problem", title="Test", description="Public", test_cases=[], examples=[], constraints=[], starter_codes={})
    submission = models.Submission(submission_id="infra-sub", student_id=student.student_id, problem_id=problem.id,
        code="print(0)", language="python", overall_score=x, score_breakdown=baseline,
        feedback={"mentor_feedback": "PRIVATE-INPUT SECRET"},
        assessment_flags={"analyzer_version": app.analyzer_fingerprint(), "judge_context": "context"},
        improved_code={"revision_policy": "GUIDED_STEPS", "guidance_version": app.CONTRACT_VERSION,
            "projection_request_id": "infra-job", "stage": "OPTIMIZE", "score_projection": app.projection_pending(x)})
    db_session.add_all([student, problem, submission])
    db_session.commit()
    monkeypatch.setattr(app, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(app, "projection_context_fingerprint", lambda *_: "context")
    monkeypatch.setattr(app, "load_problem_cases", lambda *_args, **_kw: [{"input": "PRIVATE-INPUT", "expected_output": "SECRET"}])
    monkeypatch.setattr(app.settings, "GROQ_API_KEY", "mock-only")
    monkeypatch.setattr(app, "llm", object())
    monkeypatch.setattr(app, "schedule_projection_retry", lambda *_: None)
    calls = {"generate": 0, "align": 0, "judge": 0}
    step = {"id": "one", "area": "correctness", "target": {"symbol": "print", "operation": "output value"},
            "change": "Replace the output value with the computed result.", "risk": "Preserve the existing output format.", "risk_level": "low", "expected_complexity": {}}
    async def generate(state, stage):
        calls["generate"] += 1
        assert "PRIVATE-INPUT" not in str(state) and "SECRET" not in str(state)
        if failure != "judge" and calls["generate"] == 1:
            return {"analysis_source": "fallback", "provider_error": "rate_limit", "quota_scope": failure, "retry_after": 60}
        return {"analysis_source": "groq", "guide": {"steps": [step], "guided_steps": [step["change"]]}, "candidate_code": "print(1)"}
    async def align(*args):
        calls["align"] += 1
        return {"status": "aligned", "evidence": ["Local output correction"]}
    async def judge(**kwargs):
        calls["judge"] += 1
        if failure == "judge" and calls["judge"] == 1:
            return {"status": "judge_unavailable", "available": False, "verified": False}
        return {"available": True, "verified": True, "projected_score": y, "score_breakdown": candidate}
    monkeypatch.setattr(app, "combined_stage_revision_node", generate)
    monkeypatch.setattr(app, "review_stage_alignment", align)
    monkeypatch.setattr(app, "score_revision_stage", judge)
    asyncio.run(app.verify_projection_in_background("infra-sub", "OPTIMIZE"))
    saved = db_session.query(models.Submission).filter_by(submission_id="infra-sub").one()
    assert saved.projected_score["attempts"] == 0
    assert saved.projected_score["pending"] is (failure != "daily")
    job = db_session.get(models.RevisionJob, "infra-job")
    assert job.candidate_attempts == 0 and job.generation_requests == 1
    assert saved.overall_score == x
    if failure == "daily":
        assert "next_retry_at" not in saved.projected_score
        return
    # A fresh worker/session can resume solely from the persisted state.
    revision = dict(saved.improved_code)
    revision["score_projection"] = {**revision["score_projection"], "next_retry_at": None}
    saved.improved_code = revision
    db_session.commit()
    asyncio.run(app.verify_projection_in_background("infra-sub", "OPTIMIZE"))
    saved = db_session.query(models.Submission).filter_by(submission_id="infra-sub").one()
    assert saved.projected_score["job_status"] == "passed" and saved.projected_score["attempts"] == 1
    assert calls["generate"] == (1 if failure == "judge" else 2)
    assert calls["align"] == 1  # never repeat an accepted alignment after a judge failure
    assert saved.overall_score == x
    owner = db_session.query(models.Student).filter_by(student_id="infra-learner").one()
    public = app.get_revision_job("infra-sub", "infra-job", db_session, owner)
    assert "PRIVATE-INPUT" not in str(public) and "print(1)" not in str(public)


def test_valid_revision_remains_visible_when_candidate_projection_fails(monkeypatch):
    monkeypatch.setattr(app.settings, "SCORE_PROJECTION_ENABLED", True)
    guide = {"revision_policy": "GUIDED_STEPS", "guidance_version": app.CONTRACT_VERSION,
        "guide_validated": True, "guidance_supported": True, "alignment_confirmed": False, "steps": [{"risk_level": "medium"}],
        "guided_steps": ["Local change"], "score_projection": {"job_status": "failed", "pending": False, "projected_score": 99}}
    public = app.public_guided_revision(guide)
    assert public["guided_steps"] == ["Local change"]
    assert public["verification"]["verified"] is False
    assert public["score_projection"]["projected_score"] is None
    for change in ({"guide_validated": False}, {"guidance_supported": False}, {"steps": []}):
        assert not safe_unverified_guide({**guide, **change})
        assert "guided_steps" not in app.public_guided_revision({**guide, **change})
    # A provider outage during candidate alignment is not evidence that the
    # independently schema/target-validated guide is unsupported.
    without_review = {key: value for key, value in guide.items() if key != "guidance_supported"}
    assert "guided_steps" in app.public_guided_revision(without_review)


def test_daily_quota_counts_new_jobs_not_repeat_clicks(db_session, monkeypatch):
    student = models.Student(student_id="quota-learner", name="Learner")
    problem = models.Problem(id="quota-problem", title="Test", description="Public", test_cases=[], examples=[], constraints=[], starter_codes={})
    submission = models.Submission(submission_id="quota-sub", student_id=student.student_id, problem_id=problem.id,
        code="print(0)", language="python", overall_score=80)
    db_session.add_all([student, problem, submission])
    db_session.commit()
    monkeypatch.setattr(app, "guided_revision_stage", lambda *_: "OPTIMIZE_LOCAL")
    monkeypatch.setattr(app, "previous_guided_revision_context", lambda *_: None)
    monkeypatch.setattr(app, "launch_projection_verification", lambda *_: None)
    for number in range(3):
        response = asyncio.run(app.regenerate_submission_revision("quota-sub", db_session, student))
        again = asyncio.run(app.regenerate_submission_revision("quota-sub", db_session, student))
        assert again["job_id"] == response["job_id"]
        assert db_session.query(models.RevisionJob).count() == number + 1
        revision = dict(submission.improved_code)
        revision["score_projection"] = {"pending": False, "attempts": 2, "job_status": "failed"}
        submission.improved_code = revision
        db_session.commit()
    with pytest.raises(app.HTTPException) as limit:
        asyncio.run(app.regenerate_submission_revision("quota-sub", db_session, student))
    assert limit.value.status_code == 429
    assert db_session.query(models.RevisionJob).count() == 3
    first_job = db_session.query(models.RevisionJob).order_by(models.RevisionJob.created_at).first()
    assert app.get_revision_job("quota-sub", first_job.id, db_session, student)["job_id"] == first_job.id


def test_second_bad_patch_keeps_first_supported_guide(db_session, monkeypatch):
    from agents import revision as revision_agent
    score, breakdown = student_rubric_score(100, {"time_score": 12.5, "space_score": 25}, 90)
    student = models.Student(student_id="retain-student", name="Learner")
    problem = models.Problem(id="retain-problem", title="Test", description="Public", test_cases=[], examples=[], constraints=[], starter_codes={})
    sub = models.Submission(submission_id="retain-sub", student_id=student.student_id, problem_id=problem.id,
        language="python", code="# preserved\nprint(0)\n", overall_score=score, score_breakdown=breakdown,
        assessment_flags={"analyzer_version": app.analyzer_fingerprint(), "judge_context": "context"},
        improved_code={"revision_policy": "GUIDED_STEPS", "guidance_version": app.CONTRACT_VERSION, "stage": "OPTIMIZE",
            "projection_request_id": "retain-job", "score_projection": app.projection_pending(score)})
    db_session.add_all([student, problem, sub])
    db_session.commit()
    monkeypatch.setattr(app, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(app, "projection_context_fingerprint", lambda *_: "context")
    monkeypatch.setattr(app, "load_problem_cases", lambda *_args, **_kw: [])
    monkeypatch.setattr(app.settings, "GROQ_API_KEY", "mock-only")
    monkeypatch.setattr(app, "llm", object())
    monkeypatch.setattr(app, "schedule_projection_retry", lambda *_: None)
    calls = []
    action = "Replace the output value with the computed result."
    async def generate(prompt, payload, schema, fallback, **kwargs):
        calls.append(payload)
        symbol = "print" if len(calls) == 1 else "invented_target"
        step = {"id": "one", "area": "correctness", "target": {"symbol": symbol, "operation": "output value"},
                "change": action, "expected_complexity": {}, "risk": "Keep the input and output contract."}
        return {"analysis_source": "groq", "source_hash": payload["source_context"]["source_hash"],
            "guide": {"steps": [step]}, "patches": [{"step_id": "one", "old": "print(0)", "new": "print(1)"}]}
    async def align(*_):
        return {"status": "unavailable", "checks": {"guidance_supported": True, "all_changes_explained": False}, "evidence": ["Candidate includes an extra change."]}
    monkeypatch.setattr(revision_agent, "invoke_agent", generate)
    monkeypatch.setattr(app, "review_stage_alignment", align)
    monkeypatch.setattr(app, "score_revision_stage", lambda **_: pytest.fail("Rejected patches must not reach Docker"))
    asyncio.run(app.verify_projection_in_background("retain-sub", "OPTIMIZE"))
    saved = db_session.query(models.Submission).filter_by(submission_id="retain-sub").one()
    assert saved.private_projection["last_valid_guide"]["guided_steps"] == [action]
    revision = dict(saved.improved_code)
    revision["score_projection"] = {**revision["score_projection"], "next_retry_at": None}
    saved.improved_code = revision
    db_session.commit()
    asyncio.run(app.verify_projection_in_background("retain-sub", "OPTIMIZE"))
    saved = db_session.query(models.Submission).filter_by(submission_id="retain-sub").one()
    public = app.public_guided_revision(saved.improved_code)
    assert public["guided_steps"] == [action] and public["steps"][0]["target"]["symbol"] == "print"
    assert public["score_projection"]["projected_score"] is None
    assert saved.projected_score["attempts"] == 2 and saved.overall_score == score
    assert len(calls) == 2 and "print(1)" not in str(public)
