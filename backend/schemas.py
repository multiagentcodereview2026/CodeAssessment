from datetime import datetime

from pydantic import BaseModel


class RegisterRequest(BaseModel):

    username: str
    email: str
    password: str
    role: str = "student"


class LoginResponse(BaseModel):

    access_token: str
    token_type: str


class UserResponse(BaseModel):

    id: int
    username: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


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
class AssignStudentRequest(BaseModel):
    student_username: str


class AssignmentResponse(BaseModel):
    id: int
    instructor_id: int
    student_id: int
    created_at: datetime

    class Config:
        from_attributes = True
class ProblemCreate(BaseModel):
    problem_id: str
    title: str
    description: str
    constraints: str | None = None
    input_format: str | None = None
    output_format: str | None = None
    supported_languages: str
    difficulty: str | None = None
    time_limit: int = 2
    memory_limit: int = 256


class ProblemResponse(BaseModel):
    id: int
    problem_id: str
    title: str
    description: str
    constraints: str | None
    input_format: str | None
    output_format: str | None
    supported_languages: str
    difficulty: str | None
    time_limit: int
    memory_limit: int
    created_at: datetime

    class Config:
        from_attributes = True