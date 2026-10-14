from similarity_clustering import build_approach_groups, build_similarity_clusters


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
