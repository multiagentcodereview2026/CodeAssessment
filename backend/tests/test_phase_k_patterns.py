from analysis.static_analyzer import analyze_source


def test_cpp_sliding_window_is_amortized_linear():
    result = analyze_source(
        "int f(vector<int>& a, int k) { int left=0, sum=0; "
        "for(int right=0; right<a.size(); ++right) { sum += a[right]; "
        "while(sum>k) sum -= a[left++]; } return left; }",
        "cpp",
    )
    assert result.time_complexity == "O(n)"
    assert result.space_complexity == "O(1)"


def test_cpp_monotonic_stack_is_amortized_linear():
    result = analyze_source(
        "int f(vector<int>& a) { vector<int> st; for(int x:a) { "
        "while(!st.empty() && st.back()<x) st.pop_back(); "
        "st.push_back(x); } return st.size(); }",
        "cpp",
    )
    assert result.time_complexity == "O(n)"
    assert result.space_complexity == "O(n)"


def test_sort_inside_input_loop_is_quadratic_logarithmic():
    result = analyze_source(
        "int f(vector<vector<int>>& a) { for(auto& row:a) sort(row.begin(), row.end()); return 0; }",
        "cpp",
    )
    assert result.time_complexity == "O(n^2 log n)"
