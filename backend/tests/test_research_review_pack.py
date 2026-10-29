import json
import pytest
from analysis.build_research_review_pack import build
from analysis.validate_approach_corpus import validate


def test_review_pack_is_blank_independent_reproducible_and_cannot_pass_as_gold(tmp_path):
    folder = tmp_path / "review-pack"
    manifest = build(folder)
    assert manifest["rows"] == 20
    assert manifest["generalization_accuracy_claim_allowed"] is False
    rows = [json.loads(line) for line in (folder / "reviewer-A.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len({row["solution_id"] for row in rows}) == 20
    assert all(row["snippet_time_complexity"] is None and row["ground_truth_source"] is None for row in rows)
    assert validate(str(folder / "adjudication-template.jsonl"), minimum=20, require_reviewed=True)["errors"]
    assert build(tmp_path / "second")["payload_sha256"] == manifest["payload_sha256"]
    with pytest.raises(FileExistsError):
        build(folder)
