import asyncio
import pytest

from pydantic import BaseModel

from agents import base


class ExampleOutput(BaseModel):
    summary: str


@pytest.mark.parametrize("role", ["correctness", "style", "similarity", "recommendation", "supervisor", "hints"])
def test_reduced_ai_policy_blocks_legacy_enabled_roles(monkeypatch, role):
    class ForbiddenProvider:
        async def ainvoke(self, _messages):
            pytest.fail("Deterministic roles must never contact AI")

    monkeypatch.setattr(base.settings, "AI_ALLOWED_CAPABILITIES", role)
    monkeypatch.setattr(base.settings, "GROQ_API_KEY", "test-only")
    monkeypatch.setattr(base, "llm", ForbiddenProvider())
    result = asyncio.run(base.invoke_agent(
        "prompt", {}, ExampleOutput, {"summary": "Deterministic evidence"},
        capability=role,
    ))
    assert result == {"summary": "Deterministic evidence", "analysis_source": "fallback"}


class _Response:
    def __init__(self, content):
        self.content = content


class _FakeProvider:
    def __init__(self, content=None, error=None):
        self.content = content
        self.error = error

    async def ainvoke(self, _messages):
        if self.error:
            raise self.error
        return _Response(self.content)


class _BadRequest(Exception):
    status_code = 400


def test_projection_bad_request_is_not_retried(monkeypatch):
    calls = []
    async def rejected(messages):
        calls.append(messages)
        raise _BadRequest()
    monkeypatch.setattr(base, "_request_groq", rejected)
    monkeypatch.setattr(base.settings, "GROQ_API_KEY", "test-only")
    result = asyncio.run(base.invoke_agent("JSON", {}, ExampleOutput, {}, capability="score_projection"))
    assert len(calls) == 1
    assert result["provider_error"] == "bad_request"


def test_rate_limit_cooldown_prevents_second_provider_call(monkeypatch):
    class RateLimit(Exception):
        status_code = 429
    calls = []
    class Provider:
        async def ainvoke(self, messages):
            calls.append(messages)
            raise RateLimit()
    monkeypatch.setattr(base, "llm", Provider())
    monkeypatch.setattr(base, "_groq_cooldown_until", 0)
    monkeypatch.setattr(base.settings, "GROQ_MIN_REQUEST_INTERVAL_SECONDS", 0)
    monkeypatch.setattr(base.settings, "GROQ_API_KEY", "test-only")
    async def check():
        first = await base.invoke_agent("JSON", {}, ExampleOutput, {}, capability="score_projection")
        second = await base.invoke_agent("JSON", {}, ExampleOutput, {}, capability="score_projection")
        assert first["provider_error"] == second["provider_error"] == "rate_limit"
        assert second["retry_after"] > 0
    asyncio.run(check())
    assert len(calls) == 1


def _invoke(fallback):
    return asyncio.run(base.invoke_agent(
        "prompt", {"input": "test"}, ExampleOutput, fallback,
        capability="explainability",
    ))


def test_missing_provider_returns_labeled_copy_of_deterministic_fallback(monkeypatch):
    fallback = {"summary": "Evidence-based fallback"}
    monkeypatch.setattr(base, "llm", None)
    monkeypatch.setattr(base.settings, "GROQ_API_KEY", "")

    result = _invoke(fallback)

    assert result == {"summary": "Evidence-based fallback", "analysis_source": "fallback"}
    assert "analysis_source" not in fallback


def test_valid_provider_response_is_labeled_as_groq(monkeypatch):
    monkeypatch.setattr(base, "llm", _FakeProvider('{"summary":"Provider result"}'))
    monkeypatch.setattr(base.settings, "GROQ_API_KEY", "configured-for-test")

    result = _invoke({"summary": "Fallback"})

    assert result == {"summary": "Provider result", "analysis_source": "groq"}


def test_disabled_capability_never_calls_provider(monkeypatch):
    provider = _FakeProvider('{"summary":"Provider result"}')
    monkeypatch.setattr(base, "llm", provider)
    monkeypatch.setattr(base.settings, "GROQ_API_KEY", "configured-for-test")
    monkeypatch.setattr(base.settings, "AI_ALLOWED_CAPABILITIES", "hints")

    result = asyncio.run(base.invoke_agent(
        "prompt", {"source_code": "private"}, ExampleOutput,
        {"summary": "Deterministic"}, capability="similarity",
    ))

    assert result == {"summary": "Deterministic", "analysis_source": "fallback"}


def test_provider_error_uses_fallback_without_logging_error_contents(monkeypatch, caplog):
    private_detail = "request-payload-marker"
    monkeypatch.setattr(base, "llm", _FakeProvider(error=RuntimeError(private_detail)))
    monkeypatch.setattr(base.settings, "GROQ_API_KEY", "configured-for-test")

    result = _invoke({"summary": "Safe fallback"})

    assert result["analysis_source"] == "fallback"
    assert result["summary"] == "Safe fallback"
    assert private_detail not in caplog.text
    assert "RuntimeError" in caplog.text


def test_invalid_provider_schema_is_labeled_as_fallback(monkeypatch):
    monkeypatch.setattr(base, "llm", _FakeProvider('{"unexpected":"shape"}'))
    monkeypatch.setattr(base.settings, "GROQ_API_KEY", "configured-for-test")

    result = _invoke({"summary": "Validated fallback"})

    assert result == {"summary": "Validated fallback", "analysis_source": "fallback"}


def test_bad_request_retries_without_response_format_before_fallback(monkeypatch):
    monkeypatch.setattr(base, "llm", _FakeProvider(error=_BadRequest()))
    monkeypatch.setattr(base, "plain_llm", _FakeProvider('{"summary":"Plain retry result"}'))
    monkeypatch.setattr(base.settings, "GROQ_API_KEY", "configured-for-test")

    result = _invoke({"summary": "Fallback"})

    assert result == {"summary": "Plain retry result", "analysis_source": "groq"}
