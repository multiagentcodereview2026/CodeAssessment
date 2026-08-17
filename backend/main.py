from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


app = FastAPI(
    title="AI Programming Assessment System",
    version="1.0.0"
)


# Allow the existing Vite frontend to communicate with FastAPI
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


class SubmissionRequest(BaseModel):
    student_id: str
    problem_id: str
    language: str
    code: str


class SubmissionResponse(BaseModel):
    submission_id: str
    student_id: str
    problem_id: str
    language: str
    status: str


@app.get("/")
def root():
    return {
        "message": "AI Programming Assessment System API"
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
    submission: SubmissionRequest
):

    submission_id = f"SUB-{uuid4().hex[:8]}"

    return SubmissionResponse(
        submission_id=submission_id,
        student_id=submission.student_id,
        problem_id=submission.problem_id,
        language=submission.language,
        status="SUBMITTED"
    )