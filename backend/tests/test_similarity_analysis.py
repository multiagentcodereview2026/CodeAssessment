from similarity_analysis import (
    approach_label,
    structural_explanation,
    structural_fingerprint,
    structural_overlap,
)


def test_structural_fingerprint_ignores_identifier_renaming():
    left = structural_fingerprint(
        "def solve(values):\n    total = 0\n    for value in values:\n        total += value\n    return total\n",
        "python",
    )
    right = structural_fingerprint(
        "def calculate(items):\n    answer = 0\n    for item in items:\n        answer += item\n    return answer\n",
        "python",
    )
    overlap = structural_overlap(left, right)
    assert overlap >= 0.70
    assert approach_label(left) == approach_label(right)


def test_structural_explanation_is_evidence_based_without_ai():
    left = structural_fingerprint("for (int i = 0; i < n; ++i) { sum += a[i]; }", "cpp")
    right = structural_fingerprint("for (int j = 0; j < m; ++j) { ans += b[j]; }", "cpp")
    explanation = structural_explanation(left, right, structural_overlap(left, right))
    assert explanation
    assert all("AI" not in item for item in explanation)
