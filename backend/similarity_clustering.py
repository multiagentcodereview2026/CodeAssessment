"""Build instructor review clusters from same-problem similarity candidates."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Any, Iterable


def build_similarity_clusters(cases: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return connected student groups without exposing a similarity score.

    Each case is an edge between two students for one course/problem. Connected
    edges become one review cluster, so A↔B and B↔C produces A/B/C rather than
    three unrelated alerts.
    """
    grouped: dict[tuple[Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        grouped[(case.get("courseId"), case.get("problemId"))].append(case)

    clusters: list[dict[str, Any]] = []
    for (course_id, problem_id), group_cases in grouped.items():
        graph: dict[str, set[str]] = defaultdict(set)
        students: dict[str, dict[str, Any]] = {}
        for case in group_cases:
            left = case["studentA"]
            right = case["studentB"]
            left_id, right_id = str(left["id"]), str(right["id"])
            graph[left_id].add(right_id)
            graph[right_id].add(left_id)
            students[left_id] = left
            students[right_id] = right

        visited: set[str] = set()
        for root in sorted(graph):
            if root in visited:
                continue
            stack, member_ids = [root], []
            visited.add(root)
            while stack:
                current = stack.pop()
                member_ids.append(current)
                for neighbour in graph[current]:
                    if neighbour not in visited:
                        visited.add(neighbour)
                        stack.append(neighbour)

            member_set = set(member_ids)
            cluster_cases = [
                case for case in group_cases
                if str(case["studentA"]["id"]) in member_set
                and str(case["studentB"]["id"]) in member_set
            ]
            # Ranking is presentation-only: it helps the instructor identify
            # each student's evaluated submission inside a review group. It is
            # not a similarity score and does not affect a student grade.
            ordered_members = sorted(
                (dict(students[student_id]) for student_id in member_ids),
                key=lambda member: (
                    -(float(member.get("overallScore")) if member.get("overallScore") is not None else -1),
                    str(member["id"]),
                ),
            )
            for rank, member in enumerate(ordered_members, start=1):
                member["rank"] = rank
            digest = hashlib.sha1(
                f"{course_id}:{problem_id}:{','.join(sorted(member_ids))}".encode()
            ).hexdigest()[:12]
            clusters.append({
                "id": f"cluster-{digest}",
                "courseId": course_id,
                "courseTitle": cluster_cases[0]["courseTitle"],
                "problemId": problem_id,
                "problemTitle": cluster_cases[0]["problemTitle"],
                "members": ordered_members,
                "pairCount": len(cluster_cases),
                "reviewStatus": "review_requested" if any(
                    case.get("reviewStatus") == "review_requested" for case in cluster_cases
                ) else "open",
                "caseIds": [case["id"] for case in cluster_cases],
            })
    return sorted(clusters, key=lambda cluster: (-len(cluster["members"]), cluster["problemTitle"]))
