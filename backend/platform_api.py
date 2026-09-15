"""Persistent classroom API. Instructors share one institution-wide classroom."""
from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import models
from auth import create_access_token, get_current_user, hash_password, require_instructor, verify_password
from database import get_db
from instructor_repository import INSTRUCTOR_PROBLEM_IDS, assignment_metadata, canonical_problem_id, load_problem_cases
from schemas import ProblemWrite, RegisterRequest

router = APIRouter(prefix="/api")


def user_response(user):
    return {"id": user.id, "username": user.username, "name": user.name, "email": user.email, "role": user.role, "student_id": user.student_id}


@router.post("/auth/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if "@" not in payload.email:
        raise HTTPException(422, "Enter a valid email address")
    if db.query(models.User).filter((models.User.username == payload.username) | (models.User.email == payload.email.lower())).first():
        raise HTTPException(409, "Username or email already registered")
    user = models.User(username=payload.username, email=payload.email.lower(), name=payload.name or payload.username,
                       role=payload.role, hashed_password=hash_password(payload.password),
                       student_id=payload.username if payload.role == "student" else None)
    if payload.role == "student" and not db.query(models.Student).filter_by(student_id=payload.username).first():
        db.add(models.Student(student_id=payload.username, name=user.name, email=user.email, xp=0, streak_days=0))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(409, "Username or email already registered") from error
    return user_response(user)


@router.post("/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter((models.User.username == form.username) | (models.User.email == form.username.lower())).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(401, "Incorrect username or password")
    return {"access_token": create_access_token(user.id, user.username, user.role), "token_type": "bearer"}


@router.get("/auth/me")
def me(user=Depends(get_current_user)):
    return user_response(user)


def problem_response(db, problem, *, include_private=False):
    publication = db.get(models.PublishedProblem, problem.id)
    meta = assignment_metadata(problem.id)
    if publication:
        meta = {"is_instructor_assigned": True, "course_code": publication.course_code, "due_date": publication.due_date}
    return {
        "id": problem.id, "title": problem.title, "difficulty": problem.difficulty, "category": problem.category,
        "description": problem.description, "examples": problem.examples, "constraints": problem.constraints,
        "starter_codes": problem.starter_codes, "test_cases": load_problem_cases(db, problem, public_only=not include_private),
        "optimal_time": publication.optimal_time if publication else "Not assessed",
        "optimal_space": publication.optimal_space if publication else "Not assessed", **meta,
    }


@router.get("/problems")
def problems(db: Session = Depends(get_db), user=Depends(get_current_user)):
    published = db.query(models.PublishedProblem.problem_id)
    rows = db.query(models.Problem).filter(~models.Problem.id.in_(published), ~models.Problem.id.in_(INSTRUCTOR_PROBLEM_IDS)).all()
    return [problem_response(db, row) for row in rows]


@router.get("/instructor-problems")
def instructor_problems(db: Session = Depends(get_db), user=Depends(get_current_user)):
    published = db.query(models.PublishedProblem.problem_id)
    rows = db.query(models.Problem).filter((models.Problem.id.in_(published)) | (models.Problem.id.in_(INSTRUCTOR_PROBLEM_IDS))).all()
    return [problem_response(db, row, include_private=user.role == "instructor") for row in rows]


@router.get("/problems/{problem_id}")
def problem(problem_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    row = db.get(models.Problem, canonical_problem_id(problem_id))
    if not row:
        raise HTTPException(404, "Problem not found")
    return problem_response(db, row, include_private=user.role == "instructor")


def save_problem(db, payload, user, row=None):
    if not any(not case.get("is_hidden", False) for case in payload.test_cases):
        raise HTTPException(422, "Include at least one public test case")
    for case in payload.test_cases:
        if not isinstance(case.get("input"), str) or not isinstance(case.get("expected_output"), str):
            raise HTTPException(422, "Test inputs and expected outputs must be strings")
    if payload.due_date:
        try:
            datetime.fromisoformat(payload.due_date.replace("Z", "+00:00"))
        except ValueError as error:
            raise HTTPException(422, "Due date must be an ISO date") from error
    if row is None:
        row = models.Problem(id=f"question-{uuid4().hex[:12]}")
        db.add(row)
    for key in ("title", "description", "difficulty", "category", "examples", "constraints", "starter_codes", "test_cases"):
        setattr(row, key, getattr(payload, key))
    db.flush()
    publication = db.get(models.PublishedProblem, row.id)
    if publication is None:
        publication = models.PublishedProblem(problem_id=row.id, instructor_id=user.id)
        db.add(publication)
    for key in ("course_code", "due_date", "optimal_time", "optimal_space"):
        setattr(publication, key, getattr(payload, key))
    db.query(models.ProblemTestCase).filter_by(problem_id=row.id).delete()
    db.commit()
    return problem_response(db, row, include_private=True)


@router.post("/problems", status_code=201)
def publish(payload: ProblemWrite, db: Session = Depends(get_db), user=Depends(require_instructor)):
    return save_problem(db, payload, user)


def owned_problem(db, problem_id, user):
    row = db.get(models.Problem, problem_id)
    publication = db.get(models.PublishedProblem, problem_id)
    if not row:
        raise HTTPException(404, "Problem not found")
    if not publication or publication.instructor_id != user.id:
        raise HTTPException(403, "Only the publishing instructor can modify this question")
    return row


@router.put("/problems/{problem_id}")
def update(problem_id: str, payload: ProblemWrite, db: Session = Depends(get_db), user=Depends(require_instructor)):
    return save_problem(db, payload, user, owned_problem(db, problem_id, user))


@router.delete("/problems/{problem_id}")
def delete(problem_id: str, db: Session = Depends(get_db), user=Depends(require_instructor)):
    row = owned_problem(db, problem_id, user)
    if db.query(models.Submission).filter_by(problem_id=problem_id).first():
        raise HTTPException(409, "Questions with submissions cannot be deleted")
    db.query(models.AnnouncementRead).filter_by(problem_id=problem_id).delete()
    db.query(models.PublishedProblem).filter_by(problem_id=problem_id).delete()
    db.delete(row)
    db.commit()
    return {"deleted": problem_id}


@router.get("/announcements")
def announcements(db: Session = Depends(get_db), user=Depends(get_current_user)):
    read_ids = {row.problem_id for row in db.query(models.AnnouncementRead).filter_by(user_id=user.id)}
    return [{"id": row.problem_id, "problemId": row.problem_id, "title": "New question posted",
             "message": f"{problem.title} has been posted for {row.course_code}.", "courseCode": row.course_code,
             "dueDate": row.due_date, "createdAt": row.created_at.isoformat(), "read": row.problem_id in read_ids}
            for row, problem in db.query(models.PublishedProblem, models.Problem).join(models.Problem).order_by(models.PublishedProblem.created_at.desc()).all()]


@router.patch("/announcements/{problem_id}/read")
def read_announcement(problem_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not db.get(models.PublishedProblem, problem_id):
        raise HTTPException(404, "Announcement not found")
    db.merge(models.AnnouncementRead(user_id=user.id, problem_id=problem_id))
    db.commit()
    return {"read": True}


def submission_response(db, row):
    data = {column.name: getattr(row, column.name) for column in models.Submission.__table__.columns}
    evidence = db.get(models.AssessmentEvidence, row.submission_id)
    data.update(evidence.details if evidence else {})
    data["problem_title"] = row.problem.title
    return data


@router.get("/analytics/student/{student_id}")
def analytics(student_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.role == "student" and student_id != user.username:
        raise HTTPException(403, "Access denied")
    rows = db.query(models.Submission).filter_by(student_id=student_id).order_by(models.Submission.created_at).all()
    scores = [row.overall_score for row in rows if row.overall_score is not None]
    solved = {row.problem_id for row in rows if (row.execution_result or {}).get("total_cases", 0) > 0 and row.execution_result.get("passed_cases") == row.execution_result.get("total_cases")}
    categories = {}
    for row in rows:
        if row.overall_score is not None:
            categories.setdefault(row.problem.category, []).append(row.overall_score)
    return {"overall_score": round(sum(scores) / len(scores), 1) if scores else 0,
            "problems_solved": len(solved), "total_problems": db.query(models.Problem).count(), "streak_days": 0, "xp": len(solved) * 10,
            "score_trend": [{"date": row.created_at.strftime("%b %d"), "score": row.overall_score or 0} for row in rows[-20:]],
            "category_breakdown": [{"name": name, "value": round(sum(values)/len(values), 1), "color": "#059669"} for name, values in categories.items()],
            "weak_topics": [name for name, values in categories.items() if sum(values)/len(values) < 70]}


@router.get("/instructor/overview")
def overview(db: Session = Depends(get_db), user=Depends(require_instructor)):
    students = db.query(models.Student).join(models.User, models.Student.student_id == models.User.username).all()
    rows = db.query(models.Submission).all()
    scores = [row.overall_score for row in rows if row.overall_score is not None]
    roster = []
    for student in students:
        attempts = [row for row in rows if row.student_id == student.student_id]
        values = [row.overall_score for row in attempts if row.overall_score is not None]
        average = round(sum(values)/len(values), 1) if values else 0
        roster.append({"id": student.student_id, "name": student.name, "rollNumber": student.student_id, "email": student.email or "",
                       "avatar": "", "submissionsCount": len(attempts), "avgScore": average, "trend": "neutral",
                       "weakTopics": [], "status": "On Track" if average >= 70 else "Needs Attention" if not attempts else "At Risk",
                       "department": student.department or "", "year": ""})
    return {"total_students": len(students), "total_submissions": len(rows), "active_assignments": db.query(models.PublishedProblem).count(),
            "class_avg_score": round(sum(scores)/len(scores), 1) if scores else 0, "students": roster}
