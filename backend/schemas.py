from datetime import datetime

from pydantic import BaseModel


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


class SubmissionDetails(BaseModel):

    submission_id: str
    student_id: str
    problem_id: str
    language: str
    code: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True