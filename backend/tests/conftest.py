"""Unit tests must not spend a developer's configured provider allowance."""
import pytest
from config.settings import settings


@pytest.fixture(autouse=True)
def offline_provider_defaults(monkeypatch):
    # Provider contract tests explicitly install their own dummy key/client.
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    monkeypatch.setattr(settings, "GROQ_MIN_REQUEST_INTERVAL_SECONDS", 0.0)
