import json
import pytest
from analysis.scoring_policy_audit import audit


def test_sensitivity_is_explicitly_synthetic_without_reviewers():
    result = audit()
    assert len(result["scenarios"]) == 28
    assert result["human_validation"] == "pending"
    assert "mean_absolute_error_against_instructor" not in result


def test_review_comparison_has_known_mae_and_provenance_hash():
    row = {"id": "sample", "correctness": 80, "time": 80, "space": 60, "style": 90,
           "instructor_score": 76, "reviewed_by": ["r1", "r2"]}
    result = audit(json.dumps(row))
    assert result["mean_absolute_error_against_instructor"]["default"] == 0
    assert result["review_count"] == 1
    assert len(result["review_sha256"]) == 64
    for change in ({"reviewed_by": ["r1"]}, {"style": float("nan")}, {"correctness": True}):
        with pytest.raises(ValueError):
            audit(json.dumps({**row, **change}))
    with pytest.raises(ValueError):
        audit(json.dumps(row) + '\n' + json.dumps(row))
