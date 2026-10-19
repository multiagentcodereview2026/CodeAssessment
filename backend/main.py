import asyncio
import copy
import re
from itertools import combinations
import hashlib
import json
import logging
import os
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from uuid import uuid4
from typing import Any, List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, or_, text
from analysis.analyzer_service import analyze_submission_complexity, analyze_static_complexity
from analysis.dynamic_profiler import profile_execution_results
from config.settings import settings
from scoring.rubric import complexity_dimension_percent
from similarity_analysis import approach_label, approach_summary, structural_explanation, structural_fingerprint, structural_overlap
from similarity_clustering import build_approach_groups, build_similarity_clusters, build_submission_groups

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
    ensure_submission_assignment_column,
    ensure_student_profile_columns,
    engine,
    get_db,
)
from schemas import (
    LoginRequest,
    RegisterRequest,
    AccountUpdateRequest,
    AuthUser,
    StudentCreateByInstructor,
    ProblemListItem,
    ProblemDetail,
    InstructorProblemCreate,
    InstructorProblemUpdate,
    SubmissionRequest,
    SubmissionResponse,
    SubmissionDetails,
    QuickRunRequest,
    QuickRunResponse,
    ProblemHintsResponse,
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
    CourseDiscoveryResponse,
    CourseRequestCreate,
    CourseRequestResponse,
    NotificationResponse,
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
from agents.base import llm, extract_clean_json
from agents.revision import revision_node
from agents.revision_verification import summarize_revision_verification, unverified_revision
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


def create_notification(
    db: Session,
    recipient_user_id: Optional[int],
    event_type: str,
    title: str,
    message: str,
    target_url: Optional[str] = None,
) -> None:
    if recipient_user_id is None:
        return
    db.add(models.Notification(
        recipient_user_id=recipient_user_id,
        event_type=event_type,
        title=title,
        message=message,
        target_url=target_url,
    ))


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


def average_values(values: List[float]) -> Optional[float]:
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


def topic_performance(db: Session, submissions: List[models.Submission]) -> List[dict[str, Any]]:
    latest = latest_assessed_attempts(submissions)
    categories = {
        problem_id: category or "Uncategorized"
        for problem_id, category in db.query(models.Problem.id, models.Problem.category).all()
    }
    scores_by_topic: dict[str, list[models.Submission]] = {}
    for submission in latest:
        if submission.overall_score is not None:
            scores_by_topic.setdefault(categories.get(submission.problem_id, "Uncategorized"), []).append(submission)
    results = []
    for topic, records in scores_by_topic.items():
        average = average_score(records)
        results.append({
            "topic": topic,
            "average_score": average,
            "deduction_rate": round(100 - average, 1) if average is not None else None,
            "students_assessed": len({record.student_id for record in records}),
            "students_below_60": len({record.student_id for record in records if record.overall_score < 60}),
        })
    return sorted(results, key=lambda row: (row["average_score"] if row["average_score"] is not None else 101, row["topic"]))


def student_score_extremes(db: Session, submissions: List[models.Submission]) -> dict[str, Any]:
    latest = latest_assessed_attempts(submissions)
    scores: dict[str, list[float]] = {}
    for submission in latest:
        if submission.overall_score is not None:
            scores.setdefault(submission.student_id, []).append(submission.overall_score)
    if not scores:
        return {"highest_student": None, "lowest_student": None}
    averages = {student_id: round(sum(values) / len(values), 1) for student_id, values in scores.items()}
    names = {
        student.student_id: student.name
        for student in db.query(models.Student).filter(models.Student.student_id.in_(list(averages))).all()
    }
    high_id = max(averages, key=averages.get)
    low_id = min(averages, key=averages.get)
    return {
        "highest_student": {"id": high_id, "name": names.get(high_id, high_id), "average_score": averages[high_id]},
        "lowest_student": {"id": low_id, "name": names.get(low_id, low_id), "average_score": averages[low_id]},
    }


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
        problem_titles=problem_titles,
        score_distribution=score_distribution(latest),
        topic_performance=topic_performance(db, latest),
        **student_score_extremes(db, latest),
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


def revealed_feedback_case(results):
    """Allow exactly one failed hidden case to become a student learning aid.

    The returned object is deliberately allowlisted.  Every other hidden case
    remains redacted, and judge diagnostics are not exposed.
    """
    if not isinstance(results, list):
        return None
    for case_result in results:
        if not isinstance(case_result, dict):
            continue
        is_hidden = bool(case_result.get("is_hidden", case_result.get("isHidden", False)))
        status = str(case_result.get("status") or "").upper()
        if is_hidden and status != "ACCEPTED":
            return {
                "status": status or "SYSTEM_ERROR",
                "reason": FAILED_CASE_REASONS.get(status, "This feedback case did not pass."),
                "input": str(case_result.get("input") or ""),
                "expected_output": str(case_result.get("expected_output") or ""),
                "actual_output": str(case_result.get("actual_output") or ""),
            }
    return None


def redact_hidden_execution(execution_result, *, student_view=False):
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
        existing_revealed_case = safe_result.get("revealed_feedback_case")
        revealed_case = None
        # A prior internal redaction may already have extracted the one
        # allowlisted learning case. Preserve it while removing all remaining
        # hidden result details on the final student-facing pass.
        if isinstance(existing_revealed_case, dict):
            existing = existing_revealed_case
            revealed_case = {
                "status": str(existing.get("status") or "SYSTEM_ERROR"),
                "reason": str(existing.get("reason") or "This feedback case did not pass."),
                "input": str(existing.get("input") or ""),
                "expected_output": str(existing.get("expected_output") or ""),
                "actual_output": str(existing.get("actual_output") or ""),
            }
        else:
            revealed_case = revealed_feedback_case(results)
        first_private_failure = None
        public_results = []
        for ordinal, case_result in enumerate(results, start=1):
            if not isinstance(case_result, dict):
                continue
            if case_result.get("is_hidden"):
                if first_private_failure is None and str(case_result.get("status", "")).lower() != "accepted":
                    status = str(case_result.get("status") or "SYSTEM_ERROR").upper()
                    first_private_failure = {
                        "ordinal": ordinal,
                        "status": status,
                        "reason": FAILED_CASE_REASONS.get(status, "This test did not pass."),
                    }
                for field in ("input", "expected_output", "actual_output", "stderr", "error_message"):
                    case_result.pop(field, None)
            else:
                public_results.append(case_result)

        if student_view:
            public_passed = sum(
                str(case.get("status", "")).lower() == "accepted"
                for case in public_results
            )
            safe_result["results"] = public_results
            safe_result.pop("last_failed_case", None)
            safe_result["first_private_failure"] = (
                first_private_failure
                if len(public_results) == 3
                and public_passed == 3
                else None
            )
            # One intentionally revealed learning case is the only hidden
            # test data included in a student response.
            safe_result["revealed_feedback_case"] = revealed_case
            return safe_result

        safe_result["revealed_feedback_case"] = revealed_case

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


def student_submission_details(submission):
    """Build a submission response with private tests reduced to one safe note."""
    payload = {
        field_name: getattr(submission, field_name)
        for field_name in SubmissionDetails.model_fields
        if hasattr(submission, field_name)
    }
    payload["execution_result"] = redact_hidden_execution(
        submission.execution_result,
        student_view=True,
    )
    return SubmissionDetails(**payload)


async def verify_generated_revision(revision, language, test_cases):
    """Judge generated code before presenting it as a usable reference.

    Only an allowlisted verdict/count summary is persisted. The test inputs and
    outputs remain in the judge and are never copied into the revision payload.
    """
    if not isinstance(revision, dict) or revision.get("revision_source") != "ai":
        return revision
    code = str(revision.get("improved_code") or "").strip()
    if not code or not test_cases:
        safe = dict(revision)
        safe["verification"] = unverified_revision("No judge cases were available to verify this generated draft.")
        return safe
    safe = dict(revision)
    try:
        outcome = await execute_code_sandboxed(
            source_code=code,
            language=language,
            test_cases=test_cases,
            stop_on_first_failure=False,
        )
        safe["verification"] = summarize_revision_verification(outcome)
    except Exception as error:
        logger.warning("Generated revision verification failed: %s", error)
        safe["verification"] = unverified_revision("The judge was unavailable, so this generated draft could not be verified.")
    return safe

app = FastAPI(
    title="Explainable Multi-Agent AI Code Evaluator (Production API)",
    description="Full Backend API with LangGraph Multi-Agent Orchestration, Sandboxed Execution, Problem Repository, and Analytics",
    version="1.0.0"
)

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def seed_instructor_assignments():
    """Ensure instructor assignments and their private judge data exist."""
    # Older database dumps may predate the nullable assignment link on
    # submissions.  Apply the idempotent schema migration before any request
    # can persist a submission.
    ensure_submission_assignment_column()
    ensure_student_profile_columns()
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
        institution=student.institution if student else instructor.institution,
        department=student.department if student else instructor.department,
        year=student.year if student else None,
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


@app.patch("/api/auth/account", response_model=AuthUser)
def update_account(
    payload: AccountUpdateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Persist editable account details and rotate the active session token."""
    full_name = payload.full_name.strip() if payload.full_name is not None else None
    institution = payload.institution.strip() if payload.institution is not None else None
    department = payload.department.strip() if payload.department is not None else None
    year = payload.year.strip() if payload.year is not None else None
    new_password = payload.new_password

    if full_name is not None and not full_name:
        raise HTTPException(status_code=422, detail="Name cannot be empty")
    if any(value == "" for value in (institution, department, year)):
        raise HTTPException(status_code=422, detail="Academic profile fields cannot be empty")
    if new_password is not None:
        if not payload.current_password or not verify_password(payload.current_password, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        if len(new_password) < 12:
            raise HTTPException(status_code=422, detail="New password must be at least 12 characters")
    elif payload.current_password:
        raise HTTPException(status_code=422, detail="Enter a new password to change your password")

    if all(value is None for value in (full_name, new_password, institution, department, year)):
        raise HTTPException(status_code=422, detail="Make at least one account change")

    student = current_user.student_profile
    try:
        if full_name is not None:
            current_user.full_name = full_name
            if student:
                student.name = full_name
        if any(value is not None for value in (institution, department, year)):
            if student is None:
                raise HTTPException(status_code=403, detail="Academic profile updates are available for student accounts")
            if institution is not None:
                student.institution = institution
            if department is not None:
                student.department = department
            if year is not None:
                student.year = year
        if new_password is not None:
            current_user.hashed_password = hash_password(new_password)

        current_user.token_version += 1
        db.commit()
        db.refresh(current_user)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="Unable to save these account changes. Please review your profile details and try again.") from error
    except Exception:
        db.rollback()
        raise

    return _auth_response(current_user, _issue_access_token(current_user))


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
    """Report healthy only when the configured application database responds."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as error:
        logger.warning("Database health check failed: %s", type(error).__name__)
        raise HTTPException(status_code=503, detail="Database connection unavailable") from error
    return {"status": "healthy", "database": "connected"}

# ==========================================
# Problem Repository Endpoints
# ==========================================

@app.get("/api/problems", response_model=List[ProblemListItem])
def list_problems(db: Session = Depends(get_db)):
    """Fetch the DSA practice catalogue, excluding course assignments."""
    problems = (
        db.query(models.Problem)
        .filter(models.Problem.is_public_practice == True)
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
    current_user: models.User = Depends(get_current_user),
):
    """Fetch visible course questions for the current instructor or enrolled student."""
    built_in_ids = set(INSTRUCTOR_PROBLEM_IDS)
    query = db.query(models.Problem, models.Assignment).join(
        models.AssignmentProblem, models.AssignmentProblem.problem_id == models.Problem.id
    ).join(
        models.Assignment, models.Assignment.id == models.AssignmentProblem.assignment_id
    ).join(
        models.Course, models.Course.id == models.Assignment.course_id
    ).filter(models.Course.is_active == True, models.Assignment.status.in_(["ACTIVE", "UPCOMING"]))
    if current_user.role == "instructor":
        instructor = db.query(models.Instructor).filter(models.Instructor.user_id == current_user.id).first()
        if instructor is None:
            raise HTTPException(status_code=403, detail="Instructor profile is not configured")
        query = query.filter(models.Course.instructor_id == instructor.id)
    elif current_user.role == "student":
        student = db.query(models.Student).filter(models.Student.user_id == current_user.id).first()
        if student is None:
            raise HTTPException(status_code=403, detail="Student profile is not configured")
        query = query.join(models.Enrollment, models.Enrollment.course_id == models.Course.id).filter(
            models.Enrollment.student_id == student.student_id,
            models.Enrollment.is_active == True,
        )
    else:
        raise HTTPException(status_code=403, detail="Role cannot access course questions")
    linked = query.order_by(models.Assignment.due_date, models.Problem.title).all()
    records = {problem.id: (problem, assignment) for problem, assignment in linked}
    result = []
    for problem_id in INSTRUCTOR_PROBLEM_IDS:
        if problem_id in records:
            problem, assignment = records[problem_id]
            result.append({
                "id": problem.id, "title": problem.title, "difficulty": problem.difficulty,
                "category": problem.category, "is_instructor_assigned": True,
                "assignment_id": assignment.id,
                "course_code": assignment.course.course_code,
                "due_date": utc_isoformat(assignment.due_date) if assignment.due_date else None,
                "description": problem.description,
                "examples": problem.examples or [],
                "constraints": problem.constraints or [],
                "starter_codes": problem.starter_codes or {},
                "test_cases": load_problem_cases(db, problem, public_only=current_user.role != "instructor"),
                "target_time_complexity": problem.target_time_complexity,
                "target_space_complexity": problem.target_space_complexity,
            })
    for problem_id, (problem, assignment) in records.items():
        if problem_id in built_in_ids:
            continue
        result.append({
            "id": problem.id, "title": problem.title, "difficulty": problem.difficulty,
            "category": problem.category, "is_instructor_assigned": True,
            "assignment_id": assignment.id,
            "course_code": assignment.course.course_code,
            "due_date": utc_isoformat(assignment.due_date) if assignment.due_date else None,
            "description": problem.description,
            "examples": problem.examples or [],
            "constraints": problem.constraints or [],
            "starter_codes": problem.starter_codes or {},
            "test_cases": load_problem_cases(db, problem, public_only=current_user.role != "instructor"),
            "target_time_complexity": problem.target_time_complexity,
            "target_space_complexity": problem.target_space_complexity,
        })
    return result


def instructor_problem_payload(db: Session, problem: models.Problem, assignment: models.Assignment) -> dict:
    """Build the saved question shape returned only to its owning instructor."""
    return {
        "id": problem.id,
        "title": problem.title,
        "difficulty": problem.difficulty,
        "category": problem.category,
        "description": problem.description,
        "examples": problem.examples or [],
        "constraints": problem.constraints or [],
        "starter_codes": problem.starter_codes or {},
        "test_cases": load_problem_cases(db, problem, public_only=False),
        "is_instructor_assigned": True,
        "assignment_id": assignment.id,
        "course_code": assignment.course.course_code,
        "due_date": utc_isoformat(assignment.due_date) if assignment.due_date else None,
    }


@app.post("/api/instructor/problems", response_model=ProblemDetail, status_code=status.HTTP_201_CREATED)
def create_instructor_problem(
    payload: InstructorProblemCreate,
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
):
    course = get_owned_course(db, instructor.id, payload.course_id)
    problem_id = f"instructor-{uuid4().hex}"
    cases = [case.model_dump() for case in payload.test_cases]
    problem = models.Problem(
        id=problem_id,
        title=payload.title,
        difficulty=payload.difficulty,
        category=payload.category,
        description=payload.description,
        examples=[],
        constraints=[],
        starter_codes=payload.starter_codes,
        test_cases=[{"input": c["input"], "expected_output": c["expected_output"], "is_hidden": c["is_hidden"]} for c in cases if not c["is_hidden"]][:3],
        target_time_complexity=payload.target_time_complexity,
        target_space_complexity=payload.target_space_complexity,
        complexity_source="instructor-provided",
        is_public_practice=False,
    )
    assignment = models.Assignment(
        title=payload.title,
        description=payload.description,
        course_id=course.id,
        due_date=payload.due_date,
        status="ACTIVE",
    )
    try:
        db.add(problem)
        db.flush()
        for position, case in enumerate(cases, start=1):
            case_hash = hashlib.sha256(json.dumps(
                [case["input"], case["expected_output"]], ensure_ascii=False
            ).encode()).hexdigest()
            db.add(models.ProblemTestCase(
                id=f"{problem_id}-case-{position}", problem_id=problem_id,
                position=position, visibility="HIDDEN" if case["is_hidden"] else "PUBLIC",
                input_data=case["input"], expected_output=case["expected_output"],
                content_hash=case_hash,
            ))
        db.add(assignment)
        db.flush()
        db.add(models.AssignmentProblem(assignment_id=assignment.id, problem_id=problem_id, position=1))
        for enrolled_student in db.query(models.Student).join(models.Enrollment).filter(
            models.Enrollment.course_id == course.id,
            models.Enrollment.is_active == True,
        ).all():
            create_notification(
                db,
                enrolled_student.user_id,
                "new_assignment",
                "New question posted",
                f"{problem.title} is available in {course.course_code} · {course.title}.",
                "/courses",
            )
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(problem)
    db.refresh(assignment)
    return instructor_problem_payload(db, problem, assignment)


@app.put("/api/instructor/problems/{problem_id}", response_model=ProblemDetail)
def update_instructor_problem(
    problem_id: str,
    payload: InstructorProblemUpdate,
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
):
    problem = db.query(models.Problem).filter(models.Problem.id == problem_id).first()
    assignment = db.query(models.Assignment).join(models.AssignmentProblem).join(models.Course).filter(
        models.AssignmentProblem.problem_id == problem_id,
        models.Course.instructor_id == instructor.id,
    ).first()
    if problem is None or assignment is None:
        raise HTTPException(status_code=404, detail="Question not found")
    if db.query(models.Submission.id).filter(
        (models.Submission.assignment_id == assignment.id) | (models.Submission.problem_id == problem_id)
    ).first():
        raise HTTPException(status_code=409, detail="Question cannot be edited after students have submitted")
    course = get_owned_course(db, instructor.id, payload.course_id)
    if course.id != assignment.course_id:
        raise HTTPException(status_code=422, detail="A question cannot be moved to another course after it is created")
    cases = [case.model_dump() for case in payload.test_cases]
    try:
        problem.title = payload.title
        problem.difficulty = payload.difficulty
        problem.category = payload.category
        problem.description = payload.description
        problem.starter_codes = payload.starter_codes
        problem.target_time_complexity = payload.target_time_complexity
        problem.target_space_complexity = payload.target_space_complexity
        problem.test_cases = [{"input": c["input"], "expected_output": c["expected_output"], "is_hidden": c["is_hidden"]} for c in cases if not c["is_hidden"]][:3]
        assignment.title = payload.title
        assignment.description = payload.description
        assignment.course_id = course.id
        assignment.due_date = payload.due_date
        db.query(models.ProblemTestCase).filter(models.ProblemTestCase.problem_id == problem_id).delete()
        for position, case in enumerate(cases, start=1):
            case_hash = hashlib.sha256(json.dumps(
                [case["input"], case["expected_output"]], ensure_ascii=False
            ).encode()).hexdigest()
            db.add(models.ProblemTestCase(
                id=f"{problem_id}-case-{position}", problem_id=problem_id,
                position=position, visibility="HIDDEN" if case["is_hidden"] else "PUBLIC",
                input_data=case["input"], expected_output=case["expected_output"], content_hash=case_hash,
            ))
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(problem)
    db.refresh(assignment)
    return instructor_problem_payload(db, problem, assignment)


@app.delete("/api/instructor/problems/{problem_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_instructor_problem(
    problem_id: str,
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
):
    problem = db.query(models.Problem).filter(models.Problem.id == problem_id).first()
    assignment = db.query(models.Assignment).join(models.AssignmentProblem).join(models.Course).filter(
        models.AssignmentProblem.problem_id == problem_id,
        models.Course.instructor_id == instructor.id,
    ).first()
    if problem is None or assignment is None:
        raise HTTPException(status_code=404, detail="Question not found")
    if db.query(models.Submission.id).filter(models.Submission.problem_id == problem_id).first():
        raise HTTPException(status_code=409, detail="Question cannot be deleted after students have submitted")
    try:
        db.delete(assignment)
        db.delete(problem)
        db.commit()
    except Exception:
        db.rollback()
        raise

@app.get("/api/problems/{problem_id}", response_model=ProblemDetail)
def get_problem(
    problem_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Fetch a specific problem with its description, examples, constraints, and starter codes."""
    problem_id = canonical_problem_id(problem_id)
    problem = db.query(models.Problem).filter(models.Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem '{problem_id}' not found.")
    assignments = db.query(models.Assignment).join(models.AssignmentProblem).join(models.Course).filter(
        models.AssignmentProblem.problem_id == problem_id,
        models.Assignment.status.in_(["ACTIVE", "UPCOMING"]),
        models.Course.is_active == True,
    ).all()
    assignment = assignments[0] if assignments else None
    if not problem.is_public_practice and assignment is None:
        raise HTTPException(status_code=404, detail="Course question is not available")
    if not problem.is_public_practice:
        if current_user.role == "instructor":
            instructor = db.query(models.Instructor).filter(models.Instructor.user_id == current_user.id).first()
            assignment = next((item for item in assignments if instructor is not None and item.course.instructor_id == instructor.id), None)
            allowed = assignment is not None
        elif current_user.role == "student":
            student = db.query(models.Student).filter(models.Student.user_id == current_user.id).first()
            assignment = next((item for item in assignments if student is not None and db.query(models.Enrollment.id).filter(
                models.Enrollment.student_id == student.student_id,
                models.Enrollment.course_id == item.course_id,
                models.Enrollment.is_active == True,
            ).first() is not None), None)
            allowed = assignment is not None
        else:
            allowed = False
        if not allowed:
            raise HTTPException(status_code=404, detail="Question not found")
    public_cases = load_problem_cases(db, problem, public_only=True)
    return {
        "id": problem.id, "title": problem.title, "difficulty": problem.difficulty,
        "category": problem.category, "description": problem.description,
        "examples": problem.examples, "constraints": problem.constraints,
        "starter_codes": problem.starter_codes, "test_cases": public_cases,
        **({
            "is_instructor_assigned": True,
            "course_code": assignment.course.course_code,
            "due_date": utc_isoformat(assignment.due_date) if assignment.due_date else None,
            "assignment_id": assignment.id,
        } if (assignment and not problem.is_public_practice) else assignment_metadata(problem.id)),
        "target_time_complexity": problem.target_time_complexity,
        "target_space_complexity": problem.target_space_complexity,
    }


@app.post("/api/problems/{problem_id}/hints", response_model=ProblemHintsResponse)
async def generate_problem_hints(
    problem_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Generate three progressive, public-context-only learning hints on demand."""
    problem = db.query(models.Problem).filter(models.Problem.id == canonical_problem_id(problem_id)).first()
    if problem is None or not problem.is_public_practice:
        # Course-only questions must be verified through their assignment route
        # before they can receive assistance.
        course_question = db.query(models.Assignment).join(models.AssignmentProblem).join(models.Course).filter(
            models.AssignmentProblem.problem_id == problem_id,
            models.Assignment.status.in_(["ACTIVE", "UPCOMING"]),
            models.Course.is_active == True,
        ).all()
        allowed = False
        if current_user.role == "student":
            student = db.query(models.Student).filter(models.Student.user_id == current_user.id).first()
            allowed = student is not None and any(db.query(models.Enrollment.id).filter(models.Enrollment.student_id == student.student_id, models.Enrollment.course_id == assignment.course_id, models.Enrollment.is_active == True).first() for assignment in course_question)
        elif current_user.role == "instructor":
            instructor = db.query(models.Instructor).filter(models.Instructor.user_id == current_user.id).first()
            allowed = instructor is not None and any(assignment.course.instructor_id == instructor.id for assignment in course_question)
        if problem is None or not allowed:
            raise HTTPException(status_code=404, detail="Problem not found")
    fallback_hints = ProblemHintsResponse(hints=[
        f"Start by restating what one valid result for {problem.title} must represent, then trace the public examples by hand.",
        f"Use the constraints and the listed topic ({problem.category or 'the problem statement'}) to choose the smallest data structure or state that preserves the information needed for the next step.",
        "Before coding, write three checkpoints: parse the input, update one well-named state for each step, and test boundary cases such as the smallest allowed input.",
    ])
    if llm is None:
        return fallback_hints
    prompt = (
        "Return JSON only: {\"hints\":[string,string,string]}. Generate three progressive hints for the supplied programming problem. "
        "Hint 1 is a gentle observation; Hint 2 names an algorithm/data structure and state; Hint 3 gives language-independent implementation steps. "
        "Never include full source code, hidden tests, expected hidden outputs, or a complete solution."
    )
    payload = {"title": problem.title, "description": problem.description, "constraints": problem.constraints or [], "examples": problem.examples or [], "topic": problem.category, "difficulty": problem.difficulty}
    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        response = await llm.ainvoke([SystemMessage(content=prompt), HumanMessage(content=json.dumps(payload))])
        parsed = ProblemHintsResponse.model_validate_json(extract_clean_json(response.content))
        if any(len(hint.strip()) < 12 for hint in parsed.hints):
            raise ValueError("Generated hints were incomplete")
        return parsed
    except Exception as error:
        logger.warning("Hint generation failed for %s: %s", problem.id, error)
        return fallback_hints

# ==========================================
# Code Execution & Submission Endpoints
# ==========================================

@app.post("/api/submissions/run", response_model=QuickRunResponse)
async def quick_run_code(
    payload: QuickRunRequest,
    db: Session = Depends(get_db),
    student: models.Student = Depends(get_current_student),
):
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

    public_only = os.getenv(
        "PUBLIC_ONLY_EXECUTION",
        "false",
    ).lower() in {"1", "true", "yes"}

    if public_only:
        stored_cases = [
            case
            for case in stored_cases
            if str(case.visibility).upper() == "PUBLIC"
        ]

    test_cases = [
        {
            "id": case.id,
            "input": case.input_data,
            "expected_output": case.expected_output,
            "is_hidden": str(case.visibility).upper() == "HIDDEN",
            "time_limit": case.time_limit_seconds,
            "memory_limit": case.memory_limit_mb,
        }
        for case in stored_cases
    ]

    if not test_cases and public_only:
        raise HTTPException(
            status_code=400,
            detail="No public test cases are available for this problem",
        )

    if not test_cases and not public_only:
        tc_raw = problem.test_cases

        if isinstance(tc_raw, str):
            try:
                test_cases = json.loads(tc_raw)
            except Exception:
                test_cases = []
        elif isinstance(tc_raw, list):
            test_cases = tc_raw

    if not test_cases:
        raise HTTPException(
            status_code=400,
            detail="No test cases are configured for this problem",
        )
    
    # Docker execution decides correctness. Complexity begins with a local AST
    # pass; lower-confidence results can later use observed runtime evidence
    # before an optional independent AI review.
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
    static_complexity = analyze_static_complexity(payload.code, payload.language)

    async def run_local_complexity_analysis(dynamic_complexity=None):
        evidence = await analyze_submission_complexity(
            source_code=payload.code,
            language=payload.language,
            static_result=static_complexity,
            dynamic_result=dynamic_complexity,
        )

        if evidence.final is None:
            return {
                "status": "REVIEW_REQUIRED",
                "method": "none",
                "confidence": 0.0,
                "explanation": "No complexity result is available.",
            }

        # Preserve the independent, code-derived estimates for the student's
        # saved report.  This deliberately excludes the private problem
        # benchmark used later by scoring.
        result = asdict(evidence.final)
        if evidence.static is not None:
            result["ast_estimate"] = {
                "time_complexity": evidence.static.time_complexity,
                "space_complexity": evidence.static.space_complexity,
                "status": evidence.static.status,
                "method": evidence.static.method,
            }
        if evidence.ai_review is not None:
            result["ai_estimate"] = {
                "time_complexity": evidence.ai_review.get("ai_time_complexity"),
                "space_complexity": evidence.ai_review.get("ai_space_complexity"),
                "status": evidence.ai_review.get("status"),
            }
        if evidence.dynamic is not None:
            result["runtime_estimate"] = {
                "time_complexity": evidence.dynamic.time_complexity,
                "space_complexity": evidence.dynamic.space_complexity,
                "status": evidence.dynamic.status,
                "method": evidence.dynamic.method,
                "evidence_quality": evidence.dynamic.evidence_quality,
            }
        return result

    try:
        execution_outcome = await execution_task
    except Exception as exc:
        execution_outcome = exc

    if isinstance(execution_outcome, Exception):
        logger.error("Sandbox execution failed: %s", execution_outcome)
        raise HTTPException(
            status_code=502,
            detail="Code execution service is unavailable",
        )

    exec_result = execution_outcome
    if exec_result.get("execution_status") == "system_error":
        logger.error("Sandbox execution service was unavailable: %s", exec_result.get("compile_error"))
        raise HTTPException(
            status_code=503,
            detail="Code execution service is temporarily unavailable. Please retry your submission.",
        )
    # The agent workflow needs verdicts and counts, not the input/output of a
    # private judge case. Redact only after the execution task has completed.
    safe_exec_result = redact_hidden_execution(exec_result)
    dynamic_complexity = None
    if static_complexity.confidence < settings.COMPLEXITY_AST_DIRECT_CONFIDENCE:
        dynamic_complexity = profile_execution_results(test_cases, exec_result)

    try:
        complexity_outcome = await run_local_complexity_analysis(dynamic_complexity)
    except Exception as exc:
        complexity_outcome = exc
    if isinstance(complexity_outcome, Exception):
        logger.warning(
            "Complexity analysis failed: %s",
            complexity_outcome,
        )
        precomputed_complexity_analysis = unavailable_analysis(
            "The complexity analysis service was unavailable "
            "for this submission."
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
            # Private scoring metadata. It never enters a model prompt or a
            # student response; it only lets the scorer project fixed-size
            # parameters such as k <= 100 onto its rank ladder.
            "constraints": [
                *(problem.constraints or []),
                # Legacy imported problems can have an empty JSON constraints
                # array while retaining the same published constraints in
                # their statement.  This remains backend-only score metadata.
                problem.description or "",
            ],
        },
        "precomputed_complexity_analysis": precomputed_complexity_analysis,
        "assessment_flags": {},
        "style_score": None,
        "style_details": None,
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
    safe_execution_result = redact_hidden_execution(
        final_state.get("execution_result"),
        student_view=True,
    )

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
        execution_result=safe_execution_result,
        complexity_details=final_state.get("complexity_details"),
        score_breakdown=final_state.get("score_breakdown"),
        assessment_flags=final_state.get("assessment_flags"),
        feedback=final_state.get("feedback"),
        recommendations=final_state.get("recommendations"),
        improved_code=final_state.get("improved_code"),
        projected_score=final_state.get("projected_score")
    )
    
    db.add(new_submission)
    if assignment is not None:
        create_notification(
            db,
            assignment.course.instructor.user_id,
            "new_submission",
            "New evaluated submission",
            f"{student.name} submitted {problem.title} for {assignment.course.course_code} · {assignment.course.title}.",
            f"/instructor/analytics?assignmentId={assignment.id}&courseId={assignment.course_id}",
        )
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
        score_breakdown=final_state.get("score_breakdown"),
        style_score=new_submission.style_score,
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
    return student_submission_details(submission)


@app.post("/api/submissions/{submission_id}/revision")
async def regenerate_submission_revision(
    submission_id: str,
    db: Session = Depends(get_db),
    student: models.Student = Depends(get_current_student),
):
    """Generate and persist a missing task-specific rewrite for a saved attempt."""
    submission = db.query(models.Submission).filter(
        models.Submission.submission_id == submission_id,
        models.Submission.student_id == student.student_id,
    ).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    problem = db.query(models.Problem).filter(
        models.Problem.id == submission.problem_id,
    ).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    policy = getattr(submission.assignment, "revision_policy", "VERIFIED_REFERENCE") if submission.assignment_id else "VERIFIED_REFERENCE"
    if policy == "HINTS_ONLY":
        raise HTTPException(status_code=403, detail="Your instructor has enabled hints only for this assignment.")

    state: EvaluationState = {
        "problem": {
            "title": problem.title,
            "statement": problem.description,
            "constraints": problem.constraints or [],
        },
        "submission": {"source_code": submission.code, "language": submission.language},
        "execution_result": redact_hidden_execution(submission.execution_result or {}, student_view=True),
        "feedback": submission.feedback,
        "complexity_details": submission.complexity_details,
        "style_details": (submission.feedback or {}).get("style_details") if isinstance(submission.feedback, dict) else None,
    }
    revision = (await revision_node(state)).get("improved_code") or {}
    if revision.get("revision_source") != "ai" or not revision.get("improved_code"):
        # AI code generation is optional.  Preserve task-specific guidance so
        # a student still receives a useful next step when the provider is
        # unavailable, but never label it as generated or verified code.
        revision = dict(revision)
        revision["verification"] = {
            "status": "guidance_only",
            "verified": False,
            "message": "Task-specific guidance is available, but no generated code was produced or verified.",
        }
        submission.improved_code = revision
        db.commit()
        return {"improved_code": revision}

    revision = await verify_generated_revision(
        revision, submission.language, load_problem_cases(db, problem, public_only=False),
    )
    if policy == "EXPLAIN_CHANGES":
        revision = dict(revision)
        revision["improved_code"] = ""
        revision["verification"] = {"status": "explanation_only", "verified": False, "message": "Your instructor allows explanations of changes but not full revised code for this assignment."}
    submission.improved_code = revision
    db.commit()
    return {"improved_code": revision}

@app.get("/api/submissions", response_model=List[SubmissionDetails])
def list_submissions(
    student_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    student: models.Student = Depends(get_current_student),
):
    if student_id is not None and student_id != student.student_id:
        raise HTTPException(status_code=403, detail="Cannot access another student's submissions")
    query = db.query(models.Submission).filter(models.Submission.student_id == student.student_id)
    return [
        student_submission_details(submission)
        for submission in query.order_by(models.Submission.created_at.desc()).all()
    ]

# ==========================================
# Student & Instructor Analytics Endpoints
# ==========================================

# Submission timestamps are stored in UTC. Use the app's local calendar when
# determining consecutive activity days so late-night submissions count for
# the day students see in the UI.
STUDENT_ACTIVITY_TIMEZONE = ZoneInfo("Asia/Kolkata")


def calculate_submission_streak(submissions: list[models.Submission]) -> int:
    activity_days = set()
    for submission in submissions:
        created_at = submission.created_at
        if created_at is None:
            continue
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        activity_days.add(created_at.astimezone(STUDENT_ACTIVITY_TIMEZONE).date())

    today = datetime.now(STUDENT_ACTIVITY_TIMEZONE).date()
    # A streak remains current through the day after the last activity day.
    current_day = today if today in activity_days else today - timedelta(days=1)
    if current_day not in activity_days:
        return 0

    streak = 0
    while current_day in activity_days:
        streak += 1
        current_day -= timedelta(days=1)
    return streak

def build_student_analytics(
    db: Session,
    student: models.Student,
    *,
    independent_only: bool,
) -> StudentAnalyticsResponse:
    """Build personal analytics with an explicit submission-source scope."""
    query = db.query(models.Submission).filter(
        models.Submission.student_id == student.student_id,
        models.Submission.status == "EVALUATED",
    )
    if independent_only:
        query = query.filter(models.Submission.assignment_id == None)
    submissions = query.order_by(models.Submission.created_at).all()
    latest = latest_assessed_attempts(submissions, preserve_assignment=False)
    avg_overall = average_score(latest)
    avg_correctness = average_score(latest, "correctness_score")
    avg_style = average_score(latest, "style_score")
    time_scores = [complexity_dimension_percent(submission.complexity_details, "time") for submission in latest]
    space_scores = [complexity_dimension_percent(submission.complexity_details, "space") for submission in latest]
    total_problems = db.query(models.Problem).filter(models.Problem.is_public_practice == True).count()
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
        {"name": "Time Complexity", "value": average_values([value for value in time_scores if value is not None]), "color": "#06b6d4"},
        {"name": "Space Complexity", "value": average_values([value for value in space_scores if value is not None]), "color": "#f59e0b"},
        {"name": "Code Quality & Style", "value": avg_style, "color": "#8b5cf6"},
    ]
    category_breakdown = [category for category in category_breakdown if category["value"] is not None]

    return StudentAnalyticsResponse(
        overall_score=avg_overall,
        streak_days=calculate_submission_streak(submissions),
        xp=student.xp,
        problems_solved=unique_solved,
        total_problems=total_problems,
        score_trend=score_trend,
        category_breakdown=category_breakdown,
        weak_topics=weak_topics
    )


@app.get("/api/analytics/student/{student_id}", response_model=StudentAnalyticsResponse)
def get_student_analytics(
    student_id: str,
    db: Session = Depends(get_db),
    student: models.Student = Depends(get_current_student),
):
    """Dashboard overview: independent practice plus enrolled course work."""
    if student_id != student.student_id:
        raise HTTPException(status_code=404, detail="Student not found")
    return build_student_analytics(db, student, independent_only=False)


@app.get("/api/analytics/student/{student_id}/practice", response_model=StudentAnalyticsResponse)
def get_student_practice_analytics(
    student_id: str,
    db: Session = Depends(get_db),
    student: models.Student = Depends(get_current_student),
):
    """Analytics & Progress: independent practice only, never course work."""
    if student_id != student.student_id:
        raise HTTPException(status_code=404, detail="Student not found")
    return build_student_analytics(db, student, independent_only=True)


@app.get("/api/student/recommendations")
def get_student_recommendations(
    db: Session = Depends(get_db),
    student: models.Student = Depends(get_current_student),
):
    """Evidence-based recommendations from independent practice only."""
    submissions = db.query(models.Submission).filter(
        models.Submission.student_id == student.student_id,
        models.Submission.assignment_id == None,
        models.Submission.status == "EVALUATED",
        models.Submission.overall_score.isnot(None),
    ).all()
    latest = latest_assessed_attempts(submissions, preserve_assignment=False)
    problems = db.query(models.Problem).filter(models.Problem.is_public_practice == True).order_by(models.Problem.id).all()
    problem_by_id = {problem.id: problem for problem in problems}
    scores_by_topic: dict[str, list[float]] = {}
    mastered = set()
    for submission in latest:
        problem = problem_by_id.get(submission.problem_id)
        if problem is None:
            continue
        scores_by_topic.setdefault(problem.category or "Uncategorized", []).append(submission.overall_score)
        if submission.overall_score >= 70:
            mastered.add(submission.problem_id)
    topics = [
        {"topic": topic, "average_score": round(sum(scores) / len(scores), 1), "assessed_problems": len(scores), "reason": f"Your independent-practice average in {topic} is {round(sum(scores) / len(scores), 1)}%."}
        for topic, scores in scores_by_topic.items()
        if scores and sum(scores) / len(scores) < 70
    ]
    topics.sort(key=lambda item: (item["average_score"], -item["assessed_problems"], item["topic"]))
    selected_topics = [item["topic"] for item in topics[:3]]
    candidates = [problem for problem in problems if problem.id not in mastered and (not selected_topics or problem.category in selected_topics)]
    if not latest:
        candidates = problems[:3]
        reason = "Starter recommendation: complete practice assessments to personalize this list."
    else:
        reason = "Recommended from your independent-practice topic evidence."
    return {
        "topics": topics[:3],
        "problems": [{"id": problem.id, "title": problem.title, "difficulty": problem.difficulty, "category": problem.category, "reason": reason} for problem in candidates[:3]],
        "scope": "independent_practice_only",
    }

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
        "topic_performance": topic_performance(db, latest),
        **student_score_extremes(db, latest),
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
            .join(models.User, models.Student.user_id == models.User.id)
            .filter(
                models.User.role == "student",
                models.User.is_active == True,
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


@app.get("/api/instructor/roster", response_model=List[StudentRosterItem])
def get_instructor_roster(
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
    course_id: Optional[int] = None,
):
    """Return one live performance row for every student in the instructor's active courses."""
    courses = db.query(models.Course).filter(
        models.Course.instructor_id == instructor.id,
        models.Course.is_active == True,
    ).all()
    if course_id is not None:
        course = get_owned_course(db, instructor.id, course_id)
        courses = [course] if course.is_active else []
    course_ids = [course.id for course in courses]
    if not course_ids:
        return []

    enrollments = db.query(models.Enrollment).filter(
        models.Enrollment.course_id.in_(course_ids),
        models.Enrollment.is_active == True,
    ).all()
    enrolled_courses: dict[str, set[int]] = {}
    for enrollment in enrollments:
        enrolled_courses.setdefault(enrollment.student_id, set()).add(enrollment.course_id)

    assignments = db.query(models.Assignment).filter(
        models.Assignment.course_id.in_(course_ids)
    ).all()
    assignment_ids = [assignment.id for assignment in assignments]
    courses_with_assignments = {assignment.course_id for assignment in assignments}
    submissions = db.query(models.Submission).filter(
        models.Submission.assignment_id.in_(assignment_ids)
    ).all() if assignment_ids else []
    submissions_by_student: dict[str, list[models.Submission]] = {}
    for submission in submissions:
        if submission.student_id in enrolled_courses:
            submissions_by_student.setdefault(submission.student_id, []).append(submission)

    categories = {
        problem_id: category or "Uncategorized"
        for problem_id, category in db.query(models.Problem.id, models.Problem.category).all()
    }
    students = db.query(models.Student).filter(
        models.Student.student_id.in_(list(enrolled_courses))
    ).all()

    roster: list[StudentRosterItem] = []
    for student in students:
        student_submissions = submissions_by_student.get(student.student_id, [])
        latest = latest_assessed_attempts(student_submissions)
        avg_score = average_score(latest)
        category_scores: dict[str, list[float]] = {}
        for submission in latest:
            category_scores.setdefault(categories.get(submission.problem_id, "Uncategorized"), []).append(submission.overall_score)
        weak_topics = sorted(
            category for category, scores in category_scores.items()
            if scores and sum(scores) / len(scores) < 60
        )

        chronological = sorted(
            (submission for submission in student_submissions if submission.status == "EVALUATED" and submission.overall_score is not None),
            key=lambda submission: (submission.created_at or datetime.min, submission.id or 0),
        )
        trend = "neutral"
        if len(chronological) >= 2:
            change = chronological[-1].overall_score - chronological[-2].overall_score
            trend = "up" if change >= 5 else "down" if change <= -5 else "neutral"

        has_coursework = bool(enrolled_courses[student.student_id] & courses_with_assignments)
        status_value = "On Track"
        if avg_score is not None and avg_score < 50:
            status_value = "At Risk"
        elif avg_score is not None and (avg_score < 70 or weak_topics):
            status_value = "Needs Attention"
        elif not student_submissions and has_coursework:
            status_value = "Needs Attention"

        roster.append(StudentRosterItem(
            id=student.student_id,
            name=student.name,
            rollNumber=student.student_id,
            email=student.email,
            department=student.department,
            enrolled_course_count=len(enrolled_courses[student.student_id]),
            submissions_count=len(student_submissions),
            avg_score=avg_score,
            trend=trend,
            weak_topics=weak_topics,
            status=status_value,
        ))
    return sorted(roster, key=lambda item: (item.name.lower(), item.rollNumber.lower()))

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

def course_request_response(request: models.EnrollmentRequest) -> CourseRequestResponse:
    return CourseRequestResponse(
        id=request.id,
        student_id=request.student.student_id,
        student_name=request.student.name,
        course_id=request.course.id,
        course_code=request.course.course_code,
        course_title=request.course.title,
        status=request.status,
        requested_at=request.requested_at,
    )


@app.get("/api/instructor/course-requests", response_model=List[CourseRequestResponse])
def get_instructor_course_requests(
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
    course_id: Optional[int] = None,
):
    query = db.query(models.EnrollmentRequest).join(models.Course).filter(
        models.Course.instructor_id == instructor.id,
        models.Course.is_active == True,
        models.EnrollmentRequest.status == "PENDING",
    )
    if course_id is not None:
        get_owned_course(db, instructor.id, course_id)
        query = query.filter(models.Course.id == course_id)
    requests = query.order_by(models.EnrollmentRequest.requested_at.asc()).all()
    return [course_request_response(item) for item in requests]


@app.post("/api/instructor/course-requests/{request_id}/{decision}", response_model=CourseRequestResponse)
def decide_course_request(
    request_id: int,
    decision: str,
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
):
    if decision not in {"approve", "reject"}:
        raise HTTPException(status_code=400, detail="Decision must be approve or reject")
    request = db.query(models.EnrollmentRequest).filter(models.EnrollmentRequest.id == request_id).first()
    if request is None:
        raise HTTPException(status_code=404, detail="Course request not found")
    course = get_owned_course(db, instructor.id, request.course_id)
    if request.status != "PENDING":
        raise HTTPException(status_code=409, detail="This course request has already been handled")
    student = request.student
    if decision == "approve":
        enrollment = db.query(models.Enrollment).filter(
            models.Enrollment.student_id == student.student_id,
            models.Enrollment.course_id == course.id,
        ).first()
        if enrollment is None:
            db.add(models.Enrollment(student_id=student.student_id, course_id=course.id, is_active=True))
        else:
            enrollment.is_active = True
        request.status = "APPROVED"
        notice = ("Course request approved", f"Your request to join {course.course_code} · {course.title} was approved.", "/courses")
    else:
        request.status = "REJECTED"
        notice = ("Course request update", f"Your request to join {course.course_code} · {course.title} was not approved. You may request again later.", "/courses")
    request.responded_at = datetime.utcnow()
    create_notification(db, student.user_id, "course_request_decision", notice[0], notice[1], notice[2])
    db.commit()
    db.refresh(request)
    return course_request_response(request)


@app.post("/api/student/course-requests", response_model=CourseRequestResponse, status_code=status.HTTP_201_CREATED)
def request_course_enrollment(
    payload: CourseRequestCreate,
    response: Response,
    db: Session = Depends(get_db),
    student: models.Student = Depends(get_current_student),
):
    course = db.query(models.Course).filter(
        models.Course.id == payload.course_id,
        models.Course.is_active == True,
    ).first()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.student_id == student.student_id,
        models.Enrollment.course_id == course.id,
        models.Enrollment.is_active == True,
    ).first()
    if enrollment is not None:
        raise HTTPException(status_code=409, detail="You are already enrolled in this course")
    pending = db.query(models.EnrollmentRequest).filter(
        models.EnrollmentRequest.student_id == student.student_id,
        models.EnrollmentRequest.course_id == course.id,
        models.EnrollmentRequest.status == "PENDING",
    ).first()
    if pending is not None:
        response.status_code = status.HTTP_200_OK
        return course_request_response(pending)
    request = models.EnrollmentRequest(student_id=student.student_id, course_id=course.id, status="PENDING")
    db.add(request)
    db.flush()
    create_notification(
        db,
        course.instructor.user_id,
        "course_join_request",
        "New course join request",
        f"{student.name} requested to join {course.course_code} · {course.title}.",
        f"/instructor/courses/{course.id}?tab=requests",
    )
    db.commit()
    db.refresh(request)
    return course_request_response(request)


@app.delete("/api/student/course-requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_student_course_request(
    request_id: int,
    db: Session = Depends(get_db),
    student: models.Student = Depends(get_current_student),
):
    request = db.query(models.EnrollmentRequest).filter(
        models.EnrollmentRequest.id == request_id,
        models.EnrollmentRequest.student_id == student.student_id,
        models.EnrollmentRequest.status == "PENDING",
    ).first()
    if request is None:
        raise HTTPException(status_code=404, detail="Pending course request not found")
    request.status = "CANCELLED"
    request.responded_at = datetime.utcnow()
    course = request.course
    create_notification(
        db,
        course.instructor.user_id,
        "course_request_cancelled",
        "Course join request withdrawn",
        f"{student.name} withdrew their request to join {course.course_code} · {course.title}.",
        f"/instructor/courses/{course.id}?tab=requests",
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.delete("/api/student/courses/{course_id}/enrollment", status_code=status.HTTP_204_NO_CONTENT)
def leave_student_course(
    course_id: int,
    db: Session = Depends(get_db),
    student: models.Student = Depends(get_current_student),
):
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.student_id == student.student_id,
        models.Enrollment.course_id == course_id,
        models.Enrollment.is_active == True,
    ).first()
    if enrollment is None:
        raise HTTPException(status_code=404, detail="Active enrollment not found")
    course = enrollment.course
    enrollment.is_active = False
    create_notification(
        db,
        course.instructor.user_id,
        "student_left_course",
        "Student left course",
        f"{student.name} left {course.course_code} · {course.title}.",
        f"/instructor/courses/{course.id}?tab=students",
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/notifications", response_model=List[NotificationResponse])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return db.query(models.Notification).filter(
        models.Notification.recipient_user_id == current_user.id,
    ).order_by(models.Notification.created_at.desc(), models.Notification.id.desc()).limit(100).all()


@app.patch("/api/notifications/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.recipient_user_id == current_user.id,
    ).first()
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


@app.post("/api/notifications/read-all", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db.query(models.Notification).filter(
        models.Notification.recipient_user_id == current_user.id,
        models.Notification.is_read == False,
    ).update({models.Notification.is_read: True}, synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/student/available-courses", response_model=List[CourseDiscoveryResponse])
def get_available_student_courses(
    db: Session = Depends(get_db),
    student: models.Student = Depends(get_current_student),
):
    courses = db.query(models.Course).join(models.Instructor).filter(
        models.Course.is_active == True,
    ).order_by(models.Course.course_code, models.Course.title).all()
    result = []
    for course in courses:
        enrollment = db.query(models.Enrollment).filter(
            models.Enrollment.student_id == student.student_id,
            models.Enrollment.course_id == course.id,
            models.Enrollment.is_active == True,
        ).first()
        pending = db.query(models.EnrollmentRequest).filter(
            models.EnrollmentRequest.student_id == student.student_id,
            models.EnrollmentRequest.course_id == course.id,
            models.EnrollmentRequest.status == "PENDING",
        ).first()
        result.append(CourseDiscoveryResponse(
            id=course.id,
            course_code=course.course_code,
            title=course.title,
            term=course.term,
            description=course.description,
            instructor_name=course.instructor.user.full_name,
            enrollment_status="ENROLLED" if enrollment else "PENDING" if pending else "AVAILABLE",
            request_id=pending.id if pending else None,
        ))
    return result

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

    # An enrollment must point to an authenticated student account.  A legacy
    # profile without a linked user cannot sign in to see the course.
    student_account = db.query(models.User).filter(
        models.User.id == student.user_id,
        models.User.role == "student",
        models.User.is_active == True,
    ).first()
    if student_account is None:
        raise HTTPException(
            status_code=422,
            detail="This student profile has no active student account. Ask the student to register before enrolling them.",
        )
    
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
        was_active = existing.is_active
        existing.is_active = True
        if not was_active:
            create_notification(db, student_account.id, "course_enrollment", "Added to a course", f"Your instructor added you to {course.course_code} · {course.title}.", "/courses")
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
    create_notification(db, student_account.id, "course_enrollment", "Added to a course", f"Your instructor added you to {course.course_code} · {course.title}.", "/courses")
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
    create_notification(
        db,
        enrollment.student.user_id,
        "enrollment_removed",
        "Course access ended",
        f"Your enrollment in {enrollment.course.course_code} · {enrollment.course.title} was removed by the instructor.",
        "/courses",
    )
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
        assignments = db.query(models.Assignment).filter(
            models.Assignment.course_id == course.id,
            models.Assignment.status.in_(["ACTIVE", "UPCOMING"]),
        ).all()
        assignment_ids = [assignment.id for assignment in assignments]
        assigned_problem_ids = {
            problem_id for (problem_id,) in db.query(models.AssignmentProblem.problem_id).filter(
                models.AssignmentProblem.assignment_id.in_(assignment_ids)
            ).all()
        } if assignment_ids else set()
        assessed = db.query(models.Submission).filter(
            models.Submission.student_id == student.student_id,
            models.Submission.assignment_id.in_(assignment_ids),
            models.Submission.status == "EVALUATED",
            models.Submission.overall_score.isnot(None),
        ).all() if assignment_ids else []
        latest = latest_assessed_attempts(assessed, preserve_assignment=False)
        completed_problem_ids = {submission.problem_id for submission in latest if submission.problem_id in assigned_problem_ids}
        completed = len(completed_problem_ids)
        total_assigned = len(assigned_problem_ids)
        result.append(StudentCourseResponse(
            id=course.id,
            course_code=course.course_code,
            title=course.title,
            term=course.term,
            description=course.description,
            instructor_id=course.instructor_id,
            is_active=course.is_active,
            created_at=course.created_at,
            assignments_count=len(assignments),
            instructor_name=(course.instructor.user.full_name if course.instructor and course.instructor.user and course.instructor.user.full_name else "Instructor details unavailable"),
            average_score=average_score(latest),
            completed_questions=completed,
            pending_questions=max(0, total_assigned - completed),
            progress_percent=round(completed / total_assigned * 100, 1) if total_assigned else None,
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
            revision_policy=assignment.revision_policy,
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
            revision_policy=assignment.revision_policy,
        )
        db.add(new_assignment)
        db.flush()
        for position, problem_id in enumerate(assignment.problem_ids, start=1):
            db.add(models.AssignmentProblem(
                assignment_id=new_assignment.id,
                problem_id=problem_id,
                position=position,
            ))
        enrolled_students = db.query(models.Student).join(models.Enrollment).filter(
            models.Enrollment.course_id == assignment.course_id,
            models.Enrollment.is_active == True,
        ).all()
        for enrolled_student in enrolled_students:
            create_notification(
                db,
                enrolled_student.user_id,
                "new_assignment",
                "New assignment posted",
                f"{new_assignment.title} is available in {new_assignment.course.course_code} · {new_assignment.course.title}.",
                "/courses",
            )
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
        revision_policy=new_assignment.revision_policy,
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
        revision_policy=assignment.revision_policy,
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

def _similarity_source_without_comments(code: str, language: Optional[str] = None) -> str:
    """Remove common source comments without treating comment text as code.

    This intentionally keeps C/C++ preprocessor directives and quoted strings
    intact.  It is a lightweight lexical pass for the overlap screen, not a
    language parser; AST analysis remains responsible for structural facts.
    """
    source, output, index = code or "", [], 0
    hash_starts_comment = (language or "").lower() not in {"c", "cpp", "c++", "objective-c", "objective-cpp"}
    line_start = True
    while index < len(source):
        char, next_char = source[index], source[index + 1] if index + 1 < len(source) else ""
        if char in {"'", '"'}:
            quote = char
            output.append(char)
            index += 1
            while index < len(source):
                output.append(source[index])
                if source[index] == "\\" and index + 1 < len(source):
                    index += 1
                    output.append(source[index])
                elif source[index] == quote:
                    index += 1
                    break
                index += 1
            line_start = False
            continue
        if char == "/" and next_char == "*":
            end = source.find("*/", index + 2)
            index = len(source) if end < 0 else end + 2
            continue
        if char == "/" and next_char == "/":
            end = source.find("\n", index + 2)
            index = len(source) if end < 0 else end
            continue
        if char == "#" and hash_starts_comment:
            if not (line_start and re.match(r"#\s*include\b", source[index:])):
                end = source.find("\n", index + 1)
                index = len(source) if end < 0 else end
                continue
        output.append(char)
        line_start = char == "\n" or (line_start and char.isspace())
        index += 1
    return "".join(output)


def similarity_tokens(code: str, language: Optional[str] = None) -> set[tuple[str, ...]]:
    """Create identifier-normalized token shingles for a conservative overlap screen.

    Comments are deliberately discarded.  A class-provided starter comment or
    a student's explanatory notes should never be the reason two submissions
    become a review lead; the comparison is about executable structure.
    """
    source = _similarity_source_without_comments(code, language)
    raw_tokens = re.findall(r"[A-Za-z_][A-Za-z_0-9]*|\d+(?:\.\d+)?|==|!=|<=|>=|\S", source)
    keywords = {"if", "else", "for", "while", "return", "def", "class", "function", "int", "float", "double", "string", "const", "let", "var", "void", "public", "private", "new", "true", "false", "null", "None", "import", "from", "include", "using", "namespace", "try", "catch", "break", "continue"}
    tokens = [token if token in keywords or not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", token) else "IDENT" for token in raw_tokens]
    return {tuple(tokens[index:index + 5]) for index in range(max(0, len(tokens) - 4))}


def _similarity_student_payload(student: models.Student, submission: models.Submission) -> dict[str, Any]:
    """Assessment context shown only after an instructor opens a group."""
    return {
        "id": student.student_id,
        "name": student.name,
        "rollNumber": student.student_id,
        "submissionId": submission.submission_id,
        "submittedAt": utc_isoformat(submission.created_at),
        "language": submission.language,
        "overallScore": round(submission.overall_score, 1) if submission.overall_score is not None else None,
        "correctnessScore": round(submission.correctness_score, 1) if submission.correctness_score is not None else None,
        "timeScore": complexity_dimension_percent(submission.complexity_details, "time"),
        "spaceScore": complexity_dimension_percent(submission.complexity_details, "space"),
        "styleScore": round(submission.style_score, 1) if submission.style_score is not None else None,
    }


def _latest_similarity_rows(rows: list[tuple[Any, ...]]) -> list[tuple[Any, ...]]:
    """Choose the newest evaluated submission for one assignment/student/problem.

    Similarity review must never retain an earlier source file after a student
    resubmits.  Assignment is intentionally part of the key: the same global
    problem can be reused by two different course assignments.
    """
    latest: dict[tuple[int, int, str, str], tuple[Any, ...]] = {}
    for row in rows:
        submission, assignment, course, _student, _problem = row
        key = (course.id, assignment.id, submission.student_id, submission.problem_id)
        current = latest.get(key)
        current_marker = ((current[0].created_at or datetime.min), current[0].id or 0) if current else None
        candidate_marker = (submission.created_at or datetime.min, submission.id or 0)
        if current is None or candidate_marker > current_marker:
            latest[key] = row
    return list(latest.values())


def instructor_similarity_cases(db: Session, instructor_id: int, course_id: Optional[int] = None) -> list[dict[str, Any]]:
    rows = db.query(models.Submission, models.Assignment, models.Course, models.Student, models.Problem).join(
        models.Assignment, models.Assignment.id == models.Submission.assignment_id
    ).join(models.Course, models.Course.id == models.Assignment.course_id).join(
        models.Student, models.Student.student_id == models.Submission.student_id
    ).join(models.Problem, models.Problem.id == models.Submission.problem_id).filter(
        models.Course.instructor_id == instructor_id,
        models.Course.is_active == True,
        models.Submission.status == "EVALUATED",
        *([models.Course.id == course_id] if course_id is not None else []),
    ).order_by(models.Submission.created_at.desc(), models.Submission.id.desc()).all()
    latest_rows = _latest_similarity_rows(rows)
    grouped: dict[tuple[int, int, str], list[tuple[Any, ...]]] = {}
    for row in latest_rows:
        submission, assignment, course, _student, _problem = row
        grouped.setdefault((course.id, assignment.id, submission.problem_id), []).append(row)

    fingerprints = {
        submission.submission_id: structural_fingerprint(submission.code, submission.language)
        for submission, _assignment, _course, _student, _problem in latest_rows
    }

    alerts = []
    for submissions in grouped.values():
        for left, right in combinations(submissions, 2):
            sub_a, assignment_a, course_a, student_a, problem_a = left
            sub_b, _assign_b, _course_b, student_b, _problem_b = right
            if student_a.student_id == student_b.student_id:
                continue
            tokens_a = similarity_tokens(sub_a.code, sub_a.language)
            tokens_b = similarity_tokens(sub_b.code, sub_b.language)
            if not tokens_a or not tokens_b:
                continue
            overlap = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
            percentage = round(overlap * 100)
            if percentage < 72:
                continue
            fingerprint_a = fingerprints[sub_a.submission_id]
            fingerprint_b = fingerprints[sub_b.submission_id]
            ast_overlap = structural_overlap(fingerprint_a, fingerprint_b)
            pair_id = ":".join(sorted((sub_a.submission_id, sub_b.submission_id)))
            review_status = (sub_a.assessment_flags or {}).get("similarity_reviews", {}).get(pair_id, "open")
            if review_status == "dismissed":
                continue
            created_at = sub_b.created_at or sub_a.created_at
            alerts.append({
                "id": pair_id,
                "problemId": problem_a.id,
                "problemTitle": problem_a.title,
                "courseId": course_a.id,
                "courseTitle": course_a.title,
                "assignmentId": assignment_a.id,
                "assignmentTitle": assignment_a.title,
                "studentA": _similarity_student_payload(student_a, sub_a),
                "studentB": _similarity_student_payload(student_b, sub_b),
                "similarityPercentage": percentage,
                "riskLevel": "High" if percentage >= 85 else "Medium",
                "matchedLinesCount": len(tokens_a & tokens_b),
                "timestamp": utc_isoformat(created_at) if created_at else "Unknown",
                "studentACodeSnippet": sub_a.code[:12000],
                "studentBCodeSnippet": sub_b.code[:12000],
                "astOverlap": round(ast_overlap * 100),
                "evidenceExplanation": structural_explanation(fingerprint_a, fingerprint_b, ast_overlap),
                "aiAuditNotes": "Automated normalized token and AST-structure screening. Shared boilerplate and common solution patterns can produce matches; this is a review lead, not a finding of misconduct.",
                "reviewStatus": review_status,
            })
    return sorted(alerts, key=lambda alert: (alert["similarityPercentage"], alert["timestamp"]), reverse=True)[:100]


def instructor_approach_groups(db: Session, instructor_id: int, course_id: Optional[int] = None) -> list[dict[str, Any]]:
    """Return same-problem algorithm groups separately from overlap candidates."""
    return build_approach_groups(instructor_similarity_records(db, instructor_id, course_id))


def instructor_similarity_records(db: Session, instructor_id: int, course_id: Optional[int] = None) -> list[dict[str, Any]]:
    """Return the one current assessed coursework submission per student/task."""
    rows = db.query(models.Submission, models.Assignment, models.Course, models.Student, models.Problem).join(
        models.Assignment, models.Assignment.id == models.Submission.assignment_id
    ).join(models.Course, models.Course.id == models.Assignment.course_id).join(
        models.Student, models.Student.student_id == models.Submission.student_id
    ).join(models.Problem, models.Problem.id == models.Submission.problem_id).filter(
        models.Course.instructor_id == instructor_id,
        models.Course.is_active == True,
        models.Submission.status == "EVALUATED",
        *([models.Course.id == course_id] if course_id is not None else []),
    ).order_by(models.Submission.created_at.desc(), models.Submission.id.desc()).all()
    records = []
    for submission, assignment, course, student, problem in _latest_similarity_rows(rows):
        fingerprint = structural_fingerprint(submission.code, submission.language)
        records.append({
            "courseId": course.id,
            "courseTitle": course.title,
            "assignmentId": assignment.id,
            "assignmentTitle": assignment.title,
            "problemId": problem.id,
            "problemTitle": problem.title,
            "approachLabel": approach_label(fingerprint),
            "approachSummary": approach_summary(fingerprint),
            "student": _similarity_student_payload(student, submission),
            # This remains in the instructor-only response and lets each
            # group show one representative source file without duplicating
            # every member's code in the browser.
            "sourceCode": submission.code,
        })
    return records


@app.get("/api/instructor/similarity")
def list_instructor_similarity_cases(
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
    course_id: Optional[int] = None,
):
    if course_id is not None:
        get_owned_course(db, instructor.id, course_id)
    cases = instructor_similarity_cases(db, instructor.id, course_id)
    clusters = build_similarity_clusters(cases)
    records = instructor_similarity_records(db, instructor.id, course_id)
    approach_groups = build_approach_groups(records)
    submission_groups = build_submission_groups(records, cases)
    return {
        "cases": cases,
        "total_cases": len(cases),
        "clusters": clusters,
        "total_clusters": len(clusters),
        "approach_groups": approach_groups,
        "total_approach_groups": len(approach_groups),
        "submission_groups": submission_groups,
        "total_submission_groups": len(submission_groups),
    }


@app.post("/api/instructor/similarity/{case_id}/{action}")
def update_instructor_similarity_case(
    case_id: str,
    action: str,
    db: Session = Depends(get_db),
    instructor: models.Instructor = Depends(get_current_instructor),
):
    if action not in {"dismiss", "request-review"}:
        raise HTTPException(status_code=400, detail="Unsupported similarity review action")
    case = next((item for item in instructor_similarity_cases(db, instructor.id) if item["id"] == case_id), None)
    if case is None:
        raise HTTPException(status_code=404, detail="Similarity case not found")
    status_value = "dismissed" if action == "dismiss" else "review_requested"
    pair_key = case_id
    submission_ids = {case["studentA"]["submissionId"], case["studentB"]["submissionId"]}
    records = db.query(models.Submission).filter(models.Submission.submission_id.in_(submission_ids)).all()
    for submission in records:
        flags = dict(submission.assessment_flags or {})
        reviews = dict(flags.get("similarity_reviews") or {})
        reviews[pair_key] = status_value
        flags["similarity_reviews"] = reviews
        submission.assessment_flags = flags
    db.commit()
    return {"case_id": case_id, "status": status_value}

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
        "highest_score": max((submission.overall_score for submission in latest if submission.overall_score is not None), default=None),
        "lowest_score": min((submission.overall_score for submission in latest if submission.overall_score is not None), default=None),
        "score_distribution": score_distribution(latest),
        "completion_rate": completion_rate,
        "assignment_stats": [build_assignment_stats(db, assignment).model_dump() for assignment in assignments],
        "topic_performance": topic_performance(db, latest),
        **student_score_extremes(db, latest),
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
    writer.writerow(["Student ID", "Student Name", "Course", "Completed Problems", "Average Score", "Correctness", "Complexity", "Style", "Last Submission"])
    
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
            last_sub_date
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=course_{course_id}_export.csv"}
    )
