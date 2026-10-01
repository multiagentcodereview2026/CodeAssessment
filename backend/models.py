from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    full_name = Column(String(200), nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role = Column(String(50), nullable=False, default="student")  # "student" or "instructor"
    is_active = Column(Boolean, default=True)
    token_version = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    instructor_profile = relationship("Instructor", back_populates="user", uselist=False)
    student_profile = relationship("Student", back_populates="user", uselist=False)


class Instructor(Base):
    __tablename__ = "instructors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    title = Column(String(100), nullable=True)  # e.g., "Professor", "Dr."
    department = Column(String(200), nullable=True)
    institution = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="instructor_profile")
    courses = relationship("Course", back_populates="instructor")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    course_code = Column(String(50), nullable=False, index=True)  # e.g., "CSE-301"
    title = Column(String(200), nullable=False)
    term = Column(String(100), nullable=True)  # e.g., "Fall 2024"
    description = Column(Text, nullable=True)
    instructor_id = Column(Integer, ForeignKey("instructors.id"), nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    instructor = relationship("Instructor", back_populates="courses")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="course", cascade="all, delete-orphan")


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_student_course"),)

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(100), ForeignKey("students.student_id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    enrollment_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    student = relationship("Student")
    course = relationship("Course", back_populates="enrollments")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=True)
    institution = Column(String(200), default="Keshav Memorial Institute of Technology")
    department = Column(String(100), default="Computer Science & Engineering")
    xp = Column(Integer, default=150)
    streak_days = Column(Integer, default=7)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, unique=True, index=True)

    # Relationships
    user = relationship("User", back_populates="student_profile")
    submissions = relationship("Submission", back_populates="student")
    enrollments = relationship("Enrollment", back_populates="student", cascade="all, delete-orphan")

class Problem(Base):
    __tablename__ = "problems"

    id = Column(String(100), primary_key=True, index=True) # e.g. "two-sum"
    title = Column(String(200), nullable=False)
    difficulty = Column(String(50), default="Easy") # Easy, Medium, Hard
    category = Column(String(100), default="Arrays & Hashing")
    description = Column(Text, nullable=False)
    examples = Column(JSON, nullable=False) # list of {input, output, explanation}
    constraints = Column(JSON, nullable=False) # list of constraint strings
    starter_codes = Column(JSON, nullable=False) # {cpp, python, javascript}
    test_cases = Column(JSON, nullable=False) # list of {input, expected_output, is_hidden}
    source_url = Column(String(1000), nullable=True)
    source_license = Column(String(200), nullable=True)
    # Curated/validated algorithmic targets used by the complexity assessor.
    # These are deliberately separate from observed Docker runtime and memory,
    # which cannot prove an algorithm's theoretical Big-O complexity.
    target_time_complexity = Column(String(20), nullable=True)
    target_space_complexity = Column(String(20), nullable=True)
    complexity_source = Column(String(50), nullable=True)
    complexity_confidence = Column(Float, nullable=True)
    complexity_reasoning = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=True, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    submissions = relationship("Submission", back_populates="problem")
    test_case_records = relationship("ProblemTestCase", back_populates="problem", cascade="all, delete-orphan")


class ProblemTestCase(Base):
    __tablename__ = "problem_test_cases"
    __table_args__ = (UniqueConstraint("problem_id", "position", name="uq_problem_test_case_position"),)

    id = Column(String(100), primary_key=True)
    problem_id = Column(String(100), ForeignKey("problems.id"), nullable=False, index=True)
    position = Column(Integer, nullable=False)
    visibility = Column(String(20), nullable=False, default="HIDDEN", index=True)
    input_data = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=False)
    time_limit_seconds = Column(Integer, nullable=False, default=2)
    memory_limit_mb = Column(Integer, nullable=False, default=256)
    content_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    problem = relationship("Problem", back_populates="test_case_records")

class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    due_date = Column(DateTime, nullable=True)
    status = Column(String(50), default="ACTIVE")  # ACTIVE, CLOSED, UPCOMING
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    course = relationship("Course", back_populates="assignments")
    problems = relationship("AssignmentProblem", back_populates="assignment", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="assignment")


class AssignmentProblem(Base):
    __tablename__ = "assignment_problems"
    __table_args__ = (UniqueConstraint("assignment_id", "problem_id", name="uq_assignment_problem"),)

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False, index=True)
    problem_id = Column(String(100), ForeignKey("problems.id"), nullable=False, index=True)
    position = Column(Integer, default=1)  # order in assignment
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    assignment = relationship("Assignment", back_populates="problems")
    problem = relationship("Problem")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(String(100), unique=True, nullable=False, index=True)
    student_id = Column(String(100), ForeignKey("students.student_id"), nullable=False, index=True)
    problem_id = Column(String(100), ForeignKey("problems.id"), nullable=False, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=True, index=True)  # NULL for independent practice
    language = Column(String(50), nullable=False)
    code = Column(Text, nullable=False)
    status = Column(String(50), default="SUBMITTED") # SUBMITTED, EVALUATED, FAILED
    
    # Evaluation Scores
    overall_score = Column(Float, nullable=True)
    correctness_score = Column(Float, nullable=True)
    complexity_score = Column(Float, nullable=True)
    style_score = Column(Float, nullable=True)
    similarity_score = Column(Float, nullable=True)
    
    # Deep Agent Outputs
    execution_result = Column(JSON, nullable=True)
    # Safe, student-visible complexity analysis. It deliberately omits the
    # private optimal TC/SC stored on the related problem.
    complexity_details = Column(JSON, nullable=True)
    # Internal-only review signals, deliberately excluded from response schemas.
    assessment_flags = Column(JSON, nullable=True)
    feedback = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    improved_code = Column(JSON, nullable=True)
    projected_score = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="submissions")
    problem = relationship("Problem", back_populates="submissions")
    assignment = relationship("Assignment", back_populates="submissions")
VERDICT_ACCEPTED = "ACCEPTED"
VERDICT_WRONG_ANSWER = "WRONG_ANSWER"
VERDICT_TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED"
VERDICT_MEMORY_LIMIT_EXCEEDED = "MEMORY_LIMIT_EXCEEDED"
VERDICT_OUTPUT_LIMIT_EXCEEDED = "OUTPUT_LIMIT_EXCEEDED"
VERDICT_RUNTIME_ERROR = "RUNTIME_ERROR"
VERDICT_COMPILATION_ERROR = "COMPILATION_ERROR"
VERDICT_SYSTEM_ERROR = "SYSTEM_ERROR"
