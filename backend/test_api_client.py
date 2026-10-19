"""API smoke tests that do not depend on a running local server or seeded data."""

from fastapi.testclient import TestClient

from database import Base, engine
from main import app


def test_health_and_problem_catalogue_contract():
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "healthy", "database": "connected"}

    catalogue = client.get("/api/problems")
    assert catalogue.status_code == 200
    assert isinstance(catalogue.json(), list)
    for problem in catalogue.json():
        assert isinstance(problem.get("id"), str)
        assert isinstance(problem.get("title"), str)


def test_code_execution_endpoints_require_student_authentication():
    client = TestClient(app)
    quick_run = client.post("/api/submissions/run", json={
        "language": "python",
        "code": "print(1)",
        "test_cases": [{"input": "", "expected_output": "1"}],
    })
    submission = client.post("/api/submissions/submit", json={
        "problem_id": "sample",
        "language": "python",
        "code": "print(1)",
    })

    assert quick_run.status_code == 401
    assert submission.status_code == 401


def test_cors_allows_local_frontend_and_rejects_untrusted_origins():
    client = TestClient(app)
    trusted = client.get("/health", headers={"Origin": "http://localhost:8080"})
    untrusted = client.get("/health", headers={"Origin": "https://untrusted.example"})

    assert trusted.headers.get("access-control-allow-origin") == "http://localhost:8080"
    assert "access-control-allow-origin" not in untrusted.headers
