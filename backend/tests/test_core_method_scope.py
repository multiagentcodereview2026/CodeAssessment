import asyncio

import pytest

from analysis import analyzer_service
from analysis.core_scope import extract_core_scope
from config.settings import settings


STOCK = """#include <vector>
int main() {
    int n; std::cin >> n;
    std::vector<int> prices(n);
    for (int i=0; i<n; ++i) std::cin >> prices[i];
    int profit=0;
    for(int buy=0; buy<n; ++buy)
        for(int sell=buy+1; sell<n; ++sell)
            profit=std::max(profit, prices[sell]-prices[buy]);
    std::cout << profit;
    return 0;
}"""


@pytest.mark.parametrize("identifier", ["prices", "values", "differentName"])
def test_input_storage_excluded_but_nested_algorithm_retained(identifier):
    code = STOCK.replace("prices", identifier)
    result = analyzer_service.analyze_static_complexity(code, "cpp")
    assert result.time_complexity == "O(n^2)"
    assert result.space_complexity == "O(1)"
    assert result.status == "ANALYZED"
    assert "scope:core-method" in result.signals
    assert "structural:stdin-input-sized-allocation" not in result.signals


def test_single_pass_algorithm_is_linear_with_constant_auxiliary_space():
    code = STOCK[:STOCK.index("    int profit=0;")] + """
    int low=prices[0], profit=0;
    for(int i=1; i<n; ++i) {
        low=std::min(low,prices[i]);
        profit=std::max(profit,prices[i]-low);
    }
    std::cout << profit; return 0;
    }"""
    result = analyzer_service.analyze_static_complexity(code, "cpp")
    assert result.time_complexity == "O(n)"
    assert result.space_complexity == "O(1)"


def test_temporary_copy_is_auxiliary_storage():
    code = STOCK[:STOCK.index("    int profit=0;")] + """
    std::vector<int> copy=prices;
    std::sort(copy.begin(),copy.end());
    int mismatch=0;
    for(int i=0;i<n;++i) if(copy[i]!=prices[i]) ++mismatch;
    std::cout<<mismatch; return 0;
    }"""
    result = analyzer_service.analyze_static_complexity(code, "cpp")
    assert result.space_complexity == "O(n)"


def test_reachable_helper_in_output_is_retained_and_unused_helper_removed():
    code = """int unused(int n){for(int i=0;i<n;i++)for(int j=0;j<n;j++){} return 0;}
    int calc(int n){int x=0;for(int i=0;i<n;i++)x+=i;return x;}
    int main(){int n;cin>>n;cout<<calc(n);return 0;}"""
    scope = extract_core_scope(code, "cpp")
    assert "int calc(" in scope.source
    assert "calc(n);" in scope.source
    assert "unused" not in scope.source
    result = analyzer_service.analyze_static_complexity(code, "cpp")
    assert result.time_complexity == "O(n)"


def test_output_storage_excluded_but_temporary_storage_kept():
    code = """vector<int> transform(vector<int>& input){
        vector<int> scratch(input.size());
        vector<int> answer;
        for(int i=0;i<input.size();++i){scratch[i]=input[i];answer.push_back(scratch[i]);}
        return answer;
    }"""
    scope = extract_core_scope(code, "cpp")
    assert "vector<int> answer" in scope.source
    assert "vector<int> answer" not in scope.space_source
    assert "vector<int> scratch" in scope.space_source
    assert analyzer_service.analyze_static_complexity(code, "cpp").space_complexity == "O(n)"


def test_only_required_output_does_not_count_as_auxiliary_storage():
    code = """vector<int> transform(vector<int>& input){
        vector<int> answer;
        for(int i=0;i<input.size();++i) answer.push_back(input[i]+1);
        return answer;
    }"""
    result = analyzer_service.analyze_static_complexity(code, "cpp")
    assert result.time_complexity == "O(n)"
    assert result.space_complexity == "O(1)"


def test_mixed_input_and_algorithm_loop_is_not_removed():
    code = """int main(){int n;cin>>n;int total=0;
        for(int i=0;i<n;i++){int x;cin>>x;total+=x;}
        cout<<total;return 0;}"""
    scope = extract_core_scope(code, "cpp")
    assert "total+=x" in scope.source
    assert "for(" in scope.source
    assert analyzer_service.analyze_static_complexity(code, "cpp").time_complexity == "O(n)"


def test_python_input_and_print_loops_do_not_count_as_algorithm_work():
    code = """n = int(input())
values = list(map(int, input().split()))
answer = 0
for value in values:
    answer += value
for value in values:
    print(value)
print(answer)
"""
    scope = extract_core_scope(code, "python")
    assert "input(" not in scope.source
    assert "print(" not in scope.source
    assert "answer += value" in scope.source
    result = analyzer_service.analyze_static_complexity(code, "python")
    assert result.space_complexity == "O(1)"


def test_ambiguous_entry_uses_ai_and_never_certifies_whole_file(monkeypatch):
    code = "int a(int n){return n;} int b(int n){return n+1;}"
    calls = []

    async def review(payload):
        calls.append(payload)
        return {"time_complexity": None, "space_complexity": None,
                "status": "NEEDS_REVIEW", "confidence": 0.2, "evidence": ["Ambiguous entry."]}

    monkeypatch.setattr(settings, "COMPLEXITY_AI_REVIEW_ENABLED", True)
    monkeypatch.setattr(analyzer_service, "_invoke_complexity_reviewer", review)
    monkeypatch.setattr(analyzer_service, "_review_cache", analyzer_service.ComplexityReviewCache(60))
    monkeypatch.setattr(analyzer_service, "_review_limiter", analyzer_service.AIReviewRateLimiter(20, 1))
    result = asyncio.run(analyzer_service.analyze_submission_complexity(code, "cpp"))
    assert len(calls) == 1
    assert "Auxiliary space excludes input" in calls[0]["instruction"]
    assert result.final.status != "ANALYZED"


def test_end_to_end_judge_timing_does_not_override_core_scope():
    from analysis.models import ComplexityAnalysis
    static = analyzer_service.analyze_static_complexity(STOCK, "cpp")
    dynamic = ComplexityAnalysis("O(n)", None, 0.98, "runtime", "ANALYZED", evidence_quality="strong")
    result = asyncio.run(analyzer_service.analyze_submission_complexity(STOCK, "cpp", static_result=static, dynamic_result=dynamic))
    assert result.dynamic is None
    assert result.final.time_complexity == "O(n^2)"


def test_string_line_input_is_an_input_not_auxiliary_storage():
    code = """int main(){string text;getline(cin,text);int count=0;
        for(int i=0;i<text.size();++i) count+=text[i]=='a';
        cout<<count;return 0;}"""
    scope = extract_core_scope(code, "cpp")
    assert "text" in scope.inputs
    assert "getline" not in scope.source
    assert "string text" not in scope.source
    assert analyzer_service.analyze_static_complexity(code, "cpp").space_complexity == "O(1)"


def test_java_scanner_input_setup_is_excluded():
    code = """class Main {public static void main(String[] args) {
        Scanner scan=new Scanner(System.in);
        int n=scan.nextInt(); int[] values=new int[n];
        for(int i=0;i<n;i++) values[i]=scan.nextInt();
        int total=0;for(int i=0;i<n;i++)total+=values[i];
        System.out.println(total);
    }}"""
    scope = extract_core_scope(code, "java")
    assert not scope.issues
    assert "Scanner scan" not in scope.source
    assert "int[] values" not in scope.source
    assert "total+=values[i]" in scope.source
    assert analyzer_service.analyze_static_complexity(code, "java").space_complexity == "O(1)"


def test_javascript_method_core_is_retained():
    code = """function transform(values){let total=0;
        for(let i=0;i<values.length;i++){total+=values[i];} return total;}"""
    scope = extract_core_scope(code, "javascript")
    assert not scope.issues
    assert "total+=values[i]" in scope.source


def test_recursion_stack_is_not_excluded_as_input_or_output():
    code = "int visit(int n){if(n==0)return 0;return 1+visit(n-1);}"
    result = analyzer_service.analyze_static_complexity(code, "cpp")
    assert result.space_complexity == "O(n)"


def test_empty_print_condition_does_not_create_invalid_slice():
    code = """vector<int> transform(vector<int>& input){vector<int> answer;
        for(int i=0;i<input.size();i++) answer.push_back(input[i]);
        for(int i=0;i<answer.size();i++){if(i>0) cout<<' ';cout<<answer[i];}
        return answer;}"""
    scope = extract_core_scope(code, "cpp")
    assert not scope.issues
    assert "cout" not in scope.source


def test_input_names_do_not_erase_helper_local_scratch():
    code = """int helper(int size){vector<int> values(size);
        for(int i=0;i<size;i++)values[i]=i;return values[size-1];}
        int main(){int n;cin>>n;vector<int> values(n);
        for(int i=0;i<n;i++)cin>>values[i];cout<<helper(n);return 0;}"""
    scope = extract_core_scope(code, "cpp")
    assert "vector<int> values(size)" in scope.source
    assert "vector<int> values(n)" not in scope.source


def test_python_function_wrapper_does_not_count_input_buffer():
    code = """def calculate(values):
    result = 0
    for value in values:
        result += value
    return result
values = list(map(int, input().split()))
print(calculate(values))
"""
    scope = extract_core_scope(code, "python")
    assert "input(" not in scope.source
    assert "calculate(values)" in scope.source
    assert analyzer_service.analyze_static_complexity(code, "python").space_complexity == "O(1)"


def test_python_input_variable_updates_are_algorithm_work():
    code = """n = int(input())
while n > 0:
    n = n // 2
print(n)
"""
    scope = extract_core_scope(code, "python")
    assert "n = n // 2" in scope.source
