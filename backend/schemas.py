from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

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

    class Config:
        from_attributes = True

# Submission Schemas
class SubmissionRequest(BaseModel):
    student_id: str
    problem_id: str
    language: str
    code: str
    test_cases: Optional[List[Dict[str, str]]] = None

class QuickRunRequest(BaseModel):
    language: str
    code: str
    test_cases: Optional[List[Dict[str, str]]] = None

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

class SubmissionResponse(BaseModel):
    submission_id: str
    student_id: str
    problem_id: str
    language: str
    status: str
    overall_score: Optional[float] = None
    correctness_score: Optional[float] = None
    complexity_score: Optional[float] = None
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