from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from typing import Literal

class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_.-]+$")
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=8, max_length=128)
    role: Literal['student', 'instructor'] = 'student'
    name: Optional[str] = None

class ProblemWrite(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    difficulty: Literal['Easy', 'Medium', 'Hard'] = 'Easy'
    category: str = 'Programming'
    course_code: str = Field(min_length=1, max_length=100)
    due_date: Optional[str] = None
    examples: List[Dict[str, str]] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    starter_codes: Dict[str, str] = Field(default_factory=dict)
    test_cases: List[Dict[str, Any]] = Field(min_length=1, max_length=200)
    optimal_time: str = 'Not assessed'
    optimal_space: str = 'Not assessed'

# Auth Schemas
class LoginRequest(BaseModel):
    user_id: str
    role: str # "student" or "instructor"
    password: Optional[str] = "password" # Mock password

class AuthUser(BaseModel):
    id: str
    name: str
    role: str
    email: Optional[str] = None

# Problem Schemas
class ProblemListItem(BaseModel):
    id: str
    title: str
    difficulty: str
    category: str
    is_instructor_assigned: bool = False
    course_code: Optional[str] = None
    due_date: Optional[str] = None

    class Config:
        from_attributes = True

class ProblemDetail(BaseModel):
    id: str
    title: str
    difficulty: str
    category: str
    description: str
    examples: List[Dict[str, str]]
    constraints: List[str]
    starter_codes: Dict[str, str]
    test_cases: Optional[List[Dict[str, Any]]] = None
    is_instructor_assigned: bool = False
    course_code: Optional[str] = None
    due_date: Optional[str] = None

    class Config:
        from_attributes = True

# Submission Schemas
class SubmissionRequest(BaseModel):
    student_id: Optional[str] = None
    problem_id: str
    language: str
    code: str = Field(min_length=1, max_length=100000)
    test_cases: Optional[List[Dict[str, Any]]] = None

class QuickRunRequest(BaseModel):
    language: str
    code: str = Field(min_length=1, max_length=100000)
    problem_id: Optional[str] = None
    test_cases: Optional[List[Dict[str, Any]]] = None

class QuickRunResponse(BaseModel):
    compile_status: str
    compile_error: Optional[str] = None
    execution_status: str
    stdout: str
    stderr: str
    runtime_ms: int
    memory_kb: int
    passed_cases: int
    failed_cases: int
    total_cases: int
    results: List[Dict[str, Any]] = []

class SubmissionResponse(BaseModel):
    submission_id: str
    student_id: str
    problem_id: str
    language: str
    status: str
    overall_score: Optional[float] = None
    correctness_score: Optional[float] = None
    complexity_score: Optional[float] = None
    complexity_details: Optional[Dict[str, Any]] = None
    style_score: Optional[float] = None
    similarity_score: Optional[float] = None
    execution_result: Optional[Dict[str, Any]] = None
    feedback: Optional[Dict[str, Any]] = None
    recommendations: Optional[Dict[str, Any]] = None
    improved_code: Optional[Dict[str, Any]] = None
    projected_score: Optional[Dict[str, Any]] = None

class SubmissionDetails(SubmissionResponse):
    code: str
    created_at: datetime

    class Config:
        from_attributes = True

# Analytics Schemas
class StudentAnalyticsResponse(BaseModel):
    overall_score: float
    streak_days: int
    xp: int
    problems_solved: int
    total_problems: int
    score_trend: List[Dict[str, Any]]
    category_breakdown: List[Dict[str, Any]]
    weak_topics: List[str]
