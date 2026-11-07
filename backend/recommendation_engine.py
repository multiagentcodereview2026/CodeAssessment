"""Deterministic topic progress and practice recommendation rules.

This module deliberately contains no model calls or AI calls.  A problem contributes
once to every one of its tags, using a student's best assessed score for that
problem.  Keeping the policy pure makes it straightforward to test and audit.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable


from curated_roadmap import ROADMAP_STEPS, build_roadmap


def normalize_topics(topic_tags: Any, category: str | None) -> list[str]:
    """Return ordered, de-duplicated problem topics with category as a fallback."""
    values = topic_tags if isinstance(topic_tags, list) else []
    topics: list[str] = []
    for value in values:
        topic = str(value).strip()
        if topic and topic not in topics:
            topics.append(topic)
    fallback = (category or "Uncategorized").strip() or "Uncategorized"
    if not topics:
        topics.append(fallback)
    return topics


def difficulty_plan(
    average_score: float | None,
    limit: int = 6,
    *,
    completed_problems: int = 0,
) -> list[str]:
    """Create the visible Easy -> Medium -> Hard queue for a topic.

    ``limit`` only controls the number of cards shown.  It does not change
    the roadmap's longer-term core quotas.  Keeping at least one Easy item in
    every mixed band gives learners an accessible warm-up while their topic
    average determines how much Medium/Hard practice they receive.
    """
    score = 0.0 if average_score is None else average_score
    completed = max(0, int(completed_problems))
    if limit <= 0:
        return []
    # A small sample is not enough evidence to escalate difficulty. This is
    # why two 99% submissions still receive Easy practice rather than a sudden
    # jump to Hard problems.
    if score < 60 or completed < 3:
        return ["Easy"] * limit
    if score < 65:
        return ["Easy"] * limit
    if completed < 6 or score < 70:
        return ["Easy"] * max(1, limit - 1) + ["Medium"]
    if completed < 10 or score <= 95:
        return ["Easy"] + ["Medium"] * max(1, limit - 3) + ["Hard"] * min(2, limit - 1)
    return ["Easy"] + ["Medium"] * max(1, limit - 4) + ["Hard"] * min(3, limit - 1)


def _roadmap_step_for_topic(topic: str) -> tuple[str, str] | None:
    """Return the curriculum level for an exact public problem-bank tag."""
    normalized = topic.casefold()
    for _step_id, _title, aliases, _prerequisites, level, *_targets in ROADMAP_STEPS:
        if normalized in {alias.casefold() for alias in aliases}:
            return _step_id, level
    return None


def _practice_difficulty_plan(topic_data: dict[str, Any], limit: int) -> list[str]:
    """Choose six practice cards from the topic's current score band.

    The DSA Roadmap separately enforces its exact Easy/Medium/Hard completion
    quotas. Practice recommendations are deliberately lighter-weight: each
    successful submission naturally removes its card because completed IDs are
    deprioritized, then this deterministic mix supplies the replacement.
    """
    return difficulty_plan(
        topic_data["average_score"],
        limit,
        completed_problems=topic_data["assessed_problems"],
    )


def build_recommendations(
    problems: Iterable[Any],
    submissions: Iterable[Any],
    *,
    per_topic_limit: int = 6,
    topic_limit: int = 3,
    selected_topic: str | None = None,
) -> dict[str, Any]:
    """Build topic averages and same-topic recommendations from assessed attempts.

    ``problems`` need ``id``, ``category``, ``topic_tags``, ``title`` and
    ``difficulty`` attributes.  ``submissions`` need ``problem_id`` and
    ``overall_score``.  Callers must apply their own visibility/status scope.
    """
    ordered_problems = sorted(problems, key=lambda problem: str(problem.id))
    by_id = {problem.id: problem for problem in ordered_problems}

    # A problem ID has exactly one contribution: its highest official score.
    best_scores: dict[str, float] = {}
    for submission in submissions:
        problem_id = getattr(submission, "problem_id", None)
        score = getattr(submission, "overall_score", None)
        if problem_id not in by_id or score is None:
            continue
        numeric_score = float(score)
        best_scores[problem_id] = max(best_scores.get(problem_id, float("-inf")), numeric_score)

    topic_problem_ids: dict[str, list[str]] = defaultdict(list)
    for problem in ordered_problems:
        for topic in normalize_topics(getattr(problem, "topic_tags", None), getattr(problem, "category", None)):
            topic_problem_ids[topic].append(problem.id)

    topic_rows: list[dict[str, Any]] = []
    for topic in sorted(topic_problem_ids):
        assessed = [best_scores[problem_id] for problem_id in topic_problem_ids[topic] if problem_id in best_scores]
        average = round(sum(assessed) / len(assessed), 1) if assessed else None
        completed_by_difficulty = {
            difficulty: sum(
                1
                for problem_id in topic_problem_ids[topic]
                if problem_id in best_scores and by_id[problem_id].difficulty == difficulty
            )
            for difficulty in ("Easy", "Medium", "Hard")
        }
        topic_rows.append({
            "topic": topic,
            "average_score": average,
            "assessed_problems": len(assessed),
            "completed_by_difficulty": completed_by_difficulty,
            "reason": (
                f"Best-score average across {len(assessed)} distinct {topic} problem"
                f"{'s' if len(assessed) != 1 else ''}: {average:.1f}%."
                if average is not None
                else f"No assessed {topic} problem yet. Start with an Easy problem."
            ),
        })

    # Practised lower averages need attention first. Untried topics follow in
    # stable alphabetical order so this never becomes a random list.
    requested_topic = str(selected_topic or "").strip().casefold()
    if requested_topic:
        # The Practice & topics selector is intentional focused practice.
        # It must keep serving this topic after roadmap completion instead of
        # restricting the learner to whichever three topics are auto-priority.
        priority_topics = [
            item for item in topic_rows
            if item["topic"].casefold() == requested_topic
        ]
    else:
        priority_topics = sorted(
            topic_rows,
            key=lambda item: (
                item["average_score"] is None,
                item["average_score"] if item["average_score"] is not None else 0.0,
                item["assessed_problems"],
                item["topic"],
            ),
        )[:topic_limit]

    recommendations: list[dict[str, Any]] = []
    for topic_data in priority_topics:
        topic = topic_data["topic"]
        candidates = [by_id[problem_id] for problem_id in topic_problem_ids[topic]]
        # New problem IDs always come first.  If exhausted, revisit the lowest
        # best score first; a higher score never hides a weaker result.
        candidates.sort(key=lambda problem: (
            problem.id in best_scores,
            best_scores.get(problem.id, -1.0),
            str(problem.id),
        ))
        used: set[str] = set()
        is_roadmap_topic = _roadmap_step_for_topic(topic) is not None
        planned_difficulties = _practice_difficulty_plan(topic_data, per_topic_limit)
        for difficulty in planned_difficulties:
            match = next((
                problem for problem in candidates
                if problem.id not in used
                and problem.id not in best_scores
                and problem.difficulty == difficulty
            ), None)
            if match is None:
                continue
            used.add(match.id)
            recommendations.append({
                "id": match.id,
                "title": match.title,
                "difficulty": match.difficulty,
                "category": match.category,
                "topic_tags": normalize_topics(getattr(match, "topic_tags", None), getattr(match, "category", None)),
                "topic": topic,
                "reason": (
                    f"{difficulty} practice for {topic}, ordered from your {topic_data['average_score'] if topic_data['average_score'] is not None else 'new'}% topic average."
                    if is_roadmap_topic
                    else f"{difficulty} practice for {topic}, selected from your {topic_data['average_score'] if topic_data['average_score'] is not None else 'new'}% topic evidence."
                ),
            })
        # Never replace a requested Easy/Medium/Hard slot with a harder
        # difficulty. A missing matching item is a catalogue gap, not a reason
        # to push a new learner to Medium or Hard practice.

    return {
        "topics": topic_rows,
        "priority_topics": [item["topic"] for item in priority_topics],
        "problems": recommendations,
        "best_scores": best_scores,
    }
