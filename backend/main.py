"""HTTP boundary for authentication, teaching and assessment services."""
import asyncio
import copy
import os
from contextlib import asynccontextmanager
from uuid import uuid4
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import models
from auth import get_current_user, require_student
from database import Base, SessionLocal, engine, get_db
from docker_runner.executor import execute_code_sandboxed
from instructor_repository import canonical_problem_id, load_problem_cases, provision_instructor_problems
from platform_api import router, submission_response
from schemas import QuickRunRequest, SubmissionRequest
from workflow.graph import evaluation_graph


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        provision_instructor_problems(db)
    yield


app = FastAPI(title="CodeVedha Assessment API", lifespan=lifespan)
app.add_middleware(CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","),
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)


@app.get("/health")
@app.get("/")
def health():
    return {"status": "healthy"}


def redact_hidden_execution(execution):
    safe = copy.deepcopy(execution or {})
    for result in safe.get("results", []):
        if result.get("is_hidden"):
            for field in ("input", "expected_output", "actual_output", "stderr", "error_message"):
                result.pop(field, None)
    last = safe.get("last_failed_case")
    if last:
        safe["last_failed_case"] = {key: last.get(key) for key in ("ordinal", "status", "is_hidden")}
    return safe


def get_problem_or_404(db, problem_id):
    problem = db.get(models.Problem, canonical_problem_id(problem_id))
    if not problem:
        raise HTTPException(404, "Problem not found")
    return problem


async def run_checked(code, language, cases):
    if language not in ("python", "c", "cpp", "java"):
        raise HTTPException(422, "Supported languages: Python, C, C++ and Java")
    if not cases:
        raise HTTPException(422, "This problem has no test cases")
    try:
        result = await execute_code_sandboxed(code, language, cases, stop_on_first_failure=False)
    except (ConnectionError, OSError, RuntimeError) as error:
        raise HTTPException(503, "Execution service unavailable. Start the Docker execution engine.") from error
    if any(str(case.get("status", "")).lower() == "system_error" for case in result.get("results", [])):
        raise HTTPException(503, "The execution engine could not evaluate this submission. Please retry.")
    return result


@app.post("/api/submissions/run")
async def run_code(payload: QuickRunRequest, db: Session = Depends(get_db), user=Depends(require_student)):
    cases = load_problem_cases(db, get_problem_or_404(db, payload.problem_id), public_only=True) if payload.problem_id else payload.test_cases
    if cases and len(cases) > 20:
        raise HTTPException(422, "Run at most 20 public cases at once")
    return redact_hidden_execution(await run_checked(payload.code, payload.language, cases))


@app.post("/api/submissions/submit")
async def submit(payload: SubmissionRequest, db: Session = Depends(get_db), user=Depends(require_student)):
    problem = get_problem_or_404(db, payload.problem_id)
    execution = await run_checked(payload.code, payload.language, load_problem_cases(db, problem))
    state = {
        "user": {"student_id": user.username},
        "problem": {"title": problem.title, "statement": problem.description, "constraints": problem.constraints},
        "submission": {"source_code": payload.code, "language": payload.language},
        "execution_result": redact_hidden_execution(execution), "errors": [], "status": "running",
    }
    try:
        result = await asyncio.wait_for(evaluation_graph.ainvoke(state), timeout=120)
    except asyncio.TimeoutError as error:
        raise HTTPException(503, "Assessment timed out. Your editor draft is retained; please retry.") from error
    submission_id = f"SUB-{uuid4().hex[:12]}"
    record = models.Submission(
        submission_id=submission_id, student_id=user.username, problem_id=problem.id,
        language=payload.language, code=payload.code, status="EVALUATED",
        execution_result=redact_hidden_execution(execution),
        **{key: result.get(key) for key in (
            "overall_score", "correctness_score", "complexity_score", "style_score", "similarity_score",
            "feedback", "recommendations", "improved_code", "projected_score",
        )},
    )
    db.add(record)
    db.add(models.AssessmentEvidence(submission_id=submission_id, details={
        key: result.get(key) for key in ("complexity_details", "style_details", "similarity_details", "score_breakdown", "confidence")
    }))
    db.commit()
    db.refresh(record)
    return submission_response(db, record)


@app.get("/api/submissions")
def submissions(db: Session = Depends(get_db), user=Depends(get_current_user)):
    query = db.query(models.Submission)
    if user.role == "student":
        query = query.filter(models.Submission.student_id == user.username)
    return [submission_response(db, row) for row in query.order_by(models.Submission.created_at.desc()).all()]


@app.get("/api/submissions/{submission_id}")
def submission(submission_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    row = db.query(models.Submission).filter_by(submission_id=submission_id).first()
    if not row:
        raise HTTPException(404, "Submission not found")
    if user.role == "student" and row.student_id != user.username:
        raise HTTPException(403, "This submission belongs to another student")
    return submission_response(db, row)
