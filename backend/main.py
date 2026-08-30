from uuid import uuid4
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import models
from auth import (
    create_access_token,
    get_current_user,
    hash_password,
    require_instructor,
    require_student,
    verify_password
)
from database import Base, engine, get_db
from schemas import (
    AssignStudentRequest,
    AssignmentResponse,
    LoginResponse,
    ProblemCreate,
    ProblemResponse,
    RegisterRequest,
    SubmissionDetails,
    SubmissionRequest,
    SubmissionResponse,
    UserResponse
)

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Programming Assessment System",
    description="Backend API for AI Programming Assessment System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "AI Programming Assessment System API"}


@app.get("/health")
def health():
    return {"status": "healthy"}


# =========================================================
# AUTHENTICATION
# =========================================================

@app.post("/api/auth/register", response_model=UserResponse)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    if request.role not in ["student", "instructor"]:
        raise HTTPException(
            status_code=400,
            detail="Role must be student or instructor"
        )

    identifier = request.username or request.email.split("@")[0]

    existing_email = db.query(models.User).filter(models.User.email == request.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")

    user = models.User(
        username=identifier,
        email=request.email,
        hashed_password=hash_password(request.password),
        role=request.role,
        name=request.name or identifier,
        student_id=request.student_id
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/api/auth/login", response_model=LoginResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        (models.User.username == form_data.username) | (models.User.email == form_data.username)
    ).first()

    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid username/email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(
        user_id=user.id,
        username=user.username or user.email,
        role=user.role
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@app.get("/api/auth/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)):
    return current_user


# =========================================================
# INSTRUCTOR - ASSIGN STUDENT
# =========================================================

@app.post("/api/instructor/assign-student", response_model=AssignmentResponse)
def assign_student(
    request: AssignStudentRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_instructor)
):
    student = db.query(models.User).filter(
        (models.User.username == request.student_username) | (models.User.email == request.student_username)
    ).first()

    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    if student.role != "student":
        raise HTTPException(status_code=400, detail="Selected user is not a student")

    existing_assignment = db.query(models.InstructorStudentAssignment).filter(
        models.InstructorStudentAssignment.instructor_id == current_user.id,
        models.InstructorStudentAssignment.student_id == student.id
    ).first()

    if existing_assignment:
        raise HTTPException(status_code=400, detail="Student is already assigned")

    assignment = models.InstructorStudentAssignment(
        instructor_id=current_user.id,
        student_id=student.id
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@app.get("/api/instructor/students")
def get_assigned_students(
    db: Session = Depends(get_db),
    current_user=Depends(require_instructor)
):
    assignments = db.query(models.InstructorStudentAssignment).filter(
        models.InstructorStudentAssignment.instructor_id == current_user.id
    ).all()

    students = []
    for assignment in assignments:
        student = db.query(models.User).filter(models.User.id == assignment.student_id).first()
        if student:
            students.append({
                "id": student.id,
                "username": student.username,
                "email": student.email,
                "role": student.role,
                "name": student.name,
                "student_id": student.student_id
            })
    return students


# =========================================================
# PROBLEM MANAGEMENT
# =========================================================

@app.post("/api/problems", response_model=ProblemResponse)
def create_problem(
    problem: ProblemCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_instructor)
):
    existing_problem = db.query(models.Problem).filter(
        models.Problem.problem_id == problem.problem_id
    ).first()

    if existing_problem:
        raise HTTPException(status_code=400, detail="Problem ID already exists")

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


@app.get("/api/problems", response_model=list[ProblemResponse])
def get_problems(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return db.query(models.Problem).order_by(models.Problem.created_at.desc()).all()


@app.get("/api/problems/{problem_id}", response_model=ProblemResponse)
def get_problem(
    problem_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    problem = db.query(models.Problem).filter(models.Problem.problem_id == problem_id).first()
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem


@app.put("/api/problems/{problem_id}", response_model=ProblemResponse)
def update_problem(
    problem_id: str,
    problem_data: ProblemCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_instructor)
):
    problem = db.query(models.Problem).filter(models.Problem.problem_id == problem_id).first()
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")

    problem.title = problem_data.title
    problem.description = problem_data.description
    problem.constraints = problem_data.constraints
    problem.input_format = problem_data.input_format
    problem.output_format = problem_data.output_format
    problem.supported_languages = problem_data.supported_languages
    problem.difficulty = problem_data.difficulty
    problem.time_limit = problem_data.time_limit
    problem.memory_limit = problem_data.memory_limit

    db.commit()
    db.refresh(problem)
    return problem


@app.delete("/api/problems/{problem_id}")
def delete_problem(
    problem_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_instructor)
):
    problem = db.query(models.Problem).filter(models.Problem.problem_id == problem_id).first()
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")

    db.delete(problem)
    db.commit()
    return {"message": "Problem deleted successfully", "problem_id": problem_id}


# =========================================================
# SUBMISSIONS
# =========================================================

@app.post("/api/submissions", response_model=SubmissionResponse)
def create_submission(
    submission: SubmissionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_student)
):
    submission_id = f"SUB-{uuid4().hex[:8]}"

    new_submission = models.Submission(
        submission_id=submission_id,
        student_id=submission.student_id or current_user.username or current_user.email,
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


@app.get("/api/submissions/{submission_id}", response_model=SubmissionDetails)
def get_submission(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    submission = db.query(models.Submission).filter(
        models.Submission.submission_id == submission_id
    ).first()

    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")

    if current_user.role == "student":
        if submission.student_id not in (current_user.username, current_user.email, current_user.student_id):
            raise HTTPException(
                status_code=403,
                detail="You can only access your own submissions"
            )
        return submission

    if current_user.role == "instructor":
        return submission

    raise HTTPException(status_code=403, detail="Invalid user role")


@app.get("/api/submissions", response_model=list[SubmissionDetails])
def get_submissions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role == "student":
        return db.query(models.Submission).filter(
            models.Submission.student_id.in_([current_user.username, current_user.email, current_user.student_id])
        ).order_by(models.Submission.created_at.desc()).all()

    if current_user.role == "instructor":
        return db.query(models.Submission).order_by(models.Submission.created_at.desc()).all()

    raise HTTPException(status_code=403, detail="Invalid user role")