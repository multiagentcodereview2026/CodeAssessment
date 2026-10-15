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
    grouped: dict[tuple[Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        grouped[(case.get("courseId"), case.get("assignmentId"), case.get("problemId"))].append(case)

    clusters: list[dict[str, Any]] = []
    for (course_id, assignment_id, problem_id), group_cases in grouped.items():
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
                f"{course_id}:{assignment_id}:{problem_id}:{','.join(sorted(member_ids))}".encode()
            ).hexdigest()[:12]
            clusters.append({
                "id": f"cluster-{digest}",
                "courseId": course_id,
                "courseTitle": cluster_cases[0]["courseTitle"],
                "assignmentId": assignment_id,
                "assignmentTitle": cluster_cases[0].get("assignmentTitle") or f"Assignment #{assignment_id}",
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


def build_approach_groups(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group same-problem submissions by generic AST-derived approach.

    These groups are intentionally separate from code-overlap clusters.  Two
    students independently using the same standard technique is normal and is
    never presented as a copying allegation.
    """
    grouped: dict[tuple[Any, Any, Any, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[(record.get("courseId"), record.get("assignmentId"), record.get("problemId"), record.get("approachLabel", "Unknown"))].append(record)

    groups: list[dict[str, Any]] = []
    for (course_id, assignment_id, problem_id, label), members in grouped.items():
        if len(members) < 2:
            continue
        ordered_members = sorted(
            (dict(member["student"]) for member in members),
            key=lambda member: (
                -(float(member.get("overallScore")) if member.get("overallScore") is not None else -1),
                str(member["id"]),
            ),
        )
        for rank, member in enumerate(ordered_members, start=1):
            member["rank"] = rank
        digest = hashlib.sha1(
            f"approach:{course_id}:{assignment_id}:{problem_id}:{label}:{','.join(sorted(member['id'] for member in ordered_members))}".encode()
        ).hexdigest()[:12]
        groups.append({
            "id": f"approach-{digest}",
            "courseId": course_id,
            "courseTitle": members[0]["courseTitle"],
            "assignmentId": assignment_id,
            "assignmentTitle": members[0].get("assignmentTitle") or f"Assignment #{assignment_id}",
            "problemId": problem_id,
            "problemTitle": members[0]["problemTitle"],
            "approachLabel": label,
            "approachSummary": members[0].get("approachSummary") or "",
            "members": ordered_members,
            "explanation": (
                f"{len(ordered_members)} students independently match the generic AST approach "
                f"‘{label}’ ({members[0].get('approachSummary') or 'structural evidence'}). "
                "This is informational and is not a code-overlap finding."
            ),
        })
    return sorted(groups, key=lambda group: (-len(group["members"]), group["problemTitle"], group["approachLabel"]))


def _ordered_members(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    members = sorted(
        (dict(record["student"]) for record in records),
        key=lambda member: (
            -(float(member.get("overallScore")) if member.get("overallScore") is not None else -1),
            str(member["id"]),
        ),
    )
    for rank, member in enumerate(members, start=1):
        member["rank"] = rank
    return members


def build_submission_groups(
    records: Iterable[dict[str, Any]],
    cases: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Partition every latest submission into one instructor-facing group.

    Direct normalized-token overlap has priority.  Students not connected by a
    direct-overlap edge are partitioned by generic AST structure.  A student
    with no structural peer remains visible as a one-member group.  This is a
    complete view of a problem's submissions, not a misconduct finding.
    """
    scoped_records: dict[tuple[Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        scoped_records[(record.get("courseId"), record.get("assignmentId"), record.get("problemId"))].append(record)

    scoped_cases: dict[tuple[Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        scoped_cases[(case.get("courseId"), case.get("assignmentId"), case.get("problemId"))].append(case)

    groups: list[dict[str, Any]] = []
    for scope, scope_rows in scoped_records.items():
        course_id, assignment_id, problem_id = scope
        record_by_student = {str(record["student"]["id"]): record for record in scope_rows}
        graph: dict[str, set[str]] = defaultdict(set)
        for case in scoped_cases.get(scope, []):
            left_id = str(case["studentA"]["id"])
            right_id = str(case["studentB"]["id"])
            if left_id in record_by_student and right_id in record_by_student:
                graph[left_id].add(right_id)
                graph[right_id].add(left_id)

        grouped_student_ids: set[str] = set()
        for root in sorted(graph):
            if root in grouped_student_ids:
                continue
            stack, component = [root], []
            grouped_student_ids.add(root)
            while stack:
                current = stack.pop()
                component.append(current)
                for neighbour in graph[current]:
                    if neighbour not in grouped_student_ids:
                        grouped_student_ids.add(neighbour)
                        stack.append(neighbour)

            component_set = frozenset(component)
            component_cases = [
                case for case in scoped_cases.get(scope, [])
                if str(case["studentA"]["id"]) in component_set
                and str(case["studentB"]["id"]) in component_set
            ]
            component_rows = [record_by_student[student_id] for student_id in component]
            ordered_members = _ordered_members(component_rows)
            representative_id = str(ordered_members[0]["id"])
            representative = record_by_student[representative_id]
            digest = hashlib.sha1(
                f"code:{course_id}:{assignment_id}:{problem_id}:{','.join(sorted(component_set))}".encode()
            ).hexdigest()[:12]
            groups.append({
                "id": f"submission-group-{digest}",
                "courseId": course_id,
                "courseTitle": scope_rows[0]["courseTitle"],
                "assignmentId": assignment_id,
                "assignmentTitle": scope_rows[0].get("assignmentTitle") or f"Assignment #{assignment_id}",
                "problemId": problem_id,
                "problemTitle": scope_rows[0]["problemTitle"],
                "groupKind": "code_overlap",
                "groupLabel": "Direct code overlap",
                "approachSummary": representative.get("approachSummary") or "",
                "members": ordered_members,
                "representativeCode": representative.get("sourceCode") or "",
                "pairCount": len(component_cases),
                "caseIds": [case["id"] for case in component_cases],
            })

        remaining = [record for student_id, record in record_by_student.items() if student_id not in grouped_student_ids]
        structural_buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for record in remaining:
            structural_buckets[(record.get("approachLabel", "Unknown"), record.get("approachSummary", ""))].append(record)

        for (label, summary), members in structural_buckets.items():
            ordered_members = _ordered_members(members)
            representative_id = str(ordered_members[0]["id"])
            representative = record_by_student[representative_id]
            kind = "structural" if len(ordered_members) > 1 else "individual"
            group_label = f"Same AST approach: {label}" if kind == "structural" else "Unique implementation"
            digest = hashlib.sha1(
                f"structure:{course_id}:{assignment_id}:{problem_id}:{label}:{summary}:{','.join(sorted(str(member['id']) for member in ordered_members))}".encode()
            ).hexdigest()[:12]
            groups.append({
                "id": f"submission-group-{digest}",
                "courseId": course_id,
                "courseTitle": scope_rows[0]["courseTitle"],
                "assignmentId": assignment_id,
                "assignmentTitle": scope_rows[0].get("assignmentTitle") or f"Assignment #{assignment_id}",
                "problemId": problem_id,
                "problemTitle": scope_rows[0]["problemTitle"],
                "groupKind": kind,
                "groupLabel": group_label,
                "approachSummary": summary,
                "members": ordered_members,
                "representativeCode": representative.get("sourceCode") or "",
                "pairCount": 0,
                "caseIds": [],
            })

    return sorted(groups, key=lambda group: (group["problemTitle"], -len(group["members"]), group["groupLabel"]))
