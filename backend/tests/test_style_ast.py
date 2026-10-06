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
