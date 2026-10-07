import asyncio

from agents.style import style_node
from analysis.style_ast_analyzer import analyze_style


def test_style_analysis_is_deterministic_and_ast_based():
    source = "def solve(a):\n    total = 0\n    for x in a:\n        total += x\n    return total\n"
    first = analyze_style(source, "python")
    second = analyze_style(source, "python")
    assert first == second
    assert first["method"] == "ast"
    assert first["status"] == "ANALYZED"
    assert 0 <= first["style_score"] <= 100


def test_style_flags_cryptic_names_and_missing_comments():
    result = analyze_style("def f(a):\n    q = a + 1\n    return q\n", "python")
    assert result["naming_issues"]
    assert result["readability_issues"]
    assert result["style_score"] < 100


def test_cpp_style_analysis_does_not_use_complexity_engine():
    result = analyze_style("int f(int a){int q=a+1;return q;}\n", "cpp")
    assert result["method"] == "ast"
    assert result["status"] == "ANALYZED"
    assert result["naming_issues"]


def test_cpp_index_parameter_is_not_false_positive():
    source = "int sumAt(int i, const vector<int>& values) { return values[i]; }"
    result = analyze_style(source, "cpp")
    assert not any("Parameter `i`" in issue["message"] for issue in result["naming_issues"])


def test_style_workflow_uses_ast_result_without_llm_or_complexity_fallback():
    result = asyncio.run(style_node({
        "submission": {
            "source_code": "int sumAt(int i, const vector<int>& values) { return values[i]; }",
            "language": "cpp",
        }
    }))
    assert result["style_score"] == result["style_details"]["style_score"]
    assert result["style_details"]["method"] == "ast"
    assert result["style_details"]["status"] == "ANALYZED"


def test_worst_style_is_strongly_penalized():
    source = "def f(a,b,c,d,e,f,g):\n" + "    " + "\n    ".join(
        [f"x{i} = {i}" for i in range(1, 21)]
    ) + "\n    if a:\n        if b:\n            if c:\n                if d:\n                    if e:\n                        if f:\n                            if g:\n                                return x20\n    return x1\n"
    result = analyze_style(source, "python")
    assert result["style_score"] <= 40
    assert all(issue["penalty"] >= 0 for issue in (
        result["naming_issues"] + result["readability_issues"] +
        result["modularity_issues"] + result["maintainability_issues"]
    ))


def test_modularity_flags_repeated_cpp_logic():
    source = """
int solve(int value) {
    int total = value + 7;
    total = total * 2;
    total = total * 2;
    return total;
}
"""
    result = analyze_style(source, "cpp")
    assert any("duplicated" in issue["message"].lower() for issue in result["modularity_issues"])
    assert any("duplicated" in issue["message"].lower() for issue in result["maintainability_issues"])


def test_modularity_recognizes_helper_decomposition():
    source = """
int parseValue(int value) { return value; }
int transformValue(int value) { return parseValue(value) + 1; }
int solve(int value) { return transformValue(value); }
"""
    result = analyze_style(source, "cpp")
    assert any(issue.get("credit", 0) > 0 for issue in result["modularity_issues"])


def test_python_modularity_flags_io_and_iteration_mixed_together():
    source = """
def solve(values):
    total = 0
    for value in values:
        total += value
    print(total)
    return total
"""
    result = analyze_style(source, "python")
    assert any("input/output" in issue["message"] for issue in result["modularity_issues"])


def test_python_maintainability_flags_high_coupling():
    source = """
def assemble(value):
    return parse(value) + clean(value) + normalize(value) + validate(value) + enrich(value) + publish(value)
"""
    result = analyze_style(source, "python")
    assert any("coupled" in issue["message"].lower() for issue in result["maintainability_issues"])
