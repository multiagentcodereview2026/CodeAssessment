import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./codeassessment_v2.db")


engine_options = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_options)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()


def ensure_problem_complexity_columns() -> None:
    """Add TC/SC metadata columns to an existing problem bank when needed.

    ``create_all`` creates missing tables but never alters existing tables.
    This small, idempotent migration keeps a deployed PostgreSQL or SQLite
    database compatible with the new dataset metadata without recreating the
    ``problems`` table or touching test cases and submissions.
    """
    required_columns = {
        "target_time_complexity": "VARCHAR(20)",
        "target_space_complexity": "VARCHAR(20)",
        "complexity_source": "VARCHAR(50)",
        "complexity_confidence": "FLOAT",
        "complexity_reasoning": "TEXT",
    }
    inspector = inspect(engine)
    if "problems" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("problems")}
    with engine.begin() as connection:
        for name, sql_type in required_columns.items():
            if name not in existing:
                # Both the column names and types are static values above.
                connection.execute(text(f"ALTER TABLE problems ADD COLUMN {name} {sql_type}"))


def ensure_submission_assessment_columns() -> None:
    """Add safe persisted assessment details without recreating submissions."""
    inspector = inspect(engine)
    if "submissions" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("submissions")}
    required_columns = {
        "complexity_details": "JSON",
        "assessment_flags": "JSON",
    }
    with engine.begin() as connection:
        for name, sql_type in required_columns.items():
            if name not in existing:
                # JSON is supported by PostgreSQL and SQLite's dynamic typing.
                connection.execute(text(f"ALTER TABLE submissions ADD COLUMN {name} {sql_type}"))


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
