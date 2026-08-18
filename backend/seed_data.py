import logging
from sqlalchemy.orm import Session
from database import engine, Base, SessionLocal
import models

logger = logging.getLogger(__name__)

INITIAL_STUDENTS = [
    {"student_id": "24BD1A058Z", "name": "Vignesh", "email": "vignesh@kmit.in", "xp": 420, "streak_days": 7},
    {"student_id": "24BD1A0586", "name": "Mani Greeva", "email": "manigreeva@kmit.in", "xp": 380, "streak_days": 5},
    {"student_id": "24BD1A058K", "name": "Nayaneesh", "email": "nayaneesh@kmit.in", "xp": 350, "streak_days": 4},
    {"student_id": "24BD1A058V", "name": "Pavan", "email": "pavan@kmit.in", "xp": 290, "streak_days": 3},
    {"student_id": "24BD1A059V", "name": "Karthikeya", "email": "karthikeya@kmit.in", "xp": 310, "streak_days": 4},
]

INITIAL_PROBLEMS = [
    {
        "id": "two-sum",
        "title": "Two Sum",
        "difficulty": "Easy",
        "category": "Arrays & Hashing",
        "description": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.\n\nYou may assume that each input would have exactly one solution, and you may not use the same element twice.\n\nYou can return the answer in any order.",
        "examples": [
            {"input": "nums = [2,7,11,15], target = 9", "output": "[0, 1]", "explanation": "Because nums[0] + nums[1] == 9, we return [0, 1]."},
            {"input": "nums = [3,2,4], target = 6", "output": "[1, 2]", "explanation": "Because nums[1] + nums[2] == 6, we return [1, 2]."}
        ],
        "constraints": [
            "2 <= nums.length <= 10^4",
            "-10^9 <= nums[i] <= 10^9",
            "-10^9 <= target <= 10^9",
            "Only one valid answer exists."
        ],
        "starter_codes": {
            "cpp": """class Solution {
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
};""",
            "python": """class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        seen = {}
        for i, num in enumerate(nums):
            complement = target - num
            if complement in seen:
                return [seen[complement], i]
            seen[num] = i
        return []""",
            "javascript": """var twoSum = function(nums, target) {
    const map = new Map();
    for (let i = 0; i < nums.length; i++) {
        const complement = target - nums[i];
        if (map.has(complement)) {
            return [map.get(complement), i];
        }
        map.set(nums[i], i);
    }
    return [];
};"""
        },
        "test_cases": [
            {"input": "2 7 11 15\n9", "expected_output": "[0, 1]", "is_hidden": False},
            {"input": "3 2 4\n6", "expected_output": "[1, 2]", "is_hidden": False},
            {"input": "3 3\n6", "expected_output": "[0, 1]", "is_hidden": True}
        ]
    },
    {
        "id": "binary-search",
        "title": "Binary Search",
        "difficulty": "Easy",
        "category": "Searching & Divide and Conquer",
        "description": "Given an array of integers nums which is sorted in ascending order, and an integer target, write a function to search target in nums. If target exists, then return its index. Otherwise, return -1.\n\nYou must write an algorithm with O(log n) runtime complexity.",
        "examples": [
            {"input": "nums = [-1,0,3,5,9,12], target = 9", "output": "4", "explanation": "9 exists in nums and its index is 4"},
            {"input": "nums = [-1,0,3,5,9,12], target = 2", "output": "-1", "explanation": "2 does not exist in nums so return -1"}
        ],
        "constraints": [
            "1 <= nums.length <= 10^4",
            "-10^4 < nums[i], target < 10^4",
            "All the integers in nums are unique.",
            "nums is sorted in ascending order."
        ],
        "starter_codes": {
            "cpp": """class Solution {
public:
    int search(vector<int>& nums, int target) {
        int left = 0, right = nums.size() - 1;
        while(left <= right) {
            int mid = left + (right - left) / 2;
            if(nums[mid] == target) return mid;
            if(nums[mid] < target) left = mid + 1;
            else right = mid - 1;
        }
        return -1;
    }
};""",
            "python": """class Solution:
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
        return -1""",
            "javascript": """var search = function(nums, target) {
    let left = 0, right = nums.length - 1;
    while (left <= right) {
        const mid = Math.floor((left + right) / 2);
        if (nums[mid] === target) return mid;
        if (nums[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
};"""
        },
        "test_cases": [
            {"input": "-1 0 3 5 9 12\n9", "expected_output": "4", "is_hidden": False},
            {"input": "-1 0 3 5 9 12\n2", "expected_output": "-1", "is_hidden": False}
        ]
    },
    {
        "id": "valid-parentheses",
        "title": "Valid Parentheses",
        "difficulty": "Easy",
        "category": "Stack",
        "description": "Given a string s containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.\n\nAn input string is valid if:\n1. Open brackets must be closed by the same type of brackets.\n2. Open brackets must be closed in the correct order.\n3. Every close bracket has a corresponding open bracket of the same type.",
        "examples": [
            {"input": "s = '()[]{}'", "output": "true", "explanation": "All brackets match and close properly."},
            {"input": "s = '(]'", "output": "false", "explanation": "Brackets do not match."}
        ],
        "constraints": [
            "1 <= s.length <= 10^4",
            "s consists of parentheses only '()[]{}'."
        ],
        "starter_codes": {
            "cpp": """class Solution {
public:
    bool isValid(string s) {
        stack<char> st;
        for(char c : s) {
            if(c == '(' || c == '{' || c == '[') st.push(c);
            else {
                if(st.empty()) return false;
                if(c == ')' && st.top() != '(') return false;
                if(c == '}' && st.top() != '{') return false;
                if(c == ']' && st.top() != '[') return false;
                st.pop();
            }
        }
        return st.empty();
    }
};""",
            "python": """class Solution:
    def isValid(self, s: str) -> bool:
        stack = []
        mapping = {')': '(', '}': '{', ']': '['}
        for char in s:
            if char in mapping:
                top = stack.pop() if stack else '#'
                if mapping[char] != top:
                    return False
            else:
                stack.append(char)
        return not stack""",
            "javascript": """var isValid = function(s) {
    const stack = [];
    const map = { ')': '(', '}': '{', ']': '[' };
    for (let char of s) {
        if (char in map) {
            if (stack.pop() !== map[char]) return false;
        } else {
            stack.push(char);
        }
    }
    return stack.length === 0;
};"""
        },
        "test_cases": [
            {"input": "()[]{}", "expected_output": "true", "is_hidden": False},
            {"input": "([)]", "expected_output": "false", "is_hidden": False}
        ]
    }
]

def seed_database():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        # Seed Students
        for s_data in INITIAL_STUDENTS:
            existing = db.query(models.Student).filter(models.Student.student_id == s_data["student_id"]).first()
            if not existing:
                db.add(models.Student(**s_data))

        # Seed Problems
        for p_data in INITIAL_PROBLEMS:
            existing = db.query(models.Problem).filter(models.Problem.id == p_data["id"]).first()
            if not existing:
                db.add(models.Problem(**p_data))
            else:
                for k, v in p_data.items():
                    setattr(existing, k, v)

        db.commit()
        print("Database seeded successfully with Problems and Students!")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
