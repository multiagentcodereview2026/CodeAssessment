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
from schemas import ProblemCreate
from schemas import ProblemResponse
from schemas import RegisterRequest
from schemas import SubmissionDetails
from schemas import SubmissionRequest
from schemas import SubmissionResponse
from schemas import UserResponse
from schemas import TestCaseCreate
from schemas import TestCaseResponse

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
# AUTHENTICATION
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
# PROBLEM MANAGEMENT
# =========================================================

# ---------------------------------------------------------
# CREATE PROBLEM
# ---------------------------------------------------------

@app.post(
    "/api/problems",
    response_model=ProblemResponse
)
def create_problem(
    problem: ProblemCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_instructor)
):

    existing_problem = (
        db.query(models.Problem)
        .filter(
            models.Problem.problem_id
            == problem.problem_id
        )
        .first()
    )

    if existing_problem:

        raise HTTPException(
            status_code=400,
            detail="Problem ID already exists"
        )

    new_problem = models.Problem(
        problem_id=problem.problem_id,
        title=problem.title,
        description=problem.description,
        constraints=problem.constraints,
        input_format=problem.input_format,
        output_format=problem.output_format,
        supported_languages=problem.supported_languages,
        difficulty=problem.difficulty,
        time_limit=problem.time_limit,
        memory_limit=problem.memory_limit
    )

    db.add(new_problem)
    db.commit()
    db.refresh(new_problem)

    return new_problem


# ---------------------------------------------------------
# GET ALL PROBLEMS
# ---------------------------------------------------------

@app.get(
    "/api/problems",
    response_model=list[ProblemResponse]
)
def get_problems(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    return (
        db.query(models.Problem)
        .order_by(
            models.Problem.created_at.desc()
        )
        .all()
    )


# ---------------------------------------------------------
# GET ONE PROBLEM
# ---------------------------------------------------------

@app.get(
    "/api/problems/{problem_id}",
    response_model=ProblemResponse
)
def get_problem(
    problem_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    problem = (
        db.query(models.Problem)
        .filter(
            models.Problem.problem_id
            == problem_id
        )
        .first()
    )

    if problem is None:

        raise HTTPException(
            status_code=404,
            detail="Problem not found"
        )

    return problem


# ---------------------------------------------------------
# UPDATE PROBLEM
# ---------------------------------------------------------

@app.put(
    "/api/problems/{problem_id}",
    response_model=ProblemResponse
)
def update_problem(
    problem_id: str,
    problem_data: ProblemCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_instructor)
):

    problem = (
        db.query(models.Problem)
        .filter(
            models.Problem.problem_id
            == problem_id
        )
        .first()
    )

    if problem is None:

        raise HTTPException(
            status_code=404,
            detail="Problem not found"
        )

    problem.title = problem_data.title

    problem.description = (
        problem_data.description
    )

    problem.constraints = (
        problem_data.constraints
    )

    problem.input_format = (
        problem_data.input_format
    )

    problem.output_format = (
        problem_data.output_format
    )

    problem.supported_languages = (
        problem_data.supported_languages
    )

    problem.difficulty = (
        problem_data.difficulty
    )

    problem.time_limit = (
        problem_data.time_limit
    )

    problem.memory_limit = (
        problem_data.memory_limit
    )

    db.commit()
    db.refresh(problem)

    return problem


# ---------------------------------------------------------
# DELETE PROBLEM
# ---------------------------------------------------------

@app.delete(
    "/api/problems/{problem_id}"
)
def delete_problem(
    problem_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_instructor)
):

    problem = (
        db.query(models.Problem)
        .filter(
            models.Problem.problem_id
            == problem_id
        )
        .first()
    )

    if problem is None:

        raise HTTPException(
            status_code=404,
            detail="Problem not found"
        )

    db.delete(problem)
    db.commit()

    return {
        "message": "Problem deleted successfully",
        "problem_id": problem_id
    }


# =========================================================
# SUBMISSIONS
# =========================================================

# ---------------------------------------------------------
# CREATE SUBMISSION
# ---------------------------------------------------------

@app.post(
    "/api/submissions",
    response_model=SubmissionResponse
)
def create_submission(
    submission: SubmissionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_student)
):

    if (
        submission.student_id
        != current_user.username
    ):

        raise HTTPException(
            status_code=403,
            detail=(
                "You can only submit code "
                "for your own account"
            )
        )

    # Verify that the problem exists

    problem = (
        db.query(models.Problem)
        .filter(
            models.Problem.problem_id
            == submission.problem_id
        )
        .first()
    )

    if problem is None:

        raise HTTPException(
            status_code=404,
            detail="Problem not found"
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


# ---------------------------------------------------------
# GET ONE SUBMISSION
# ---------------------------------------------------------

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

    # Student access

    if current_user.role == "student":

        if (
            submission.student_id
            != current_user.username
        ):

            raise HTTPException(
                status_code=403,
                detail=(
                    "You can only access "
                    "your own submissions"
                )
            )

        return submission

    # Instructor access

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
                detail=(
                    "Student is not assigned "
                    "to this instructor"
                )
            )

        return submission

    raise HTTPException(
        status_code=403,
        detail="Invalid user role"
    )


# ---------------------------------------------------------
# GET SUBMISSIONS
# ---------------------------------------------------------

@app.get(
    "/api/submissions",
    response_model=list[SubmissionDetails]
)
def get_submissions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    # Student

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

    # Instructor

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
@app.post(
    "/api/problems/{problem_id}/test-cases",
    response_model=TestCaseResponse
)
def create_test_case(
    problem_id: str,
    test_case: TestCaseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_instructor)
):
    # Check whether the problem exists
    problem = (
        db.query(models.Problem)
        .filter(
            models.Problem.problem_id == problem_id
        )
        .first()
    )

    if problem is None:
        raise HTTPException(
            status_code=404,
            detail="Problem not found"
        )

    new_test_case = models.TestCase(
        problem_id=problem_id,
        input_data=test_case.input_data,
        expected_output=test_case.expected_output,
        is_hidden=test_case.is_hidden
    )

    db.add(new_test_case)
    db.commit()
    db.refresh(new_test_case)

    return new_test_case
@app.get(
    "/api/problems/{problem_id}/test-cases",
    response_model=list[TestCaseResponse]
)
def get_test_cases(
    problem_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Check whether problem exists
    problem = (
        db.query(models.Problem)
        .filter(
            models.Problem.problem_id == problem_id
        )
        .first()
    )

    if problem is None:
        raise HTTPException(
            status_code=404,
            detail="Problem not found"
        )

    test_cases = (
        db.query(models.TestCase)
        .filter(
            models.TestCase.problem_id == problem_id
        )
        .all()
    )

    # Students should not receive hidden test cases
    if current_user.role == "student":
        test_cases = [
            tc for tc in test_cases
            if not tc.is_hidden
        ]

    return test_cases
@app.delete(
    "/api/test-cases/{test_case_id}"
)
def delete_test_case(
    test_case_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_instructor)
):
    test_case = (
        db.query(models.TestCase)
        .filter(
            models.TestCase.id == test_case_id
        )
        .first()
    )

    if test_case is None:
        raise HTTPException(
            status_code=404,
            detail="Test case not found"
        )

    db.delete(test_case)
    db.commit()

    return {
        "message": "Test case deleted successfully"
    }