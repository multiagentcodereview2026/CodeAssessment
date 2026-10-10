"""Build deterministic 200+ Stage 10 synthetic holdout fixtures."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


LANGUAGES = ("python", "cpp", "c", "java", "javascript")
PATTERNS = (
    ("constant", "O(1)", "O(1)"),
    ("linear", "O(n)", "O(1)"),
    ("nested", "O(n^2)", "O(1)"),
    ("dynamic", "O(n)", "O(n)"),
)


def _source(language: str, pattern: str, variant: int, adversarial: bool) -> str:
    name = f"solve_{pattern}_{variant}"
    if language == "python":
        if pattern == "constant": return f"def {name}(x):\n    return x + {variant}\n"
        if pattern == "linear": return f"def {name}(values):\n    total = 0\n    for value in values:\n        total += value + {variant}\n    return total\n"
        if pattern == "nested": return f"def {name}(values):\n    total = 0\n    for left in values:\n        for right in values:\n            total += left - right + {variant}\n    return total\n"
        return f"def {name}(values):\n    result = []\n    for value in values:\n        result.append(value + {variant})\n    return result\n"
    if language in {"cpp", "c"}:
        typ = "int"
        if pattern == "constant": return f"{typ} {name}({typ} x){{return x+{variant};}}"
        if pattern == "linear": return f"{typ} {name}({typ}* a,{typ} n){{{typ} s=0;for({typ} i=0;i<n;i++)s+=a[i]+{variant};return s;}}"
        if pattern == "nested": return f"{typ} {name}({typ}* a,{typ} n){{{typ} s=0;for({typ} i=0;i<n;i++)for({typ} j=0;j<n;j++)s+=a[i]-a[j]+{variant};return s;}}"
        return f"void {name}({typ}* a,{typ} n){{vector<{typ}> out;for({typ} i=0;i<n;i++)out.push_back(a[i]+{variant});}}"
    if language == "java":
        if pattern == "constant": return f"class Solution{{int {name}(int x){{return x+{variant};}}}}"
        if pattern == "linear": return f"class Solution{{int {name}(int[] a){{int s=0;for(int i=0;i<a.length;i++)s+=a[i]+{variant};return s;}}}}"
        if pattern == "nested": return f"class Solution{{int {name}(int[] a){{int s=0;for(int i=0;i<a.length;i++)for(int j=0;j<a.length;j++)s+=a[i]-a[j]+{variant};return s;}}}}"
        return f"class Solution{{int[] {name}(int[] a){{int[] out=new int[a.length];for(int i=0;i<a.length;i++)out[i]=a[i]+{variant};return out;}}}}"
    if pattern == "constant": return f"function {name}(x){{return x+{variant};}}"
    if pattern == "linear": return f"function {name}(a){{let s=0;for(let i=0;i<a.length;i++)s+=a[i]+{variant};return s;}}"
    if pattern == "nested": return f"function {name}(a){{let s=0;for(let i=0;i<a.length;i++)for(let j=0;j<a.length;j++)s+=a[i]-a[j]+{variant};return s;}}"
    return f"function {name}(a){{const out=[];for(let i=0;i<a.length;i++)out.push(a[i]+{variant});return out;}}"


def build(output_dir: str, per_language: int = 80) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    records = {"unseen": [], "adversarial": []}
    for language in LANGUAGES:
        for index in range(per_language):
            pattern, time, space = PATTERNS[index % len(PATTERNS)]
            target = "unseen" if index < per_language // 2 else "adversarial"
            row = {
                "problem_id": f"v3-stage10-{target}-{language}-{index:03d}",
                "title": f"Stage 10 synthetic {pattern} {language} {index}",
                "language": language,
                "reference_source": _source(language, pattern, index + 1, target == "adversarial"),
                "target_time_complexity": time,
                "target_space_complexity": space,
                "label_source": "synthetic_fixture",
            }
            records[target].append(row)
    for name, rows in records.items():
        (out / f"v3-stage10-{name}-200.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
        )
    return {name: len(rows) for name, rows in records.items()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output_dir), indent=2))
