import asyncio

from pydantic import BaseModel

from agents import base


class ExampleOutput(BaseModel):
    summary: str


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


def _invoke(fallback):
    return asyncio.run(base.invoke_agent(
        "prompt", {"input": "test"}, ExampleOutput, fallback,
        capability="hints",
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
