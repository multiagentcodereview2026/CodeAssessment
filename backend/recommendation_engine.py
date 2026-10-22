"""Deterministic topic progress and practice recommendation rules.

This module deliberately contains no model calls or AI calls.  A problem contributes
once to every one of its tags, using a student's best assessed score for that
problem.  Keeping the policy pure makes it straightforward to test and audit.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable


# This is a curriculum order, not an access-control list.  Students can still
# open and solve any public problem; it only determines the optional roadmap's
# next guided step. Aliases allow legacy catalogue categories to participate.
# id, title, accepted tags, prerequisites, level, core, mastery min, mastery max
# These targets are deliberately curriculum metadata, not AI estimates.
ROADMAP_STEPS = (
    ("arrays", "Arrays", ("Array", "Arrays", "Arrays & Hashing"), (), "Fundamental", 15, 40, 60),
    ("strings", "Strings", ("String", "Strings"), ("arrays",), "Fundamental", 12, 30, 45),
    ("sorting", "Sorting", ("Sorting",), ("strings",), "Fundamental", 10, 25, 40),
    ("two-pointers", "Two Pointers", ("Two Pointers",), ("sorting",), "Fundamental", 10, 25, 40),
    ("stack", "Stack", ("Stack", "Stack / Queue"), ("two-pointers",), "Fundamental", 10, 25, 35),
    ("linked-list", "Linked List", ("Linked List", "Linked Lists"), ("stack",), "Fundamental", 10, 25, 35),
    ("matrix", "Matrix", ("Matrix", "Geometry"), ("linked-list",), "Fundamental", 8, 20, 30),
    ("simulation", "Simulation", ("Simulation", "Enumeration"), ("matrix",), "Fundamental", 8, 15, 25),
    ("hash-table", "Hash Table", ("Hash Table", "Arrays & Hashing"), ("simulation",), "Intermediate", 12, 30, 45),
    ("math", "Math", ("Math",), ("hash-table",), "Intermediate", 10, 25, 40),
    ("binary-search", "Binary Search", ("Binary Search", "Searching"), ("math",), "Intermediate", 12, 30, 40),
    ("dfs", "DFS", ("Depth-First Search", "DFS"), ("binary-search",), "Intermediate", 12, 30, 40),
    ("bfs", "BFS", ("Breadth-First Search", "BFS"), ("dfs",), "Intermediate", 10, 25, 35),
    ("trees", "Trees", ("Tree", "Trees"), ("bfs",), "Intermediate", 10, 25, 35),
    ("binary-tree", "Binary Tree", ("Binary Tree",), ("trees",), "Intermediate", 10, 25, 35),
    ("binary-search-tree", "Binary Search Tree", ("Binary Search Tree",), ("binary-tree",), "Intermediate", 8, 20, 30),
    ("greedy", "Greedy", ("Greedy",), ("binary-search-tree",), "Intermediate", 10, 25, 35),
    ("backtracking", "Backtracking", ("Backtracking", "Recursion"), ("greedy",), "Advanced", 8, 20, 30),
    ("dynamic-programming", "Dynamic Programming", ("Dynamic Programming", "Memoization"), ("backtracking",), "Advanced", 15, 40, 60),
    ("divide-conquer", "Divide and Conquer", ("Divide and Conquer",), ("dynamic-programming",), "Advanced", 6, 15, 25),
    ("union-find", "Union-Find", ("Union Find", "Union-Find"), ("divide-conquer",), "Advanced", 6, 15, 25),
    ("monotonic-stack", "Monotonic Stack", ("Monotonic Stack",), ("union-find",), "Advanced", 6, 15, 25),
    ("topological-sort", "Topological Sort", ("Topological Sort",), ("monotonic-stack",), "Advanced", 6, 15, 25),
    ("quickselect", "Quickselect", ("Quickselect",), ("topological-sort",), "Advanced", 5, 10, 15),
    ("bitmask", "Bitmask", ("Bit Manipulation", "Bitmask"), ("quickselect",), "Advanced", 5, 15, 25),
)

ROADMAP_CORE_AVERAGE = 90.0
ROADMAP_MASTERY_AVERAGE = 97.0
ROADMAP_OVERALL_MILESTONES = (
    ("Starter", 30), ("Fundamentals complete", 160), ("Intermediate complete", 340),
    ("Advanced core complete", 500), ("Mastery library", 600),
)


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


def difficulty_plan(average_score: float | None, limit: int = 6) -> list[str]:
    """Create the published, deterministic difficulty mix for a topic."""
    score = 0.0 if average_score is None else average_score
    if score < 60:
        return ["Easy"] * limit
    if score < 75:
        return ["Easy"] * ((limit * 2 + 2) // 3) + ["Medium"] * (limit // 3)
    if score <= 95:
        return ["Medium"] * ((limit * 2 + 2) // 3) + ["Hard"] * (limit // 3)
    return ["Hard"] * limit


def _roadmap_step_for_topic(topic: str) -> tuple[str, str] | None:
    """Return the curriculum level for an exact public problem-bank tag."""
    normalized = topic.casefold()
    for _step_id, _title, aliases, _prerequisites, level, *_targets in ROADMAP_STEPS:
        if normalized in {alias.casefold() for alias in aliases}:
            return _step_id, level
    return None


def _practice_difficulty_plan(topic_data: dict[str, Any], limit: int) -> list[str]:
    """Choose a topic's next level from evidence, never average alone.

    A perfect score on a single Easy problem therefore remains an Easy
    recommendation until the student demonstrates the curriculum's required
    Easy coverage. This applies even when the learner has not opted into the
    visible roadmap page.
    """
    roadmap_step = _roadmap_step_for_topic(topic_data["topic"])
    completed_by_difficulty = topic_data["completed_by_difficulty"]
    average = topic_data["average_score"]
    if roadmap_step:
        _step_id, level = roadmap_step
        requirements = CORE_DIFFICULTY_MIX[level]
        if completed_by_difficulty["Easy"] < requirements["Easy"]:
            return ["Easy"] * limit
        if average is None or average < ROADMAP_CORE_AVERAGE:
            return ["Easy"] * limit
        if completed_by_difficulty["Medium"] < requirements["Medium"]:
            return ["Medium"] * limit
        if completed_by_difficulty["Hard"] < requirements["Hard"]:
            return ["Hard"] * limit
    # Tags outside the roadmap still require enough evidence before Hard work.
    if topic_data["assessed_problems"] < 3:
        return ["Easy"] * limit
    return difficulty_plan(average, limit)


def build_recommendations(
    problems: Iterable[Any],
    submissions: Iterable[Any],
    *,
    per_topic_limit: int = 6,
    topic_limit: int = 3,
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
            match = next((problem for problem in candidates if problem.id not in used and problem.difficulty == difficulty), None)
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
                    f"Build {difficulty} coverage for {topic} before advancing difficulty."
                    if is_roadmap_topic
                    else f"{difficulty} practice for {topic}, selected from your {topic_data['average_score'] if topic_data['average_score'] is not None else 'new'}% topic evidence."
                ),
            })

    return {
        "topics": topic_rows,
        "priority_topics": [item["topic"] for item in priority_topics],
        "problems": recommendations,
        "best_scores": best_scores,
    }


CORE_DIFFICULTY_MIX = {
    "Fundamental": {"Easy": 12, "Medium": 10, "Hard": 5},
    "Intermediate": {"Easy": 10, "Medium": 10, "Hard": 5},
    "Advanced": {"Easy": 8, "Medium": 6, "Hard": 4},
}


def _coverage_requirements(level: str, total: int, *, mastery: bool) -> dict[str, int]:
    """Require a meaningful difficulty spread; no topic can be Easy-only."""
    if not mastery:
        return dict(CORE_DIFFICULTY_MIX[level])
    return {
        "Easy": max(6, round(total * 0.25)),
        "Medium": max(8, round(total * 0.45)),
        "Hard": max(4, round(total * 0.20)),
    }


def _roadmap_difficulty(
    completed: int,
    average_score: float | None,
    completed_by_difficulty: dict[str, int],
    core_requirements: dict[str, int],
) -> str:
    """Choose the next level, filling a balanced core before advancing."""
    if completed_by_difficulty.get("Easy", 0) < core_requirements["Easy"]:
        return "Easy"
    if completed_by_difficulty.get("Medium", 0) < core_requirements["Medium"]:
        return "Medium"
    if average_score < ROADMAP_CORE_AVERAGE:
        return "Easy" if average_score < 75 else "Medium"
    if completed_by_difficulty.get("Hard", 0) < core_requirements["Hard"]:
        return "Hard"
    if completed < 20:
        return "Medium"
    return "Hard"


def build_roadmap(problems: Iterable[Any], submissions: Iterable[Any]) -> dict[str, Any]:
    """Return the optional curriculum state and one deterministic next problem.

    The caller scopes inputs to evaluated independent-practice submissions and
    public problems.  Scores are never persisted here: the best score is
    recalculated from the official submission history on each request.
    """
    ordered_problems = sorted(problems, key=lambda problem: str(problem.id))
    known_problem_ids = {problem.id for problem in ordered_problems}
    best_scores: dict[str, float] = {}
    for submission in submissions:
        problem_id = getattr(submission, "problem_id", None)
        score = getattr(submission, "overall_score", None)
        if problem_id not in known_problem_ids or score is None:
            continue
        best_scores[problem_id] = max(best_scores.get(problem_id, float("-inf")), float(score))

    raw_steps: list[dict[str, Any]] = []
    for step_id, title, aliases, prerequisites, level, configured_core, configured_mastery_min, mastery_max in ROADMAP_STEPS:
        accepted_tags = {tag.casefold() for tag in aliases}
        topic_problems = [
            problem for problem in ordered_problems
            if any(tag.casefold() in accepted_tags for tag in normalize_topics(
                getattr(problem, "topic_tags", None), getattr(problem, "category", None)
            ))
        ]
        scores = [best_scores[problem.id] for problem in topic_problems if problem.id in best_scores]
        completed = len(scores)
        average = round(sum(scores) / completed, 1) if completed else None
        completed_by_difficulty = {
            difficulty: sum(1 for problem in topic_problems if problem.id in best_scores and problem.difficulty == difficulty)
            for difficulty in ("Easy", "Medium", "Hard")
        }
        # Every roadmap algorithm now has a 20-problem minimum core. Existing
        # per-topic targets remain useful as a lower bound for mastery only.
        core_requirements = _coverage_requirements(level, configured_core, mastery=False)
        core_required = max(configured_core, sum(core_requirements.values()))
        mastery_min = max(core_required, configured_mastery_min)
        mastery_max = max(mastery_min, mastery_max)
        mastery_requirements = _coverage_requirements(level, mastery_min, mastery=True)
        core_coverage_met = all(completed_by_difficulty[level] >= count for level, count in core_requirements.items())
        mastery_coverage_met = all(completed_by_difficulty[level] >= count for level, count in mastery_requirements.items())
        raw_steps.append({
            "id": step_id,
            "title": title,
            "aliases": aliases,
            "prerequisites": prerequisites,
            "level": level,
            "problems": topic_problems,
            "catalogue_problems": len(topic_problems),
            "completed_problems": completed,
            "average_score": average,
            "core_required": core_required,
            "mastery_min": mastery_min,
            "mastery_max": mastery_max,
            "completed_by_difficulty": completed_by_difficulty,
            "core_difficulty_requirements": core_requirements,
            "mastery_difficulty_requirements": mastery_requirements,
            "core_complete": completed >= core_required and average is not None and average >= ROADMAP_CORE_AVERAGE and core_coverage_met,
            "mastered": completed >= mastery_min and average is not None and average >= ROADMAP_MASTERY_AVERAGE and mastery_coverage_met,
        })

    by_id = {step["id"]: step for step in raw_steps}
    current_id: str | None = None
    for step in raw_steps:
        unlocked = all(by_id[dependency]["core_complete"] for dependency in step["prerequisites"])
        step["unlocked"] = unlocked
        if unlocked and not step["core_complete"] and current_id is None:
            current_id = step["id"]

    # Once every core milestone is completed, keep the final topic as the
    # current refinement target instead of making the roadmap appear empty.
    if current_id is None and raw_steps:
        current_id = raw_steps[-1]["id"]

    next_problem = None
    if current_id is not None:
        current = by_id[current_id]
        desired_difficulty = _roadmap_difficulty(
            current["completed_problems"],
            current["average_score"],
            current["completed_by_difficulty"],
            current["core_difficulty_requirements"],
        )
        rank = {"Easy": 0, "Medium": 1, "Hard": 2}
        candidates = sorted(current["problems"], key=lambda problem: (
            problem.id in best_scores,
            best_scores.get(problem.id, -1.0),
            str(problem.id),
        ))
        exact = [problem for problem in candidates if problem.difficulty == desired_difficulty]
        # Never silently substitute a different difficulty. A missing exact
        # item is a curation gap, not a reason to give the student the wrong
        # roadmap exercise.
        selected = (exact or [None])[0]
        if selected is not None:
            next_problem = {
                "id": selected.id,
                "title": selected.title,
                "difficulty": selected.difficulty,
                "category": selected.category,
                "topic": current["title"],
                "reason": f"Next {current['title']} roadmap problem at {desired_difficulty} level.",
            }

    steps = []
    for step in raw_steps:
        if not step["unlocked"]:
            status = "LOCKED"
        elif step["mastered"]:
            status = "MASTERED"
        elif step["core_complete"]:
            status = "CORE_COMPLETE"
        elif step["id"] == current_id:
            status = "CURRENT"
        else:
            status = "AVAILABLE"
        steps.append({
            "id": step["id"], "title": step["title"], "level": step["level"], "status": status,
            "unlocked": step["unlocked"], "catalogue_problems": step["catalogue_problems"],
            "completed_problems": step["completed_problems"], "average_score": step["average_score"],
            "core_complete": step["core_complete"], "mastered": step["mastered"],
            "core_required_problems": step["core_required"],
            "core_required_average": ROADMAP_CORE_AVERAGE,
            "completed_by_difficulty": step["completed_by_difficulty"],
            "core_difficulty_requirements": step["core_difficulty_requirements"],
            "mastery_min_problems": step["mastery_min"],
            "mastery_max_problems": step["mastery_max"],
            "mastery_required_average": ROADMAP_MASTERY_AVERAGE,
            "mastery_difficulty_requirements": step["mastery_difficulty_requirements"],
            "prerequisites": list(step["prerequisites"]),
        })

    total_completed = len(best_scores)
    next_requirement = None
    if current_id is not None and next_problem is None:
        current = by_id[current_id]
        next_requirement = {
            "topic": current["title"],
            "difficulty": _roadmap_difficulty(
                current["completed_problems"], current["average_score"],
                current["completed_by_difficulty"], current["core_difficulty_requirements"],
            ),
        }
    return {
        "steps": steps,
        "current_step_id": current_id,
        "next_problem": next_problem,
        "next_requirement": next_requirement,
        "total_completed_problems": total_completed,
        "overall_milestones": [
            {"name": name, "target": target, "completed": total_completed >= target}
            for name, target in ROADMAP_OVERALL_MILESTONES
        ],
    }
