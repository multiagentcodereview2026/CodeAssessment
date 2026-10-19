import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.models import VERDICT_SYSTEM_ERROR


client = TestClient(app)


def test_health_is_unhealthy_when_docker_is_unavailable(monkeypatch):
    monkeypatch.setattr("app.main.is_docker_available", lambda: False)
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["detail"] == "Docker execution sandbox is not ready"


def test_execute_rejects_empty_code_and_missing_cases():
    empty_code = client.post("/execute", json={"code": "   ", "language": "python", "test_cases": [{"id": 1, "input": "", "expected_output": ""}]})
    no_cases = client.post("/execute", json={"code": "print(1)", "language": "python", "test_cases": []})
    assert empty_code.status_code == 400
    assert no_cases.status_code == 400


def test_execute_rejects_malformed_request():
    response = client.post("/execute", json={"code": "print(1)", "language": "python", "test_cases": [{"id": 1}]})
    assert response.status_code == 422


def test_unknown_language_returns_structured_system_error():
    response = client.post("/execute", json={"code": "print(1)", "language": "unknown", "test_cases": [{"id": 1, "input": "", "expected_output": ""}]})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == VERDICT_SYSTEM_ERROR
    assert body["compile_success"] is False
    assert body["tests_failed"] == 1
