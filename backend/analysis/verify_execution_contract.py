"""Live, synthetic judge contract checks. No accounts or database writes.

Run inside backend's Compose network:
python -m analysis.verify_execution_contract --output /tmp/execution-contract.json
These checks establish execution behavior for these examples, not research accuracy.
"""
import argparse
import asyncio
import hashlib
import json
import time
from pathlib import Path
from docker_runner.executor import execute_code_sandboxed

SUM_SOURCES = {
    "python": "import sys\na,b=map(int,sys.stdin.read().split());print(a+b)",
    "cpp": '#include <iostream>\nint main(){long long a,b;std::cin>>a>>b;std::cout<<a+b;}',
    "c": '#include <stdio.h>\nint main(){long long a,b;scanf("%lld%lld",&a,&b);printf("%lld",a+b);}',
    "java": 'import java.util.*; public class Main { public static void main(String[] args){Scanner s=new Scanner(System.in);System.out.println(s.nextLong()+s.nextLong());}}',
    "javascript": "const [a,b]=require('fs').readFileSync(0,'utf8').trim().split(/\\s+/).map(Number);console.log(a+b);",
}
MERGE_SOURCE = r'''#include <algorithm>
#include <iostream>
#include <vector>
using namespace std;
int main(){
 int n; if(!(cin>>n))return 1;
 vector<pair<int,int>> a(n);
 for(auto &p:a){int width;cin>>width; if(width!=2)return 2;cin>>p.first>>p.second;}
 sort(a.begin(),a.end()); vector<pair<int,int>> merged;
 for(auto p:a){if(merged.empty()||p.first>merged.back().second)merged.push_back(p);else merged.back().second=max(merged.back().second,p.second);}
 for(auto p:merged)cout<<p.first<<' '<<p.second<<'\n';
}'''


async def run():
    checks = []
    async def check(name, language, source, cases, expected_passes):
        started = time.perf_counter()
        result = await execute_code_sandboxed(source_code=source, language=language, test_cases=cases, stop_on_first_failure=False)
        passed = result.get("compile_status") == "success" and result.get("passed_cases") == expected_passes and result.get("total_cases") == len(cases)
        checks.append({"name": name, "language": language, "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                       "ok": passed, "compile_status": result.get("compile_status"), "execution_status": result.get("execution_status"),
                       "judge_request_wall_ms": round((time.perf_counter() - started) * 1000, 2),
                       "passed_cases": result.get("passed_cases"), "total_cases": result.get("total_cases")})
    sum_cases = [{"id": "sum-positive", "input": "2 3\n", "expected_output": "5"}, {"id": "sum-negative", "input": "-8\n3\n", "expected_output": "-5"}, {"id": "sum-zero", "input": "0 0", "expected_output": "0"}]
    for language, source in SUM_SOURCES.items():
        await check("stdin-sum", language, source, sum_cases, 3)
    merge_cases = [
        {"id": "endpoint-chain", "input": "4\n2\n1 2\n2\n2 3\n2\n3 4\n2\n4 5\n", "expected_output": "1 5"},
        {"id": "unsorted-overlap", "input": "6\n2\n3 6\n2\n1 2\n2\n15 18\n2\n8 10\n2\n4 5\n2\n11 13\n", "expected_output": "1 2 3 6 8 10 11 13 15 18"},
        {"id": "nested-intervals", "input": "3\n2\n1 10\n2\n2 3\n2\n4 8\n", "expected_output": "1 10"},
    ]
    await check("nested-array-merge", "cpp", MERGE_SOURCE, merge_cases, 3)
    # Changed source must actually execute and fail; a previous correct output
    # must never be reused. Re-running the original must pass again.
    await check("changed-source-rejected", "cpp", '#include <iostream>\nint main(){std::cout<<"wrong";}', merge_cases, 0)
    await check("correct-source-rerun", "cpp", MERGE_SOURCE, merge_cases, 3)
    return {"kind": "synthetic_execution_contract", "all_passed": all(row["ok"] for row in checks), "checks": checks,
            "latency_scope": "One request per check, including compilation and containers; not page latency, algorithmic growth, or a representative latency benchmark.",
            "warning": "This smoke matrix is not a measured application accuracy benchmark."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = asyncio.run(run())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["all_passed"] else 1)
