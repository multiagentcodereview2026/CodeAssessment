from similarity_clustering import build_approach_groups, build_similarity_clusters, build_submission_groups


def case(identifier, left, right, problem="p-1"):
    return {
        "id": identifier,
        "courseId": 1,
        "courseTitle": "Algorithms",
        "problemId": problem,
        "problemTitle": problem,
        "studentA": {"id": left, "name": left, "submissionId": f"sub-{left}"},
        "studentB": {"id": right, "name": right, "submissionId": f"sub-{right}"},
        "reviewStatus": "open",
    }


def test_connected_pairs_become_one_student_cluster():
    clusters = build_similarity_clusters([case("ab", "a", "b"), case("bc", "b", "c")])
    assert len(clusters) == 1
    assert [member["id"] for member in clusters[0]["members"]] == ["a", "b", "c"]
    assert clusters[0]["pairCount"] == 2
    assert [member["rank"] for member in clusters[0]["members"]] == [1, 2, 3]


def test_different_problems_never_share_a_cluster():
    clusters = build_similarity_clusters([case("ab", "a", "b", "p-1"), case("ac", "a", "c", "p-2")])
    assert len(clusters) == 2


def test_approach_groups_are_informational_and_problem_scoped():
    records = [
        {"courseId": 1, "courseTitle": "Algorithms", "problemId": "p-1", "problemTitle": "P1", "approachLabel": "Dynamic Programming", "approachSummary": "matrix-like state", "student": {"id": "a", "overallScore": 90}},
        {"courseId": 1, "courseTitle": "Algorithms", "problemId": "p-1", "problemTitle": "P1", "approachLabel": "Dynamic Programming", "approachSummary": "matrix-like state", "student": {"id": "b", "overallScore": 80}},
        {"courseId": 1, "courseTitle": "Algorithms", "problemId": "p-2", "problemTitle": "P2", "approachLabel": "Dynamic Programming", "approachSummary": "matrix-like state", "student": {"id": "c", "overallScore": 70}},
    ]
    groups = build_approach_groups(records)
    assert len(groups) == 1
    assert [member["id"] for member in groups[0]["members"]] == ["a", "b"]
    assert "not a code-overlap finding" in groups[0]["explanation"]


def test_submission_groups_include_every_latest_student_exactly_once():
    records = [
        {"courseId": 1, "courseTitle": "Algorithms", "assignmentId": 9, "problemId": "p-1", "problemTitle": "P1", "approachLabel": "Iterative Loop", "approachSummary": "loop depth 1", "sourceCode": "a", "student": {"id": "a", "overallScore": 90}},
        {"courseId": 1, "courseTitle": "Algorithms", "assignmentId": 9, "problemId": "p-1", "problemTitle": "P1", "approachLabel": "Iterative Loop", "approachSummary": "loop depth 1", "sourceCode": "b", "student": {"id": "b", "overallScore": 80}},
        {"courseId": 1, "courseTitle": "Algorithms", "assignmentId": 9, "problemId": "p-1", "problemTitle": "P1", "approachLabel": "Dynamic Programming", "approachSummary": "matrix-like state", "sourceCode": "c", "student": {"id": "c", "overallScore": 70}},
        {"courseId": 1, "courseTitle": "Algorithms", "assignmentId": 9, "problemId": "p-1", "problemTitle": "P1", "approachLabel": "Dynamic Programming", "approachSummary": "matrix-like state", "sourceCode": "d", "student": {"id": "d", "overallScore": 60}},
        {"courseId": 1, "courseTitle": "Algorithms", "assignmentId": 9, "problemId": "p-1", "problemTitle": "P1", "approachLabel": "Recursion", "approachSummary": "recursion", "sourceCode": "e", "student": {"id": "e", "overallScore": 50}},
    ]
    groups = build_submission_groups(records, [case("ab", "a", "b") | {"assignmentId": 9}])
    assert len(groups) == 3
    assert {member["id"] for group in groups for member in group["members"]} == {"a", "b", "c", "d", "e"}
    assert sum(len(group["members"]) for group in groups) == 5
    assert any(group["groupKind"] == "code_overlap" and len(group["members"]) == 2 for group in groups)
    assert any(group["groupKind"] == "structural" and len(group["members"]) == 2 for group in groups)
    assert any(group["groupKind"] == "individual" and len(group["members"]) == 1 for group in groups)


def test_newest_submission_replaces_old_group_membership_when_it_becomes_similar():
    # These are the two latest records after student A resubmits.  The older
    # independent implementation is deliberately absent from the input.
    records = [
        {"courseId": 1, "courseTitle": "Algorithms", "assignmentId": 9, "problemId": "p-1", "problemTitle": "P1", "approachLabel": "Iterative Loop", "approachSummary": "loop depth 1", "sourceCode": "new-a", "student": {"id": "a", "submissionId": "a-new", "overallScore": 91}},
        {"courseId": 1, "courseTitle": "Algorithms", "assignmentId": 9, "problemId": "p-1", "problemTitle": "P1", "approachLabel": "Iterative Loop", "approachSummary": "loop depth 1", "sourceCode": "b-current", "student": {"id": "b", "submissionId": "b-current", "overallScore": 89}},
    ]

    groups = build_submission_groups(records, [case("new-ab", "a", "b") | {"assignmentId": 9}])

    assert len(groups) == 1
    assert groups[0]["groupKind"] == "code_overlap"
    assert {member["submissionId"] for member in groups[0]["members"]} == {"a-new", "b-current"}
