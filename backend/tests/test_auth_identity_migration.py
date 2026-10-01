import os
import subprocess
import sys
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy import inspect, text
from sqlalchemy.engine import URL


def test_legacy_schema_migration_adds_and_backfills_auth_links(tmp_path):
    backend_dir = Path(__file__).resolve().parents[1]
    database_path = tmp_path / "legacy.sqlite"
    database_url = URL.create("sqlite", database=str(database_path)).render_as_string(
        hide_password=False
    )
    engine = sa.create_engine(database_url)

    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE users ("
            "id INTEGER PRIMARY KEY, username VARCHAR(100) UNIQUE NOT NULL, "
            "email VARCHAR(200) UNIQUE NOT NULL, full_name VARCHAR(200) NOT NULL, "
            "hashed_password VARCHAR(200) NOT NULL, role VARCHAR(50) NOT NULL, "
            "is_active BOOLEAN, created_at DATETIME)"
        ))
        connection.execute(text(
            "CREATE TABLE students ("
            "id INTEGER PRIMARY KEY, student_id VARCHAR(100) UNIQUE NOT NULL, "
            "name VARCHAR(200) NOT NULL, email VARCHAR(200), institution VARCHAR(200), "
            "department VARCHAR(100), xp INTEGER, streak_days INTEGER, created_at DATETIME)"
        ))
        connection.execute(text(
            "CREATE TABLE problems ("
            "id VARCHAR(100) PRIMARY KEY, title VARCHAR(200) NOT NULL, "
            "difficulty VARCHAR(50), category VARCHAR(100), description TEXT NOT NULL, "
            "examples JSON NOT NULL, constraints JSON NOT NULL, starter_codes JSON NOT NULL, "
            "test_cases JSON NOT NULL, created_at DATETIME)"
        ))
        connection.execute(text(
            "CREATE TABLE submissions ("
            "id INTEGER PRIMARY KEY, submission_id VARCHAR(100) UNIQUE NOT NULL, "
            "student_id VARCHAR(100) NOT NULL, problem_id VARCHAR(100) NOT NULL, "
            "language VARCHAR(50) NOT NULL, code TEXT NOT NULL, status VARCHAR(50), "
            "overall_score FLOAT, correctness_score FLOAT, complexity_score FLOAT, "
            "style_score FLOAT, similarity_score FLOAT, execution_result JSON, feedback JSON, "
            "recommendations JSON, improved_code JSON, projected_score JSON, created_at DATETIME)"
        ))
        connection.execute(text(
            "INSERT INTO users (id, username, email, full_name, hashed_password, role, is_active) "
            "VALUES (1, 'legacy-student', 'legacy@example.com', 'Legacy Student', 'unused', 'student', 1)"
        ))
        connection.execute(text(
            "INSERT INTO students (id, student_id, name, email) "
            "VALUES (1, 'legacy-student', 'Legacy Student', 'legacy@example.com')"
        ))

    environment = os.environ.copy()
    environment["DATABASE_URL"] = database_url
    command = [sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"]
    first_run = subprocess.run(command, cwd=backend_dir, env=environment, capture_output=True, text=True)
    assert first_run.returncode == 0, first_run.stdout + first_run.stderr
    second_run = subprocess.run(command, cwd=backend_dir, env=environment, capture_output=True, text=True)
    assert second_run.returncode == 0, second_run.stdout + second_run.stderr

    inspector = inspect(engine)
    student_columns = {column["name"] for column in inspector.get_columns("students")}
    user_columns = {column["name"] for column in inspector.get_columns("users")}
    problem_columns = {column["name"] for column in inspector.get_columns("problems")}
    submission_columns = {column["name"] for column in inspector.get_columns("submissions")}
    assert "user_id" in student_columns
    assert "token_version" in user_columns
    assert {"target_time_complexity", "target_space_complexity", "complexity_reasoning"}.issubset(problem_columns)
    assert {"assignment_id", "complexity_details", "assessment_flags"}.issubset(submission_columns)
    assert any(
        foreign_key.get("constrained_columns") == ["user_id"]
        and foreign_key.get("referred_table") == "users"
        for foreign_key in inspector.get_foreign_keys("students")
    )
    assert any(
        index.get("column_names") == ["user_id"] and index.get("unique")
        for index in inspector.get_indexes("students")
    )
    with engine.connect() as connection:
        linked_user_id = connection.execute(text(
            "SELECT user_id FROM students WHERE student_id = 'legacy-student'"
        )).scalar_one()
    assert linked_user_id == 1

    engine.dispose()
