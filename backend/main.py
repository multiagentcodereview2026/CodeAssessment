from uuid import uuid4

from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import models

from database import Base
from database import engine
from database import get_db

from schemas import SubmissionDetails
from schemas import SubmissionRequest
from schemas import SubmissionResponse
from schemas import UserRegister
from schemas import UserLogin
from schemas import Token
from schemas import UserOut

from auth import hash_password
from auth import verify_password
from auth import create_access_token


Base.metadata.create_all(
    bind=engine
)


app = FastAPI(
    title="AI Programming Assessment System",
    description="Backend API for student code submissions",
    version="1.0.0"
)


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


@app.get("/")
def root():

    return {
        "message":
        "AI Programming Assessment System API"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


@app.post(
    "/api/submissions",
    response_model=SubmissionResponse
)
def create_submission(
    submission: SubmissionRequest,
    db: Session = Depends(get_db)
):

    


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

        submission_id=
        new_submission.submission_id,

        student_id=
        new_submission.student_id,

        problem_id=
        new_submission.problem_id,

        language=
        new_submission.language,

        status=
        new_submission.status
    )


@app.get(
    "/api/submissions/{submission_id}",
    response_model=SubmissionDetails
)
def get_submission(
    submission_id: str,
    db: Session = Depends(get_db)
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


    return submission


@app.get(
    "/api/submissions",
    response_model=list[SubmissionDetails]
)
def get_submissions(
    db: Session = Depends(get_db)
):

    submissions = (
        db.query(models.Submission)
        .order_by(
            models.Submission.created_at.desc()
        )
        .all()
    )
@app.post(
    "/api/auth/register",
    response_model=UserOut
)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):

    existing_user = (
        db.query(models.User)
        .filter(
            models.User.email == user_data.email
        )
        .first()
    )

    if existing_user is not None:

        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    if user_data.role not in ("student", "instructor"):

        raise HTTPException(
            status_code=400,
            detail="Role must be 'student' or 'instructor'"
        )

    new_user = models.User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        name=user_data.name,
        role=user_data.role,
        student_id=user_data.student_id
    )

    db.add(new_user)

    db.commit()

    db.refresh(new_user)

    return new_user


@app.post(
    "/api/auth/login",
    response_model=Token
)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):

    user = (
        db.query(models.User)
        .filter(
            models.User.email == credentials.email
        )
        .first()
    )

    if user is None or not verify_password(
        credentials.password, user.hashed_password
    ):

        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role
        }
    )

    return Token(access_token=access_token)

    return submissions