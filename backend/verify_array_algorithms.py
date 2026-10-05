#!/usr/bin/env python3
"""
Array Algorithm Complexity Verification Suite
Tests 20+ array algorithms with TC/SC validation across C++, Python, Java
"""
import sys
from analysis.static_analyzer import analyze_source
from scoring.complexity import normalize_complexity

# 20+ Array Algorithm Test Cases
ARRAY_ALGORITHMS = {
    "linear_search": {
        "cpp": """
int linear_search(vector<int>& arr, int target) {
    for (int i = 0; i < arr.size(); i++) {
        if (arr[i] == target) return i;
    }
    return -1;
}
""",
        "python": """
def linear_search(arr, target):
    for i in range(len(arr)):
        if arr[i] == target:
            return i
    return -1
""",
        "java": """
public int linearSearch(int[] arr, int target) {
    for (int i = 0; i < arr.length; i++) {
        if (arr[i] == target) return i;
    }
    return -1;
}
""",
        "expected_tc": "O(n)",
        "expected_sc": "O(1)",
    },
    "reverse_array": {
        "cpp": """
void reverse_array(vector<int>& arr) {
    int n = arr.size();
    for (int i = 0; i < n / 2; i++) {
        swap(arr[i], arr[n - 1 - i]);
    }
}
""",
        "python": """
def reverse_array(arr):
    n = len(arr)
    for i in range(n // 2):
        arr[i], arr[n - 1 - i] = arr[n - 1 - i], arr[i]
""",
        "java": """
public void reverseArray(int[] arr) {
    int n = arr.length;
    for (int i = 0; i < n / 2; i++) {
        int temp = arr[i];
        arr[i] = arr[n - 1 - i];
        arr[n - 1 - i] = temp;
    }
}
""",
        "expected_tc": "O(n)",
        "expected_sc": "O(1)",
    },
    "find_max": {
        "cpp": """
int find_max(vector<int>& arr) {
    int max_val = arr[0];
    for (int i = 1; i < arr.size(); i++) {
        if (arr[i] > max_val) max_val = arr[i];
    }
    return max_val;
}
""",
        "python": """
def find_max(arr):
    max_val = arr[0]
    for i in range(1, len(arr)):
        if arr[i] > max_val:
            max_val = arr[i]
    return max_val
""",
        "java": """
public int findMax(int[] arr) {
    int maxVal = arr[0];
    for (int i = 1; i < arr.length; i++) {
        if (arr[i] > maxVal) maxVal = arr[i];
    }
    return maxVal;
}
""",
        "expected_tc": "O(n)",
        "expected_sc": "O(1)",
    },
    "array_sum": {
        "cpp": """
int array_sum(vector<int>& arr) {
    int sum = 0;
    for (int i = 0; i < arr.size(); i++) {
        sum += arr[i];
    }
    return sum;
}
""",
        "python": """
def array_sum(arr):
    sum_val = 0
    for i in range(len(arr)):
        sum_val += arr[i]
    return sum_val
""",
        "java": """
public int arraySum(int[] arr) {
    int sum = 0;
    for (int i = 0; i < arr.length; i++) {
        sum += arr[i];
    }
    return sum;
}
""",
        "expected_tc": "O(n)",
        "expected_sc": "O(1)",
    },
    "contains_duplicate": {
        "cpp": """
bool contains_duplicate(vector<int>& nums) {
    unordered_set<int> seen;
    for (int num : nums) {
        if (seen.count(num)) return true;
        seen.insert(num);
    }
    return false;
}
""",
        "python": """
def contains_duplicate(nums):
    seen = set()
    for num in nums:
        if num in seen:
            return True
        seen.add(num)
    return False
""",
        "java": """
public boolean containsDuplicate(int[] nums) {
    Set<Integer> seen = new HashSet<>();
    for (int num : nums) {
        if (seen.contains(num)) return true;
        seen.add(num);
    }
    return false;
}
""",
        "expected_tc": "O(n)",
        "expected_sc": "O(n)",
    },
    "remove_duplicates": {
        "cpp": """
int remove_duplicates(vector<int>& nums) {
    if (nums.size() == 0) return 0;
    int j = 0;
    for (int i = 1; i < nums.size(); i++) {
        if (nums[i] != nums[j]) {
            j++;
            nums[j] = nums[i];
        }
    }
    return j + 1;
}
""",
        "python": """
def remove_duplicates(nums):
    if len(nums) == 0:
        return 0
    j = 0
    for i in range(1, len(nums)):
        if nums[i] != nums[j]:
            j += 1
            nums[j] = nums[i]
    return j + 1
""",
        "java": """
public int removeDuplicates(int[] nums) {
    if (nums.length == 0) return 0;
    int j = 0;
    for (int i = 1; i < nums.length; i++) {
        if (nums[i] != nums[j]) {
            j++;
            nums[j] = nums[i];
        }
    }
    return j + 1;
}
""",
        "expected_tc": "O(n)",
        "expected_sc": "O(1)",
    },
    "rotate_array": {
        "cpp": """
void rotate_array(vector<int>& nums, int k) {
    int n = nums.size();
    k = k % n;
    vector<int> temp(k);
    for (int i = 0; i < k; i++) {
        temp[i] = nums[n - k + i];
    }
    for (int i = n - 1; i >= k; i--) {
        nums[i] = nums[i - k];
    }
    for (int i = 0; i < k; i++) {
        nums[i] = temp[i];
    }
}
""",
        "python": """
def rotate_array(nums, k):
    n = len(nums)
    k = k % n
    temp = nums[-k:]
    for i in range(n - 1, k - 1, -1):
        nums[i] = nums[i - k]
    for i in range(k):
        nums[i] = temp[i]
""",
        "java": """
public void rotateArray(int[] nums, int k) {
    int n = nums.length;
    k = k % n;
    int[] temp = new int[k];
    for (int i = 0; i < k; i++) {
        temp[i] = nums[n - k + i];
    }
    for (int i = n - 1; i >= k; i--) {
        nums[i] = nums[i - k];
    }
    for (int i = 0; i < k; i++) {
        nums[i] = temp[i];
    }
}
""",
        "expected_tc": "O(n)",
        "expected_sc": "O(k)",
    },
    "move_zeros": {
        "cpp": """
void move_zeros(vector<int>& nums) {
    int j = 0;
    for (int i = 0; i < nums.size(); i++) {
        if (nums[i] != 0) {
            swap(nums[i], nums[j]);
            j++;
        }
    }
}
""",
        "python": """
def move_zeros(nums):
    j = 0
    for i in range(len(nums)):
        if nums[i] != 0:
            nums[i], nums[j] = nums[j], nums[i]
            j += 1
""",
        "java": """
public void moveZeros(int[] nums) {
    int j = 0;
    for (int i = 0; i < nums.length; i++) {
        if (nums[i] != 0) {
            int temp = nums[i];
            nums[i] = nums[j];
            nums[j] = temp;
            j++;
        }
    }
}
""",
        "expected_tc": "O(n)",
        "expected_sc": "O(1)",
    },
    "product_except_self": {
        "cpp": """
vector<int> product_except_self(vector<int>& nums) {
    int n = nums.size();
    vector<int> result(n);
    result[0] = 1;
    for (int i = 1; i < n; i++) {
        result[i] = result[i - 1] * nums[i - 1];
    }
    int right = 1;
    for (int i = n - 1; i >= 0; i--) {
        result[i] *= right;
        right *= nums[i];
    }
    return result;
}
""",
        "python": """
def product_except_self(nums):
    n = len(nums)
    result = [1] * n
    for i in range(1, n):
        result[i] = result[i - 1] * nums[i - 1]
    right = 1
    for i in range(n - 1, -1, -1):
        result[i] *= right
        right *= nums[i]
    return result
""",
        "java": """
public int[] productExceptSelf(int[] nums) {
    int n = nums.length;
    int[] result = new int[n];
    result[0] = 1;
    for (int i = 1; i < n; i++) {
        result[i] = result[i - 1] * nums[i - 1];
    }
    int right = 1;
    for (int i = n - 1; i >= 0; i--) {
        result[i] *= right;
        right *= nums[i];
    }
    return result;
}
""",
        "expected_tc": "O(n)",
        "expected_sc": "O(n)",
    },
    "max_subarray": {
        "cpp": """
int max_subarray(vector<int>& nums) {
    int max_sum = nums[0];
    int current_sum = nums[0];
    for (int i = 1; i < nums.size(); i++) {
        current_sum = max(nums[i], current_sum + nums[i]);
        max_sum = max(max_sum, current_sum);
    }
    return max_sum;
}
""",
        "python": """
def max_subarray(nums):
    max_sum = nums[0]
    current_sum = nums[0]
    for i in range(1, len(nums)):
        current_sum = max(nums[i], current_sum + nums[i])
        max_sum = max(max_sum, current_sum)
    return max_sum
""",
        "java": """
public int maxSubarray(int[] nums) {
    int maxSum = nums[0];
    int currentSum = nums[0];
    for (int i = 1; i < nums.length; i++) {
        currentSum = Math.max(nums[i], currentSum + nums[i]);
        maxSum = Math.max(maxSum, currentSum);
    }
    return maxSum;
}
""",
        "expected_tc": "O(n)",
        "expected_sc": "O(1)",
    },
    "first_missing_positive": {
        "cpp": """
int first_missing_positive(vector<int>& nums) {
    unordered_set<int> num_set(nums.begin(), nums.end());
    int missing = 1;
    while (num_set.count(missing)) {
        missing++;
    }
    return missing;
}
""",
        "python": """
def first_missing_positive(nums):
    num_set = set(nums)
    missing = 1
    while missing in num_set:
        missing += 1
    return missing
""",
        "java": """
public int firstMissingPositive(int[] nums) {
    Set<Integer> numSet = new HashSet<>();
    for (int num : nums) numSet.add(num);
    int missing = 1;
    while (numSet.contains(missing)) {
        missing++;
    }
    return missing;
}
""",
        "expected_tc": "O(n)",
        "expected_sc": "O(n)",
    },
    "merge_sorted_arrays": {
        "cpp": """
vector<int> merge_sorted_arrays(vector<int>& arr1, vector<int>& arr2) {
    vector<int> result;
    int i = 0, j = 0;
    while (i < arr1.size() && j < arr2.size()) {
        if (arr1[i] <= arr2[j]) {
            result.push_back(arr1[i++]);
        } else {
            result.push_back(arr2[j++]);
        }
    }
    while (i < arr1.size()) result.push_back(arr1[i++]);
    while (j < arr2.size()) result.push_back(arr2[j++]);
    return result;
}
""",
        "python": """
def merge_sorted_arrays(arr1, arr2):
    result = []
    i = j = 0
    while i < len(arr1) and j < len(arr2):
        if arr1[i] <= arr2[j]:
            result.append(arr1[i])
            i += 1
        else:
            result.append(arr2[j])
            j += 1
    result.extend(arr1[i:])
    result.extend(arr2[j:])
    return result
""",
        "java": """
public int[] mergeSortedArrays(int[] arr1, int[] arr2) {
    List<Integer> result = new ArrayList<>();
    int i = 0, j = 0;
    while (i < arr1.length && j < arr2.length) {
        if (arr1[i] <= arr2[j]) {
            result.add(arr1[i++]);
        } else {
            result.add(arr2[j++]);
        }
    }
    while (i < arr1.length) result.add(arr1[i++]);
    while (j < arr2.length) result.add(arr2[j++]);
    return result.stream().mapToInt(x -> x).toArray();
}
""",
        "expected_tc": "O(n+m)",
        "expected_sc": "O(n+m)",
    },
    "search_rotated_sorted_array": {
        "cpp": """
int search_rotated_sorted_array(vector<int>& nums, int target) {
    int left = 0, right = nums.size() - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (nums[mid] == target) return mid;
        if (nums[left] <= nums[mid]) {
            if (target >= nums[left] && target < nums[mid]) {
                right = mid - 1;
            } else {
                left = mid + 1;
            }
        } else {
            if (target > nums[mid] && target <= nums[right]) {
                left = mid + 1;
            } else {
                right = mid - 1;
            }
        }
    }
    return -1;
}
""",
        "python": """
def search_rotated_sorted_array(nums, target):
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] == target:
            return mid
        if nums[left] <= nums[mid]:
            if target >= nums[left] and target < nums[mid]:
                right = mid - 1
            else:
                left = mid + 1
        else:
            if target > nums[mid] and target <= nums[right]:
                left = mid + 1
            else:
                right = mid - 1
    return -1
""",
        "java": """
public int searchRotatedSortedArray(int[] nums, int target) {
    int left = 0, right = nums.length - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (nums[mid] == target) return mid;
        if (nums[left] <= nums[mid]) {
            if (target >= nums[left] && target < nums[mid]) {
                right = mid - 1;
            } else {
                left = mid + 1;
            }
        } else {
            if (target > nums[mid] && target <= nums[right]) {
                left = mid + 1;
            } else {
                right = mid - 1;
            }
        }
    }
    return -1;
}
""",
        "expected_tc": "O(log n)",
        "expected_sc": "O(1)",
    },
    "min_rotated_sorted_array": {
        "cpp": """
int min_rotated_sorted_array(vector<int>& nums) {
    int left = 0, right = nums.size() - 1;
    while (left < right) {
        int mid = left + (right - left) / 2;
        if (nums[mid] > nums[right]) {
            left = mid + 1;
        } else {
            right = mid;
        }
    }
    return nums[left];
}
""",
        "python": """
def min_rotated_sorted_array(nums):
    left, right = 0, len(nums) - 1
    while left < right:
        mid = (left + right) // 2
        if nums[mid] > nums[right]:
            left = mid + 1
        else:
            right = mid
    return nums[left]
""",
        "java": """
public int minRotatedSortedArray(int[] nums) {
    int left = 0, right = nums.length - 1;
    while (left < right) {
        int mid = left + (right - left) / 2;
        if (nums[mid] > nums[right]) {
            left = mid + 1;
        } else {
            right = mid;
        }
    }
    return nums[left];
}
""",
        "expected_tc": "O(log n)",
        "expected_sc": "O(1)",
    },
    "longest_consecutive": {
        "cpp": """
int longest_consecutive(vector<int>& nums) {
    if (nums.empty()) return 0;
    unordered_set<int> num_set(nums.begin(), nums.end());
    int max_streak = 1;
    for (int num : num_set) {
        if (!num_set.count(num - 1)) {
            int current = num, streak = 1;
            while (num_set.count(current + 1)) {
                current++;
                streak++;
            }
            max_streak = max(max_streak, streak);
        }
    }
    return max_streak;
}
""",
        "python": """
def longest_consecutive(nums):
    if not nums:
        return 0
    num_set = set(nums)
    max_streak = 1
    for num in num_set:
        if num - 1 not in num_set:
            current = num
            streak = 1
            while current + 1 in num_set:
                current += 1
                streak += 1
            max_streak = max(max_streak, streak)
    return max_streak
""",
        "java": """
public int longestConsecutive(int[] nums) {
    if (nums.length == 0) return 0;
    Set<Integer> numSet = new HashSet<>();
    for (int num : nums) numSet.add(num);
    int maxStreak = 1;
    for (int num : numSet) {
        if (!numSet.contains(num - 1)) {
            int current = num, streak = 1;
            while (numSet.contains(current + 1)) {
                current++;
                streak++;
            }
            maxStreak = Math.max(maxStreak, streak);
        }
    }
    return maxStreak;
}
""",
        "expected_tc": "O(n)",
        "expected_sc": "O(n)",
    },
    "trap_water": {
        "cpp": """
int trap_water(vector<int>& height) {
    if (height.empty()) return 0;
    int n = height.size();
    vector<int> left(n), right(n);
    left[0] = height[0];
    for (int i = 1; i < n; i++) {
        left[i] = max(left[i - 1], height[i]);
    }
    right[n - 1] = height[n - 1];
    for (int i = n - 2; i >= 0; i--) {
        right[i] = max(right[i + 1], height[i]);
    }
    int water = 0;
    for (int i = 0; i < n; i++) {
        water += min(left[i], right[i]) - height[i];
    }
    return water;
}
""",
        "python": """
def trap_water(height):
    if not height:
        return 0
    n = len(height)
    left = [0] * n
    right = [0] * n
    left[0] = height[0]
    for i in range(1, n):
        left[i] = max(left[i - 1], height[i])
    right[n - 1] = height[n - 1]
    for i in range(n - 2, -1, -1):
        right[i] = max(right[i + 1], height[i])
    water = 0
    for i in range(n):
        water += min(left[i], right[i]) - height[i]
    return water
""",
        "java": """
public int trapWater(int[] height) {
    if (height.length == 0) return 0;
    int n = height.length;
    int[] left = new int[n];
    int[] right = new int[n];
    left[0] = height[0];
    for (int i = 1; i < n; i++) {
        left[i] = Math.max(left[i - 1], height[i]);
    }
    right[n - 1] = height[n - 1];
    for (int i = n - 2; i >= 0; i--) {
        right[i] = Math.max(right[i + 1], height[i]);
    }
    int water = 0;
    for (int i = 0; i < n; i++) {
        water += Math.min(left[i], right[i]) - height[i];
    }
    return water;
}
""",
        "expected_tc": "O(n)",
        "expected_sc": "O(n)",
    },
    "three_sum": {
        "cpp": """
vector<vector<int>> three_sum(vector<int>& nums) {
    set<vector<int>> result_set;
    sort(nums.begin(), nums.end());
    for (int i = 0; i < nums.size() - 2; i++) {
        int left = i + 1, right = nums.size() - 1;
        while (left < right) {
            int sum = nums[i] + nums[left] + nums[right];
            if (sum == 0) {
                result_set.insert({nums[i], nums[left], nums[right]});
                left++;
                right--;
            } else if (sum < 0) {
                left++;
            } else {
                right--;
            }
        }
    }
    vector<vector<int>> result(result_set.begin(), result_set.end());
    return result;
}
""",
        "python": """
def three_sum(nums):
    result_set = set()
    nums.sort()
    for i in range(len(nums) - 2):
        left, right = i + 1, len(nums) - 1
        while left < right:
            s = nums[i] + nums[left] + nums[right]
            if s == 0:
                result_set.add((nums[i], nums[left], nums[right]))
                left += 1
                right -= 1
            elif s < 0:
                left += 1
            else:
                right -= 1
    return [list(t) for t in result_set]
""",
        "java": """
public List<List<Integer>> threeSum(int[] nums) {
    Set<List<Integer>> resultSet = new HashSet<>();
    Arrays.sort(nums);
    for (int i = 0; i < nums.length - 2; i++) {
        int left = i + 1, right = nums.length - 1;
        while (left < right) {
            int sum = nums[i] + nums[left] + nums[right];
            if (sum == 0) {
                resultSet.add(Arrays.asList(nums[i], nums[left], nums[right]));
                left++;
                right--;
            } else if (sum < 0) {
                left++;
            } else {
                right--;
            }
        }
    }
    return new ArrayList<>(resultSet);
}
""",
        "expected_tc": "O(n^2)",
        "expected_sc": "O(1)",
    },
    "container_with_most_water": {
        "cpp": """
int container_with_most_water(vector<int>& height) {
    int left = 0, right = height.size() - 1;
    int max_area = 0;
    while (left < right) {
        int width = right - left;
        int h = min(height[left], height[right]);
        max_area = max(max_area, width * h);
        if (height[left] < height[right]) {
            left++;
        } else {
            right--;
        }
    }
    return max_area;
}
""",
        "python": """
def container_with_most_water(height):
    left, right = 0, len(height) - 1
    max_area = 0
    while left < right:
        width = right - left
        h = min(height[left], height[right])
        max_area = max(max_area, width * h)
        if height[left] < height[right]:
            left += 1
        else:
            right -= 1
    return max_area
""",
        "java": """
public int containerWithMostWater(int[] height) {
    int left = 0, right = height.length - 1;
    int maxArea = 0;
    while (left < right) {
        int width = right - left;
        int h = Math.min(height[left], height[right]);
        maxArea = Math.max(maxArea, width * h);
        if (height[left] < height[right]) {
            left++;
        } else {
            right--;
        }
    }
    return maxArea;
}
""",
        "expected_tc": "O(n)",
        "expected_sc": "O(1)",
    },
    "next_permutation": {
        "cpp": """
void next_permutation(vector<int>& nums) {
    int n = nums.size();
    int i = n - 2;
    while (i >= 0 && nums[i] >= nums[i + 1]) i--;
    if (i == -1) {
        sort(nums.begin(), nums.end());
        return;
    }
    int j = n - 1;
    while (j > i && nums[j] <= nums[i]) j--;
    swap(nums[i], nums[j]);
    sort(nums.begin() + i + 1, nums.end());
}
""",
        "python": """
def next_permutation(nums):
    i = len(nums) - 2
    while i >= 0 and nums[i] >= nums[i + 1]:
        i -= 1
    if i == -1:
        nums.sort()
        return
    j = len(nums) - 1
    while j > i and nums[j] <= nums[i]:
        j -= 1
    nums[i], nums[j] = nums[j], nums[i]
    nums[i + 1:] = sorted(nums[i + 1:])
""",
        "java": """
public void nextPermutation(int[] nums) {
    int i = nums.length - 2;
    while (i >= 0 && nums[i] >= nums[i + 1]) i--;
    if (i == -1) {
        Arrays.sort(nums);
        return;
    }
    int j = nums.length - 1;
    while (j > i && nums[j] <= nums[i]) j--;
    int temp = nums[i];
    nums[i] = nums[j];
    nums[j] = temp;
    Arrays.sort(nums, i + 1, nums.length);
}
""",
        "expected_tc": "O(n log n)",
        "expected_sc": "O(1)",
    },
    "sliding_window_max": {
        "cpp": """
vector<int> sliding_window_max(vector<int>& nums, int k) {
    vector<int> result;
    deque<int> dq;
    for (int i = 0; i < nums.size(); i++) {
        if (!dq.empty() && dq.front() < i - k + 1) {
            dq.pop_front();
        }
        while (!dq.empty() && nums[dq.back()] < nums[i]) {
            dq.pop_back();
        }
        dq.push_back(i);
        if (i >= k - 1) {
            result.push_back(nums[dq.front()]);
        }
    }
    return result;
}
""",
        "python": """
def sliding_window_max(nums, k):
    result = []
    dq = []
    for i in range(len(nums)):
        if dq and dq[0] < i - k + 1:
            dq.pop(0)
        while dq and nums[dq[-1]] < nums[i]:
            dq.pop()
        dq.append(i)
        if i >= k - 1:
            result.append(nums[dq[0]])
    return result
""",
        "java": """
public int[] slidingWindowMax(int[] nums, int k) {
    List<Integer> result = new ArrayList<>();
    Deque<Integer> dq = new LinkedList<>();
    for (int i = 0; i < nums.length; i++) {
        if (!dq.isEmpty() && dq.peekFirst() < i - k + 1) {
            dq.pollFirst();
        }
        while (!dq.isEmpty() && nums[dq.peekLast()] < nums[i]) {
            dq.pollLast();
        }
        dq.addLast(i);
        if (i >= k - 1) {
            result.add(nums[dq.peekFirst()]);
        }
    }
    return result.stream().mapToInt(x -> x).toArray();
}
""",
        "expected_tc": "O(n)",
        "expected_sc": "O(k)",
    },
}

def verify_algorithm(algo_name, code, language, expected_tc, expected_sc):
    """Verify TC/SC for a single algorithm"""
    print(f"\n{'='*75}")
    print(f"Algorithm: {algo_name.upper()} | Language: {language.upper()}")
    print(f"{'='*75}")

    try:
        result = analyze_source(code, language)
        detected_tc = normalize_complexity(result.time_complexity)
        detected_sc = normalize_complexity(result.space_complexity)

        tc_match = detected_tc == expected_tc
        sc_match = detected_sc == expected_sc
        overall_pass = tc_match and sc_match

        print(f"Expected TC: {expected_tc:<15} | Detected: {detected_tc:<15} | {'✓ PASS' if tc_match else '✗ FAIL'}")
        print(f"Expected SC: {expected_sc:<15} | Detected: {detected_sc:<15} | {'✓ PASS' if sc_match else '✗ FAIL'}")
        print(f"Confidence:  {result.confidence}")
        print(f"Method:      {result.method}")

        return overall_pass
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return False

def main():
    print("\n" + "="*75)
    print("ARRAY ALGORITHM COMPLEXITY VERIFICATION SUITE")
    print("Testing 20+ Array Algorithms Across C++, Python, Java")
    print("="*75)

    total_tests = 0
    passed_tests = 0

    for algo_name, algo_data in ARRAY_ALGORITHMS.items():
        expected_tc = algo_data["expected_tc"]
        expected_sc = algo_data["expected_sc"]

        for lang in ["cpp", "python", "java"]:
            if lang in algo_data:
                total_tests += 1
                if verify_algorithm(algo_name, algo_data[lang], lang, expected_tc, expected_sc):
                    passed_tests += 1

    # Summary
    print(f"\n{'='*75}")
    print(f"SUMMARY - ARRAY ALGORITHMS")
    print(f"{'='*75}")
    print(f"Total Algorithms:  {len(ARRAY_ALGORITHMS)}")
    print(f"Total Tests:       {total_tests}")
    print(f"Passed Tests:      {passed_tests}")
    print(f"Failed Tests:      {total_tests - passed_tests}")
    print(f"Pass Rate:         {(passed_tests/total_tests*100):.1f}%")
    print(f"{'='*75}\n")

    return 0 if passed_tests == total_tests else 1

if __name__ == "__main__":
    sys.exit(main())
