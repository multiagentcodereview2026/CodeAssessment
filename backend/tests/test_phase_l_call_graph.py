from analysis.static_analyzer import analyze_source


def test_cpp_mutual_recursion_is_linear():
    result = analyze_source(
        "bool odd(int); bool even(int n){ if(n==0)return true; return odd(n-1); } "
        "bool odd(int n){ if(n==0)return false; return even(n-1); }",
        "cpp",
    )
    assert result.time_complexity == "O(n)"
    assert result.space_complexity == "O(n)"


def test_python_mutual_recursion_is_linear():
    result = analyze_source(
        "def even(n):\n"
        "    if n == 0: return True\n"
        "    return odd(n - 1)\n"
        "def odd(n):\n"
        "    if n == 0: return False\n"
        "    return even(n - 1)\n",
        "python",
    )
    assert result.time_complexity == "O(n)"
    assert result.space_complexity == "O(n)"


def test_cross_function_branching_recursion_is_exponential():
    result = analyze_source(
        "void choose_next(int n, int i); "
        "void choose(int n, int i){ if(i>=n)return; choose_next(n,i+1); } "
        "void choose_next(int n, int i){ if(i>=n)return; "
        "choose(n,i+1); choose(n,i+1); }",
        "cpp",
    )
    assert result.time_complexity == "O(2^n)"
    assert result.space_complexity == "O(n)"
