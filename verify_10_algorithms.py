#!/usr/bin/env python3
"""
AST Complexity Verification for 10 Algorithms
Run with: docker exec codeassessment-backend-1 python /app/verify_10_algorithms.py
"""
from analysis.ast_parser import ASTComplexityAnalyzer
from analysis.ast_engine import infer_complexity_from_ir

# 10 Problem Test Suite
test_cases = [
    {
        "name": "1. Two Sum",
        "language": "cpp",
        "code": """
vector<int> twoSum(vector<int>& nums, int target) {
    unordered_map<int, int> map;
    for (int i = 0; i < nums.size(); i++) {
        int complement = target - nums[i];
        if (map.find(complement) != map.end()) {
            return {map[complement], i};
        }
        map[nums[i]] = i;
    }
    return {};
}
""",
        "expected": ("O(n)", "O(n)")
    },
    {
        "name": "2. 3Sum",
        "language": "cpp",
        "code": """
vector<vector<int>> threeSum(vector<int>& nums) {
    sort(nums.begin(), nums.end());
    vector<vector<int>> result;
    for (int i = 0; i < nums.size(); i++) {
        int left = i + 1, right = nums.size() - 1;
        while (left < right) {
            int sum = nums[i] + nums[left] + nums[right];
            if (sum == 0) {
                result.push_back({nums[i], nums[left], nums[right]});
                left++; right--;
            } else if (sum < 0) left++;
            else right--;
        }
    }
    return result;
}
""",
        "expected": ("O(n^2)", "O(1)")
    },
    {
        "name": "3. 3Sum Closest",
        "language": "cpp",
        "code": """
int threeSumClosest(vector<int>& nums, int target) {
    sort(nums.begin(), nums.end());
    int closest = INT_MAX;
    int minDiff = INT_MAX;
    for (int i = 0; i < nums.size(); i++) {
        int left = i + 1, right = nums.size() - 1;
        while (left < right) {
            int sum = nums[i] + nums[left] + nums[right];
            int diff = abs(sum - target);
            if (diff < minDiff) {
                minDiff = diff;
                closest = sum;
            }
            if (sum < target) left++;
            else right--;
        }
    }
    return closest;
}
""",
        "expected": ("O(n^2)", "O(1)")
    },
    {
        "name": "4. 4Sum",
        "language": "cpp",
        "code": """
vector<vector<int>> fourSum(vector<int>& nums, int target) {
    sort(nums.begin(), nums.end());
    vector<vector<int>> result;
    for (int i = 0; i < nums.size(); i++) {
        for (int j = i + 1; j < nums.size(); j++) {
            int left = j + 1, right = nums.size() - 1;
            while (left < right) {
                long long sum = (long long)nums[i] + nums[j] + nums[left] + nums[right];
                if (sum == target) {
                    result.push_back({nums[i], nums[j], nums[left], nums[right]});
                    left++; right--;
                } else if (sum < target) left++;
                else right--;
            }
        }
    }
    return result;
}
""",
        "expected": ("O(n^3)", "O(1)")
    },
    {
        "name": "5. Median of Two Sorted Arrays",
        "language": "cpp",
        "code": """
double findMedianSortedArrays(vector<int>& nums1, vector<int>& nums2) {
    vector<int> merged;
    int i = 0, j = 0;
    while (i < nums1.size() && j < nums2.size()) {
        if (nums1[i] < nums2[j]) merged.push_back(nums1[i++]);
        else merged.push_back(nums2[j++]);
    }
    while (i < nums1.size()) merged.push_back(nums1[i++]);
    while (j < nums2.size()) merged.push_back(nums2[j++]);
    int n = merged.size();
    if (n % 2 == 1) return merged[n/2];
    return (merged[n/2-1] + merged[n/2]) / 2.0;
}
""",
        "expected": ("O(m+n)", "O(m+n)")
    },
    {
        "name": "6. Palindrome Number",
        "language": "cpp",
        "code": """
bool isPalindrome(int x) {
    if (x < 0 || (x % 10 == 0 && x != 0)) return false;
    int reversed = 0;
    while (x > reversed) {
        reversed = reversed * 10 + x % 10;
        x /= 10;
    }
    return x == reversed || x == reversed / 10;
}
""",
        "expected": ("O(log n)", "O(1)")
    },
    {
        "name": "7. Roman to Integer",
        "language": "cpp",
        "code": """
int romanToInt(string s) {
    unordered_map<char, int> vals = {{'I', 1}, {'V', 5}, {'X', 10}, {'L', 50}, {'C', 100}, {'D', 500}, {'M', 1000}};
    int total = 0;
    for (int i = 0; i < s.length(); i++) {
        if (i + 1 < s.length() && vals[s[i]] < vals[s[i+1]]) {
            total -= vals[s[i]];
        } else {
            total += vals[s[i]];
        }
    }
    return total;
}
""",
        "expected": ("O(n)", "O(1)")
    },
    {
        "name": "8. Container with Most Water",
        "language": "cpp",
        "code": """
int maxArea(vector<int>& height) {
    int maxA = 0;
    int left = 0, right = height.size() - 1;
    while (left < right) {
        int h = min(height[left], height[right]);
        int w = right - left;
        maxA = max(maxA, h * w);
        if (height[left] < height[right]) left++;
        else right--;
    }
    return maxA;
}
""",
        "expected": ("O(n)", "O(1)")
    },
    {
        "name": "9. Quicksort",
        "language": "cpp",
        "code": """
void quickSort(vector<int>& arr, int low, int high) {
    if (low < high) {
        int pi = partition(arr, low, high);
        quickSort(arr, low, pi - 1);
        quickSort(arr, pi + 1, high);
    }
}
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
""",
        "expected": ("O(n log n)", "O(log n)")
    },
    {
        "name": "10. Merge Sort",
        "language": "cpp",
        "code": """
void mergeSort(vector<int>& arr, int left, int right) {
    if (left < right) {
        int mid = left + (right - left) / 2;
        mergeSort(arr, left, mid);
        mergeSort(arr, mid + 1, right);
        merge(arr, left, mid, right);
    }
}
void merge(vector<int>& arr, int left, int mid, int right) {
    vector<int> temp(right - left + 1);
    int i = left, j = mid + 1, k = 0;
    while (i <= mid && j <= right) {
        if (arr[i] <= arr[j]) temp[k++] = arr[i++];
        else temp[k++] = arr[j++];
    }
    while (i <= mid) temp[k++] = arr[i++];
    while (j <= right) temp[k++] = arr[j++];
    for (i = left, k = 0; i <= right; i++, k++) {
        arr[i] = temp[k];
    }
}
""",
        "expected": ("O(n log n)", "O(n)")
    }
]

print("=" * 100)
print("AST COMPLEXITY VERIFICATION - 10 ALGORITHM TEST SUITE")
print("=" * 100)

passed = 0
failed = 0
results = []

for test in test_cases:
    name = test["name"]
    lang = test["language"]
    code = test["code"]
    exp_time, exp_space = test["expected"]

    analyzer = ASTComplexityAnalyzer(code, lang)
    ir = analyzer.analyze()

    if ir:
        complexity = infer_complexity_from_ir(ir)
        time_match = complexity.time_complexity == exp_time
        space_match = complexity.space_complexity == exp_space

        if time_match and space_match:
            status = "✅"
            passed += 1
        else:
            status = "⚠️ "
            failed += 1

        results.append((name, status, exp_time, complexity.time_complexity, exp_space, complexity.space_complexity))

        print(f"\n{status} {name}")
        print(f"   Time:  Expected {exp_time:<15} | Got {complexity.time_complexity:<15}")
        print(f"   Space: Expected {exp_space:<15} | Got {complexity.space_complexity:<15}")
    else:
        failed += 1
        results.append((name, "❌", exp_time, "FAILED", exp_space, "FAILED"))
        print(f"\n❌ {name} - AST parsing failed")

print("\n" + "=" * 100)
print(f"SUMMARY: {passed}/10 PERFECT MATCH | {failed}/10 WITH ISSUES")
print("=" * 100)

print("\n📊 DETAILED RESULTS TABLE:")
print("-" * 100)
print(f"{'Algorithm':<30} | {'Status':<5} | {'Expected Time':<15} | {'Got Time':<15} | {'Space Match':<10}")
print("-" * 100)
for name, status, exp_t, got_t, exp_s, got_s in results:
    space_ok = "✅" if exp_s == got_s else "❌"
    print(f"{name:<30} | {status:<5} | {exp_t:<15} | {got_t:<15} | {space_ok:<10}")
print("-" * 100)

if passed == 10:
    print("\n🎉 PERFECT! ALL 10 ALGORITHMS VERIFIED CORRECTLY!")
elif passed >= 8:
    print(f"\n✅ EXCELLENT! {passed}/10 algorithms verified correctly!")
elif passed >= 5:
    print(f"\n⚠️  MODERATE: {passed}/10 algorithms verified. Inference needs tuning for {failed} cases.")
else:
    print(f"\n⚠️  AST working but needs refinement. {passed}/10 perfect matches.")

print("\nTo copy-paste verification commands, see full output above.")
