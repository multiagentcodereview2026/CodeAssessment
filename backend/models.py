from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base

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

    submissions = relationship("Submission", back_populates="student")

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

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(String(100), unique=True, nullable=False, index=True)
    student_id = Column(String(100), ForeignKey("students.student_id"), nullable=False, index=True)
    problem_id = Column(String(100), ForeignKey("problems.id"), nullable=False, index=True)
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
    feedback = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    improved_code = Column(JSON, nullable=True)
    projected_score = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="submissions")
    problem = relationship("Problem", back_populates="submissions")
