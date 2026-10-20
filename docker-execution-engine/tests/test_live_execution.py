"""Docker-backed integration tests for every advertised execution language."""
import os
import sys
import asyncio

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.languages import LANGUAGES, get_language_config
from app.models import VERDICT_ACCEPTED, VERDICT_COMPILATION_ERROR, VERDICT_MEMORY_LIMIT_EXCEEDED, VERDICT_OUTPUT_LIMIT_EXCEEDED, VERDICT_RUNTIME_ERROR, VERDICT_TIME_LIMIT_EXCEEDED, VERDICT_WRONG_ANSWER
from app.queue_worker import process_execution_request
from app.sandbox import execute_in_sandbox, is_docker_available
from app.schemas import ExecuteRequest


DOCKER_AVAILABLE = is_docker_available()
pytestmark = pytest.mark.skipif(not DOCKER_AVAILABLE, reason="Docker daemon is not available")


PROGRAMS = {
    "python": "a, b = map(int, input().split())\nprint(a + b)\n",
    "c": "#include <stdio.h>\nint main(){int a,b;if(scanf(\"%d%d\",&a,&b)!=2)return 1;printf(\"%d\\n\",a+b);}\n",
    "cpp": "#include <iostream>\nint main(){int a,b;std::cin>>a>>b;std::cout<<a+b<<'\\n';}\n",
    "java": "import java.util.*; public class Main { public static void main(String[] x){ Scanner s=new Scanner(System.in); System.out.println(s.nextInt()+s.nextInt()); }}\n",
    "javascript": "const fs=require('fs'); const [a,b]=fs.readFileSync(0,'utf8').trim().split(/\\s+/).map(Number); console.log(a+b);\n",
}


@pytest.mark.parametrize("language", sorted(LANGUAGES))
def test_each_supported_language_accepts_and_reports_wrong_answer(language):
    config = get_language_config(language)
    code = PROGRAMS[language]

    accepted = execute_in_sandbox(code, config, "3 5", "8")
    assert accepted.status == VERDICT_ACCEPTED
    assert accepted.actual_output.strip() == "8"

    wrong = execute_in_sandbox(code, config, "3 5", "9")
    assert wrong.status == VERDICT_WRONG_ANSWER


@pytest.mark.parametrize("language", ["c", "cpp", "java"])
def test_compiled_language_reports_compile_errors(language):
    result = execute_in_sandbox("this is not valid source", get_language_config(language), "", "")
    assert result.status == VERDICT_COMPILATION_ERROR
    assert result.compile_success is False


def test_python_runtime_error_is_reported():
    result = execute_in_sandbox("raise RuntimeError('expected test failure')", get_language_config("python"), "", "")
    assert result.status == VERDICT_RUNTIME_ERROR


def test_python_timeout_is_reported():
    result = execute_in_sandbox("while True: pass", get_language_config("python"), "", "", time_limit=1)
    assert result.status == VERDICT_TIME_LIMIT_EXCEEDED


def test_cpp_merge_intervals_nested_stdin_and_whitespace_output():
    """Regression for LeetCode 56-style nested-list judge input.

    The program reads the documented recursive length-prefixed stdin contract
    and prints one merged interval per line. The stored expected result uses a
    flattened whitespace representation, which must compare as equivalent.
    """
    code = r'''
#include <algorithm>
#include <iostream>
#include <vector>
using namespace std;
int main() {
    int count;
    if (!(cin >> count)) return 0;
    vector<vector<int>> intervals(count);
    for (auto& interval : intervals) {
        int length; cin >> length;
        interval.resize(length);
        for (int& value : interval) cin >> value;
    }
    sort(intervals.begin(), intervals.end());
    vector<vector<int>> merged;
    for (const auto& interval : intervals) {
        if (merged.empty() || merged.back()[1] < interval[0]) merged.push_back(interval);
        else merged.back()[1] = max(merged.back()[1], interval[1]);
    }
    for (const auto& interval : merged) cout << interval[0] << ' ' << interval[1] << '\n';
}
'''
    request = ExecuteRequest(
        code=code,
        language="cpp",
        test_cases=[
            {"id": "merge-1", "input": "4\n2\n1 2\n2\n2 3\n2\n3 4\n2\n4 5", "expected_output": "1 5"},
            {"id": "merge-2", "input": "6\n2\n1 2\n2\n3 5\n2\n6 7\n2\n8 10\n2\n12 16\n2\n4 9", "expected_output": "1 2 3 10 12 16"},
            {"id": "merge-3", "input": "4\n2\n1 3\n2\n2 6\n2\n8 10\n2\n15 18", "expected_output": "1 6 8 10 15 18"},
        ],
    )
    result = asyncio.run(process_execution_request(request))
    assert result.status == VERDICT_ACCEPTED
    assert result.tests_passed == 3
    assert all(case.status == VERDICT_ACCEPTED for case in result.results)


def test_output_limit_is_reported(monkeypatch):
    monkeypatch.setenv("EXECUTION_MAX_OUTPUT_BYTES", "1024")
    code = "while True: print('x' * 4096)"
    result = execute_in_sandbox(code, get_language_config("python"), "", "", time_limit=3)
    assert result.status == VERDICT_OUTPUT_LIMIT_EXCEEDED


def test_memory_exhaustion_is_reported():
    code = "data = bytearray(128 * 1024 * 1024)\nfor offset in range(0, len(data), 4096): data[offset] = 1\n"
    result = execute_in_sandbox(code, get_language_config("python"), "", "", time_limit=5, memory_limit=64)
    assert result.status == VERDICT_MEMORY_LIMIT_EXCEEDED


def test_empty_input_and_multiple_test_cases_are_ordered_and_aggregated():
    code = "import sys\ndata = sys.stdin.read()\nprint(len(data.strip()))\n"
    request = ExecuteRequest(
        code=code,
        language="python",
        test_cases=[
            {"id": "empty", "input": "", "expected_output": "0"},
            {"id": "spaces", "input": "  \n", "expected_output": "0"},
            {"id": "text", "input": "hello", "expected_output": "5"},
        ],
    )
    result = asyncio.run(process_execution_request(request))
    assert result.status == VERDICT_ACCEPTED
    assert result.tests_total == 3
    assert result.tests_passed == 3
    assert [case.test_case_id for case in result.results] == ["empty", "spaces", "text"]
