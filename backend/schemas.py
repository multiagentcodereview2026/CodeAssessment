from datetime import datetime
from pydantic import BaseModel


class RegisterRequest(BaseModel):
    username: str | None = None
    email: str
    password: str
    role: str = "student"
    name: str | None = None
    student_id: str | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str | None = None
    email: str
    role: str
    name: str | None = None
    student_id: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserRegister(BaseModel):
    email: str
    password: str
    name: str | None = None
    role: str = "student"
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
    name: str | None = None
    role: str
    student_id: str | None = None

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
    constraints: str | None = None
    input_format: str | None = None
    output_format: str | None = None
    supported_languages: str
    difficulty: str | None = None
    time_limit: int
    memory_limit: int
    created_at: datetime

    class Config:
        from_attributes = True