"""P6 regression tests: fixed-size inner loops must not add asymptotic depth."""

from analysis.static_analyzer import analyze_source


def test_python_fixed_inner_loop_is_constant():
    result = analyze_source(
        "def f(a):\n"
        "    total = 0\n"
        "    for x in a:\n"
        "        for d in range(4):\n"
        "            total += x + d\n"
        "    return total\n",
        "python",
    )
    assert result.time_complexity == "O(n)"


def test_cpp_fixed_inner_loop_is_constant():
    result = analyze_source(
        "int f(vector<int>& a) { int total=0; "
        "for (int i=0; i<a.size(); ++i) "
        "for (int d=0; d<26; ++d) total += a[i]+d; return total; }",
        "cpp",
    )
    assert result.time_complexity == "O(n)"


def test_variable_inner_loop_still_multiplies():
    result = analyze_source(
        "int f(int n, int m) { int total=0; "
        "for (int i=0; i<n; ++i) "
        "for (int j=0; j<m; ++j) total += i+j; return total; }",
        "cpp",
    )
    assert result.time_complexity in {"O(n*m)", "O(m*n)", "O(n^2)"}
