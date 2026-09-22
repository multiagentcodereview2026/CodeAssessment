"""Trusted, language-neutral instructor assignments and judge cases.

Every assignment uses a complete-program stdin/stdout contract, so the same
case data works for C, C++, Java and Python.  Only the first three cases are
public; the remaining cases stay server-side in PostgreSQL.
"""


def _case(input_data: str, expected_output: str, *, hidden: bool) -> dict:
    return {
        "input": input_data,
        "expected_output": expected_output,
        "is_hidden": hidden,
        "time_limit": 2,
        "memory_limit": 256,
    }


EMPTY_PROGRAMS = {
    "c": "#include <stdio.h>\n\nint main(void) {\n    return 0;\n}\n",
    "cpp": "#include <iostream>\nusing namespace std;\n\nint main() {\n    return 0;\n}\n",
    "java": "import java.util.*;\n\npublic class Main {\n    public static void main(String[] args) {\n    }\n}\n",
    "python": "def main():\n    pass\n\nif __name__ == \"__main__\":\n    main()\n",
}


INSTRUCTOR_PROBLEMS = [
    {
        "id": "prob-1",
        "slug": "two-sum",
        "title": "Two Sum",
        "difficulty": "Easy",
        "category": "Arrays / Hashing",
        "target_time_complexity": "O(n)",
        "target_space_complexity": "O(n)",
        "complexity_reasoning": "One pass with a hash map storing previously seen values.",
        "course_code": "CS201",
        "due_date": "15 May, 2026",
        "description": """Given an array of integers and a target, print the zero-based indices of the two distinct elements whose sum equals the target. Exactly one valid pair exists. Print the smaller index first.

Platform Input/Output Format
The first line contains n. The second line contains n space-separated integers. The third line contains target. Print the two zero-based indices separated by one space. Write a complete program that reads standard input and writes standard output. Do not print explanatory text.""",
        "examples": [
            {"input": "4\n2 7 11 15\n9", "output": "0 1", "explanation": "nums[0] + nums[1] = 9."},
            {"input": "3\n3 2 4\n6", "output": "1 2", "explanation": "nums[1] + nums[2] = 6."},
        ],
        "constraints": [
            "2 <= n <= 10000",
            "-10^9 <= nums[i], target <= 10^9",
            "Exactly one valid answer exists.",
        ],
        "starter_codes": EMPTY_PROGRAMS,
        "source_url": None,
        "source_license": "Instructor-authored",
        "test_cases": [
            _case("4\n2 7 11 15\n9", "0 1", hidden=False),
            _case("3\n3 2 4\n6", "1 2", hidden=False),
            _case("2\n3 3\n6", "0 1", hidden=False),
            _case("5\n1 5 8 10 14\n19", "1 4", hidden=True),
            _case("5\n-3 4 3 90 7\n0", "0 2", hidden=True),
            _case("4\n-1 -2 -3 -4\n-6", "1 3", hidden=True),
            _case("6\n0 4 3 0 9 2\n0", "0 3", hidden=True),
            _case("3\n1000000000 -1000000000 5\n0", "0 1", hidden=True),
            _case("7\n1 2 3 4 5 6 7\n13", "5 6", hidden=True),
            _case("4\n8 1 2 7\n9", "0 1", hidden=True),
            _case("5\n2 8 12 15 1\n16", "3 4", hidden=True),
            _case("6\n-10 20 5 3 -2 8\n6", "4 5", hidden=True),
        ],
    },
    {
        "id": "prob-2",
        "slug": "binary-search",
        "title": "Binary Search",
        "difficulty": "Easy",
        "category": "Binary Search",
        "target_time_complexity": "O(log n)",
        "target_space_complexity": "O(1)",
        "complexity_reasoning": "Iterative binary search halves the remaining interval each step.",
        "course_code": "CS301",
        "due_date": "18 May, 2026",
        "description": """Given a sorted array of distinct integers and a target, print the zero-based index of the target. Print -1 when it is absent. Your solution should run in O(log n) time.

Platform Input/Output Format
The first line contains n. The second line contains n space-separated integers in ascending order. The third line contains target. Print one integer. Write a complete program that reads standard input and writes standard output. Do not print explanatory text.""",
        "examples": [
            {"input": "6\n-1 0 3 5 9 12\n9", "output": "4", "explanation": "9 is at index 4."},
            {"input": "6\n-1 0 3 5 9 12\n2", "output": "-1", "explanation": "2 is absent."},
        ],
        "constraints": [
            "1 <= n <= 10000",
            "-10^9 <= nums[i], target <= 10^9",
            "All values are distinct and sorted in ascending order.",
        ],
        "starter_codes": EMPTY_PROGRAMS,
        "source_url": None,
        "source_license": "Instructor-authored",
        "test_cases": [
            _case("6\n-1 0 3 5 9 12\n9", "4", hidden=False),
            _case("6\n-1 0 3 5 9 12\n2", "-1", hidden=False),
            _case("1\n5\n5", "0", hidden=False),
            _case("1\n5\n-5", "-1", hidden=True),
            _case("5\n1 2 3 4 5\n1", "0", hidden=True),
            _case("5\n1 2 3 4 5\n5", "4", hidden=True),
            _case("6\n-10 -3 0 7 11 20\n-10", "0", hidden=True),
            _case("6\n-10 -3 0 7 11 20\n20", "5", hidden=True),
            _case("6\n1 3 5 7 9 11\n6", "-1", hidden=True),
            _case("7\n-100 -50 -1 0 2 50 100\n0", "3", hidden=True),
            _case("8\n2 4 6 8 10 12 14 16\n14", "6", hidden=True),
            _case("4\n-8 -4 -2 -1\n-3", "-1", hidden=True),
        ],
    },
    {
        "id": "prob-3",
        "slug": "reverse-linked-list",
        "title": "Reverse Linked List",
        "difficulty": "Easy",
        "category": "Linked Lists",
        "target_time_complexity": "O(n)",
        "target_space_complexity": "O(1)",
        "complexity_reasoning": "Reverse each link once using a constant number of pointers.",
        "course_code": "CS201",
        "due_date": "21 May, 2026",
        "description": """The input values represent a singly linked list from head to tail. Reverse the list and print its values from the new head to the new tail.

Platform Input/Output Format
The first line contains n. When n is greater than zero, the second line contains n space-separated node values. Print the reversed values separated by one space. For an empty list, print an empty line. Write a complete program that reads standard input and writes standard output. Do not print explanatory text.""",
        "examples": [
            {"input": "5\n1 2 3 4 5", "output": "5 4 3 2 1", "explanation": "The links are reversed."},
            {"input": "2\n1 2", "output": "2 1", "explanation": "The new head is 2."},
        ],
        "constraints": [
            "0 <= n <= 5000",
            "-5000 <= node value <= 5000",
        ],
        "starter_codes": EMPTY_PROGRAMS,
        "source_url": None,
        "source_license": "Instructor-authored",
        "test_cases": [
            _case("5\n1 2 3 4 5", "5 4 3 2 1", hidden=False),
            _case("2\n1 2", "2 1", hidden=False),
            _case("0\n", "", hidden=False),
            _case("1\n42", "42", hidden=True),
            _case("4\n-1 -2 -3 -4", "-4 -3 -2 -1", hidden=True),
            _case("6\n1 1 2 2 3 3", "3 3 2 2 1 1", hidden=True),
            _case("5\n0 0 0 0 0", "0 0 0 0 0", hidden=True),
            _case("3\n5000 0 -5000", "-5000 0 5000", hidden=True),
            _case("7\n9 8 7 6 5 4 3", "3 4 5 6 7 8 9", hidden=True),
            _case("4\n10 20 30 40", "40 30 20 10", hidden=True),
            _case("8\n-2 4 -6 8 -10 12 -14 16", "16 -14 12 -10 8 -6 4 -2", hidden=True),
            _case("3\n7 7 7", "7 7 7", hidden=True),
        ],
    },
    {
        "id": "prob-5",
        "slug": "valid-parentheses",
        "title": "Valid Parentheses",
        "difficulty": "Easy",
        "category": "Stack / Queue",
        "target_time_complexity": "O(n)",
        "target_space_complexity": "O(n)",
        "complexity_reasoning": "Scan once and keep unmatched opening brackets on a stack.",
        "course_code": "CS201",
        "due_date": "25 May, 2026",
        "description": """Given a string containing only (), [] and {}, decide whether it is valid. Every opening bracket must be closed by the same type in the correct order.

Platform Input/Output Format
The input contains one non-empty bracket string on a single line. Print true when it is valid; otherwise print false. Write a complete program that reads standard input and writes standard output. Do not print explanatory text.""",
        "examples": [
            {"input": "()", "output": "true", "explanation": "The pair is balanced."},
            {"input": "()[]{}", "output": "true", "explanation": "All pairs close correctly."},
            {"input": "(]", "output": "false", "explanation": "The bracket types do not match."},
        ],
        "constraints": [
            "1 <= s.length <= 10000",
            "s contains only the characters ()[]{}.",
        ],
        "starter_codes": EMPTY_PROGRAMS,
        "source_url": None,
        "source_license": "Instructor-authored",
        "test_cases": [
            _case("()", "true", hidden=False),
            _case("()[]{}", "true", hidden=False),
            _case("(]", "false", hidden=False),
            _case("((", "false", hidden=True),
            _case("))", "false", hidden=True),
            _case("{[]}", "true", hidden=True),
            _case("([)]", "false", hidden=True),
            _case("(([]){})", "true", hidden=True),
            _case("[", "false", hidden=True),
            _case("]", "false", hidden=True),
            _case("([]{})", "true", hidden=True),
            _case("((((()))))", "true", hidden=True),
        ],
    },
]
