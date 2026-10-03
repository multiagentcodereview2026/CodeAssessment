from datetime import datetime
from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field, field_validator

# Auth Schemas
class LoginRequest(BaseModel):
    user_id: str
    role: Literal["student", "instructor"]
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    role: Literal["student"] = "student"

class AuthUser(BaseModel):
    id: str
    username: str
    name: str
    role: str
    email: Optional[str] = None
    access_token: Optional[str] = None
    token_type: Optional[str] = None

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
    code: str
    assignment_id: Optional[int] = None
    test_cases: Optional[List[Dict[str, Any]]] = None

class QuickRunRequest(BaseModel):
    language: str
    code: str
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
    assignment_id: Optional[int] = None
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
    overall_score: Optional[float] = None
    streak_days: int
    xp: int
    problems_solved: int
    total_problems: int
    score_trend: List[Dict[str, Any]]
    category_breakdown: List[Dict[str, Any]]
    weak_topics: List[str]

# ============ Instructor Schemas ============

class CourseCreate(BaseModel):
    course_code: str
    title: str
    term: Optional[str] = None
    description: Optional[str] = None

    @field_validator("course_code", "title")
    @classmethod
    def validate_required_course_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Course code and title cannot be empty")
        return value

class CourseUpdate(BaseModel):
    course_code: Optional[str] = None
    title: Optional[str] = None
    term: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class CourseResponse(BaseModel):
    id: int
    course_code: str
    title: str
    term: Optional[str] = None
    description: Optional[str] = None
    instructor_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class EnrollmentCreate(BaseModel):
    student_id: str
    course_id: int

class EnrollmentResponse(BaseModel):
    id: int
    student_id: str
    course_id: int
    enrollment_date: datetime
    is_active: bool
    student_name: Optional[str] = None
    student_email: Optional[str] = None

    class Config:
        from_attributes = True

class StudentLookupItem(BaseModel):
    student_id: str
    name: str
class StudentCreateByInstructor(BaseModel):
    student_id: str
    name: str
    email: Optional[str] = None

    @field_validator("student_id", "name")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Student ID and name cannot be empty")
        return value

class StudentCourseResponse(CourseResponse):
    assignments_count: int = 0

class StudentAssignmentResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    course_id: int
    course_title: str
    due_date: Optional[datetime] = None
    status: str
    problems: List[str]
    problem_titles: List[str]

class AssignmentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    course_id: int
    problem_ids: List[str] = Field(min_length=1)
    due_date: Optional[datetime] = None
    status: Literal["ACTIVE", "UPCOMING", "CLOSED"] = "ACTIVE"

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Assignment title cannot be empty")
        return value

    @field_validator("problem_ids")
    @classmethod
    def validate_problem_ids(cls, values: List[str]) -> List[str]:
        normalized = [value.strip() for value in values]
        if any(not value for value in normalized):
            raise ValueError("Problem IDs cannot be empty")
        if len(set(normalized)) != len(normalized):
            raise ValueError("Duplicate problem IDs are not allowed")
        return normalized

class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[Literal["ACTIVE", "UPCOMING", "CLOSED"]] = None
    problem_ids: Optional[List[str]] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Assignment title cannot be empty")
        return value

    @field_validator("problem_ids")
    @classmethod
    def validate_problem_ids(cls, values: Optional[List[str]]) -> Optional[List[str]]:
        if values is None:
            return values
        if not values:
            raise ValueError("An assignment must include at least one problem")
        normalized = [value.strip() for value in values]
        if any(not value for value in normalized):
            raise ValueError("Problem IDs cannot be empty")
        if len(set(normalized)) != len(normalized):
            raise ValueError("Duplicate problem IDs are not allowed")
        return normalized

class AssignmentResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    course_id: int
    due_date: Optional[datetime] = None
    status: str
    created_at: datetime
    problems: List[str] = []

    class Config:
        from_attributes = True

class InstructorOverview(BaseModel):
    total_students: int
    active_assignments: int
    total_submissions: int
    class_avg_score: Optional[str] = None
    highest_score: Optional[float] = None
    lowest_score: Optional[float] = None
    score_distribution: List[Dict[str, Any]] = []
    total_courses: int = 0
    total_assignments: int = 0
    courses: List[Dict[str, Any]] = []
    students: List[Dict[str, Any]] = []

class CourseWithStats(CourseResponse):
    student_count: int = 0
    assignment_count: int = 0
    submission_count: int = 0
    unique_submitters: int = 0
    unsubmitted_students: int = 0
    assigned_problem_count: int = 0
    avg_score: Optional[float] = None

class StudentRosterItem(BaseModel):
    id: str
    name: str
    rollNumber: str
    email: Optional[str] = None
    submissions_count: int = 0
    avg_score: Optional[float] = None
    trend: Optional[str] = None
    weak_topics: List[str] = []
    status: str = "On Track"

    class Config:
        from_attributes = True

class AssignmentWithStats(AssignmentResponse):
    total_students: int = 0
    submitted_count: int = 0
    total_attempts: int = 0
    unique_submitters: int = 0
    unsubmitted_students: int = 0
    avg_score: Optional[float] = None
    highest_score: Optional[float] = None
    lowest_score: Optional[float] = None
    avg_correctness: Optional[float] = None
    avg_complexity: Optional[float] = None
    avg_style: Optional[float] = None
    avg_similarity: Optional[float] = None
    problem_titles: List[str] = []
class InstructorStudentProgressResponse(BaseModel):
    student_id: str
    student_name: str
    course_title: str
    assigned_problems: int
    completed_problems: int
    pending_problems: int
    average_score: Optional[float] = None
    latest_score: Optional[float] = None
    correctness_avg: Optional[float] = None
    complexity_avg: Optional[float] = None
    style_avg: Optional[float] = None
    similarity_avg: Optional[float] = None
    total_attempts: int
    latest_submission: Optional[dict] = None
    progress_trend: List[float] = []
