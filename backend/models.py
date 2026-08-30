from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text

from database import Base


class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    email = Column(
        String(200),
        unique=True,
        nullable=False,
        index=True
    )

    hashed_password = Column(
        String(255),
        nullable=False
    )

    role = Column(
        String(20),
        nullable=False,
        default="student"
    )

    name = Column(
        String(200),
        nullable=True
    )

    student_id = Column(
        String(100),
        unique=True,
        nullable=True,
        index=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class Submission(Base):

    __tablename__ = "submissions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    submission_id = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    student_id = Column(
        String(100),
        nullable=False,
        index=True
    )

    problem_id = Column(
        String(100),
        nullable=False
    )

    language = Column(
        String(50),
        nullable=False
    )

    code = Column(
        Text,
        nullable=False
    )

    status = Column(
        String(50),
        default="SUBMITTED"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
