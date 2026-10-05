from analysis.build_phase2_time_review import classify


def test_time_review_marks_nested_overcount_for_review():
    queue, _ = classify({"target_time": "O(n)", "detected_time": "O(n^2)", "signals": ["loop-depth:2"]})
    assert queue == "POSSIBLE_AST_OVERCOUNT"


def test_time_review_marks_undercount_for_review():
    queue, _ = classify({"target_time": "O(n^2)", "detected_time": "O(n)", "signals": []})
    assert queue == "POSSIBLE_AST_UNDERCOUNT"
