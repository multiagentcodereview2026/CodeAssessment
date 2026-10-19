import json

from analysis.benchmark_approach_corpus import run


def test_review_exclusions_change_only_the_benchmark_denominator(tmp_path):
    dataset = tmp_path / "samples.jsonl"
    dataset.write_text(
        "\n".join(
            [
                json.dumps({
                    "problem_id": "sample-1",
                    "solution_id": "sample-correct",
                    "language": "c",
                    "source": "int scan(int* values, int size) { int total = 0; for (int i = 0; i < size; ++i) total += values[i]; return total; }",
                    "snippet_time_complexity": "O(n)",
                    "snippet_space_complexity": "O(1)",
                }),
                json.dumps({
                    "problem_id": "sample-2",
                    "solution_id": "sample-reviewed-conflict",
                    "language": "c",
                    "source": "int scan(int* values, int size) { int total = 0; for (int i = 0; i < size; ++i) total += values[i]; return total; }",
                    "snippet_time_complexity": "O(n^2)",
                    "snippet_space_complexity": "O(1)",
                }),
            ]
        ) + "\n",
        encoding="utf-8",
    )
    exclusions = tmp_path / "review-exclusions.json"
    exclusions.write_text(json.dumps({"exclusions": [{
        "solution_id": "sample-reviewed-conflict",
        "reason": "Reviewed label conflicts with the visible single input scan.",
    }]}), encoding="utf-8")

    report = run(str(dataset), mode="structural", review_exclusions_path=str(exclusions))

    assert report["total"] == 2
    assert report["raw_eligible"] == 2
    assert report["reviewed_excluded"] == 1
    assert report["eligible"] == 1
    assert report["correct"] == 1
    assert report["accuracy"] == 1.0
