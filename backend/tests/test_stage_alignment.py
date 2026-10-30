import asyncio

import pytest

from agents import revision


STATE = {
    "problem": {"title": "Sum", "statement": "Sum the inputs."},
    "submission": {"source_code": "print(sum(values))", "language": "python"},
    "guided_revision": {"stage": "OPTIMIZE_SPACE", "guided_steps": ["Accumulate input without storing it."]},
}


@pytest.mark.parametrize("failure", [None, "guidance_supported", "candidate_follows_guidance", "stage_scope_preserved", "provider", "evidence"])
def test_alignment_requires_review_of_all_three_concerns(monkeypatch, failure):
    async def reviewer(prompt, payload, schema, fallback, **kwargs):
        assert payload["guidance"] == STATE["guided_revision"]
        assert payload["original_source"] == STATE["submission"]["source_code"]
        assert "private tests" in prompt
        assert kwargs["capability"] == "score_projection"
        result = dict(guidance_supported=True, candidate_follows_guidance=True,
                      stage_scope_preserved=True, evidence=["Input is accumulated into a scalar."],
                      analysis_source="groq")
        if failure == "provider":
            result["analysis_source"] = "fallback"
        elif failure == "evidence":
            result["evidence"] = []
        elif failure:
            result[failure] = False
        return result
    monkeypatch.setattr(revision, "invoke_agent", reviewer)
    result = asyncio.run(revision.review_stage_alignment(STATE, "OPTIMIZE_SPACE", "print(total)"))
    assert (result["status"] == "aligned") is (failure is None)


def test_missing_guidance_never_calls_provider(monkeypatch):
    async def forbidden(*args, **kwargs):
        pytest.fail("Missing guidance must not be reviewed")
    monkeypatch.setattr(revision, "invoke_agent", forbidden)
    assert asyncio.run(revision.review_stage_alignment({}, "OPTIMIZE", "print(1)"))["status"] == "unavailable"


def test_private_generation_receives_exact_displayed_guidance(monkeypatch):
    async def generate(prompt, payload, schema, fallback, **kwargs):
        assert payload["guidance"] == STATE["guided_revision"]
        return {"improved_code": "print(total)", "analysis_source": "groq"}
    monkeypatch.setattr(revision, "invoke_agent", generate)
    result = asyncio.run(revision.private_stage_revision_node(STATE, "OPTIMIZE_SPACE"))
    assert result["private_revision"]["revision_source"] == "ai"
