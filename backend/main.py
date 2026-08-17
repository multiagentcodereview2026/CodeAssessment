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
            name=submission.student_id
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


    return submissions