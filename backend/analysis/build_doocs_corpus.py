"""Extract a genuine AST benchmark from a separate Doocs checkout.

Only source files with a matching README complexity statement are emitted.
This produces canonical/reference rows; it does not invent missing approaches.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from .complexity_normalizer import normalize_complexity


EXTENSIONS = {".py": "python", ".cpp": "cpp", ".c": "c", ".java": "java", ".js": "javascript"}


def _complexity_after(text: str, start: int) -> str | None:
    match = re.search(r"O\s*\(", text[start:], re.IGNORECASE)
    if not match:
        return None
    begin = start + match.start()
    depth = 0
    for index in range(begin + 1, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                raw = text[begin:index + 1]
                normalized = normalize_complexity(raw)
                if normalized:
                    return normalized
                # README prose sometimes uses LaTeX notation such as
                # O(\max (m, n)); retain it in a canonical plain-text form.
                inner = raw[2:-1].replace("\\max", "max").replace("\\log", "log")
                inner = re.sub(r"\s+", "", inner)
                return f"O({inner})"
    return None


def _read_complexities(readme: str) -> tuple[str | None, str | None]:
    # A README commonly mentions complexities while explaining alternatives,
    # then states the selected solution's complexity at the end.  Use the
    # final explicit statement rather than the first explanatory occurrence.
    # Match an explicit complexity declaration, not arbitrary prose that
    # happens to contain the word ``time`` or ``space``.  README explanations
    # often include a later sentence such as ``time. Ignoring ...``; treating
    # that as the label silently changes the ground truth to an unrelated
    # O(1) expression.
    time_matches = list(re.finditer(
        r"(?:time|temporal|时间)\s*(?:complexity|complexity：|复杂度)",
        readme,
        re.IGNORECASE,
    ))
    space_matches = list(re.finditer(
        r"(?:space|memory|空间)\s*(?:complexity|complexity：|复杂度)",
        readme,
        re.IGNORECASE,
    ))
    time = _complexity_after(readme, time_matches[-1].start()) if time_matches else None
    space = _complexity_after(readme, space_matches[-1].start()) if space_matches else None
    return time, space


def build(root: Path, output: Path, limit: int | None = None) -> dict[str, Any]:
    # Doocs stores problems exactly two levels below solution/: range/problem.
    # Avoid a full recursive walk of the large checkout.
    problem_dirs = sorted(
        path
        for bucket in (root / "solution").iterdir()
        if bucket.is_dir()
        for path in bucket.iterdir()
        if path.is_dir() and re.match(r"^\d{4}\.", path.name)
    )
    if limit is not None:
        problem_dirs = problem_dirs[:limit]

    records: list[dict[str, Any]] = []
    skipped = {"missing_readme": 0, "missing_complexity": 0, "missing_source": 0}
    for problem_dir in problem_dirs:
        problem_match = re.match(r"^(\d+)[. ](.*)$", problem_dir.name)
        if not problem_match:
            continue
        problem_id = f"leetcode-{int(problem_match.group(1))}"
        title = problem_match.group(2)
        readme_path = problem_dir / "README_EN.md"
        if not readme_path.is_file():
            skipped["missing_readme"] += 1
            continue
        time, space = _read_complexities(readme_path.read_text(encoding="utf-8", errors="ignore"))
        if not time or not space:
            skipped["missing_complexity"] += 1
            continue
        for source_path in sorted(problem_dir.iterdir()):
            language = EXTENSIONS.get(source_path.suffix.lower())
            if not language or not source_path.is_file():
                continue
            source = source_path.read_text(encoding="utf-8", errors="ignore").strip()
            if not source:
                skipped["missing_source"] += 1
                continue
            relative_source_path = str(source_path.relative_to(root)).replace("\\", "/")
            source_key = re.sub(r"[^a-zA-Z0-9]+", "-", relative_source_path).strip("-").lower()
            records.append({
                "problem_id": problem_id,
                "title": title,
                "solution_id": f"doocs-{problem_id}-{language}-{source_key}",
                "language": language,
                "approach": "canonical",
                "source": source,
                "snippet_time_complexity": time,
                "snippet_space_complexity": space,
                "ground_truth_source": "doocs_readme",
                "source_repository": "https://github.com/doocs/leetcode",
                "source_path": relative_source_path,
            })

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {"problem_dirs": len(problem_dirs), "records": len(records), "languages": sorted({r["language"] for r in records}), "skipped": skipped, "output": str(output)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    print(json.dumps(build(args.root, args.output, args.limit), indent=2))


if __name__ == "__main__":
    main()
