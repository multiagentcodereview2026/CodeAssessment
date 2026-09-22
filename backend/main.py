import asyncio
import copy
import json
import logging
from uuid import uuid4
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func

import models
from database import (
    Base,
    SessionLocal,
    engine,
    ensure_problem_complexity_columns,
    ensure_submission_assessment_columns,
    get_db,
)
from schemas import (
    LoginRequest,
    AuthUser,
    ProblemListItem,
    ProblemDetail,
    SubmissionRequest,
    SubmissionResponse,
    SubmissionDetails,
    QuickRunRequest,
    QuickRunResponse,
    StudentAnalyticsResponse
)
from docker_runner.executor import execute_code_sandboxed
from agents.complexity import analyze_student_complexity, unavailable_analysis
from workflow.graph import evaluation_graph
from workflow.state import EvaluationState
from instructor_repository import (
    INSTRUCTOR_PROBLEM_IDS,
    assignment_metadata,
    canonical_problem_id,
    load_problem_cases,
    provision_instructor_problems,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("evaluator_backend")


def redact_hidden_execution(execution_result):
    """Keep hidden judge data out of API responses and persisted submissions.

    The execution engine needs the input and expected output to judge a case,
    but students must never receive those values through the submission APIs.
    Public-case diagnostics remain unchanged.
    """
    if not isinstance(execution_result, dict):
        return execution_result

    safe_result = copy.deepcopy(execution_result)
    results = safe_result.get("results")
    if not isinstance(results, list):
        return safe_result

    for case_result in results:
        if isinstance(case_result, dict) and case_result.get("is_hidden"):
            for field in ("input", "expected_output", "actual_output", "stderr"):
                case_result.pop(field, None)

    return safe_result

# Create tables
Base.metadata.create_all(bind=engine)
ensure_problem_complexity_columns()
ensure_submission_assessment_columns()

app = FastAPI(
    title="Explainable Multi-Agent AI Code Evaluator (Production API)",
    description="Full Backend API with LangGraph Multi-Agent Orchestration, Sandboxed Execution, Problem Repository, and Analytics",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def seed_instructor_assignments():
    """Ensure instructor assignments and their private judge data exist."""
    db = SessionLocal()
    try:
        created = provision_instructor_problems(db)
        if created:
            logger.info("Provisioned %s instructor assignments", created)
    finally:
        db.close()

@app.post("/api/auth/login", response_model=AuthUser)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    # Instructor Login (Accepts any password)
    if payload.role == "instructor":
        return AuthUser(id=payload.user_id, name="Prof. Kodacharya", role="instructor", email="instructor@kodacharya.edu")
    
    # Student Login (Accepts any password)
    if payload.role == "student":
        student = db.query(models.Student).filter(models.Student.student_id == payload.user_id).first()
        if not student:
            # Auto-provision any student ID for the demo
            student_name = "Demo Student" if payload.user_id == "demo_student" else payload.user_id
            student = models.Student(student_id=payload.user_id, name=student_name, email=f"{payload.user_id}@codevedha.edu", xp=100, streak_days=1)
            db.add(student)
            db.commit()
            db.refresh(student)
        return AuthUser(id=student.student_id, name=student.name, role="student", email=student.email)

    raise HTTPException(status_code=400, detail="Invalid role")

@app.get("/")
def root():
    return {
        "message": "Explainable Multi-Agent AI Code Assessment Production API is online.",
        "status": "healthy",
        "engine": "LangGraph + Groq"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

# ==========================================
# Problem Repository Endpoints
# ==========================================

@app.get("/api/problems", response_model=List[ProblemListItem])
def list_problems(db: Session = Depends(get_db)):
    """Fetch the DSA practice catalogue, excluding course assignments."""
    problems = (
        db.query(models.Problem)
        .filter(~models.Problem.id.in_(INSTRUCTOR_PROBLEM_IDS))
        .order_by(models.Problem.id)
        .all()
    )
    return [{
        "id": problem.id,
        "title": problem.title,
        "difficulty": problem.difficulty,
        "category": problem.category,
    } for problem in problems]


@app.get("/api/instructor-problems", response_model=List[ProblemListItem])
def list_instructor_problems(db: Session = Depends(get_db)):
    """Fetch course assignments without exposing their hidden cases."""
    problems = (
        db.query(models.Problem)
        .filter(models.Problem.id.in_(INSTRUCTOR_PROBLEM_IDS))
        .all()
    )
    by_id = {problem.id: problem for problem in problems}
    return [{
        "id": problem.id,
        "title": problem.title,
        "difficulty": problem.difficulty,
        "category": problem.category,
        **assignment_metadata(problem.id),
    } for problem_id in INSTRUCTOR_PROBLEM_IDS if (problem := by_id.get(problem_id))]

@app.get("/api/problems/{problem_id}", response_model=ProblemDetail)
def get_problem(problem_id: str, db: Session = Depends(get_db)):
    """Fetch a specific problem with its description, examples, constraints, and starter codes."""
    problem_id = canonical_problem_id(problem_id)
    problem = db.query(models.Problem).filter(models.Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem '{problem_id}' not found.")
    public_cases = load_problem_cases(db, problem, public_only=True)
    return {
        "id": problem.id, "title": problem.title, "difficulty": problem.difficulty,
        "category": problem.category, "description": problem.description,
        "examples": problem.examples, "constraints": problem.constraints,
        "starter_codes": problem.starter_codes, "test_cases": public_cases,
        **assignment_metadata(problem.id),
    }

# ==========================================
# Code Execution & Submission Endpoints
# ==========================================

@app.post("/api/submissions/run", response_model=QuickRunResponse)
async def quick_run_code(payload: QuickRunRequest, db: Session = Depends(get_db)):
    """Executes code against test cases in the sandbox without triggering AI evaluation."""
    test_cases = payload.test_cases
    if payload.problem_id:
        problem_id = canonical_problem_id(payload.problem_id)
        problem = db.query(models.Problem).filter(models.Problem.id == problem_id).first()
        if not problem:
            raise HTTPException(status_code=404, detail="Problem not found")
        test_cases = load_problem_cases(db, problem, public_only=True)
    if not test_cases:
        raise HTTPException(status_code=400, detail="No public test cases are available for this problem")
    res = await execute_code_sandboxed(
        source_code=payload.code,
        language=payload.language,
        test_cases=test_cases
    )
    return res

@app.post("/api/submissions/submit", response_model=SubmissionResponse)
async def submit_and_evaluate_code(
    payload: SubmissionRequest,
    db: Session = Depends(get_db)
):
    """
    Complete Multi-Agent Evaluation:
    1. Look up problem and test cases.
    2. Sandboxed execution and complexity analysis run in parallel.
    3. LangGraph assessment scores correctness from observed cases and
       complexity against a private backend target.
    4. Atomic DB Persistence.
    """
    problem_id = canonical_problem_id(payload.problem_id)
    logger.info(f"Received submission for student '{payload.student_id}' on problem '{problem_id}'")

    # Fetch problem details
    problem = db.query(models.Problem).filter(models.Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    stored_cases = (
        db.query(models.ProblemTestCase)
        .filter(models.ProblemTestCase.problem_id == problem_id)
        .order_by(models.ProblemTestCase.position)
        .all()
    )
    test_cases = []
    if stored_cases:
        test_cases = [
            {
                "id": case.id,
                "input": case.input_data,
                "expected_output": case.expected_output,
                "is_hidden": case.visibility == "HIDDEN",
                "time_limit": case.time_limit_seconds,
                "memory_limit": case.memory_limit_mb,
            }
            for case in stored_cases
        ]
    else:
        tc_raw = problem.test_cases
        if isinstance(tc_raw, str):
            try:
                test_cases = json.loads(tc_raw)
            except Exception:
                test_cases = []
        elif isinstance(tc_raw, list):
            test_cases = tc_raw
    
    # Docker execution decides correctness. Groq only sees the public problem
    # information and source code; it never receives hidden cases or TC/SC
    # targets. Starting both tasks here removes unnecessary sequential delay.
    public_problem = {
        "title": problem.title,
        "statement": problem.description,
        "constraints": problem.constraints,
        "category": problem.category,
        "difficulty": problem.difficulty,
    }
    execution_task = asyncio.create_task(execute_code_sandboxed(
        source_code=payload.code,
        language=payload.language,
        test_cases=test_cases,
        # A final submission must produce an accurate passed/total result.
        # The engine still uses bounded parallelism, so this does not run all
        # containers at once and exhaust the host.
        stop_on_first_failure=False,
    ))
    complexity_task = asyncio.create_task(
        analyze_student_complexity(public_problem, payload.code, payload.language)
    )

    execution_outcome, complexity_outcome = await asyncio.gather(
        execution_task,
        complexity_task,
        return_exceptions=True,
    )
    if isinstance(execution_outcome, Exception):
        logger.error("Sandbox execution failed: %s", execution_outcome)
        raise HTTPException(status_code=502, detail="Code execution service is unavailable")
    exec_result = execution_outcome
    if isinstance(complexity_outcome, Exception):
        logger.warning("Complexity analysis failed: %s", complexity_outcome)
        precomputed_complexity_analysis = unavailable_analysis(
            "The complexity analysis service was unavailable for this submission."
        )
    else:
        precomputed_complexity_analysis = complexity_outcome

    # 2. Build LangGraph State
    initial_state: EvaluationState = {
        "user": {"student_id": payload.student_id, "name": payload.student_id},
        "problem": public_problem,
        "submission": {
            "source_code": payload.code,
            "language": payload.language
        },
        "execution_result": exec_result,
        "validation_result": None,
        "correctness_score": None,
        "correctness_details": None,
        "complexity_score": None,
        "complexity_details": None,
        # This object remains in process only. Do not add it to any prompt,
        # submission JSON, or response schema.
        "complexity_target": {
            "time": problem.target_time_complexity,
            "space": problem.target_space_complexity,
        },
        "precomputed_complexity_analysis": precomputed_complexity_analysis,
        "assessment_flags": {},
        "style_score": None,
        "style_details": None,
        "similarity_score": None,
        "similarity_details": None,
        "overall_score": None,
        "score_breakdown": None,
        "confidence": None,
        "feedback": None,
        "recommendations": None,
        "improved_code": None,
        "learning_analytics": None,
        "projected_score": None,
        "status": "running",
        "errors": []
    }

    # 3. Execute LangGraph Multi-Agent Engine
    final_state = await evaluation_graph.ainvoke(initial_state)
    safe_execution_result = redact_hidden_execution(final_state.get("execution_result"))

    # 4. Save into Database
    submission_id = f"SUB-{uuid4().hex[:8].upper()}"
    
    # Ensure student exists
    student = db.query(models.Student).filter(models.Student.student_id == payload.student_id).first()
    if not student:
        student = models.Student(student_id=payload.student_id, name=payload.student_id)
        db.add(student)
        db.commit()

    new_submission = models.Submission(
        submission_id=submission_id,
        student_id=payload.student_id,
        problem_id=problem_id,
        language=payload.language,
        code=payload.code,
        status="EVALUATED",
        overall_score=final_state.get("overall_score"),
        correctness_score=final_state.get("correctness_score"),
        complexity_score=final_state.get("complexity_score"),
        style_score=final_state.get("style_score"),
        similarity_score=final_state.get("similarity_score"),
        execution_result=safe_execution_result,
        complexity_details=final_state.get("complexity_details"),
        assessment_flags=final_state.get("assessment_flags"),
        feedback=final_state.get("feedback"),
        recommendations=final_state.get("recommendations"),
        improved_code=final_state.get("improved_code"),
        projected_score=final_state.get("projected_score")
    )
    
    db.add(new_submission)
    db.commit()
    db.refresh(new_submission)

    return SubmissionResponse(
        submission_id=new_submission.submission_id,
        student_id=new_submission.student_id,
        problem_id=new_submission.problem_id,
        language=new_submission.language,
        status=new_submission.status,
        overall_score=new_submission.overall_score,
        correctness_score=new_submission.correctness_score,
        complexity_score=new_submission.complexity_score,
        complexity_details=final_state.get("complexity_details"),
        style_score=new_submission.style_score,
        similarity_score=new_submission.similarity_score,
        execution_result=new_submission.execution_result,
        feedback=new_submission.feedback,
        recommendations=new_submission.recommendations,
        improved_code=new_submission.improved_code,
        projected_score=new_submission.projected_score
    )

@app.get("/api/submissions/{submission_id}", response_model=SubmissionDetails)
def get_submission(submission_id: str, db: Session = Depends(get_db)):
    submission = db.query(models.Submission).filter(models.Submission.submission_id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission

@app.get("/api/submissions", response_model=List[SubmissionDetails])
def list_submissions(
    student_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(models.Submission)
    if student_id:
        query = query.filter(models.Submission.student_id == student_id)
    return query.order_by(models.Submission.created_at.desc()).all()

# ==========================================
# Student & Instructor Analytics Endpoints
# ==========================================

@app.get("/api/analytics/student/{student_id}", response_model=StudentAnalyticsResponse)
def get_student_analytics(student_id: str, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    submissions = db.query(models.Submission).filter(models.Submission.student_id == student_id).all()
    
    total_problems = db.query(models.Problem).count() or 5
    unique_solved = len(set(s.problem_id for s in submissions if (s.overall_score or 0) >= 70))

    # Calculate category averages
    avg_correctness = db.query(func.avg(models.Submission.correctness_score)).filter(models.Submission.student_id == student_id).scalar() or 85.0
    avg_complexity = db.query(func.avg(models.Submission.complexity_score)).filter(models.Submission.student_id == student_id).scalar() or 80.0
    avg_style = db.query(func.avg(models.Submission.style_score)).filter(models.Submission.student_id == student_id).scalar() or 85.0
    avg_overall = db.query(func.avg(models.Submission.overall_score)).filter(models.Submission.student_id == student_id).scalar() or 88.5

    return StudentAnalyticsResponse(
        overall_score=round(avg_overall, 1),
        streak_days=student.streak_days,
        xp=student.xp,
        problems_solved=max(unique_solved, 1),
        total_problems=total_problems,
        score_trend=[
            {"date": "Apr 1", "score": 30},
            {"date": "Apr 8", "score": 45},
            {"date": "Apr 15", "score": 42},
            {"date": "Apr 22", "score": 65},
            {"date": "Apr 29", "score": round(avg_overall, 1)}
        ],
        category_breakdown=[
            {"name": "Correctness", "value": round(avg_correctness, 1), "color": "#10b981"},
            {"name": "Time & Space Complexity", "value": round(avg_complexity, 1), "color": "#3b82f6"},
            {"name": "Code Quality & Style", "value": round(avg_style, 1), "color": "#8b5cf6"},
            {"name": "Originality", "value": 85.0, "color": "#ec4899"}
        ],
        weak_topics=["Dynamic Programming", "Graph Traversals", "Bit Manipulation"]
    )

@app.get("/api/instructor/overview")
def get_instructor_overview(db: Session = Depends(get_db)):
    students = db.query(models.Student).all()
    total_submissions = db.query(models.Submission).count()
    avg_class_score = db.query(func.avg(models.Submission.overall_score)).scalar() or 82.4
    
    student_list = []
    for s in students:
        s_subs = db.query(models.Submission).filter(models.Submission.student_id == s.student_id).all()
        s_avg = (sum(sub.overall_score or 0 for sub in s_subs) / len(s_subs)) if s_subs else 82.0
        student_list.append({
            "id": s.student_id,
            "name": f"{s.name} ({s.student_id})",
            "course": "Data Structures & Algorithms",
            "subs": len(s_subs),
            "avg": f"{round(s_avg, 1)}%",
            "grade": "A" if s_avg >= 85 else "B+",
            "status": "Active" if s_avg >= 60 else "At Risk"
        })

    return {
        "total_students": len(students),
        "active_assignments": 6,
        "total_submissions": total_submissions,
        "class_avg_score": f"{round(avg_class_score, 1)}%",
        "students": student_list
    }
