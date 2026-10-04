#!/usr/bin/env python3
"""
CLI Verification Script for AST Complexity Analysis Engine
Tests 7+ algorithms across all supported languages with TC/SC validation
"""
import sys
from analysis.similarity_detector import compute_code_similarity
from analysis.static_analyzer import analyze_source
from scoring.complexity import normalize_complexity

# Define test algorithms with expected TC/SC
ALGORITHMS = {
    "binary_search": {
        "cpp": """
int binary_search(vector<int>& arr, int target) {
    int low = 0, right = arr.size() - 1;
    while (low <= right) {
        int mid = low + (right - low) / 2;
        if (arr[mid] == target) return mid;
        if (arr[mid] < target) low = mid + 1;
        else right = mid - 1;
    }
    return -1;
}
""",
        "python": """
def binary_search(arr, target):
    low, right = 0, len(arr) - 1
    while low <= right:
        mid = (low + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            right = mid - 1
    return -1
""",
        "java": """
public int binarySearch(int[] arr, int target) {
    int low = 0, right = arr.length - 1;
    while (low <= right) {
        int mid = low + (right - low) / 2;
        if (arr[mid] == target) return mid;
        if (arr[mid] < target) low = mid + 1;
        else right = mid - 1;
    }
    return -1;
}
""",
        "expected_tc": "O(log n)",
        "expected_sc": "O(1)",
    },
    "merge_sort": {
        "cpp": """
void merge_sort(vector<int>& arr, int left, int right) {
    if (left < right) {
        int mid = left + (right - left) / 2;
        merge_sort(arr, left, mid);
        merge_sort(arr, mid + 1, right);
        merge(arr, left, mid, right);
    }
}
void merge(vector<int>& arr, int left, int mid, int right) {
    vector<int> temp;
    int i = left, j = mid + 1;
    while (i <= mid && j <= right) {
        if (arr[i] <= arr[j]) temp.push_back(arr[i++]);
        else temp.push_back(arr[j++]);
    }
}
""",
        "python": """
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)
def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
""",
        "java": """
public void mergeSort(int[] arr, int left, int right) {
    if (left < right) {
        int mid = left + (right - left) / 2;
        mergeSort(arr, left, mid);
        mergeSort(arr, mid + 1, right);
        merge(arr, left, mid, right);
    }
}
private void merge(int[] arr, int left, int mid, int right) {
    int[] temp = new int[right - left + 1];
    int i = left, j = mid + 1, k = 0;
    while (i <= mid && j <= right) {
        if (arr[i] <= arr[j]) temp[k++] = arr[i++];
        else temp[k++] = arr[j++];
    }
}
""",
        "expected_tc": "O(n log n)",
        "expected_sc": "O(n)",
    },
    "two_sum": {
        "cpp": """
vector<int> two_sum(vector<int>& nums, int target) {
    unordered_map<int, int> m;
    for (int i = 0; i < nums.size(); i++) {
        int complement = target - nums[i];
        if (m.count(complement)) return {m[complement], i};
        m[nums[i]] = i;
    }
    return {};
}
""",
        "python": """
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
""",
        "java": """
public int[] twoSum(int[] nums, int target) {
    Map<Integer, Integer> map = new HashMap<>();
    for (int i = 0; i < nums.length; i++) {
        int complement = target - nums[i];
        if (map.containsKey(complement)) {
            return new int[]{map.get(complement), i};
        }
        map.put(nums[i], i);
    }
    return new int[]{};
}
""",
        "expected_tc": "O(n)",
        "expected_sc": "O(n)",
    },
    "bubble_sort": {
        "cpp": """
void bubble_sort(vector<int>& arr) {
    for (int i = 0; i < arr.size(); i++) {
        for (int j = 0; j < arr.size() - i - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                swap(arr[j], arr[j + 1]);
            }
        }
    }
}
""",
        "python": """
def bubble_sort(arr):
    for i in range(len(arr)):
        for j in range(len(arr) - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
""",
        "java": """
public void bubbleSort(int[] arr) {
    for (int i = 0; i < arr.length; i++) {
        for (int j = 0; j < arr.length - i - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                int temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }
}
""",
        "expected_tc": "O(n^2)",
        "expected_sc": "O(1)",
    },
    "dfs_graph": {
        "cpp": """
void dfs(vector<vector<int>>& adj, int node, vector<bool>& visited) {
    visited[node] = true;
    for (int neighbor : adj[node]) {
        if (!visited[neighbor]) {
            dfs(adj, neighbor, visited);
        }
    }
}
""",
        "python": """
def dfs(adj, node, visited):
    visited[node] = True
    for neighbor in adj[node]:
        if not visited[neighbor]:
            dfs(adj, neighbor, visited)
""",
        "java": """
public void dfs(List<List<Integer>> adj, int node, boolean[] visited) {
    visited[node] = true;
    for (int neighbor : adj.get(node)) {
        if (!visited[neighbor]) {
            dfs(adj, neighbor, visited);
        }
    }
}
""",
        "expected_tc": "O(V+E)",
        "expected_sc": "O(V)",
    },
    "quick_sort": {
        "cpp": """
int partition(vector<int>& arr, int low, int high) {
    int pivot = arr[high];
    int i = low - 1;
    for (int j = low; j < high; j++) {
        if (arr[j] < pivot) {
            i++;
            swap(arr[i], arr[j]);
        }
    }
    swap(arr[i + 1], arr[high]);
    return i + 1;
}
void quick_sort(vector<int>& arr, int low, int high) {
    if (low < high) {
        int pi = partition(arr, low, high);
        quick_sort(arr, low, pi - 1);
        quick_sort(arr, pi + 1, high);
    }
}
""",
        "python": """
def quick_sort(arr, low, high):
    if low < high:
        pi = partition(arr, low, high)
        quick_sort(arr, low, pi - 1)
        quick_sort(arr, pi + 1, high)
def partition(arr, low, high):
    pivot = arr[high]
    i = low - 1
    for j in range(low, high):
        if arr[j] < pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1
""",
        "java": """
public void quickSort(int[] arr, int low, int high) {
    if (low < high) {
        int pi = partition(arr, low, high);
        quickSort(arr, low, pi - 1);
        quickSort(arr, pi + 1, high);
    }
}
private int partition(int[] arr, int low, int high) {
    int pivot = arr[high];
    int i = low - 1;
    for (int j = low; j < high; j++) {
        if (arr[j] < pivot) {
            int temp = arr[++i];
            arr[i] = arr[j];
            arr[j] = temp;
        }
    }
    int temp = arr[i + 1];
    arr[i + 1] = arr[high];
    arr[high] = temp;
    return i + 1;
}
""",
        "expected_tc": "O(n log n)",
        "expected_sc": "O(log n)",
    },
    "fibonacci_memo": {
        "cpp": """
int fib(int n, unordered_map<int, int>& memo) {
    if (n <= 1) return n;
    if (memo.count(n)) return memo[n];
    memo[n] = fib(n - 1, memo) + fib(n - 2, memo);
    return memo[n];
}
""",
        "python": """
def fib(n, memo=None):
    if memo is None:
        memo = {}
    if n <= 1:
        return n
    if n in memo:
        return memo[n]
    memo[n] = fib(n - 1, memo) + fib(n - 2, memo)
    return memo[n]
""",
        "java": """
public int fib(int n, Map<Integer, Integer> memo) {
    if (n <= 1) return n;
    if (memo.containsKey(n)) return memo.get(n);
    memo.put(n, fib(n - 1, memo) + fib(n - 2, memo));
    return memo.get(n);
}
""",
        "expected_tc": "O(n)",
        "expected_sc": "O(n)",
    },
    "permutations": {
        "cpp": """
void permute(vector<int>& arr, int l, int r, vector<vector<int>>& result) {
    if (l == r) {
        result.push_back(arr);
    } else {
        for (int i = l; i <= r; i++) {
            swap(arr[l], arr[i]);
            permute(arr, l + 1, r, result);
            swap(arr[l], arr[i]);
        }
    }
}
""",
        "python": """
def permute(arr, l, r, result):
    if l == r:
        result.append(arr[:])
    else:
        for i in range(l, r + 1):
            arr[l], arr[i] = arr[i], arr[l]
            permute(arr, l + 1, r, result)
            arr[l], arr[i] = arr[i], arr[l]
""",
        "java": """
public void permute(int[] arr, int l, int r, List<List<Integer>> result) {
    if (l == r) {
        List<Integer> perm = new ArrayList<>();
        for (int x : arr) perm.add(x);
        result.add(perm);
    } else {
        for (int i = l; i <= r; i++) {
            int temp = arr[l];
            arr[l] = arr[i];
            arr[i] = temp;
            permute(arr, l + 1, r, result);
            temp = arr[l];
            arr[l] = arr[i];
            arr[i] = temp;
        }
    }
}
""",
        "expected_tc": "O(n!)",
        "expected_sc": "O(n)",
    },
}

def verify_algorithm(algo_name, code, language, expected_tc, expected_sc):
    """Verify TC/SC for a single algorithm"""
    print(f"\n{'='*70}")
    print(f"Algorithm: {algo_name.upper()} | Language: {language.upper()}")
    print(f"{'='*70}")

    try:
        result = analyze_source(code, language)
        detected_tc = normalize_complexity(result.time_complexity)
        detected_sc = normalize_complexity(result.space_complexity)

        print(f"Expected TC: {expected_tc:<15} | Detected: {detected_tc:<15} | {'✓ PASS' if detected_tc == expected_tc else '✗ FAIL'}")
        print(f"Expected SC: {expected_sc:<15} | Detected: {detected_sc:<15} | {'✓ PASS' if detected_sc == expected_sc else '✗ FAIL'}")
        print(f"Confidence:  {result.confidence}")
        print(f"Method:      {result.method}")

        return detected_tc == expected_tc and detected_sc == expected_sc
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return False

def main():
    print("\n" + "="*70)
    print("AST COMPLEXITY ANALYSIS VERIFICATION SUITE")
    print("Testing 7+ Algorithms Across All Languages")
    print("="*70)

    total_tests = 0
    passed_tests = 0

    for algo_name, algo_data in ALGORITHMS.items():
        expected_tc = algo_data["expected_tc"]
        expected_sc = algo_data["expected_sc"]

        for lang in ["cpp", "python", "java"]:
            if lang in algo_data:
                total_tests += 1
                if verify_algorithm(algo_name, algo_data[lang], lang, expected_tc, expected_sc):
                    passed_tests += 1

    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"Total Tests:   {total_tests}")
    print(f"Passed Tests:  {passed_tests}")
    print(f"Failed Tests:  {total_tests - passed_tests}")
    print(f"Pass Rate:     {(passed_tests/total_tests*100):.1f}%")
    print(f"{'='*70}\n")

    return 0 if passed_tests == total_tests else 1

if __name__ == "__main__":
    sys.exit(main())
