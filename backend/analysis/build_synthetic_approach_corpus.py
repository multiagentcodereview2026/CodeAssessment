"""Build a controlled five-language, three-approach AST benchmark.

The problem IDs/titles come from the real problem bank, but the snippets are
synthetic structural fixtures.  They are intentionally marked as such and
must never be reported as human-reviewed production accuracy.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


LANGUAGES = ("python", "cpp", "c", "java", "javascript")
APPROACHES = ("brute", "better", "optimal")


def _sources(language: str, approach: str) -> tuple[str, str]:
    if language == "python":
        if approach == "brute":
            return ("""def solve(values):
    total = 0
    n = len(values)
    for i in range(n):
        for j in range(n):
            for k in range(n):
                total += values[i] + values[j] + values[k]
    return total
""", "O(n^3)", "O(1)")
        if approach == "better":
            return ("""def solve(values):
    total = 0
    n = len(values)
    for i in range(n):
        for j in range(n):
            total += values[i] + values[j]
    return total
""", "O(n^2)", "O(1)")
        return ("""def solve(values):
    total = 0
    for value in values:
        total += value
    return total
""", "O(n)", "O(1)")

    if language == "cpp":
        loops = {
            "brute": ("for (int i = 0; i < n; ++i) for (int j = 0; j < n; ++j) for (int k = 0; k < n; ++k) total += values[i] + values[j] + values[k];", "O(n^3)"),
            "better": ("for (int i = 0; i < n; ++i) for (int j = 0; j < n; ++j) total += values[i] + values[j];", "O(n^2)"),
            "optimal": ("for (int value : values) total += value;", "O(n)"),
        }
        body, time = loops[approach]
        return (f"""#include <vector>
int solve(const std::vector<int>& values) {{
    int total = 0;
    int n = static_cast<int>(values.size());
    {body}
    return total;
}}
""", time, "O(1)")

    if language == "c":
        loops = {
            "brute": ("for (int i = 0; i < n; ++i) for (int j = 0; j < n; ++j) for (int k = 0; k < n; ++k) total += values[i] + values[j] + values[k];", "O(n^3)"),
            "better": ("for (int i = 0; i < n; ++i) for (int j = 0; j < n; ++j) total += values[i] + values[j];", "O(n^2)"),
            "optimal": ("for (int i = 0; i < n; ++i) total += values[i];", "O(n)"),
        }
        body, time = loops[approach]
        return (f"""int solve(const int* values, int n) {{
    int total = 0;
    {body}
    return total;
}}
""", time, "O(1)")

    if language == "java":
        loops = {
            "brute": ("for (int i = 0; i < n; i++) for (int j = 0; j < n; j++) for (int k = 0; k < n; k++) total += values[i] + values[j] + values[k];", "O(n^3)"),
            "better": ("for (int i = 0; i < n; i++) for (int j = 0; j < n; j++) total += values[i] + values[j];", "O(n^2)"),
            "optimal": ("for (int value : values) total += value;", "O(n)"),
        }
        body, time = loops[approach]
        return (f"""class Solution {{
    int solve(int[] values) {{
        int total = 0;
        int n = values.length;
        {body}
        return total;
    }}
}}
""", time, "O(1)")

    loops = {
        "brute": ("for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) for (let k = 0; k < n; k++) total += values[i] + values[j] + values[k];", "O(n^3)"),
        "better": ("for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) total += values[i] + values[j];", "O(n^2)"),
        "optimal": ("for (const value of values) total += value;", "O(n)"),
    }
    body, time = loops[approach]
    return (f"""function solve(values) {{
    let total = 0;
    const n = values.length;
    {body}
    return total;
}}
""", time, "O(1)")


def build(bank: Path, output: Path, limit: int = 100) -> dict[str, Any]:
    rows = [json.loads(line) for line in bank.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    selected = []
    seen = set()
    for row in rows:
        problem_id = str(row.get("problem_id") or "").strip()
        if problem_id and problem_id not in seen:
            selected.append(row)
            seen.add(problem_id)
        if len(selected) == limit:
            break
    if len(selected) < limit:
        raise ValueError(f"Problem bank contains only {len(selected)} unique IDs; need {limit}.")

    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output.open("w", encoding="utf-8", newline="\n") as stream:
        for row in selected:
            for language in LANGUAGES:
                for approach in APPROACHES:
                    source, time, space = _sources(language, approach)
                    record = {
                        "problem_id": row["problem_id"],
                        "title": row.get("title"),
                        "solution_id": f"synthetic-{row['problem_id']}-{language}-{approach}",
                        "language": language,
                        "approach": approach,
                        "source": source,
                        "snippet_time_complexity": time,
                        "snippet_space_complexity": space,
                        "ground_truth_source": "synthetic_generated",
                        "optimal_time_complexity": row.get("target_time_complexity"),
                        "optimal_space_complexity": row.get("target_space_complexity"),
                        "label_source": "synthetic_generated",
                    }
                    stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                    count += 1
    return {"problems": len(selected), "languages": len(LANGUAGES), "approaches": len(APPROACHES), "rows": count, "output": str(output)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bank", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    print(json.dumps(build(args.bank, args.output, args.limit), indent=2))


if __name__ == "__main__":
    main()
