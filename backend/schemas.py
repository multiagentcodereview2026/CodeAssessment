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


class UserRegister(BaseModel):

    email: str
    password: str
    name: str
    role: str
    student_id: str | None = None


class UserLogin(BaseModel):

    email: str
    password: str


class Token(BaseModel):

    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):

    id: int
    email: str
    name: str | None
    role: str
    student_id: str | None

    class Config:
        from_attributes = True