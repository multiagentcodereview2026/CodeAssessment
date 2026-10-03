import asyncio
import copy
import json
import logging
from datetime import datetime
from uuid import uuid4
from typing import Any, List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy import or_

import models
from auth import (
    create_access_token,
    get_current_user,
    hash_password,
    require_instructor,
    require_student,
    verify_password,
)
from database import (
    SessionLocal,
    get_db,
)
from schemas import (
    LoginRequest,
    RegisterRequest,
    AuthUser,
    StudentCreateByInstructor,
    ProblemListItem,
    ProblemDetail,
    SubmissionRequest,
    SubmissionResponse,
    SubmissionDetails,
    QuickRunRequest,
    QuickRunResponse,
    StudentAnalyticsResponse,
    # Instructor schemas
    CourseCreate,
    CourseResponse,
    CourseUpdate,
    CourseWithStats,
    EnrollmentCreate,
    EnrollmentResponse,
    StudentLookupItem,
    StudentCourseResponse,
    StudentAssignmentResponse,
    AssignmentCreate,
    AssignmentUpdate,
    AssignmentResponse,
    AssignmentWithStats,
    InstructorOverview,
    StudentRosterItem, InstructorStudentProgressResponse,
    utc_isoformat,
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


def get_current_instructor(
    current_user: models.User = Depends(require_instructor),
    db: Session = Depends(get_db),
) -> models.Instructor:
    instructor = db.query(models.Instructor).filter(
        models.Instructor.user_id == current_user.id
    ).first()
    if instructor is None:
        raise HTTPException(status_code=403, detail="Instructor profile is not configured")
    return instructor


def get_current_student(
    current_user: models.User = Depends(require_student),
    db: Session = Depends(get_db),
) -> models.Student:
    student = db.query(models.Student).filter(
        models.Student.user_id == current_user.id
    ).first()
    if student is None:
        raise HTTPException(status_code=403, detail="Student profile is not configured")
    return student


def get_owned_course(db: Session, instructor_id: int, course_id: int) -> models.Course:
    course = db.query(models.Course).filter(
        models.Course.id == course_id,
        models.Course.instructor_id == instructor_id,
    ).first()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


def get_owned_assignment(db: Session, instructor_id: int, assignment_id: int) -> models.Assignment:
    assignment = db.query(models.Assignment).join(models.Course).filter(
        models.Assignment.id == assignment_id,
        models.Course.instructor_id == instructor_id,
    ).first()
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


def get_student_assignment_for_problem(
    db: Session,
    student_id: str,
    assignment_id: int,
    problem_id: str,
) -> models.Assignment:
    assignment = db.query(models.Assignment).join(models.Course).filter(
        models.Assignment.id == assignment_id,
        models.Course.is_active == True,
        models.Assignment.status == "ACTIVE",
    ).first()
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment is not available")

    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.student_id == student_id,
        models.Enrollment.course_id == assignment.course_id,
        models.Enrollment.is_active == True,
    ).first()
    if enrollment is None:
        raise HTTPException(status_code=403, detail="Active course enrollment is required")

    assigned_problem = db.query(models.AssignmentProblem.id).filter(
        models.AssignmentProblem.assignment_id == assignment.id,
        models.AssignmentProblem.problem_id == problem_id,
    ).first()
    if assigned_problem is None:
        raise HTTPException(status_code=403, detail="Problem is not part of this assignment")
    return assignment


def latest_assessed_attempts(
    submissions: List[models.Submission],
    *,
    preserve_assignment: bool = True,
) -> List[models.Submission]:
    latest: dict[tuple[Optional[int], str, str], models.Submission] = {}
    for submission in submissions:
        if submission.status != "EVALUATED" or submission.overall_score is None:
            continue
        assignment_scope = submission.assignment_id if preserve_assignment else None
        key = (assignment_scope, submission.student_id, submission.problem_id)
        current = latest.get(key)
        current_key = (current.created_at or datetime.min, current.id or 0) if current else None
        candidate_key = (submission.created_at or datetime.min, submission.id or 0)
        if current is None or candidate_key > current_key:
            latest[key] = submission
    return list(latest.values())


def average_score(submissions: List[models.Submission], field: str = "overall_score") -> Optional[float]:
    values = [getattr(submission, field) for submission in submissions if getattr(submission, field) is not None]
    return round(sum(values) / len(values), 1) if values else None


def score_distribution(submissions: List[models.Submission]) -> List[dict[str, Any]]:
    ranges = [("0-20", 0, 20), ("21-40", 21, 40), ("41-60", 41, 60), ("61-80", 61, 80), ("81-100", 81, 100)]
    scores = [max(0, min(100, round(submission.overall_score))) for submission in submissions if submission.overall_score is not None]
    counts = [sum(1 for score in scores if lower <= score <= upper) for _, lower, upper in ranges]
    maximum = max(counts, default=0)
    return [
        {"range": label, "count": count, "heightPercent": round(count / maximum * 100, 1) if maximum else 0}
        for (label, _, _), count in zip(ranges, counts)
        if scores
    ]


def build_assignment_stats(db: Session, assignment: models.Assignment) -> AssignmentWithStats:
    links = db.query(models.AssignmentProblem).filter(
        models.AssignmentProblem.assignment_id == assignment.id
    ).order_by(models.AssignmentProblem.position, models.AssignmentProblem.id).all()
    problem_titles = [
        problem.title
        for link in links
        if (problem := db.query(models.Problem).filter(models.Problem.id == link.problem_id).first())
    ]
    submissions = db.query(models.Submission).filter(
        models.Submission.assignment_id == assignment.id
    ).all()
    evaluated = [submission for submission in submissions if submission.status == "EVALUATED"]
    latest = latest_assessed_attempts(evaluated)
    submitters = {submission.student_id for submission in submissions}
    enrollment_count = db.query(models.Enrollment).filter(
        models.Enrollment.course_id == assignment.course_id,
        models.Enrollment.is_active == True,
    ).count()
    scores = [submission.overall_score for submission in latest if submission.overall_score is not None]

    return AssignmentWithStats(
        id=assignment.id,
        title=assignment.title,
        description=assignment.description,
        course_id=assignment.course_id,
        due_date=assignment.due_date,
        status=assignment.status,
        created_at=assignment.created_at,
        problems=[link.problem_id for link in links],
        total_students=enrollment_count,
        submitted_count=len(submitters),
        total_attempts=len(submissions),
        unique_submitters=len(submitters),
        unsubmitted_students=max(0, enrollment_count - len(submitters)),
        avg_score=average_score(latest),
        highest_score=max(scores) if scores else None,
        lowest_score=min(scores) if scores else None,
        avg_correctness=average_score(latest, "correctness_score"),
        avg_complexity=average_score(latest, "complexity_score"),
        avg_style=average_score(latest, "style_score"),
        avg_similarity=average_score(latest, "similarity_score"),
        problem_titles=problem_titles,
    )


def build_course_stats(db: Session, course: models.Course) -> CourseWithStats:
    enrollments = db.query(models.Enrollment).filter(
        models.Enrollment.course_id == course.id,
        models.Enrollment.is_active == True,
    ).all()
    assignments = db.query(models.Assignment).filter(
        models.Assignment.course_id == course.id,
    ).all()
    assignment_ids = [assignment.id for assignment in assignments]
    submissions = db.query(models.Submission).filter(
        models.Submission.assignment_id.in_(assignment_ids)
    ).all() if assignment_ids else []
    evaluated = [submission for submission in submissions if submission.status == "EVALUATED"]
    latest = latest_assessed_attempts(evaluated)
    unique_submitters = {submission.student_id for submission in submissions}
    assigned_problem_count = db.query(models.AssignmentProblem.id).filter(
        models.AssignmentProblem.assignment_id.in_(assignment_ids)
    ).count() if assignment_ids else 0
    scores = [submission.overall_score for submission in latest if submission.overall_score is not None]

    return CourseWithStats(
        id=course.id,
        course_code=course.course_code,
        title=course.title,
        term=course.term,
        description=course.description,
        instructor_id=course.instructor_id,
        is_active=course.is_active,
        created_at=course.created_at,
        student_count=len(enrollments),
        assignment_count=len(assignments),
        submission_count=len(submissions),
        unique_submitters=len(unique_submitters),
        unsubmitted_students=max(0, len(enrollments) - len(unique_submitters)),
        assigned_problem_count=assigned_problem_count,
        avg_score=average_score(latest),
    )


FAILED_CASE_REASONS = {
    "WRONG_ANSWER": "Your output did not match the expected output.",
    "RUNTIME_ERROR": "Your program ended with a runtime error.",
    "TIME_LIMIT_EXCEEDED": "Your program exceeded the time limit.",
    "MEMORY_LIMIT_EXCEEDED": "Your program exceeded the memory limit.",
    "OUTPUT_LIMIT_EXCEEDED": "Your program produced too much output.",
    "SYSTEM_ERROR": "The test could not be evaluated because of a system error.",
}


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
    if isinstance(results, list):
        for case_result in results:
            if isinstance(case_result, dict) and case_result.get("is_hidden"):
                for field in ("input", "expected_output", "actual_output", "stderr", "error_message"):
                    case_result.pop(field, None)

    # The execution layer deliberately provides only fixed metadata for the
    # final failed hidden test. Keep the stored/API shape allowlisted even if
    # a future runner adds diagnostic fields to this object.
    last_failed_case = safe_result.get("last_failed_case")
    if isinstance(last_failed_case, dict):
        try:
            ordinal = max(1, int(last_failed_case.get("ordinal")))
        except (TypeError, ValueError):
            safe_result["last_failed_case"] = None
        else:
            status = str(last_failed_case.get("status") or "SYSTEM_ERROR").upper()
            safe_result["last_failed_case"] = {
                "ordinal": ordinal,
                "status": status,
                "reason": FAILED_CASE_REASONS.get(status, "This test did not pass."),
                "is_hidden": bool(last_failed_case.get("is_hidden")),
            }

    return safe_result

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

def _auth_response(user: models.User, access_token: Optional[str] = None) -> AuthUser:
    student = user.student_profile
    instructor = user.instructor_profile
    if user.role == "student" and student is None:
        raise HTTPException(status_code=403, detail="Student profile is not configured")
    if user.role == "instructor" and instructor is None:
        raise HTTPException(status_code=403, detail="Instructor profile is not configured")

    return AuthUser(
        id=student.student_id if student else user.username,
        username=student.student_id if student else user.username,
        name=user.full_name,
        role=user.role,
        email=user.email,
        access_token=access_token,
        token_type="bearer" if access_token else None,
    )


def _issue_access_token(user: models.User) -> str:
    try:
        return create_access_token(user.id, user.username, user.role, user.token_version)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail="Authentication signing key is not configured") from error


@app.post("/api/auth/register", response_model=AuthUser, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    username = payload.username.strip()
    email = payload.email.strip().lower()
    if not username or "@" not in email or len(payload.password) < 12:
        raise HTTPException(status_code=422, detail="Provide a username, valid email, and password of at least 12 characters")

    existing_user = db.query(models.User).filter(
        or_(models.User.username == username, func.lower(models.User.email) == email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Username or email is already registered")

    student = db.query(models.Student).filter(models.Student.student_id == username).first()
    if student and (student.user_id is not None or not student.email or student.email.lower() != email):
        raise HTTPException(status_code=409, detail="Student record cannot be linked with the supplied identity")

    try:
        user = models.User(
            username=username,
            email=email,
            full_name=(payload.full_name or username).strip(),
            hashed_password=hash_password(payload.password),
            role="student",
        )
        db.add(user)
        db.flush()
        if student is None:
            student = models.Student(student_id=username, name=user.full_name, email=email, user_id=user.id)
            db.add(student)
        else:
            student.user_id = user.id
        token = _issue_access_token(user)
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise

    return _auth_response(user, token)


@app.post("/api/auth/login", response_model=AuthUser)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    identifier = payload.user_id.strip()
    user = db.query(models.User).filter(
        or_(models.User.username == identifier, func.lower(models.User.email) == identifier.lower())
    ).first()
    if (
        user is None
        or not user.is_active
        or user.role != payload.role
        or not verify_password(payload.password, user.hashed_password)
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials", headers={"WWW-Authenticate": "Bearer"})

    token = _issue_access_token(user)
    return _auth_response(user, token)


@app.get("/api/auth/me", response_model=AuthUser)
def get_authenticated_user(current_user: models.User = Depends(get_current_user)):
    return _auth_response(current_user)


@app.post("/api/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.token_version += 1
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

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
def list_instructor_problems(
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
):
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
    db: Session = Depends(get_db),
    student: models.Student = Depends(get_current_student),
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
    logger.info(f"Received submission for student '{student.student_id}' on problem '{problem_id}'")

    # Fetch problem details
    problem = db.query(models.Problem).filter(models.Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    assignment = None
    if payload.assignment_id is not None:
        assignment = get_student_assignment_for_problem(
            db,
            student.student_id,
            payload.assignment_id,
            problem_id,
        )

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
    # The agent workflow needs verdicts and counts, not the input/output of a
    # private judge case. Redact only after the execution task has completed.
    safe_exec_result = redact_hidden_execution(exec_result)
    if isinstance(complexity_outcome, Exception):
        logger.warning("Complexity analysis failed: %s", complexity_outcome)
        precomputed_complexity_analysis = unavailable_analysis(
            "The complexity analysis service was unavailable for this submission."
        )
    else:
        precomputed_complexity_analysis = complexity_outcome

    # 2. Build LangGraph State
    initial_state: EvaluationState = {
        "user": {"student_id": student.student_id, "name": student.name},
        "problem": public_problem,
        "submission": {
            "source_code": payload.code,
            "language": payload.language
        },
        "execution_result": safe_exec_result,
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
    
    new_submission = models.Submission(
        submission_id=submission_id,
        student_id=student.student_id,
        problem_id=problem_id,
        assignment_id=assignment.id if assignment else None,
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
        assignment_id=new_submission.assignment_id,
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
def get_submission(
    submission_id: str,
    db: Session = Depends(get_db),
    student: models.Student = Depends(get_current_student),
):
    submission = db.query(models.Submission).filter(
        models.Submission.submission_id == submission_id,
        models.Submission.student_id == student.student_id,
    ).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission

@app.get("/api/submissions", response_model=List[SubmissionDetails])
def list_submissions(
    student_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    student: models.Student = Depends(get_current_student),
):
    if student_id is not None and student_id != student.student_id:
        raise HTTPException(status_code=403, detail="Cannot access another student's submissions")
    query = db.query(models.Submission).filter(models.Submission.student_id == student.student_id)
    return query.order_by(models.Submission.created_at.desc()).all()

# ==========================================
# Student & Instructor Analytics Endpoints
# ==========================================

@app.get("/api/analytics/student/{student_id}", response_model=StudentAnalyticsResponse)
def get_student_analytics(
    student_id: str,
    db: Session = Depends(get_db),
    student: models.Student = Depends(get_current_student),
):
    if student_id != student.student_id:
        raise HTTPException(status_code=404, detail="Student not found")

    submissions = db.query(models.Submission).filter(
        models.Submission.student_id == student_id,
        models.Submission.status == "EVALUATED",
    ).order_by(models.Submission.created_at).all()
    latest = latest_assessed_attempts(submissions, preserve_assignment=False)
    avg_overall = average_score(latest)
    avg_correctness = average_score(latest, "correctness_score")
    avg_complexity = average_score(latest, "complexity_score")
    avg_style = average_score(latest, "style_score")
    avg_similarity = average_score(latest, "similarity_score")
    total_problems = db.query(models.Problem).count()
    unique_solved = len({submission.problem_id for submission in latest if submission.overall_score >= 70})

    score_trend = [
        {"date": utc_isoformat(submission.created_at), "score": submission.overall_score}
        for submission in sorted(latest, key=lambda item: (item.created_at, item.id or 0))
    ]
    category_scores: dict[str, list[float]] = {}
    problem_categories = {
        problem.id: problem.category
        for problem in db.query(models.Problem.id, models.Problem.category).all()
    }
    for submission in latest:
        category = problem_categories.get(submission.problem_id) or "Uncategorized"
        category_scores.setdefault(category, []).append(submission.overall_score)
    weak_topics = [
        category
        for category, scores in category_scores.items()
        if len(scores) >= 3 and sum(scores) / len(scores) < 70
    ]

    category_breakdown = [
        {"name": "Correctness", "value": avg_correctness, "color": "#10b981"},
        {"name": "Time & Space Complexity", "value": avg_complexity, "color": "#3b82f6"},
        {"name": "Code Quality & Style", "value": avg_style, "color": "#8b5cf6"},
        {"name": "Originality", "value": round(100 - avg_similarity, 1) if avg_similarity is not None else None, "color": "#ec4899"},
    ]
    category_breakdown = [category for category in category_breakdown if category["value"] is not None]

    return StudentAnalyticsResponse(
        overall_score=avg_overall,
        streak_days=student.streak_days,
        xp=student.xp,
        problems_solved=unique_solved,
        total_problems=total_problems,
        score_trend=score_trend,
        category_breakdown=category_breakdown,
        weak_topics=weak_topics
    )

@app.get("/api/instructor/overview")
def get_instructor_overview(
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
):
    """Get instructor dashboard overview with REAL database data.
    
    Returns metrics based on actual course enrollments and assignment submissions.
    Independent practice submissions (assignment_id = NULL) are NOT included.
    """
    courses = db.query(models.Course).filter(
        models.Course.instructor_id == instructor.id,
        models.Course.is_active == True,
    ).all()
    course_ids = [c.id for c in courses]
    assignments = db.query(models.Assignment).filter(
        models.Assignment.course_id.in_(course_ids)
    ).all() if course_ids else []
    assignment_ids = [assignment.id for assignment in assignments]
    enrollments = db.query(models.Enrollment).filter(
        models.Enrollment.course_id.in_(course_ids),
        models.Enrollment.is_active == True,
    ).all() if course_ids else []
    unique_student_ids = {enrollment.student_id for enrollment in enrollments}
    total_students = len(unique_student_ids)
    course_title_by_student: dict[str, set[str]] = {}
    for enrollment in enrollments:
        course_title_by_student.setdefault(enrollment.student_id, set()).add(enrollment.course.title)

    assignment_submissions = db.query(models.Submission).filter(
        models.Submission.assignment_id.in_(assignment_ids),
        models.Submission.status == "EVALUATED",
    ).all() if assignment_ids else []
    relevant_submissions = [submission for submission in assignment_submissions if submission.student_id in unique_student_ids]
    total_submissions = len(relevant_submissions)
    latest = latest_assessed_attempts(relevant_submissions)
    class_avg_score = average_score(latest)
    scores = [submission.overall_score for submission in latest if submission.overall_score is not None]
    active_assignments = sum(assignment.status == "ACTIVE" for assignment in assignments)

    student_list = []
    for student_id in unique_student_ids:
        student = db.query(models.Student).filter(models.Student.student_id == student_id).first()
        if not student:
            continue
        student_submissions = [submission for submission in relevant_submissions if submission.student_id == student_id]
        student_latest = [submission for submission in latest if submission.student_id == student_id]
        student_avg = average_score(student_latest)
        if student_avg is None:
            grade, student_status = None, "No submissions"
        elif student_avg >= 85:
            grade = "A"
            student_status = "On Track"
        elif student_avg >= 70:
            grade = "B+"
            student_status = "On Track"
        elif student_avg >= 60:
            grade = "B"
            student_status = "At Risk"
        else:
            grade = "C"
            student_status = "Needs Attention"
        
        student_list.append({
            "id": student.student_id,
            "name": f"{student.name} ({student.student_id})",
            "course": ", ".join(sorted(course_title_by_student.get(student_id, set()))),
            "subs": len(student_submissions),
            "avg": f"{student_avg}%" if student_avg is not None else None,
            "grade": grade,
            "status": student_status
        })

    course_list = [
        {
            "id": c.id,
            "course_code": c.course_code,
            "title": c.title,
            "term": c.term,
            "description": c.description,
            "instructor_id": c.instructor_id,
            "is_active": c.is_active,
            "created_at": c.created_at.isoformat() if c.created_at else None
        }
        for c in courses
    ]
    
    return {
        "total_students": total_students,
        "active_assignments": active_assignments,
        "total_submissions": total_submissions,
        "total_courses": len(courses),
        "total_assignments": len(assignments),
        "class_avg_score": f"{class_avg_score}%" if class_avg_score is not None else None,
        "highest_score": max(scores) if scores else None,
        "lowest_score": min(scores) if scores else None,
        "score_distribution": score_distribution(latest),
        "courses": course_list,
        "students": student_list
    }


# ============ Instructor Course Management APIs ============

@app.post("/api/instructor/courses", response_model=CourseResponse)
def create_course(
    course: CourseCreate,
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
):
    """Create a course owned by the authenticated instructor."""
    
    new_course = models.Course(
        course_code=course.course_code,
        title=course.title,
        term=course.term,
        description=course.description,
        instructor_id=instructor.id,
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course


@app.get("/api/instructor/courses", response_model=List[CourseWithStats])
def get_courses(
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
):
    """Get all courses for the instructor with stats."""
    courses = db.query(models.Course).filter(
        models.Course.instructor_id == instructor.id,
        models.Course.is_active == True,
    ).all()
    return [build_course_stats(db, course) for course in courses]


@app.get("/api/instructor/courses/{course_id}", response_model=CourseWithStats)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
):
    """Get a specific course with stats."""
    course = get_owned_course(db, instructor.id, course_id)
    return build_course_stats(db, course)


@app.patch("/api/instructor/courses/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: int,
    payload: CourseUpdate,
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
):
    course = get_owned_course(db, instructor.id, course_id)
    updates = payload.model_dump(exclude_unset=True)
    for field in ("course_code", "title"):
        if field in updates and not (updates[field] or "").strip():
            raise HTTPException(status_code=422, detail=f"{field} cannot be empty")
    for field in ("course_code", "title", "term", "description"):
        if field in updates and isinstance(updates[field], str):
            updates[field] = updates[field].strip() or None
    for field, value in updates.items():
        setattr(course, field, value)
    db.commit()
    db.refresh(course)
    return course


@app.delete("/api/instructor/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_course(
    course_id: int,
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
):
    course = get_owned_course(db, instructor.id, course_id)
    course.is_active = False
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/instructor/students", response_model=List[StudentLookupItem])
def search_students(
    query: Optional[str] = Query(None, min_length=1, max_length=100),
    course_id: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
):
    """
    Search students or return students enrolled in a specific instructor-owned course.

    - query only: search by Student ID or name
    - course_id only: return the course roster
    - both: search students and optionally scope to the course
    """

    if course_id is not None:
        # Verify the course belongs to the authenticated instructor.
        get_owned_course(db, instructor.id, course_id)

        students = (
            db.query(models.Student)
            .join(
                models.Enrollment,
                models.Enrollment.student_id == models.Student.student_id,
            )
            .filter(
                models.Enrollment.course_id == course_id,
                models.Enrollment.is_active == True,
            )
            .order_by(models.Student.name)
        )

        if query:
            needle = query.strip()
            students = students.filter(
                models.Student.student_id.ilike(f"%{needle}%")
                | models.Student.name.ilike(f"%{needle}%")
            )

        students = students.limit(limit).all()

    else:
        if not query:
            return []

        needle = query.strip()

        if not needle:
            return []

        students = (
            db.query(models.Student)
            .filter(
                models.Student.student_id.ilike(f"%{needle}%")
                | models.Student.name.ilike(f"%{needle}%")
            )
            .order_by(models.Student.name)
            .limit(limit)
            .all()
        )

    return [
        StudentLookupItem(
            student_id=student.student_id,
            name=student.name,
        )
        for student in students
    ]

@app.post("/api/instructor/students", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def create_and_enroll_student(
    payload: StudentCreateByInstructor,
    response: Response,
    course_id: int = Query(...),
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
):
    """Create or reuse a student profile and enroll them in an owned course."""

    course = get_owned_course(db, instructor.id, course_id)

    student_id = payload.student_id.strip()
    name = payload.name.strip() if payload.name else ""
    email = payload.email.strip() if payload.email else None

    existing_student = (
        db.query(models.Student)
        .filter(func.lower(models.Student.student_id) == student_id.lower())
        .first()
    )

    if existing_student is not None:
        name_changed = name and name.casefold() != existing_student.name.strip().casefold()
        email_changed = email and email.casefold() != (existing_student.email or "").strip().casefold()
        if name_changed or email_changed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Student ID {existing_student.student_id} already has a saved profile with different details. "
                    "Nothing was changed. Leave name and email blank or use the saved details to enroll this student."
                ),
            )
    elif email:
        email_owner = (
            db.query(models.Student)
            .filter(func.lower(models.Student.email) == email.casefold())
            .first()
        )
        if email_owner is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"This email is already saved under Student ID {email_owner.student_id}. "
                    "Use that ID to enroll the existing profile instead of creating a duplicate."
                ),
            )

    if existing_student is None and not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Student name is required when creating a new student profile.",
        )

    try:
        student = existing_student
        if student is None:
            student = models.Student(
                student_id=student_id,
                name=name,
                email=email,
            )
            db.add(student)
            db.flush()

        existing_enrollment = (
            db.query(models.Enrollment)
            .filter(
                models.Enrollment.student_id == student.student_id,
                models.Enrollment.course_id == course.id,
            )
            .first()
        )

        if existing_enrollment is not None:
            if not existing_enrollment.is_active:
                existing_enrollment.is_active = True
                db.commit()
                db.refresh(existing_enrollment)
            response.status_code = status.HTTP_200_OK
            return EnrollmentResponse(
                id=existing_enrollment.id,
                student_id=student.student_id,
                course_id=course.id,
                enrollment_date=existing_enrollment.enrollment_date,
                is_active=existing_enrollment.is_active,
                student_name=student.name,
                student_email=student.email,
            )

        enrollment = models.Enrollment(
            student_id=student.student_id,
            course_id=course.id,
            is_active=True,
        )

        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)
        db.refresh(student)

    except Exception:
        db.rollback()
        raise

    return EnrollmentResponse(
        id=enrollment.id,
        student_id=student.student_id,
        course_id=course.id,
        enrollment_date=enrollment.enrollment_date,
        is_active=enrollment.is_active,
        student_name=student.name,
        student_email=student.email,
    )


# ============ Instructor Enrollment APIs ============

@app.post("/api/instructor/enrollments", response_model=EnrollmentResponse)
def enroll_student(
    enrollment: EnrollmentCreate,
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
):
    """Enroll a student in a course."""
    get_owned_course(db, instructor.id, enrollment.course_id)
    # Check if student exists
    student = db.query(models.Student).filter(
        models.Student.student_id == enrollment.student_id
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check if course exists
    course = db.query(models.Course).filter(models.Course.id == enrollment.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if already enrolled
    existing = db.query(models.Enrollment).filter(
        models.Enrollment.student_id == enrollment.student_id,
        models.Enrollment.course_id == enrollment.course_id
    ).first()
    
    if existing:
        # Reactivate if inactive
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return EnrollmentResponse(
            id=existing.id,
            student_id=existing.student_id,
            course_id=existing.course_id,
            enrollment_date=existing.enrollment_date,
            is_active=existing.is_active,
            student_name=student.name,
            student_email=student.email
        )
    
    # Create new enrollment
    new_enrollment = models.Enrollment(
        student_id=enrollment.student_id,
        course_id=enrollment.course_id
    )
    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)
    
    return EnrollmentResponse(
        id=new_enrollment.id,
        student_id=new_enrollment.student_id,
        course_id=new_enrollment.course_id,
        enrollment_date=new_enrollment.enrollment_date,
        is_active=new_enrollment.is_active,
        student_name=student.name,
        student_email=student.email
    )


@app.get("/api/instructor/courses/{course_id}/students", response_model=List[EnrollmentResponse])
def get_course_students(
    course_id: int,
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
):
    """Get all students enrolled in a course."""
    get_owned_course(db, instructor.id, course_id)
    enrollments = db.query(models.Enrollment).filter(
        models.Enrollment.course_id == course_id,
        models.Enrollment.is_active == True
    ).all()
    
    result = []
    for e in enrollments:
        student = db.query(models.Student).filter(
            models.Student.student_id == e.student_id
        ).first()
        
        result.append(EnrollmentResponse(
            id=e.id,
            student_id=e.student_id,
            course_id=e.course_id,
            enrollment_date=e.enrollment_date,
            is_active=e.is_active,
            student_name=student.name if student else None,
            student_email=student.email if student else None
        ))
    
    return result


@app.delete("/api/instructor/enrollments/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
):
    enrollment = db.query(models.Enrollment).filter(models.Enrollment.id == enrollment_id).first()
    if enrollment is None:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    get_owned_course(db, instructor.id, enrollment.course_id)
    enrollment.is_active = False
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/student/courses", response_model=List[StudentCourseResponse])
def get_student_courses(
    db: Session = Depends(get_db),
    student: models.Student = Depends(get_current_student),
):
    enrollments = db.query(models.Enrollment).join(models.Course).filter(
        models.Enrollment.student_id == student.student_id,
        models.Enrollment.is_active == True,
        models.Course.is_active == True,
    ).all()
    result = []
    for enrollment in enrollments:
        course = enrollment.course
        assignment_count = db.query(models.Assignment).filter(
            models.Assignment.course_id == course.id,
            models.Assignment.status.in_(["ACTIVE", "UPCOMING"]),
        ).count()
        result.append(StudentCourseResponse(
            id=course.id,
            course_code=course.course_code,
            title=course.title,
            term=course.term,
            description=course.description,
            instructor_id=course.instructor_id,
            is_active=course.is_active,
            created_at=course.created_at,
            assignments_count=assignment_count,
        ))
    return result


@app.get("/api/student/courses/{course_id}/assignments", response_model=List[StudentAssignmentResponse])
def get_student_course_assignments(
    course_id: int,
    db: Session = Depends(get_db),
    student: models.Student = Depends(get_current_student),
):
    enrollment = db.query(models.Enrollment).join(models.Course).filter(
        models.Enrollment.student_id == student.student_id,
        models.Enrollment.course_id == course_id,
        models.Enrollment.is_active == True,
        models.Course.is_active == True,
    ).first()
    if enrollment is None:
        raise HTTPException(status_code=404, detail="Course not found")

    assignments = db.query(models.Assignment).filter(
        models.Assignment.course_id == course_id,
        models.Assignment.status.in_(["ACTIVE", "UPCOMING"]),
    ).order_by(models.Assignment.due_date, models.Assignment.created_at).all()
    result = []
    for assignment in assignments:
        links = db.query(models.AssignmentProblem).filter(
            models.AssignmentProblem.assignment_id == assignment.id
        ).order_by(models.AssignmentProblem.position, models.AssignmentProblem.id).all()
        problems = [
            db.query(models.Problem).filter(models.Problem.id == link.problem_id).first()
            for link in links
        ]
        result.append(StudentAssignmentResponse(
            id=assignment.id,
            title=assignment.title,
            description=assignment.description,
            course_id=course_id,
            course_title=enrollment.course.title,
            due_date=assignment.due_date,
            status=assignment.status,
            problems=[link.problem_id for link in links],
            problem_titles=[problem.title for problem in problems if problem is not None],
        ))
    return result


# ============ Instructor Assignment APIs ============

@app.get("/api/instructor/assignments", response_model=List[AssignmentWithStats])
def list_assignments(
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
):
    """List all assignments for the instructor with aggregated stats."""
    assignments = db.query(models.Assignment).join(models.Course).filter(
        models.Course.instructor_id == instructor.id,
    ).order_by(models.Assignment.created_at.desc()).all()
    return [build_assignment_stats(db, assignment) for assignment in assignments]


@app.post("/api/instructor/assignments", response_model=AssignmentResponse)
def create_assignment(
    assignment: AssignmentCreate,
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
):
    """Create a new assignment with problems."""
    get_owned_course(db, instructor.id, assignment.course_id)

    found_ids = {
        problem_id
        for (problem_id,) in db.query(models.Problem.id).filter(
            models.Problem.id.in_(assignment.problem_ids)
        ).all()
    }
    missing_ids = [problem_id for problem_id in assignment.problem_ids if problem_id not in found_ids]
    if missing_ids:
        raise HTTPException(status_code=422, detail={"unknown_problem_ids": missing_ids})

    try:
        new_assignment = models.Assignment(
            title=assignment.title,
            description=assignment.description,
            course_id=assignment.course_id,
            due_date=assignment.due_date,
            status=assignment.status,
        )
        db.add(new_assignment)
        db.flush()
        for position, problem_id in enumerate(assignment.problem_ids, start=1):
            db.add(models.AssignmentProblem(
                assignment_id=new_assignment.id,
                problem_id=problem_id,
                position=position,
            ))
        db.commit()
        db.refresh(new_assignment)
    except Exception:
        db.rollback()
        raise
    
    return AssignmentResponse(
        id=new_assignment.id,
        title=new_assignment.title,
        description=new_assignment.description,
        course_id=new_assignment.course_id,
        due_date=new_assignment.due_date,
        status=new_assignment.status,
        created_at=new_assignment.created_at,
        problems=assignment.problem_ids
    )


@app.patch("/api/instructor/assignments/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(
    assignment_id: int,
    payload: AssignmentUpdate,
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
):
    assignment = get_owned_assignment(db, instructor.id, assignment_id)
    updates = payload.model_dump(exclude_unset=True)
    requested_problem_ids = updates.pop("problem_ids", None)
    has_submissions = db.query(models.Submission.id).filter(
        models.Submission.assignment_id == assignment.id
    ).first() is not None

    semantic_fields = {"title", "description", "due_date"}
    if has_submissions and (semantic_fields.intersection(updates) or requested_problem_ids is not None):
        raise HTTPException(
            status_code=409,
            detail="Assignment content cannot change after a student submission exists; status changes remain allowed",
        )

    if requested_problem_ids is not None:
        existing_problem_ids = [link.problem_id for link in db.query(models.AssignmentProblem).filter(
            models.AssignmentProblem.assignment_id == assignment.id
        ).order_by(models.AssignmentProblem.position, models.AssignmentProblem.id).all()]
        if requested_problem_ids != existing_problem_ids:
            found_ids = {
                problem_id
                for (problem_id,) in db.query(models.Problem.id).filter(
                    models.Problem.id.in_(requested_problem_ids)
                ).all()
            }
            missing_ids = [problem_id for problem_id in requested_problem_ids if problem_id not in found_ids]
            if missing_ids:
                raise HTTPException(status_code=422, detail={"unknown_problem_ids": missing_ids})
            db.query(models.AssignmentProblem).filter(
                models.AssignmentProblem.assignment_id == assignment.id
            ).delete(synchronize_session=False)
            for position, problem_id in enumerate(requested_problem_ids, start=1):
                db.add(models.AssignmentProblem(
                    assignment_id=assignment.id,
                    problem_id=problem_id,
                    position=position,
                ))

    for field, value in updates.items():
        setattr(assignment, field, value)
    try:
        db.commit()
        db.refresh(assignment)
    except Exception:
        db.rollback()
        raise

    links = db.query(models.AssignmentProblem).filter(
        models.AssignmentProblem.assignment_id == assignment.id
    ).order_by(models.AssignmentProblem.position, models.AssignmentProblem.id).all()
    return AssignmentResponse(
        id=assignment.id,
        title=assignment.title,
        description=assignment.description,
        course_id=assignment.course_id,
        due_date=assignment.due_date,
        status=assignment.status,
        created_at=assignment.created_at,
        problems=[link.problem_id for link in links],
    )


@app.get("/api/instructor/courses/{course_id}/assignments", response_model=List[AssignmentWithStats])
def get_course_assignments(
    course_id: int,
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
):
    """Get all assignments for a course with stats."""
    get_owned_course(db, instructor.id, course_id)
    assignments = db.query(models.Assignment).filter(
        models.Assignment.course_id == course_id
    ).all()
    return [build_assignment_stats(db, assignment) for assignment in assignments]


@app.get("/api/instructor/assignments/{assignment_id}", response_model=AssignmentWithStats)
def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
):
    """Get a specific assignment with stats."""
    assignment = get_owned_assignment(db, instructor.id, assignment_id)
    
    return build_assignment_stats(db, assignment)


# ============ Instructor Analytics APIs ============

@app.get("/api/instructor/courses/{course_id}/analytics")
def get_course_analytics(
    course_id: int,
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
):
    """Get analytics for a specific course."""
    course = get_owned_course(db, instructor.id, course_id)
    assignments = db.query(models.Assignment).filter(
        models.Assignment.course_id == course_id
    ).all()
    assignment_ids = [a.id for a in assignments]
    enrollments = db.query(models.Enrollment).filter(
        models.Enrollment.course_id == course_id,
        models.Enrollment.is_active == True
    ).all()
    total_students = len(enrollments)
    submissions = db.query(models.Submission).filter(
        models.Submission.assignment_id.in_(assignment_ids)
    ).all()
    evaluated = [submission for submission in submissions if submission.status == "EVALUATED"]
    latest = latest_assessed_attempts(evaluated)
    enrolled_student_ids = {enrollment.student_id for enrollment in enrollments}
    completion_assignments = [assignment for assignment in assignments if assignment.status != "UPCOMING"]
    expected_completions = total_students * len(completion_assignments)
    completed_pairs = {
        (submission.assignment_id, submission.student_id)
        for submission in submissions
        if submission.student_id in enrolled_student_ids
        and any(assignment.id == submission.assignment_id for assignment in completion_assignments)
    }
    completion_rate = round(len(completed_pairs) / expected_completions * 100, 1) if expected_completions else None

    category_by_problem = {
        problem.id: problem.category or "Uncategorized"
        for problem in db.query(models.Problem.id, models.Problem.category).all()
    }
    scores_by_category: dict[str, list[float]] = {}
    for submission in latest:
        category = category_by_problem.get(submission.problem_id, "Uncategorized")
        scores_by_category.setdefault(category, []).append(submission.overall_score)
    topic_performance = [
        {"topic": topic, "avg_score": round(sum(scores) / len(scores), 1), "assessed_problems": len(scores)}
        for topic, scores in sorted(scores_by_category.items())
    ]
    unique_submitters = {submission.student_id for submission in submissions}
    return {
        "course_id": course_id,
        "course_name": course.title,
        "total_students": total_students,
        "total_assignments": len(assignments),
        "total_submissions": len(submissions),
        "unique_submitters": len(unique_submitters),
        "unsubmitted_students": max(0, total_students - len(unique_submitters)),
        "avg_score": average_score(latest),
        "score_distribution": score_distribution(latest),
        "completion_rate": completion_rate,
        "assignment_stats": [build_assignment_stats(db, assignment).model_dump() for assignment in assignments],
        "topic_performance": topic_performance,
    }
@app.get("/api/instructor/courses/{course_id}/students/{student_id}/progress", response_model=InstructorStudentProgressResponse)
def get_instructor_student_progress(
    course_id: int,
    student_id: str,
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
):
    course = get_owned_course(db, instructor.id, course_id)
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.course_id == course_id,
        models.Enrollment.student_id == student_id,
        models.Enrollment.is_active == True
    ).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Student is not enrolled in this course")

    student = db.query(models.Student).filter(models.Student.student_id == student_id).first()
    
    assignments = db.query(models.Assignment).filter(models.Assignment.course_id == course_id).all()
    assignment_ids = [a.id for a in assignments]
    
    assigned_problems = db.query(models.AssignmentProblem).filter(
        models.AssignmentProblem.assignment_id.in_(assignment_ids)
    ).all()
    
    total_assigned = len(assigned_problems)
    
    submissions = db.query(models.Submission).filter(
        models.Submission.student_id == student_id,
        models.Submission.assignment_id.in_(assignment_ids)
    ).order_by(models.Submission.created_at.desc()).all()
    
    total_attempts = len(submissions)
    
    completed_problems = set()
    latest_evaluated_by_problem = {}
    
    for sub in submissions:
        if sub.status == "EVALUATED" and sub.overall_score is not None:
            if sub.problem_id not in latest_evaluated_by_problem:
                latest_evaluated_by_problem[sub.problem_id] = sub
                completed_problems.add(sub.problem_id)
                
    evaluated_subs = list(latest_evaluated_by_problem.values())
    
    avg_score = sum(s.overall_score for s in evaluated_subs) / len(evaluated_subs) if evaluated_subs else None
    
    # Calculate dimensional averages
    corr_avg = sum(s.correctness_score or 0 for s in evaluated_subs) / len(evaluated_subs) if evaluated_subs else None
    comp_avg = sum(s.complexity_score or 0 for s in evaluated_subs) / len(evaluated_subs) if evaluated_subs else None
    style_avg = sum(s.style_score or 0 for s in evaluated_subs) / len(evaluated_subs) if evaluated_subs else None
    sim_avg = sum(s.similarity_score or 0 for s in evaluated_subs) / len(evaluated_subs) if evaluated_subs else None

    # Sort chronological for progress trend
    chronological_evaluated = [s for s in reversed(submissions) if s.status == "EVALUATED" and s.overall_score is not None]
    progress_trend = [s.overall_score for s in chronological_evaluated[-10:]]
    
    latest_score = chronological_evaluated[-1].overall_score if chronological_evaluated else None
    latest_sub = chronological_evaluated[-1] if chronological_evaluated else None
    
    return {
        "student_id": student.student_id,
        "student_name": student.name,
        "course_title": course.title,
        "assigned_problems": total_assigned,
        "completed_problems": len(completed_problems),
        "pending_problems": max(0, total_assigned - len(completed_problems)),
        "average_score": avg_score,
        "latest_score": latest_score,
        "correctness_avg": corr_avg,
        "complexity_avg": comp_avg,
        "style_avg": style_avg,
        "similarity_avg": sim_avg,
        "total_attempts": total_attempts,
        "latest_submission": {
            "id": latest_sub.submission_id,
            "score": latest_sub.overall_score,
            "date": utc_isoformat(latest_sub.created_at),
            "problem_id": latest_sub.problem_id,
            "feedback": latest_sub.feedback,
            "recommendations": latest_sub.recommendations,
        } if latest_sub else None,
        "progress_trend": progress_trend
    }
import io
import csv
from fastapi.responses import StreamingResponse

@app.get("/api/instructor/courses/{course_id}/export")
def export_course_csv(
    course_id: int,
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
):
    course = get_owned_course(db, instructor.id, course_id)
    assignments = db.query(models.Assignment).filter(models.Assignment.course_id == course_id).all()
    assignment_ids = [a.id for a in assignments]
    
    enrollments = db.query(models.Enrollment).filter(models.Enrollment.course_id == course_id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student ID", "Student Name", "Course", "Completed Problems", "Average Score", "Correctness", "Complexity", "Style", "Similarity", "Last Submission"])
    
    for enroll in enrollments:
        student = db.query(models.Student).filter(models.Student.student_id == enroll.student_id).first()
        submissions = db.query(models.Submission).filter(
            models.Submission.student_id == enroll.student_id,
            models.Submission.assignment_id.in_(assignment_ids),
            models.Submission.status == "EVALUATED"
        ).order_by(models.Submission.created_at.desc()).all()
        
        completed_problems = set()
        latest_evaluated = {}
        for sub in submissions:
            if sub.overall_score is not None:
                if sub.problem_id not in latest_evaluated:
                    latest_evaluated[sub.problem_id] = sub
                    completed_problems.add(sub.problem_id)
        
        evaluated_subs = list(latest_evaluated.values())
        avg_score = round(sum(s.overall_score for s in evaluated_subs) / len(evaluated_subs), 2) if evaluated_subs else "N/A"
        avg_corr = round(sum(s.correctness_score or 0 for s in evaluated_subs) / len(evaluated_subs), 2) if evaluated_subs else "N/A"
        avg_comp = round(sum(s.complexity_score or 0 for s in evaluated_subs) / len(evaluated_subs), 2) if evaluated_subs else "N/A"
        avg_style = round(sum(s.style_score or 0 for s in evaluated_subs) / len(evaluated_subs), 2) if evaluated_subs else "N/A"
        avg_sim = round(sum(s.similarity_score or 0 for s in evaluated_subs) / len(evaluated_subs), 2) if evaluated_subs else "N/A"
        
        last_sub_date = utc_isoformat(submissions[0].created_at) if submissions else "N/A"
        
        writer.writerow([
            student.student_id,
            student.name,
            course.course_code,
            len(completed_problems),
            avg_score,
            avg_corr,
            avg_comp,
            avg_style,
            avg_sim,
            last_sub_date
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=course_{course_id}_export.csv"}
    )
