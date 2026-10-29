import asyncio

from agents import similarity


def _state():
    return {
        "problem": {"id": "problem-1", "title": "Example"},
        "submission": {"source_code": "def solve(a): return a + 1", "language": "python"},
        "user": {"student_id": "student-1"},
    }


def test_no_peer_submissions_is_not_fabricated_as_an_originality_score(monkeypatch):
    monkeypatch.setattr(similarity, "get_peer_submissions", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(
        similarity,
        "invoke_agent",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("LLM should not invent a comparison")),
    )

    result = asyncio.run(similarity.similarity_node(_state()))

    assert result["similarity_score"] is None
    assert result["similarity_details"]["originality_score"] is None
    assert result["similarity_details"]["comparison_status"] == "no_peer_submissions"
    assert result["similarity_details"]["comparison_available"] is False


def test_database_failure_is_distinguished_from_an_empty_comparison_set(monkeypatch):
    monkeypatch.setattr(similarity, "get_peer_submissions", lambda *_args, **_kwargs: None)

    result = asyncio.run(similarity.similarity_node(_state()))

    assert result["similarity_score"] is None
    assert result["similarity_details"]["comparison_status"] == "database_unavailable"
    assert "could not be loaded" in result["similarity_details"]["reasoning"]


def test_peer_comparison_calculates_similarity_from_real_peer_rows(monkeypatch):
    peer_code = "def other(values):\n    total = 0\n    for item in values:\n        total += item\n    return total"
    source_code = "def solve(values):\n    total = 0\n    for item in values:\n        total += item\n    return total"
    monkeypatch.setattr(
        similarity,
        "get_peer_submissions",
        lambda *_args, **_kwargs: [{"submission_id": "peer-1", "code": peer_code}],
    )

    async def fake_invoke(_prompt, _payload, _schema, fallback, **_kwargs):
        return {**fallback, "analysis_source": "fallback"}

    monkeypatch.setattr(similarity, "invoke_agent", fake_invoke)
    state = _state()
    state["submission"]["source_code"] = source_code

    result = asyncio.run(similarity.similarity_node(state))

    assert result["similarity_score"] == similarity.calculate_jaccard_similarity(source_code, peer_code)
    assert result["similarity_score"] != 10.0
    assert result["similarity_details"]["comparison_count"] == 1
    assert result["similarity_details"]["similar_submission_ids"] == ["peer-1"]
