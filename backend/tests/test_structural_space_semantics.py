"""Regression tests for generic auxiliary-space evidence."""

import pytest

from analysis.static_analyzer import analyze_source


def test_linked_list_scan_with_materialized_node_vector_is_linear_space():
    result = analyze_source(
        "struct ListNode { int val; ListNode* next; }; "
        "ListNode* f(ListNode* head) { vector<ListNode*> nodes; "
        "for (auto* cur=head; cur; cur=cur->next) nodes.push_back(cur); "
        "return head; }",
        "cpp",
    )
    assert result.time_complexity == "O(n)"
    assert result.space_complexity == "O(n)"
    assert "structural:single-linked-list-scan" in result.signals


def test_linked_list_scan_without_materialized_storage_is_constant_space():
    result = analyze_source(
        "struct ListNode { int val; ListNode* next; }; "
        "ListNode* f(ListNode* head) { ListNode* cur=head; "
        "while (cur) cur=cur->next; return head; }",
        "cpp",
    )
    assert result.time_complexity == "O(n)"
    assert result.space_complexity == "O(1)"


def test_linked_list_visited_set_is_linear_space():
    result = analyze_source(
        "struct ListNode { int val; ListNode* next; }; "
        "bool f(ListNode* head) { unordered_set<ListNode*> visited; "
        "while (head) { if (visited.count(head)) return true; "
        "visited.insert(head); head=head->next; } return false; }",
        "cpp",
    )
    assert result.time_complexity == "O(n)"
    assert result.space_complexity == "O(n)"


def test_linked_list_python_value_buffer_is_linear_space():
    result = analyze_source(
        "class ListNode: pass\n"
        "def f(head):\n"
        "    values = []\n"
        "    cur = head\n"
        "    while cur:\n"
        "        values.append(cur.val)\n"
        "        cur = cur.next\n"
        "    return values == values[::-1]\n",
        "python",
    )
    assert result.time_complexity == "O(n)"
    assert result.space_complexity == "O(n)"


def test_linked_list_javascript_visited_set_is_linear_space():
    result = analyze_source(
        "function ListNode(value) { this.val = value; this.next = null; } "
        "function f(head) { const visited = new Set(); let cur = head; "
        "while (cur) { visited.add(cur); cur = cur.next; } return false; }",
        "javascript",
    )
    assert result.time_complexity == "O(n)"
    assert result.space_complexity == "O(n)"


def test_generic_node_type_with_next_field_is_not_misclassified_as_graph():
    result = analyze_source(
        "struct Node { int value; Node* next; }; "
        "bool f(Node* head) { unordered_set<Node*> visited; "
        "while (head) { visited.insert(head); head = head->next; } "
        "return false; }",
        "cpp",
    )
    assert result.time_complexity == "O(n)"
    assert result.space_complexity == "O(n)"
    assert "structural:single-linked-list-scan" in result.signals


def test_nested_vector_dimensions_preserve_time_and_space_exponents():
    cases = [
        (
            "int f(int n) { vector<vector<int>> a(n, vector<int>(n)); return a[0][0]; }",
            "O(n^2)",
        ),
        (
            "int f(int n) { vector<vector<vector<int>>> a(n, "
            "vector<vector<int>>(n, vector<int>(n))); return a[0][0][0]; }",
            "O(n^3)",
        ),
        (
            "int f(int n) { vector<vector<vector<vector<int>>>> a(n, "
            "vector<vector<vector<int>>>(n, vector<vector<int>>(n, "
            "vector<int>(n)))); return a[0][0][0][0]; }",
            "O(n^4)",
        ),
    ]
    for source, expected in cases:
        result = analyze_source(source, "cpp")
        assert result.time_complexity == expected
        assert result.space_complexity == expected


def test_nested_vector_input_type_is_not_counted_as_new_storage():
    result = analyze_source(
        "int f(vector<vector<int>>& a) { return a[0][0]; }",
        "cpp",
    )
    assert result.time_complexity == "O(1)"
    assert result.space_complexity == "O(1)"


def test_deduplicated_result_from_two_inputs_is_bounded_by_smaller_input():
    result = analyze_source(
        "vector<int> f(vector<int>& a, vector<int>& b) { vector<int> out; "
        "for (int x : a) for (int y : b) "
        "if (x == y && find(out.begin(), out.end(), x) == out.end()) "
        "{ out.push_back(x); break; } return out; }",
        "cpp",
    )
    assert result.time_complexity == "O(m*n)"
    assert result.space_complexity == "O(min(m,n))"
    assert "structural:deduplicated-two-input-result" in result.signals


def test_sequential_hash_loops_are_not_promoted_to_nested_depth():
    result = analyze_source(
        "string f(string s) { unordered_map<char,int> counts; "
        "for (char c : s) counts[c]++; "
        "vector<pair<char,int>> values(counts.begin(), counts.end()); "
        "sort(values.begin(), values.end()); string out; "
        "for (auto& value : values) out.append(value.second, value.first); "
        "return out; }",
        "cpp",
    )
    assert result.time_complexity == "O(n log n)"
    assert result.space_complexity == "O(n)"


def test_genuinely_nested_hash_scan_remains_quadratic():
    result = analyze_source(
        "int f(vector<int>& a) { unordered_set<int> seen; int total=0; "
        "for (int x : a) { for (int y : a) { "
        "if (seen.count(x+y)) total++; } seen.insert(x); } return total; }",
        "cpp",
    )
    assert result.time_complexity == "O(n^2)"


def test_sequential_scans_of_two_inputs_keep_additive_time_and_fixed_table_space():
    result = analyze_source(
        "bool f(string left, string right) { vector<int> counts(26, 0); "
        "for (char c : right) counts[c - 'a']++; "
        "for (char c : left) { if (--counts[c - 'a'] < 0) return false; } "
        "return true; }",
        "cpp",
    )
    assert result.time_complexity == "O(m+n)"
    assert result.space_complexity == "O(1)"
    assert "structural:sequential-independent-input-scans" in result.signals


@pytest.mark.parametrize("separator", [" ", "\n", "\n\n"])
@pytest.mark.parametrize("function_name", ["visit", "CountEntries"])
def test_disjoint_child_recursion_is_linear_not_exponential_in_strict_mode(separator, function_name):
    result = analyze_source(
        "struct Entry { Entry* first; Entry* second; };" + separator
        + f"int {function_name}(Entry* item) {{ if (!item) return 0; "
        + f"return 1 + {function_name}(item->first) + {function_name}(item->second); }}",
        "cpp",
        mode="structural",
    )
    assert result.time_complexity == "O(n)"
    assert result.space_complexity == "O(n)"
    assert "structural:disjoint-child-recursion" in result.signals


@pytest.mark.parametrize("arguments", ["item->first, item->first", "item->first, item->second"])
def test_ordinary_helper_calls_do_not_create_recursive_child_traversal(arguments):
    first, second = arguments.split(", ")
    result = analyze_source(
        "struct Entry { Entry* first; Entry* second; }; "
        "int value(Entry* item) { return item ? 1 : 0; } "
        f"int total(Entry* item) {{ return value({first}) + value({second}); }}",
        "cpp",
        mode="structural",
    )
    assert result.time_complexity == "O(1)"
    assert "structural:disjoint-child-recursion" not in result.signals


def test_single_progressing_recursion_is_linear_in_strict_mode():
    result = analyze_source(
        "int parse(const string& text, int index) { "
        "if (index >= text.size()) return 0; "
        "return text[index] + parse(text, index + 1); }",
        "cpp",
        mode="structural",
    )
    assert result.time_complexity == "O(n)"
    assert result.space_complexity == "O(n)"
    assert "structural:single-progressing-recursion" in result.signals



