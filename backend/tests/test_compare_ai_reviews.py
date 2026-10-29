import copy
import pytest
from analysis.compare_ai_reviews import compare


def fixture():
    original = [{"solution_id": "s1", "problem_id": "original-group", "language": "python", "source": 'def solve():\n    return "a b"\n'}]
    review = [{"solution_id": "s1", "language": "python", "time_complexity": "O(1)", "auxiliary_space": "O(1)", "reviewer_type": "ai_assisted", "reviewer_id": "self-reported-model", "ground_truth_source": "ai_assisted_unverified"}]
    return original, review, copy.deepcopy(review)


def test_ai_agreement_preserves_canonical_groups_and_unverified_provenance():
    original, a, b = fixture()
    b[0].update(source=original[0]["source"] + "\n", problem_id="changed-group", source_sha256_declared="incorrect", source_sha256_recomputed_match=True)
    report, proposed = compare(original, a, b)
    assert report["model_agreement"]["joint_agrees"] == 1
    assert report["human_validated"] is False
    assert proposed[0]["ground_truth_source"] == "ai_assisted_unverified"
    assert proposed[0]["problem_id"] == "original-group"
    assert report["review_metadata"][1]["changed_problem_group_ids"] == ["s1"]
    assert report["review_metadata"][1]["hash_claim_warnings"]


def test_disagreement_is_not_adjudicated_automatically():
    original, a, b = fixture()
    b[0]["time_complexity"] = "O(n)"
    report, proposed = compare(original, a, b)
    assert report["model_agreement"]["joint_agrees"] == 0
    assert proposed == []


@pytest.mark.parametrize("change", [{"source": 'def solve():\n    return "ab"\n'}, {"ground_truth_source": "human_reviewed"}, {"solution_id": "unknown"}, {"time_complexity": None}])
def test_wrong_source_missing_labels_and_false_human_tags_are_rejected(change):
    original, a, b = fixture()
    b[0].update(change)
    with pytest.raises(ValueError):
        compare(original, a, b)


def test_duplicate_review_rows_are_rejected():
    original, a, b = fixture()
    b.append(copy.deepcopy(b[0]))
    with pytest.raises(ValueError):
        compare(original, a, b)
