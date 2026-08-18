from uuid import uuid4

from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session

import models

from auth import create_access_token
from auth import get_current_user
from auth import hash_password
from auth import require_instructor
from auth import require_student
from auth import verify_password

from database import Base
from database import engine
from database import get_db

from schemas import AssignStudentRequest
from schemas import AssignmentResponse
from schemas import LoginResponse
from schemas import RegisterRequest
from schemas import SubmissionDetails
from schemas import SubmissionRequest
from schemas import SubmissionResponse
from schemas import UserResponse


# =========================================================
# DATABASE
# =========================================================

Base.metadata.create_all(
    bind=engine
)


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="AI Programming Assessment System",
    description="Backend API for AI Programming Assessment System",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "message": "AI Programming Assessment System API"
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# =========================================================
# REGISTER
# =========================================================

@app.post(
    "/api/auth/register",
    response_model=UserResponse
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):

    if request.role not in [
        "student",
        "instructor"
    ]:

        raise HTTPException(
            status_code=400,
            detail="Role must be student or instructor"
        )


    existing_username = (
        db.query(models.User)
        .filter(
            models.User.username
            == request.username
        )
        .first()
    )

    if existing_username:

        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )


    existing_email = (
        db.query(models.User)
        .filter(
            models.User.email
            == request.email
        )
        .first()
    )

    if existing_email:

        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )


    user = models.User(
        username=request.username,
        email=request.email,
        password_hash=hash_password(
            request.password
        ),
        role=request.role
    )


    db.add(user)

    db.commit()

    db.refresh(user)


    return user


# =========================================================
# LOGIN
# =========================================================

@app.post(
    "/api/auth/login",
    response_model=LoginResponse
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    user = (
        db.query(models.User)
        .filter(
            models.User.username
            == form_data.username
        )
        .first()
    )


    if user is None:

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )


    if not verify_password(
        form_data.password,
        user.password_hash
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )


    access_token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role
    )


    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# =========================================================
# CURRENT USER
# =========================================================

@app.get(
    "/api/auth/me",
    response_model=UserResponse
)
def get_me(
    current_user=Depends(get_current_user)
):

    return current_user


# =========================================================
# INSTRUCTOR - ASSIGN STUDENT
# =========================================================

@app.post(
    "/api/instructor/assign-student",
    response_model=AssignmentResponse
)
def assign_student(
    request: AssignStudentRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_instructor)
):

    student = (
        db.query(models.User)
        .filter(
            models.User.username
            == request.student_username
        )
        .first()
    )


    if student is None:

        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )


    if student.role != "student":

        raise HTTPException(
            status_code=400,
            detail="Selected user is not a student"
        )


    existing_assignment = (
        db.query(
            models.InstructorStudentAssignment
        )
        .filter(
            models.InstructorStudentAssignment.instructor_id
            == current_user.id,
            models.InstructorStudentAssignment.student_id
            == student.id
        )
        .first()
    )


    if existing_assignment:

        raise HTTPException(
            status_code=400,
            detail="Student is already assigned"
        )


    assignment = (
        models.InstructorStudentAssignment(
            instructor_id=current_user.id,
            student_id=student.id
        )
    )


    db.add(assignment)

    db.commit()

    db.refresh(assignment)


    return assignment


# =========================================================
# INSTRUCTOR - GET ASSIGNED STUDENTS
# =========================================================

@app.get(
    "/api/instructor/students"
)
def get_assigned_students(
    db: Session = Depends(get_db),
    current_user=Depends(require_instructor)
):

    assignments = (
        db.query(
            models.InstructorStudentAssignment
        )
        .filter(
            models.InstructorStudentAssignment.instructor_id
            == current_user.id
        )
        .all()
    )


    students = []


    for assignment in assignments:

        student = (
            db.query(models.User)
            .filter(
                models.User.id
                == assignment.student_id
            )
            .first()
        )


        if student:

            students.append({
                "id": student.id,
                "username": student.username,
                "email": student.email,
                "role": student.role
            })


    return students


# =========================================================
# CREATE SUBMISSION
# =========================================================

@app.post(
    "/api/submissions",
    response_model=SubmissionResponse
)
def create_submission(
    submission: SubmissionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_student)
):

    # Student can submit only for their own account

    if (
        submission.student_id
        != current_user.username
    ):

        raise HTTPException(
            status_code=403,
            detail="You can only submit code for your own account"
        )


    existing_student = (
        db.query(models.Student)
        .filter(
            models.Student.student_id
            == submission.student_id
        )
        .first()
    )


    if existing_student is None:

        student = models.Student(
            student_id=submission.student_id,
            name=current_user.username
        )

        db.add(student)

        db.commit()


    submission_id = (
        f"SUB-{uuid4().hex[:8]}"
    )


    new_submission = models.Submission(
        submission_id=submission_id,
        student_id=submission.student_id,
        problem_id=submission.problem_id,
        language=submission.language,
        code=submission.code,
        status="SUBMITTED"
    )


    db.add(new_submission)

    db.commit()

    db.refresh(new_submission)


    return SubmissionResponse(
        submission_id=new_submission.submission_id,
        student_id=new_submission.student_id,
        problem_id=new_submission.problem_id,
        language=new_submission.language,
        status=new_submission.status
    )


# =========================================================
# GET ONE SUBMISSION
# =========================================================

@app.get(
    "/api/submissions/{submission_id}",
    response_model=SubmissionDetails
)
def get_submission(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    submission = (
        db.query(models.Submission)
        .filter(
            models.Submission.submission_id
            == submission_id
        )
        .first()
    )


    if submission is None:

        raise HTTPException(
            status_code=404,
            detail="Submission not found"
        )


    # -----------------------------------------------------
    # STUDENT ACCESS
    # -----------------------------------------------------

    if current_user.role == "student":

        if (
            submission.student_id
            != current_user.username
        ):

            raise HTTPException(
                status_code=403,
                detail="You can only access your own submissions"
            )

        return submission


    # -----------------------------------------------------
    # INSTRUCTOR ACCESS
    # -----------------------------------------------------

    if current_user.role == "instructor":

        student = (
            db.query(models.User)
            .filter(
                models.User.username
                == submission.student_id
            )
            .first()
        )


        if student is None:

            raise HTTPException(
                status_code=403,
                detail="Student account not found"
            )


        assignment = (
            db.query(
                models.InstructorStudentAssignment
            )
            .filter(
                models.InstructorStudentAssignment.instructor_id
                == current_user.id,

                models.InstructorStudentAssignment.student_id
                == student.id
            )
            .first()
        )


        if assignment is None:

            raise HTTPException(
                status_code=403,
                detail="Student is not assigned to this instructor"
            )


        return submission


    raise HTTPException(
        status_code=403,
        detail="Invalid user role"
    )


# =========================================================
# GET SUBMISSIONS
# =========================================================

@app.get(
    "/api/submissions",
    response_model=list[SubmissionDetails]
)
def get_submissions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    # -----------------------------------------------------
    # STUDENT
    # -----------------------------------------------------

    if current_user.role == "student":

        return (
            db.query(models.Submission)
            .filter(
                models.Submission.student_id
                == current_user.username
            )
            .order_by(
                models.Submission.created_at.desc()
            )
            .all()
        )


    # -----------------------------------------------------
    # INSTRUCTOR
    # -----------------------------------------------------

    if current_user.role == "instructor":

        assignments = (
            db.query(
                models.InstructorStudentAssignment
            )
            .filter(
                models.InstructorStudentAssignment.instructor_id
                == current_user.id
            )
            .all()
        )


        if not assignments:

            return []


        student_user_ids = [
            assignment.student_id
            for assignment in assignments
        ]


        students = (
            db.query(models.User)
            .filter(
                models.User.id.in_(
                    student_user_ids
                )
            )
            .all()
        )


        student_usernames = [
            student.username
            for student in students
        ]


        if not student_usernames:

            return []


        return (
            db.query(models.Submission)
            .filter(
                models.Submission.student_id.in_(
                    student_usernames
                )
            )
            .order_by(
                models.Submission.created_at.desc()
            )
            .all()
        )


    raise HTTPException(
        status_code=403,
        detail="Invalid user role"
    )