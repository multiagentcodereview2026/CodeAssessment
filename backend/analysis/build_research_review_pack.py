"""Create an unlabeled original synthetic pilot for two independent reviewers.

No analyzer is called and no ground truth is inferred. This is a pilot review
pack, not a representative or held-out real-student research benchmark.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

PYTHON = [
    "def solve(a):\n    total = 0\n    for value in a:\n        total += value\n    return total\n",
    "def solve(a):\n    total = 0\n    for i in range(len(a)):\n        total = 0\n        for value in a:\n            total += value\n    return total\n",
    "def solve(a, target):\n    for i, value in enumerate(a):\n        if value == target:\n            return i\n    return -1\n",
    "def solve(a, target):\n    left, right = 0, len(a) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if a[mid] == target:\n            return mid\n        if a[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1\n",
]
CPP = [
    "long long solve(const std::vector<int>& a) { long long total=0; for(int value:a) total+=value; return total; }",
    "long long solve(const std::vector<int>& a) { long long total=0; for(int i=0;i<(int)a.size();++i) { total=0; for(int value:a) total+=value; } return total; }",
    "int solve(const std::vector<int>& a,int target) { for(int i=0;i<(int)a.size();++i) if(a[i]==target) return i; return -1; }",
    "int solve(const std::vector<int>& a,int target) { int left=0,right=(int)a.size()-1; while(left<=right) { int mid=left+(right-left)/2; if(a[mid]==target)return mid; if(a[mid]<target)left=mid+1;else right=mid-1; } return -1; }",
]
C = [
    "long long solve(const int *a,int n) { long long total=0; for(int i=0;i<n;++i)total+=a[i];return total; }",
    "long long solve(const int *a,int n) { long long total=0; for(int i=0;i<n;++i){total=0;for(int j=0;j<n;++j)total+=a[j];}return total; }",
    "int solve(const int *a,int n,int target) { for(int i=0;i<n;++i)if(a[i]==target)return i;return -1; }",
    "int solve(const int *a,int n,int target) { int left=0,right=n-1;while(left<=right){int mid=left+(right-left)/2;if(a[mid]==target)return mid;if(a[mid]<target)left=mid+1;else right=mid-1;}return -1; }",
]
JAVA = [
    "static long solve(int[] a) { long total=0;for(int value:a)total+=value;return total; }",
    "static long solve(int[] a) { long total=0;for(int i=0;i<a.length;++i){total=0;for(int value:a)total+=value;}return total; }",
    "static int solve(int[] a,int target) { for(int i=0;i<a.length;++i)if(a[i]==target)return i;return -1; }",
    "static int solve(int[] a,int target) { int left=0,right=a.length-1;while(left<=right){int mid=left+(right-left)/2;if(a[mid]==target)return mid;if(a[mid]<target)left=mid+1;else right=mid-1;}return -1; }",
]
JS = [
    "function solve(a){let total=0;for(const value of a)total+=value;return total;}",
    "function solve(a){let total=0;for(let i=0;i<a.length;i++){total=0;for(const value of a)total+=value;}return total;}",
    "function solve(a,target){for(let i=0;i<a.length;i++)if(a[i]===target)return i;return -1;}",
    "function solve(a,target){let left=0,right=a.length-1;while(left<=right){const mid=left+Math.floor((right-left)/2);if(a[mid]===target)return mid;if(a[mid]<target)left=mid+1;else right=mid-1;}return -1;}",
]


def samples():
    rows = []
    for language, sources in {"python": PYTHON, "cpp": CPP, "c": C, "java": JAVA, "javascript": JS}.items():
        for variant, source in enumerate(sources, 1):
            if language == "cpp":
                source = "#include <vector>\n" + source + "\n"
            if language == "java":
                source = "class Candidate {\n" + source + "\n}\n"
            problem = "pilot-sum" if variant <= 2 else "pilot-search"
            statement = "Return the sum of integer array a; an empty array sums to zero." if variant <= 2 else "For a sorted ascending integer array a, return any index holding target, or -1 when target is absent."
            rows.append({"problem_id": problem, "solution_id": f"{language}-S{variant:02}", "approach": f"variant-{variant}", "language": language,
                "statement": statement, "constraints": "0 <= n <= 1000; each value and target is an integer between -1000000 and 1000000. Analyze growth with n as variable, not as a constant due to the finite bound.",
                "source": source, "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                "provenance": "Original AI-assisted synthetic pilot fixture, authored for this repository; not real student code or independently reviewed ground truth.",
                "snippet_time_complexity": None, "snippet_space_complexity": None, "ground_truth_source": None,
                "reviewer_id": None, "review_date": None, "rationale": None, "overall_instructor_grade": None,
                "correctness": None, "time": None, "space": None, "style": None})
    return rows


def build(output: Path):
    rows = samples()
    output.mkdir(parents=True, exist_ok=False)
    payload = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    for name in ("reviewer-A.jsonl", "reviewer-B.jsonl", "adjudication-template.jsonl"):
        (output / name).write_text(payload, encoding="utf-8")
    readable = "# Independent code review\n\nReviewer ID: ______  Date: ______\n\nRecord worst-case time and auxiliary space (excluding input; including stack). n is array length. Do not view another review or analyzer output before locking your answers.\n\n"
    for row in rows:
        readable += f"## {row['solution_id']}\n\n{row['statement']}\n\n{row['constraints']}\n\n```{row['language']}\n{row['source']}\n```\n\nSource SHA-256: {row['source_sha256']}\n\nTime: ______\n\nAuxiliary space: ______\n\nReasoning and assumptions: ______\n\nIndependent overall grade (if justified): ______\n\nCorrectness evidence (if executed): ______\n\n"
    for name in ("reviewer-A.md", "reviewer-B.md"):
        (output / name).write_text(readable, encoding="utf-8")
    manifest = {"kind": "unlabeled_synthetic_pilot", "rows": len(rows), "problem_groups": 2, "languages": 5,
                "labels_status": "pending_independent_review", "payload_sha256": hashlib.sha256(payload.encode()).hexdigest(),
                "generalization_accuracy_claim_allowed": False}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (output / "START_HERE.md").write_text(
        "# Independent review pilot\n\nGive reviewer-A.md and reviewer-B.md to two people separately (or their matching JSONL forms if preferred). Keep analyzer outputs hidden until both reviews are locked. Do not share completed answers between reviewers. Transfer signed-off answers to the adjudication JSONL for analysis.\n\n"
        "Analyze the exact function body. n is array length. Report worst-case time and auxiliary space (including stack, excluding the supplied input). Fill reviewer_id, review_date, rationale, and the two snippet labels. Grade the solution independently before viewing the platform's weights; leave unsupported fields blank. Optional correctness grades require independent execution evidence.\n\n"
        "This pack has 20 AI-assisted synthetic snippets from only two problem groups. It is a convenience pilot, not a representative holdout or independent real-student accuracy dataset. Do not invent extra records or treat translated variants as independent problems.\n\n"
        "After both reviews, resolve disagreements manually in adjudication-template.jsonl. Preserve both original files. Only after real agreement/adjudication set ground_truth_source to human_reviewed and keep a record of both reviewers and the adjudicator's reasons. Blank files must fail corpus validation.\n\n"
        "Validate the completed pilot with analysis.validate_approach_corpus --dataset <adjudicated-file> --minimum 20 --require-reviewed, then run analysis.benchmark_ai_ast. Report the sample size, synthetic provenance and limited problem diversity beside results. A larger licensed code corpus is still needed for generalization claims.\n\n"
        "For overall-grade and feedback review, use docs/RESEARCH_REVIEW_FORM.md in the repository. Never expose private learner data or hidden judge cases in a public report.\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    print(json.dumps(build(parser.parse_args().output_dir), indent=2))
