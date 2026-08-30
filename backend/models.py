from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default="student")
    name = Column(String(200), nullable=True)
    student_id = Column(String(100), unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(String(100), unique=True, nullable=False, index=True)
    student_id = Column(String(100), nullable=False, index=True)
    problem_id = Column(String(100), nullable=False)
    language = Column(String(50), nullable=False)
    code = Column(Text, nullable=False)
    status = Column(String(50), default="SUBMITTED")
    created_at = Column(DateTime, default=datetime.utcnow)


class InstructorStudentAssignment(Base):
    __tablename__ = "instructor_student_assignments"

    id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(Integer, nullable=False, index=True)
    student_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Problem(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    constraints = Column(Text, nullable=True)
    input_format = Column(Text, nullable=True)
    output_format = Column(Text, nullable=True)
    supported_languages = Column(String(500), nullable=False)
    difficulty = Column(String(50), nullable=True)
    time_limit = Column(Integer, nullable=False, default=2)
    memory_limit = Column(Integer, nullable=False, default=256)
    created_at = Column(DateTime, default=datetime.utcnow)
