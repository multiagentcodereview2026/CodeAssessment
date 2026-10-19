"""C++ fixtures for the local complexity detector.

These are detector tests only.  They never execute a submission, create a
database row, or expose hidden test cases.
"""

import pytest

from analysis.static_analyzer import (
    _has_constant_factor_progress_loop,
    _has_input_derived_growing_text,
    _has_recursive_leaf_path_materialization,
    _has_nested_collection_edge_growth,
    _has_input_loop_with_derived_logarithmic_inner_loop,
    _has_multi_branch_numeric_recursion,
    _has_state_dependent_loop_recursion,
    _has_monotonic_shared_pointer_loops,
    analyze_cpp,
    analyze_source,
)


@pytest.mark.parametrize(
    ("source", "expected_time", "expected_space"),
    [
        (
            "int f(vector<int>& nums) { int total=0; for (int x: nums) total += x; return total; }",
            "O(n)",
            "O(1)",
        ),
        (
            "int f(vector<int>& a, int target) { int low=0, right=a.size()-1; while(low<=right) { int mid=(low+right)/2; if(a[mid]<target) low=mid+1; else right=mid-1; } return -1; }",
            "O(log n)",
            "O(1)",
        ),
        (
            "int f(vector<int>& a) { sort(a.begin(), a.end()); return a[0]; }",
            "O(n log n)",
            "O(1)",
        ),
        (
            "int f(vector<int>& a) { int ans=0; for(int i=0;i<a.size();++i) { for(int j=0;j<a.size();++j) ans += a[i]*a[j]; } return ans; }",
            "O(n^2)",
            "O(1)",
        ),
        (
            "void f(vector<vector<int>>& groups) { for(auto& g: groups) { sort(g.begin(), g.end()); } }",
            "O(n^2 log n)",
            "O(1)",
        ),
        (
            "int f(vector<int>& a) { unordered_map<int,int> freq; for(int x: a) ++freq[x]; return freq.size(); }",
            "O(n)",
            "O(n)",
        ),
        (
            "int f(vector<int>& a) { vector<int> dp(a.size()); for(int i=0;i<a.size();++i) dp[i]=a[i]; return dp.back(); }",
            "O(n)",
            "O(n)",
        ),
    ],
)
def test_cpp_static_detector_fixtures(source, expected_time, expected_space):
    result = analyze_cpp(source)
    assert result.time_complexity == expected_time
    assert result.space_complexity == expected_space


def test_cpp_sliding_window_left_right_names_are_not_tree_space_evidence():
    source = (
        "class Solution { public: int lengthOfLongestSubstring(string s) { "
        "unordered_set<char> seen; int left=0, best=0; "
        "for (int right=0; right<s.size(); ++right) { "
        "while (seen.count(s[right])) { seen.erase(s[left]); ++left; } "
        "seen.insert(s[right]); best=max(best,right-left+1); } return best; } };"
    )
    result = analyze_cpp(source)
    assert result.space_complexity == "O(n)"


def test_linear_vote_style_scan_is_classified_from_structure_not_function_name():
    source = (
        "int scan(vector<int>& values) { int first=0, second=0, a=0, b=0; "
        "for (int value : values) { if (value == first) ++a; else if (value == second) ++b; "
        "else if (a == 0) { first=value; a=1; } else if (b == 0) { second=value; b=1; } "
        "else { --a; --b; } } for (int value : values) { if (value == first) ++a; } return first; }"
    )
    result = analyze_source(source, "cpp")
    assert result.time_complexity == "O(n)"
    assert result.space_complexity == "O(1)"


def test_literal_capacity_auxiliary_table_is_constant_space_without_name_rules():
    source = (
        "int scan(string input) { vector<int> buckets(128, 0); "
        "for (char value : input) ++buckets[value]; int total=0; "
        "for (int value : buckets) total += value; return total; }"
    )
    result = analyze_source(source, "cpp")
    assert result.time_complexity == "O(n)"
    assert result.space_complexity == "O(1)"
    assert "structural:fixed-capacity-auxiliary-storage" in result.signals


@pytest.mark.parametrize(
    ("language", "source"),
    [
        (
            "c",
            "int* scan(int* values, int size) { int* pair = malloc(2 * sizeof(int)); for(int i=0;i<size;i++) for(int j=i+1;j<size;j++) { pair[0]=i; pair[1]=j; return pair; } return 0; }",
        ),
        (
            "cpp",
            "vector<int> scan(vector<int>& values) { for(int i=0;i<values.size();i++) for(int j=i+1;j<values.size();j++) if(values[i] != values[j]) return {i, j}; return {}; }",
        ),
        (
            "java",
            "class Scan { int[] run(int[] values) { for(int i=0;i<values.length;i++) for(int j=i+1;j<values.length;j++) if(values[i] != values[j]) return new int[]{i, j}; return new int[0]; } }",
        ),
    ],
)
def test_literal_sized_result_storage_is_constant_space_without_name_rules(language, source):
    result = analyze_source(source, language)
    assert result.time_complexity == "O(n^2)"
    assert result.space_complexity == "O(1)"


def test_input_derived_row_copy_is_linear_auxiliary_space_without_name_rules():
    source = (
        "int scan(vector<vector<int>>& matrix) { vector<int> state = matrix.back(); "
        "for (int index=0; index<state.size(); ++index) state[index] += 1; return state[0]; }"
    )
    result = analyze_source(source, "cpp")
    assert result.time_complexity == "O(n)"
    assert result.space_complexity == "O(n)"
    assert "structural:input-derived-linear-copy" in result.signals


def test_input_derived_growing_text_is_linear_auxiliary_space_without_name_rules():
    source = """
std::string scan(const std::string& input) {
    std::string output = "";
    for (char value : input) {
        if (value != ' ') output += value;
    }
    return output;
}
"""
    result = analyze_source(source, "cpp")
    assert result.time_complexity == "O(n)"
    assert result.space_complexity == "O(n)"
    assert _has_input_derived_growing_text(source)


def test_nested_collection_growth_is_vertex_edge_space_without_name_rules():
    source = """
def scan(n, edges):
    buckets = [[] for _ in range(n)]
    for first, second in edges:
        buckets[first].append(second)
    seen = [False] * n
    return seen
"""
    assert _has_nested_collection_edge_growth(source)


def test_shared_monotonic_boundaries_are_amortized_linear_without_name_rules():
    source = (
        "bool scan(string text) { int left=0, right=text.length()-1; "
        "while (left < right) { while (left < right && text[left] == ' ') left++; "
        "while (left < right && text[right] == ' ') right--; if (left < right) { left++; right--; } } "
        "return true; }"
    )
    result = analyze_source(source, "cpp")
    assert result.time_complexity == "O(n)"
    assert _has_monotonic_shared_pointer_loops(source)


def test_input_sized_slice_reduction_inside_loop_is_quadratic_without_name_rules():
    source = """
def scan(values):
    n = len(values)
    total = 0
    for index in range(1, n - 1):
        total += max(values[:index + 1]) - min(values[index:])
    return total
"""
    result = analyze_source(source, "python")
    assert result.time_complexity == "O(n^2)"
    assert "structural:input-slice-reduction-inside-loop" in result.signals


def test_input_sized_slice_reduction_inside_nested_loops_is_cubic_without_name_rules():
    source = """
def scan(values):
    n = len(values)
    best = 0
    for left in range(n):
        for right in range(left, n):
            best = max(best, sum(values[left:right + 1]))
    return best
"""
    result = analyze_source(source, "python")
    assert result.time_complexity == "O(n^3)"
    assert "structural:input-slice-reduction-inside-nested-loops" in result.signals


def test_literal_factor_loop_progress_is_logarithmic_without_name_rules():
    source = """
function scan(value) {
    while (value % 3 === 0) {
        value /= 3;
    }
    return value;
}
"""
    result = analyze_source(source, "javascript")
    assert result.time_complexity == "O(log n)"
    assert "structural:constant-factor-loop-progress" in result.signals


def test_decimal_factor_loop_progress_is_recognized_without_name_rules():
    source = """
int reduce(int value) {
    int total = 0;
    while (value > 0) {
        total += value % 10;
        value /= 10;
    }
    return total;
}
"""
    assert _has_constant_factor_progress_loop(source)


def test_input_loop_with_derived_halving_work_is_n_log_n_without_name_rules():
    source = """
int scan(int limit) {
    int total = 0;
    for (int index = 0; index <= limit; ++index) {
        int value = index;
        while (value > 0) {
            total += value & 1;
            value >>= 1;
        }
    }
    return total;
}
"""
    result = analyze_source(source, "cpp")
    assert result.time_complexity == "O(n log n)"
    assert _has_input_loop_with_derived_logarithmic_inner_loop(source)


def test_python_input_loop_with_derived_halving_work_is_n_log_n_without_name_rules():
    source = """
def scan(limit):
    total = 0
    for index in range(limit + 1):
        value = index
        while value > 0:
            total += value & 1
            value >>= 1
    return total
"""
    result = analyze_source(source, "python")
    assert result.time_complexity == "O(n log n)"
    assert _has_input_loop_with_derived_logarithmic_inner_loop(source)


def test_multi_branch_numeric_recursion_is_exponential_without_name_rules():
    source = """
int explore(int first, int second) {
    if (first == 0 || second == 0) return 1;
    return explore(first - 1, second) + explore(first, second - 1);
}
"""
    result = analyze_source(source, "c", mode="structural")
    assert result.time_complexity == "O(2^n)"
    assert _has_multi_branch_numeric_recursion(source)


def test_state_dependent_loop_recursion_is_exponential_without_name_rules():
    source = """
def explore(index, limit):
    if index >= limit:
        return 1
    total = 0
    for candidate in range(index + 1, limit + 1):
        total += explore(candidate, limit)
    return total
"""
    result = analyze_source(source, "python")
    assert result.time_complexity == "O(2^n)"
    assert _has_state_dependent_loop_recursion(source)


def test_loop_calling_a_nonrecursive_helper_is_not_state_dependent_recursion():
    source = """
bool validate(const char* text, int start, int end) {
    int balance = 0;
    for (int index = start; index <= end; ++index) balance += text[index];
    return balance == 0;
}

int scan(const char* text, int size) {
    for (int start = 0; start < size; ++start) {
        for (int end = start + 1; end < size; ++end) validate(text, start, end);
    }
    return 0;
}
"""
    assert not _has_state_dependent_loop_recursion(source)


def test_nested_loops_are_not_hidden_by_an_external_helper_call():
    source = """
def compare(left, right):
    return left < right

def count_pairs(values):
    result = []
    n = len(values)
    for first in range(n):
        total = 0
        for second in range(first + 1, n):
            if compare(values[first], values[second]):
                total += 1
        result.append(total)
    return result
"""
    result = analyze_source(source, "python", mode="structural")
    assert result.time_complexity == "O(n^2)"


def test_child_pointer_recursion_is_not_numeric_branching_recursion():
    source = """
int visit(Node* root) {
    if (!root) return 0;
    return visit(root->left) + visit(root->right);
}
"""
    assert not _has_multi_branch_numeric_recursion(source)


def test_recursive_leaf_path_copy_is_quadratic_without_name_rules():
    source = """
def scan(root):
    answers = []
    def walk(node, path):
        if not node:
            return
        path.append(node.value)
        if not node.left and not node.right:
            answers.append(list(path))
        else:
            walk(node.left, path)
            walk(node.right, path)
        path.pop()
    walk(root, [])
    return answers
"""
    result = analyze_source(source, "python")
    assert result.time_complexity == "O(n^2)"
    assert _has_recursive_leaf_path_materialization(source)


def test_variable_sized_comparator_reorder_is_n_log_n_without_name_rules():
    source = """
int scan(int* values, int size) {
    reorder(values, size, sizeof(int), comparator);
    return values[0];
}
"""
    result = analyze_source(source, "c", mode="structural")
    assert result.time_complexity == "O(n log n)"
    assert "structural:comparison-reorder-over-linear-population" in result.signals


def test_comparator_reorder_over_product_population_is_n_squared_log_n_without_name_rules():
    source = """
int scan(int** grid, int rows, int columns) {
    int total = rows * columns;
    int* values = malloc(total * sizeof(int));
    for (int row = 0; row < rows; ++row) {
        for (int column = 0; column < columns; ++column) values[row * columns + column] = grid[row][column];
    }
    reorder(values, total, sizeof(int), comparator);
    return values[0];
}
"""
    result = analyze_source(source, "c", mode="structural")
    assert result.time_complexity == "O(n^2 log n)"
    assert "structural:comparison-reorder-over-quadratic-population" in result.signals


def test_cpp_all_substrings_with_pairwise_character_checks_complexity():
    source = r"""
    #include <bits/stdc++.h>
    using namespace std;
    int main() {
        string s;
        cin >> s;
        int n = s.length();
        vector<string> subs;
        for (int i = 0; i < n; i++) {
            for (int j = i; j < n; j++) {
                string temp = "";
                for (int k = i; k <= j; k++) {
                    temp += s[k];
                }
                subs.push_back(temp);
            }
        }
        int ans = 0;
        for (int i = 0; i < (int)subs.size(); i++) {
            bool valid = true;
            for (int j = 0; j < (int)subs[i].length(); j++) {
                for (int k = j + 1; k < (int)subs[i].length(); k++) {
                    if (subs[i][j] == subs[i][k]) valid = false;
                }
            }
        }
    }
    """
    result = analyze_cpp(source)
    assert result.time_complexity == "O(n^4)"
    assert result.space_complexity == "O(n^3)"

    assessed_result = analyze_source(source, "cpp")
    assert assessed_result.time_complexity == "O(n^4)"
    assert assessed_result.space_complexity == "O(n^3)"
