import {
  UserProfile,
  Problem,
  AssessmentResult,
  SubmissionItem,
  StudentProgress,
  StudentRosterItem,
  Assignment,
  SimilarityAlert,
  ReportItem
} from '../types';

export const MOCK_STUDENT_USER: UserProfile = {
  id: 'usr-student-01',
  name: 'Vignesh Reddy',
  email: 'vignesh@example.com',
  role: 'student',
  avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
  rollNumber: '21C51234',
  institution: 'Geethanjali College of Engg',
  department: 'CSE',
  year: '3rd Year'
};

export const MOCK_INSTRUCTOR_USER: UserProfile = {
  id: 'usr-inst-01',
  name: 'Prof. Sarah Miller',
  email: 's.miller@university.edu',
  role: 'instructor',
  avatar: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80',
  rollNumber: 'FAC-9082',
  institution: 'Geethanjali College of Engg',
  department: 'Computer Science & Engineering',
  year: 'Associate Professor'
};

export const MOCK_PROBLEMS: Problem[] = [
  {
    id: 'prob-1',
    title: 'Two Sum',
    slug: 'two-sum',
    difficulty: 'Easy',
    tags: ['Hash Map', 'Arrays', 'Two Pointers'],
    acceptanceRate: '54.2%',
    origin: 'instructor_assigned',
    assignmentId: 'asg-1',
    instructorName: 'Prof. Sarah Miller',
    dueDate: '10 May, 2026',
    studentStatus: 'In Progress',
    description: `Given an array of integers \`nums\` and an integer \`target\`, return *indices of the two numbers such that they add up to \`target\`*.

You may assume that each input would have ***exactly one solution***, and you may not use the *same* element twice.

You can return the answer in any order.`,
    examples: [
      {
        input: 'nums = [2,7,11,15], target = 9',
        output: '[0,1]',
        explanation: 'Because nums[0] + nums[1] == 9, we return [0, 1].'
      },
      {
        input: 'nums = [3,2,4], target = 6',
        output: '[1,2]',
        explanation: 'Because nums[1] + nums[2] == 6, we return [1, 2].'
      },
      {
        input: 'nums = [3,3], target = 6',
        output: '[0,1]'
      }
    ],
    constraints: [
      '2 <= nums.length <= 10^4',
      '-10^9 <= nums[i] <= 10^9',
      '-10^9 <= target <= 10^9',
      'Only one valid answer exists.'
    ],
    testCases: [
      {
        id: 'tc-1',
        input: 'nums = [2,7,11,15], target = 9',
        expectedOutput: '[0,1]'
      },
      {
        id: 'tc-2',
        input: 'nums = [3,2,4], target = 6',
        expectedOutput: '[1,2]'
      },
      {
        id: 'tc-3',
        input: 'nums = [3,3], target = 6',
        expectedOutput: '[0,1]'
      },
      {
        id: 'tc-4',
        input: 'nums = [1,5,8,10,14], target = 19',
        expectedOutput: '[1,4]',
        isHidden: true
      }
    ],
    starterCode: {
      'cpp': `class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        unordered_map<int, int> mp;
        for(int i = 0; i < nums.size(); i++) {
            int rem = target - nums[i];
            if(mp.find(rem) != mp.end()) {
                return {mp[rem], i};
            }
            mp[nums[i]] = i;
        }
        return {};
    }
};`,
      'python': `class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        seen = {}
        for i, num in enumerate(nums):
            diff = target - num
            if diff in seen:
                return [seen[diff], i]
            seen[num] = i
        return []`,
      'java': `class Solution {
    public int[] twoSum(int[] nums, int target) {
        Map<Integer, Integer> map = new HashMap<>();
        for (int i = 0; i < nums.length; i++) {
            int complement = target - nums[i];
            if (map.containsKey(complement)) {
                return new int[] { map.get(complement), i };
            }
            map.put(nums[i], i);
        }
        return new int[0];
    }
}`,
      'typescript': `function twoSum(nums: number[], target: number): number[] {
    const map = new Map<number, number>();
    for (let i = 0; i < nums.length; i++) {
        const diff = target - nums[i];
        if (map.has(diff)) {
            return [map.get(diff)!, i];
        }
        map.set(nums[i], i);
    }
    return [];
};`
    },
    solutionCode: {
      'cpp': `class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        unordered_map<int, int> numToIndex;
        numToIndex.reserve(nums.size());
        
        for (int currentIndex = 0; currentIndex < static_cast<int>(nums.size()); ++currentIndex) {
            int complement = target - nums[currentIndex];
            auto foundIt = numToIndex.find(complement);
            if (foundIt != numToIndex.end()) {
                return {foundIt->second, currentIndex};
            }
            numToIndex[nums[currentIndex]] = currentIndex;
        }
        return {};
    }
};`
    },
    optimalComplexity: {
      time: 'O(N)',
      space: 'O(N)'
    }
  },
  {
    id: 'prob-2',
    title: 'Binary Search',
    slug: 'binary-search',
    difficulty: 'Easy',
    tags: ['Binary Search', 'Arrays'],
    acceptanceRate: '56.8%',
    origin: 'instructor_assigned',
    assignmentId: 'asg-1',
    instructorName: 'Prof. Sarah Miller',
    dueDate: '10 May, 2026',
    studentStatus: 'Submitted',
    description: `Given an array of integers \`nums\` which is sorted in ascending order, and an integer \`target\`, write a function to search \`target\` in \`nums\`. If \`target\` exists, then return its index. Otherwise, return \`-1\`.

You must write an algorithm with \`O(log n)\` runtime complexity.`,
    examples: [
      {
        input: 'nums = [-1,0,3,5,9,12], target = 9',
        output: '4',
        explanation: '9 exists in nums and its index is 4'
      },
      {
        input: 'nums = [-1,0,3,5,9,12], target = 2',
        output: '-1',
        explanation: '2 does not exist in nums so return -1'
      }
    ],
    constraints: [
      '1 <= nums.length <= 10^4',
      '-10^4 < nums[i], target < 10^4',
      'All the integers in nums are unique.',
      'nums is sorted in ascending order.'
    ],
    testCases: [
      {
        id: 'tc-b1',
        input: 'nums = [-1,0,3,5,9,12], target = 9',
        expectedOutput: '4'
      },
      {
        id: 'tc-b2',
        input: 'nums = [-1,0,3,5,9,12], target = 2',
        expectedOutput: '-1'
      },
      {
        id: 'tc-b3',
        input: 'nums = [5], target = 5',
        expectedOutput: '0'
      }
    ],
    starterCode: {
      'cpp': `class Solution {
public:
    int search(vector<int>& nums, int target) {
        int left = 0;
        int right = nums.size() - 1;
        while (left <= right) {
            int mid = left + (right - left) / 2;
            if (nums[mid] == target) return mid;
            if (nums[mid] < target) left = mid + 1;
            else right = mid - 1;
        }
        return -1;
    }
};`,
      'python': `class Solution:
    def search(self, nums: list[int], target: int) -> int:
        left, right = 0, len(nums) - 1
        while left <= right:
            mid = (left + right) // 2
            if nums[mid] == target:
                return mid
            elif nums[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        return -1`
    },
    solutionCode: {},
    optimalComplexity: {
      time: 'O(log N)',
      space: 'O(1)'
    }
  },
  {
    id: 'prob-3',
    title: 'Reverse Linked List',
    slug: 'reverse-linked-list',
    difficulty: 'Easy',
    tags: ['Linked List', 'Recursion'],
    acceptanceRate: '74.1%',
    origin: 'instructor_assigned',
    assignmentId: 'asg-2',
    instructorName: 'Prof. Sarah Miller',
    dueDate: '20 May, 2026',
    studentStatus: 'Not Started',
    description: `Given the \`head\` of a singly linked list, reverse the list, and return the reversed list.`,
    examples: [
      {
        input: 'head = [1,2,3,4,5]',
        output: '[5,4,3,2,1]'
      },
      {
        input: 'head = [1,2]',
        output: '[2,1]'
      }
    ],
    constraints: [
      'The number of nodes in the list is the range [0, 5000].',
      '-5000 <= Node.val <= 5000'
    ],
    testCases: [
      {
        id: 'tc-r1',
        input: 'head = [1,2,3,4,5]',
        expectedOutput: '[5,4,3,2,1]'
      },
      {
        id: 'tc-r2',
        input: 'head = [1,2]',
        expectedOutput: '[2,1]'
      }
    ],
    starterCode: {
      'cpp': `class Solution {
public:
    ListNode* reverseList(ListNode* head) {
        ListNode* prev = nullptr;
        ListNode* curr = head;
        while (curr != nullptr) {
            ListNode* nextTemp = curr->next;
            curr->next = prev;
            prev = curr;
            curr = nextTemp;
        }
        return prev;
    }
};`
    },
    solutionCode: {},
    optimalComplexity: {
      time: 'O(N)',
      space: 'O(1)'
    }
  },
  {
    id: 'prob-4',
    title: 'Tree Inorder Traversal',
    slug: 'tree-inorder-traversal',
    difficulty: 'Easy',
    tags: ['Tree', 'Depth-First Search', 'Binary Tree'],
    acceptanceRate: '75.9%',
    origin: 'self_practice',
    studentStatus: 'Submitted',
    description: `Given the \`root\` of a binary tree, return the inorder traversal of its nodes' values.`,
    examples: [
      {
        input: 'root = [1,null,2,3]',
        output: '[1,3,2]'
      },
      {
        input: 'root = []',
        output: '[]'
      }
    ],
    constraints: [
      'The number of nodes in the tree is in the range [0, 100].',
      '-100 <= Node.val <= 100'
    ],
    testCases: [
      {
        id: 'tc-t1',
        input: 'root = [1,null,2,3]',
        expectedOutput: '[1,3,2]'
      }
    ],
    starterCode: {
      'cpp': `class Solution {
public:
    vector<int> inorderTraversal(TreeNode* root) {
        vector<int> res;
        inorder(root, res);
        return res;
    }
private:
    void inorder(TreeNode* node, vector<int>& res) {
        if (!node) return;
        inorder(node->left, res);
        res.push_back(node->val);
        inorder(node->right, res);
    }
};`
    },
    solutionCode: {},
    optimalComplexity: {
      time: 'O(N)',
      space: 'O(H)'
    }
  },
  {
    id: 'prob-5',
    title: 'Valid Parentheses',
    slug: 'valid-parentheses',
    difficulty: 'Easy',
    tags: ['Stack', 'String'],
    acceptanceRate: '40.3%',
    origin: 'self_practice',
    studentStatus: 'Not Started',
    description: `Given a string \`s\` containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.`,
    examples: [
      {
        input: 's = "()"',
        output: 'true'
      },
      {
        input: 's = "()[]{}"',
        output: 'true'
      },
      {
        input: 's = "(]"',
        output: 'false'
      }
    ],
    constraints: [
      '1 <= s.length <= 10^4',
      's consists of parentheses only \'()[]{}\'.'
    ],
    testCases: [
      {
        id: 'tc-vp1',
        input: 's = "()"',
        expectedOutput: 'true'
      }
    ],
    starterCode: {
      'cpp': `class Solution {
public:
    bool isValid(string s) {
        stack<char> st;
        for (char c : s) {
            if (c == '(' || c == '{' || c == '[') st.push(c);
            else {
                if (st.empty()) return false;
                char top = st.top();
                st.pop();
                if ((c == ')' && top != '(') ||
                    (c == '}' && top != '{') ||
                    (c == ']' && top != '[')) return false;
            }
        }
        return st.empty();
    }
};`
    },
    solutionCode: {},
    optimalComplexity: {
      time: 'O(N)',
      space: 'O(N)'
    }
  },
  {
    id: 'prob-6',
    title: 'Coin Change',
    slug: 'coin-change',
    difficulty: 'Medium',
    tags: ['Dynamic Programming', 'Breadth-First Search'],
    acceptanceRate: '42.8%',
    origin: 'self_practice',
    studentStatus: 'Not Started',
    description: `You are given an integer array \`coins\` representing coins of different denominations and an integer \`amount\` representing a total amount of money.

Return *the fewest number of coins that you need to make up that amount*. If that amount of money cannot be made up by any combination of the coins, return \`-1\`.`,
    examples: [
      {
        input: 'coins = [1,2,5], amount = 11',
        output: '3',
        explanation: '11 = 5 + 5 + 1'
      }
    ],
    constraints: [
      '1 <= coins.length <= 12',
      '1 <= coins[i] <= 2^31 - 1',
      '0 <= amount <= 10^4'
    ],
    testCases: [
      {
        id: 'tc-cc1',
        input: 'coins = [1,2,5], amount = 11',
        expectedOutput: '3'
      }
    ],
    starterCode: {
      'cpp': `class Solution {
public:
    int coinChange(vector<int>& coins, int amount) {
        vector<int> dp(amount + 1, amount + 1);
        dp[0] = 0;
        for (int i = 1; i <= amount; i++) {
            for (int coin : coins) {
                if (i >= coin) {
                    dp[i] = min(dp[i], dp[i - coin] + 1);
                }
            }
        }
        return dp[amount] > amount ? -1 : dp[amount];
    }
};`
    },
    solutionCode: {},
    optimalComplexity: {
      time: 'O(amount * coins.length)',
      space: 'O(amount)'
    }
  },
  {
    id: 'prob-7',
    title: 'Maximum Subarray',
    slug: 'maximum-subarray',
    difficulty: 'Medium',
    tags: ['Dynamic Programming', 'Divide and Conquer'],
    acceptanceRate: '50.1%',
    origin: 'self_practice',
    studentStatus: 'Not Started',
    description: `Given an integer array \`nums\`, find the subarray with the largest sum, and return its sum.`,
    examples: [
      {
        input: 'nums = [-2,1,-3,4,-1,2,1,-5,4]',
        output: '6',
        explanation: 'The subarray [4,-1,2,1] has the largest sum 6.'
      }
    ],
    constraints: [
      '1 <= nums.length <= 10^5',
      '-10^4 <= nums[i] <= 10^4'
    ],
    testCases: [
      {
        id: 'tc-ms1',
        input: 'nums = [-2,1,-3,4,-1,2,1,-5,4]',
        expectedOutput: '6'
      }
    ],
    starterCode: {
      'cpp': `class Solution {
public:
    int maxSubArray(vector<int>& nums) {
        int maxSum = nums[0];
        int currentSum = nums[0];
        for (size_t i = 1; i < nums.size(); ++i) {
            currentSum = max(nums[i], currentSum + nums[i]);
            maxSum = max(maxSum, currentSum);
        }
        return maxSum;
    }
};`
    },
    solutionCode: {},
    optimalComplexity: {
      time: 'O(N)',
      space: 'O(1)'
    }
  }
];

export const MOCK_DEFAULT_ASSESSMENT: AssessmentResult = {
  submissionId: 'SUB123456',
  problemId: 'prob-1',
  problemTitle: 'Two Sum',
  timestamp: '01 May, 10:30 AM',
  language: 'C++',
  isAssignedSubmission: true,
  code: `class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        unordered_map<int, int> mp;
        for(int i = 0; i < nums.size(); i++) {
            int rem = target - nums[i];
            if(mp.find(rem) != mp.end()) {
                return {mp[rem], i};
            }
            mp[nums[i]] = i;
        }
        return {};
    }
};`,
  status: 'Accepted',
  executionTime: '124 ms',
  memory: '5.2 MB',
  multiScores: {
    correctness: {
      score: 20,
      max: 25,
      notes: 'All public test cases passed. Edge case with duplicate negative keys passed without memory corruption.'
    },
    timeComplexity: {
      score: 18,
      max: 25,
      detected: 'O(N)',
      optimal: 'O(N)',
      notes: 'Optimal single-pass linear time lookup achieved with Hash Table.'
    },
    spaceComplexity: {
      score: 12,
      max: 15,
      detected: 'O(N)',
      optimal: 'O(N)',
      notes: 'Standard auxiliary hash map. Could pre-allocate capacity with mp.reserve() for large inputs.'
    },
    codeQuality: {
      score: 18,
      max: 20,
      styleScore: 9,
      structureScore: 9,
      notes: 'Clean structure. Short variable names ("mp", "rem") could be improved for enterprise style.'
    },
    similarity: {
      score: 17,
      max: 20,
      originalityPercent: 92,
      plagiarismRisk: 'Low',
      notes: 'High semantic originality. No direct duplication detected in peer cohort.'
    },
    overallScore: 85
  },
  explainableFeedback: 'Good use of HashMap to achieve optimal time complexity O(n). All edge cases passed successfully. Consider improving variable naming (e.g. `numToIndexMap`, `complement`) and pre-allocating hash bucket space for better readability and memory locality.',
  suggestedImprovements: [
    'Use descriptive variable names (e.g., replace `mp` with `numToIndexMap` and `rem` with `complement`)',
    'Add structured inline comments for better readability in collaborative reviews',
    'Consider reserve pre-allocation (`mp.reserve(nums.size())`) for large array bounds'
  ],
  recommendedTopics: ['Hash Map', 'Arrays', 'Two Pointers'],
  practiceProblems: [
    {
      id: 'prob-p1',
      title: '4Sum',
      difficulty: 'Medium',
      tags: ['Array', 'Two Pointers', 'Hash Table']
    },
    {
      id: 'prob-p2',
      title: 'Subarray Sum Equals K',
      difficulty: 'Medium',
      tags: ['Array', 'Hash Table', 'Prefix Sum']
    },
    {
      id: 'prob-p3',
      title: 'Complement of Base 10 Integer',
      difficulty: 'Easy',
      tags: ['Bit Manipulation']
    }
  ],
  scoreProjection: {
    currentScore: 85,
    projectedScore: 92,
    improvementDelta: 7,
    focusAreas: [
      'Optimize Space Complexity via bucket reservation',
      'Improve Code Readability & variable naming standards'
    ],
    iterationTimeline: [
      { stage: 'Initial Submission', score: 72, note: 'Brute force O(N^2) submission' },
      { stage: 'Revised Submission', score: 85, note: 'Linear hash map implementation' },
      { stage: 'AI Projected Score', score: 92, note: 'Target with styling & reserve optimization' },
      { stage: 'Final Target', score: 98, note: 'Zero-overhead cache locality' }
    ]
  },
  aiRevisedCode: `class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        std::unordered_map<int, int> numToIndexMap;
        numToIndexMap.reserve(nums.size());

        for (int currentIndex = 0; currentIndex < static_cast<int>(nums.size()); ++currentIndex) {
            const int complement = target - nums[currentIndex];
            
            auto mapIterator = numToIndexMap.find(complement);
            if (mapIterator != numToIndexMap.end()) {
                return {mapIterator->second, currentIndex};
            }
            
            numToIndexMap[nums[currentIndex]] = currentIndex;
        }

        return {}; // No solution found
    }
};`,
  testResults: [
    {
      id: 'tr-1',
      testCaseNumber: 1,
      input: 'nums = [2,7,11,15], target = 9',
      expectedOutput: '[0,1]',
      actualOutput: '[0,1]',
      passed: true,
      executionTimeMs: 4,
      memoryMb: 1.8
    },
    {
      id: 'tr-2',
      testCaseNumber: 2,
      input: 'nums = [3,2,4], target = 6',
      expectedOutput: '[1,2]',
      actualOutput: '[1,2]',
      passed: true,
      executionTimeMs: 3,
      memoryMb: 1.7
    },
    {
      id: 'tr-3',
      testCaseNumber: 3,
      input: 'nums = [3,3], target = 6',
      expectedOutput: '[0,1]',
      actualOutput: '[0,1]',
      passed: true,
      executionTimeMs: 2,
      memoryMb: 1.7
    }
  ]
};

export const MOCK_RECENT_SUBMISSIONS: SubmissionItem[] = [
  {
    id: 'sub-01',
    problemId: 'prob-1',
    problemTitle: 'Two Sum',
    score: 85,
    status: 'Passed',
    language: 'C++',
    date: '01 May, 10:30 AM',
    passedTestCases: 3,
    totalTestCases: 3,
    origin: 'instructor_assigned',
    assignmentId: 'asg-1',
    feedbackSummary: 'Good use of HashMap. Consider better variable names.'
  },
  {
    id: 'sub-02',
    problemId: 'prob-2',
    problemTitle: 'Binary Search',
    score: 70,
    status: 'Passed',
    language: 'C++',
    date: '01 May, 09:15 AM',
    passedTestCases: 3,
    totalTestCases: 3,
    origin: 'instructor_assigned',
    assignmentId: 'asg-1',
    feedbackSummary: 'Logic is correct. Try to handle edge cases clearly.'
  },
  {
    id: 'sub-03',
    problemId: 'prob-3',
    problemTitle: 'Reverse Linked List',
    score: 60,
    status: 'Partial',
    language: 'C++',
    date: '30 Apr, 05:40 PM',
    passedTestCases: 1,
    totalTestCases: 2,
    origin: 'instructor_assigned',
    assignmentId: 'asg-2',
    feedbackSummary: 'Check null conditions while reversing the list.'
  },
  {
    id: 'sub-04',
    problemId: 'prob-4',
    problemTitle: 'Tree Inorder Traversal',
    score: 90,
    status: 'Passed',
    language: 'C++',
    date: '30 Apr, 07:20 PM',
    passedTestCases: 1,
    totalTestCases: 1,
    origin: 'self_practice',
    feedbackSummary: 'Efficient solution! Good recursive approach.'
  },
  {
    id: 'sub-05',
    problemId: 'prob-5',
    problemTitle: 'Valid Parentheses',
    score: 80,
    status: 'Passed',
    language: 'C++',
    date: '29 Apr, 02:10 PM',
    passedTestCases: 1,
    totalTestCases: 1,
    origin: 'self_practice',
    feedbackSummary: 'Stack implemented properly. Consider early exit.'
  }
];

export const MOCK_STUDENT_PROGRESS: StudentProgress = {
  overallScore: 82.6,
  problemsSolved: 24,
  totalProblems: 30,
  currentStreak: 7,
  rankPercentile: 'Top 12%',
  progressPercent: 72,
  topicsCovered: 12,
  totalTopics: 18,
  hoursSpent: '18 h 45 m',
  weakTopics: ['Dynamic Programming', 'Graphs', 'Trees'],
  categoryWiseScores: [
    { name: 'Correctness', percentage: 28.5, color: '#3b82f6', scoreDisplay: '28.5%' },
    { name: 'Time Complexity', percentage: 18.7, color: '#06b6d4', scoreDisplay: '18.7%' },
    { name: 'Space Complexity', percentage: 14.5, color: '#f59e0b', scoreDisplay: '14.5%' },
    { name: 'Code Quality', percentage: 27.8, color: '#8b5cf6', scoreDisplay: '27.8%' },
    { name: 'Similarity (Originality)', percentage: 10.6, color: '#10b981', scoreDisplay: '10.6%' }
  ],
  scoreTrend: [
    { date: 'Apr 1', score: 65 },
    { date: 'Apr 8', score: 72 },
    { date: 'Apr 15', score: 70 },
    { date: 'Apr 22', score: 79 },
    { date: 'Apr 29', score: 85 }
  ]
};

export const MOCK_STUDENT_ROSTER: StudentRosterItem[] = [
  {
    id: 'stu-1',
    name: 'Vignesh Reddy',
    rollNumber: '21C51234',
    email: 'vignesh@example.com',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80',
    submissionsCount: 12,
    avgScore: 82.6,
    trend: 'up',
    weakTopics: ['DP', 'Graphs'],
    status: 'On Track',
    department: 'CSE',
    year: '3rd Year'
  },
  {
    id: 'stu-2',
    name: 'Arjun K.',
    rollNumber: '21C51208',
    email: 'arjun.k@example.com',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&auto=format&fit=crop&q=80',
    submissionsCount: 11,
    avgScore: 76.4,
    trend: 'up',
    weakTopics: ['Trees'],
    status: 'On Track',
    department: 'CSE',
    year: '3rd Year'
  },
  {
    id: 'stu-3',
    name: 'Sai Kiran',
    rollNumber: '21C51289',
    email: 'sai.kiran@example.com',
    avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&auto=format&fit=crop&q=80',
    submissionsCount: 10,
    avgScore: 68.2,
    trend: 'down',
    weakTopics: ['DP', 'Arrays'],
    status: 'Needs Attention',
    department: 'CSE',
    year: '3rd Year'
  },
  {
    id: 'stu-4',
    name: 'Harish N.',
    rollNumber: '21C51245',
    email: 'harish.n@example.com',
    avatar: 'https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=100&auto=format&fit=crop&q=80',
    submissionsCount: 9,
    avgScore: 64.1,
    trend: 'down',
    weakTopics: ['Graphs'],
    status: 'At Risk',
    department: 'CSE',
    year: '3rd Year'
  },
  {
    id: 'stu-5',
    name: 'Karthik P.',
    rollNumber: '21C51252',
    email: 'karthik.p@example.com',
    avatar: 'https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=100&auto=format&fit=crop&q=80',
    submissionsCount: 9,
    avgScore: 58.7,
    trend: 'down',
    weakTopics: ['DP', 'Math'],
    status: 'At Risk',
    department: 'CSE',
    year: '3rd Year'
  },
  {
    id: 'stu-6',
    name: 'Ananya Sharma',
    rollNumber: '21C51212',
    email: 'ananya.s@example.com',
    avatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=100&auto=format&fit=crop&q=80',
    submissionsCount: 14,
    avgScore: 92.4,
    trend: 'up',
    weakTopics: ['Bit Manipulation'],
    status: 'On Track',
    department: 'CSE',
    year: '3rd Year'
  }
];

export const MOCK_ASSIGNMENTS: Assignment[] = [
  {
    id: 'asg-1',
    title: 'DSA Assignment 1: Arrays & Hash Tables',
    description: 'Instructor assigned: Core arrays, two pointers, and hash table assessment with complexity constraints.',
    course: 'CSE-301 Data Structures',
    instructorName: 'Prof. Sarah Miller',
    problemsCount: 2,
    problemIds: ['prob-1', 'prob-2'],
    assignedProblems: [
      { problemId: 'prob-1', problemTitle: 'Two Sum', difficulty: 'Easy', studentStatus: 'In Progress' },
      { problemId: 'prob-2', problemTitle: 'Binary Search', difficulty: 'Easy', studentStatus: 'Submitted', score: 70 }
    ],
    submittedCount: 48,
    totalCount: 48,
    avgScore: 72.1,
    dueDate: '10 May, 2026',
    postedDate: '01 May, 2026',
    status: 'Active',
    studentStatus: 'In Progress'
  },
  {
    id: 'asg-2',
    title: 'Recursion & Pointer Manipulation',
    description: 'Instructor assigned: Linked list reversal and recursive stack bounds.',
    course: 'CSE-301 Data Structures',
    instructorName: 'Prof. Sarah Miller',
    problemsCount: 1,
    problemIds: ['prob-3'],
    assignedProblems: [
      { problemId: 'prob-3', problemTitle: 'Reverse Linked List', difficulty: 'Easy', studentStatus: 'Not Started' }
    ],
    submittedCount: 45,
    totalCount: 48,
    avgScore: 75.6,
    dueDate: '20 May, 2026',
    postedDate: '02 May, 2026',
    status: 'Active',
    studentStatus: 'Not Started'
  }
];

export const MOCK_SIMILARITY_ALERTS: SimilarityAlert[] = [
  {
    id: 'sim-1',
    problemId: 'prob-1',
    problemTitle: 'Two Sum',
    studentA: { id: 'stu-3', name: 'Sai Kiran', rollNumber: '21C51289', submissionId: 'SUB90112' },
    studentB: { id: 'stu-4', name: 'Harish N.', rollNumber: '21C51245', submissionId: 'SUB90119' },
    similarityPercentage: 89,
    riskLevel: 'High',
    matchedLinesCount: 14,
    timestamp: '30 Apr, 06:12 PM',
    studentACodeSnippet: `vector<int> twoSum(vector<int>& arr, int tar) {
    unordered_map<int,int> h;
    for(int idx = 0; idx < arr.size(); idx++) {
        int diff = tar - arr[idx];
        if(h.count(diff)) return {h[diff], idx};
        h[arr[idx]] = idx;
    }
    return {};
}`,
    studentBCodeSnippet: `vector<int> twoSum(vector<int>& arr, int tar) {
    unordered_map<int,int> h;
    for(int idx = 0; idx < arr.size(); idx++) {
        int diff = tar - arr[idx];
        if(h.count(diff)) return {h[diff], idx};
        h[arr[idx]] = idx;
    }
    return {};
}`,
    aiAuditNotes: 'Identical Abstract Syntax Tree (AST) node sequence and exact duplicate identifier patterns. Variable names "arr", "tar", "h", "idx" identical across both submissions with token match ratio > 0.88.'
  }
];

export const MOCK_REPORTS: ReportItem[] = [
  {
    id: 'rep-1',
    title: 'Class Performance Report',
    description: 'Comprehensive grade distributions, multi-agent score statistics, and test pass rates.',
    type: 'Performance',
    generatedDate: '01 May, 2026',
    fileSize: '2.4 MB',
    format: 'PDF'
  },
  {
    id: 'rep-2',
    title: 'Assignment Completion Report',
    description: 'Per-problem submission counts, submission timelines, and late penalty records.',
    type: 'Assignment',
    generatedDate: '30 Apr, 2026',
    fileSize: '1.8 MB',
    format: 'PDF'
  },
  {
    id: 'rep-3',
    title: 'Topic Wise Analytics Report',
    description: 'Cohort strengths and weakness metrics across Dynamic Programming, Graphs, and Hash Tables.',
    type: 'Topic',
    generatedDate: '28 Apr, 2026',
    fileSize: '890 KB',
    format: 'CSV'
  },
  {
    id: 'rep-4',
    title: 'At-Risk Students Action Report',
    description: 'Intervention list of students scoring below 65% with specific concept gap diagnosis.',
    type: 'At-Risk',
    generatedDate: '27 Apr, 2026',
    fileSize: '450 KB',
    format: 'PDF'
  }
];

export const MOCK_INSTRUCTOR_STATS = {
  totalStudents: 48,
  activeAssignments: 6,
  totalSubmissions: 152,
  averageScore: 74.3,
  highestScore: 96.2,
  lowestScore: 32.1,
  scoreDistribution: [
    { range: '0-20', count: 2, heightPercent: 12 },
    { range: '21-40', count: 5, heightPercent: 24 },
    { range: '41-60', count: 10, heightPercent: 55 },
    { range: '61-80', count: 18, heightPercent: 95 },
    { range: '81-100', count: 13, heightPercent: 72 }
  ]
};
