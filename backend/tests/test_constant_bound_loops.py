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


def test_sort_once_with_sequential_scans_is_n_log_n_not_nested_work():
    result = analyze_source(
        "int main() { int n; cin >> n; vector<int> values(n); "
        "for (int i = 0; i < n; ++i) cin >> values[i]; "
        "vector<int> expected = values; sort(expected.begin(), expected.end()); "
        "int mismatches = 0; "
        "for (int i = 0; i < n; ++i) if (values[i] != expected[i]) ++mismatches; "
        "cout << mismatches; }",
        "cpp",
    )
    assert result.time_complexity == "O(n log n)"
    assert result.space_complexity == "O(n)"


def test_cpp_only_literal_bound_is_constant():
    result = analyze_source(
        "int f() { int total=0; for (int i=0; i<2; ++i) total += i; return total; }",
        "cpp",
    )
    assert result.time_complexity == "O(1)"
    assert result.space_complexity == "O(1)"


def test_python_only_literal_bound_is_constant():
    result = analyze_source(
        "def f():\n"
        "    total = 0\n"
        "    for i in range(2):\n"
        "        total += i\n"
        "    return total\n",
        "python",
    )
    assert result.time_complexity == "O(1)"
    assert result.space_complexity == "O(1)"


def test_named_literal_bound_is_constant():
    result = analyze_source(
        "int f() { int n=10; int total=0; "
        "for (int i=0; i<n; ++i) total += i; return total; }",
        "cpp",
    )
    assert result.time_complexity == "O(1)"
    assert result.space_complexity == "O(1)"


def test_literal_loop_does_not_hide_input_sized_allocation():
    result = analyze_source(
        "int f(int n) { vector<int> values(n); "
        "for (int i=0; i<2; ++i) values[i] = i; return values[0]; }",
        "cpp",
    )
    # Constructing vector<int>(n) itself is linear; the literal loop does not
    # add another asymptotic factor.
    assert result.time_complexity == "O(n)"
    assert result.space_complexity == "O(n)"
