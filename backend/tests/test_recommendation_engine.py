from types import SimpleNamespace

from recommendation_engine import build_recommendations, build_roadmap, difficulty_plan


def problem(problem_id, difficulty, category, topic_tags):
    return SimpleNamespace(
        id=problem_id,
        title=problem_id.replace("-", " ").title(),
        difficulty=difficulty,
        category=category,
        topic_tags=topic_tags,
    )


def submission(problem_id, score):
    return SimpleNamespace(problem_id=problem_id, overall_score=score)


def test_best_score_is_used_once_for_every_problem_tag():
    problems = [
        problem("window-a", "Easy", "Array", ["Array", "Two Pointers"]),
        problem("window-b", "Medium", "Array", ["Array"]),
    ]
    result = build_recommendations(
        problems,
        [submission("window-a", 40), submission("window-a", 90), submission("window-b", 70)],
    )

    topics = {item["topic"]: item for item in result["topics"]}
    assert topics["Array"]["assessed_problems"] == 2
    assert topics["Array"]["average_score"] == 80.0
    assert topics["Two Pointers"]["assessed_problems"] == 1
    assert topics["Two Pointers"]["average_score"] == 90.0


def test_difficulty_policy_matches_published_ranges():
    assert set(difficulty_plan(59)) == {"Easy"}
    assert difficulty_plan(99, completed_problems=2) == ["Easy"] * 6
    assert difficulty_plan(65, completed_problems=3) == ["Easy", "Easy", "Easy", "Easy", "Easy", "Medium"]
    assert difficulty_plan(75, completed_problems=6) == ["Easy", "Medium", "Medium", "Medium", "Hard", "Hard"]
    assert difficulty_plan(96, completed_problems=10) == ["Easy", "Medium", "Medium", "Hard", "Hard", "Hard"]


def test_recommendations_are_same_topic_and_prefer_unattempted_ids():
    problems = [
        problem("array-easy-attempted", "Easy", "Array", ["Array"]),
        problem("array-easy-new", "Easy", "Array", ["Array"]),
        problem("array-medium-new", "Medium", "Array", ["Array"]),
        problem("tree-easy-new", "Easy", "Tree", ["Tree"]),
    ]
    result = build_recommendations(problems, [submission("array-easy-attempted", 50)], topic_limit=1)

    assert result["priority_topics"] == ["Array"]
    assert result["problems"][0]["id"] == "array-easy-new"
    assert all(item["topic"] == "Array" for item in result["problems"])


def test_selected_topic_remains_available_after_core_or_high_score_progress():
    problems = [
        problem("array-done", "Easy", "Array", ["Array"]),
        problem("array-next-easy", "Easy", "Array", ["Array"]),
        problem("array-next-medium", "Medium", "Array", ["Array"]),
        problem("array-next-hard", "Hard", "Array", ["Array"]),
        problem("greedy-done", "Easy", "Greedy", ["Greedy"]),
        problem("greedy-next", "Easy", "Greedy", ["Greedy"]),
    ]
    result = build_recommendations(
        problems,
        [submission("array-done", 100), submission("greedy-done", 50)],
        selected_topic="Array",
    )

    assert result["priority_topics"] == ["Array"]
    assert result["problems"]
    assert all(item["topic"] == "Array" for item in result["problems"])


def test_small_sample_does_not_fill_easy_queue_with_harder_problems():
    problems = [
        problem("array-easy-done", "Easy", "Array", ["Array"]),
        problem("array-easy-next", "Easy", "Array", ["Array"]),
        problem("array-hard-next", "Hard", "Array", ["Array"]),
    ]
    result = build_recommendations(problems, [submission("array-easy-done", 100)], topic_limit=1)

    assert result["problems"]
    assert [item["difficulty"] for item in result["problems"]] == ["Easy"]


def test_roadmap_uses_the_exact_curated_array_set():
    from curated_roadmap import CURRICULUM
    configured = next(s for s in CURRICULUM['steps'] if s['id'] == 'arrays')
    problems = [problem(p['id'], p['difficulty'], 'Array', ['Array']) for p in configured['problems']]
    result = build_roadmap(problems, [submission(p.id, 95) for p in problems])
    arrays = next(step for step in result['steps'] if step['id'] == 'arrays')
    assert arrays['core_required_problems'] == 22
    assert arrays['core_complete'] is True
    assert arrays['mastered'] is False
    assert arrays['completed_by_difficulty'] == {'Easy': 11, 'Medium': 9, 'Hard': 2}
