"""Live synthetic candidate-to-official-score contract; no application DB writes.

The candidate is an original fixture, not an AI-provider observation. This
checks the judge, saved rubric and official assessment path under two policies.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path

BASELINE = r'''#include <iostream>
#include <vector>
int main(){int n;std::cin>>n;std::vector<long long>a(n);for(auto &v:a)std::cin>>v;
long long total=0;for(int i=0;i<n;++i){total=0;for(int j=0;j<n;++j)total+=a[j];}
std::cout<<total;return 0;}'''
CANDIDATE = r'''#include <iostream>
int main(){int n;std::cin>>n;long long total=0;
for(int i=0;i<n;++i){long long value;std::cin>>value;total+=value;}
std::cout<<total;return 0;}'''
CASES = [{"id": "positive", "input": "3\n1 2 3", "expected_output": "6"},
         {"id": "negative", "input": "4\n-1 2 -3 4", "expected_output": "2"},
         {"id": "empty", "input": "0", "expected_output": "0"}]


async def run():
    # Set before importing application modules, which initialize the database
    # and optional provider at import time. Never connect to the real database.
    os.environ["DATABASE_URL"] = "sqlite://"
    os.environ["GROQ_API_KEY"] = ""
    os.environ["AI_ALLOWED_CAPABILITIES"] = ""
    os.environ["COMPLEXITY_AI_REVIEW_ENABLED"] = "false"
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    import main
    import models
    from database import Base
    from schemas import SubmissionRequest
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    reports = []
    try:
        learner = models.Student(student_id="synthetic-contract-only", name="Synthetic contract")
        db.add(learner)
        for name, weights in [("default", None), ("custom", {"correctness": 20, "time": 50, "space": 25, "style": 5})]:
            problem = models.Problem(id=f"contract-{name}", title="Synthetic sum", description="Return the sum of n supplied integers. The first token is n, followed by n integers.",
                examples=[], constraints=["0 <= n <= 100000"], starter_codes={}, test_cases=CASES,
                target_time_complexity="O(n)", target_space_complexity="O(1)", is_public_practice=True, scoring_weights=weights)
            db.add(problem)
            db.commit()
            original = await main.submit_and_evaluate_code(SubmissionRequest(problem_id=problem.id, code=BASELINE, language="cpp"), db, learner)
            saved = db.query(models.Submission).filter_by(submission_id=original.submission_id).one()
            forecast = await main.score_revision_stage(original_submission=saved, problem=problem, source_code=CANDIDATE, language="cpp", test_cases=CASES)
            official = await main.submit_and_evaluate_code(SubmissionRequest(problem_id=problem.id, code=CANDIDATE, language="cpp"), db, learner)
            available = forecast.get("available") is True and forecast.get("verified") is True
            matches = available and forecast.get("projected_score") == official.overall_score
            reports.append({"policy": name, "baseline_score": original.overall_score,
                "candidate_score": forecast.get("projected_score"), "official_score": official.overall_score,
                "candidate_verified": available, "score_matches": matches,
                "gain_matches": matches and forecast.get("expected_improvement") == round(official.overall_score - original.overall_score, 1),
                "saved_rubric": saved.score_breakdown.get("rubric"),
                "candidate_tests_passed": (official.execution_result or {}).get("passed_cases"),
                "candidate_tests_total": (official.execution_result or {}).get("total_cases")})
    finally:
        db.close()
        engine.dispose()
    return {"kind": "synthetic_candidate_score_contract", "database": "isolated_in_memory_only",
            "provider_observation": False, "all_passed": all(row["score_matches"] and row["gain_matches"] for row in reports),
            "checks": reports, "warning": "Two original synthetic examples verify this contract, not AI-generation accuracy or student learning outcomes."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = asyncio.run(run())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["all_passed"] else 1)
