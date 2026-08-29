from services.evaluator import evaluate_submission


class TestCase:
    def __init__(
        self,
        id,
        input_data,
        expected_output
    ):
        self.id = id
        self.input_data = input_data
        self.expected_output = expected_output


test_cases = [
    TestCase(
        1,
        "10 20\n",
        "30"
    ),
    TestCase(
        2,
        "5 7\n",
        "12"
    )
]


code = """
a, b = map(int, input().split())
print(a + b)
"""


result = evaluate_submission(
    code=code,
    test_cases=test_cases
)


print(result)