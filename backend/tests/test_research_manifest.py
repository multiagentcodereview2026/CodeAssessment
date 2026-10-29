import json
from analysis.research_manifest import manifest


def test_release_manifest_allowlists_sources_and_never_keys_or_data(tmp_path, monkeypatch):
    from config.settings import settings
    source = tmp_path / "backend" / "agents"
    source.mkdir(parents=True)
    (source / "example.py").write_text("pass", encoding="utf-8")
    (tmp_path / ".env").write_text("GROQ_API_KEY=SECRET-DO-NOT-EXPORT", encoding="utf-8")
    (tmp_path / "private.db").write_text("PRIVATE-DATABASE", encoding="utf-8")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "SECRET-DO-NOT-EXPORT")
    result = manifest(tmp_path, "example-commit", "host_tooling")
    text = json.dumps(result)
    assert "SECRET-DO-NOT-EXPORT" not in text and "PRIVATE-DATABASE" not in text
    assert set(result["files"]) == {"backend/agents/example.py"}
    first_hash = result["source_sha256"]
    (source / "example.py").write_text("print(1)", encoding="utf-8")
    assert manifest(tmp_path, "example-commit", "host_tooling")["source_sha256"] != first_hash
