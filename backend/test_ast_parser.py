#!/usr/bin/env python3
"""
Test script to verify the rebuilt AST parser works correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.ast_parser import ASTComplexityAnalyzer
from analysis.complexity_ir import ComplexityIR


def test_simple_loop():
    """Test detection of simple loop."""
    code = """
int sum_array(vector<int>& arr) {
    int sum = 0;
    for (int i = 0; i < arr.size(); i++) {
        sum += arr[i];
    }
    return sum;
}
"""
    analyzer = ASTComplexityAnalyzer(code, "cpp")
    ir = analyzer.analyze()

    print("Test 1: Simple loop")
    print(f"  Loop depth: {ir.loop.depth}")
    print(f"  Loop structure: {ir.loop.structure}")
    print(f"  Loop bounds: {ir.loop.bounds}")
    print(f"  Has dynamic allocation: {ir.has_dynamic_allocation}")
    print(f"  Multiple input bounds: {ir.multiple_input_bounds}")
    print()


def test_nested_loops():
    """Test detection of nested loops."""
    code = """
void bubble_sort(vector<int>& arr) {
    int n = arr.size();
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n - i - 1; j++) {
            if (arr[j] > arr[j+1]) {
                swap(arr[j], arr[j+1]);
            }
        }
    }
}
"""
    analyzer = ASTComplexityAnalyzer(code, "cpp")
    ir = analyzer.analyze()

    print("Test 2: Nested loops (bubble sort)")
    print(f"  Loop depth: {ir.loop.depth}")
    print(f"  Loop structure: {ir.loop.structure}")
    print(f"  Loop bounds: {ir.loop.bounds}")
    print(f"  Distinct params: {ir.loop.distinct_params}")
    print()


def test_recursive_function():
    """Test detection of recursion."""
    code = """
int fibonacci(int n) {
    if (n <= 1) return n;
    return fibonacci(n-1) + fibonacci(n-2);
}
"""
    analyzer = ASTComplexityAnalyzer(code, "cpp")
    ir = analyzer.analyze()

    print("Test 3: Recursive function (Fibonacci)")
    print(f"  Is recursive: {ir.recursion.is_recursive}")
    print(f"  Branch factor: {ir.recursion.branch_factor}")
    print(f"  Pattern: {ir.recursion.pattern}")
    print(f"  Is divide and conquer: {ir.recursion.is_divide_and_conquer}")
    print()


def test_binary_search():
    """Test detection of binary search pattern."""
    code = """
int binary_search(vector<int>& nums, int target) {
    int left = 0, right = nums.size() - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (nums[mid] == target) return mid;
        if (nums[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}
"""
    analyzer = ASTComplexityAnalyzer(code, "cpp")
    ir = analyzer.analyze()

    print("Test 4: Binary search")
    print(f"  Has binary search: {ir.loop.has_binary_search}")
    print(f"  Is logarithmic step: {ir.loop.is_logarithmic_step}")
    print()


def test_heap_operations():
    """Test detection of heap operations."""
    code = """
int kth_smallest(vector<int>& nums, int k) {
    priority_queue<int> max_heap;
    for (int num : nums) {
        max_heap.push(num);
        if (max_heap.size() > k) {
            max_heap.pop();
        }
    }
    return max_heap.top();
}
"""
    analyzer = ASTComplexityAnalyzer(code, "cpp")
    ir = analyzer.analyze()

    print("Test 5: Heap operations")
    print(f"  Has heap operations: {ir.has_heap_operations}")
    print(f"  Loop has heap operations: {ir.loop.has_heap_operations}")
    print()


def test_matrix_bounds():
    """Test detection of matrix bounds."""
    code = """
int sum_matrix(vector<vector<int>>& matrix) {
    int sum = 0;
    for (int i = 0; i < matrix.size(); i++) {
        for (int j = 0; j < matrix[i].size(); j++) {
            sum += matrix[i][j];
        }
    }
    return sum;
}
"""
    analyzer = ASTComplexityAnalyzer(code, "cpp")
    ir = analyzer.analyze()

    print("Test 6: Matrix bounds")
    print(f"  Has matrix bounds (loop): {ir.loop.has_matrix_bounds}")
    print()


def test_dynamic_allocation():
    """Test detection of dynamic allocation."""
    code = """
vector<int> process_data(vector<int>& input) {
    vector<int> result;
    for (int x : input) {
        result.push_back(x * 2);
    }
    return result;
}
"""
    analyzer = ASTComplexityAnalyzer(code, "cpp")
    ir = analyzer.analyze()

    print("Test 7: Dynamic allocation")
    print(f"  Has dynamic allocation: {ir.has_dynamic_allocation}")
    print(f"  Has 2D allocation: {ir.has_2d_allocation}")
    print()


def test_graph_structure():
    """Test detection of graph structure."""
    code = """
void dfs(int node, vector<vector<int>>& graph, vector<bool>& visited) {
    visited[node] = true;
    for (int neighbor : graph[node]) {
        if (!visited[neighbor]) {
            dfs(neighbor, graph, visited);
        }
    }
}
"""
    analyzer = ASTComplexityAnalyzer(code, "cpp")
    ir = analyzer.analyze()

    print("Test 8: Graph structure")
    print(f"  Is graph: {ir.graph.is_graph}")
    print(f"  Graph structure: {ir.graph.structure}")
    print()


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Rebuilt AST Parser")
    print("=" * 60)
    print()

    tests = [
        test_simple_loop,
        test_nested_loops,
        test_recursive_function,
        test_binary_search,
        test_heap_operations,
        test_matrix_bounds,
        test_dynamic_allocation,
        test_graph_structure,
    ]

    passed = 0
    failed = 0

    for i, test in enumerate(tests, 1):
        try:
            test()
            passed += 1
            print(f"[OK] Test {i} passed\n")
        except Exception as e:
            failed += 1
            print(f"[FAIL] Test {i} failed: {e}\n")

    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("[SUCCESS] All tests passed! The AST parser is working correctly.")
    else:
        print("[WARNING] Some tests failed. Check the output above for details.")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)