import os

from dotenv import load_dotenv
from groq import Groq

from schemas import CorrectnessResult


# Load environment variables from .env
load_dotenv()


# Create Groq client
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError(
        "GROQ_API_KEY was not found. "
        "Please add it to the .env file."
    )

client = Groq(api_key=api_key)


def analyze_correctness(
    problem: str,
    code: str,
    execution_results: str,
    language: str = "Python"
) -> CorrectnessResult:
    """
    Analyze the correctness of a student's code using
    the actual execution and test results.
    """

    prompt = f"""
You are a code correctness assessment agent.

Your task is to evaluate whether a student's submitted program
correctly solves the given programming problem.

You must rely primarily on the execution/test results provided.
Do not invent test results.

Programming Language:
{language}

Problem:
{problem}

Student Code:
{code}

Execution/Test Results:
{execution_results}

Evaluate:

1. Number of tests passed
2. Total number of tests
3. Overall correctness score from 0 to 100
4. Whether the solution is fully correct
5. Specific correctness issues
6. A concise explanation
7. Your confidence from 0 to 1

Scoring guideline:

- 100: All observed tests pass and no correctness issue is evident.
- 80-99: Mostly correct with minor observed failures.
- 50-79: Partially correct with significant observed failures.
- 1-49: Mostly incorrect.
- 0: Completely incorrect or unable to execute.

Return ONLY valid JSON matching this structure:

{{
    "passed_tests": 0,
    "total_tests": 0,
    "correctness_score": 0,
    "is_correct": false,
    "issues": [],
    "coverage_warning": "",
    "explanation": "",
    "confidence": 0
}}

Important rules:

- Base correctness_score primarily on the observed execution results.
- Do not invent failed tests.
- If all observed tests pass, do not reduce the correctness score merely because
  you suspect an untested edge case.
- Mention possible insufficient test coverage in coverage_warning.
- is_correct should indicate whether all observed tests passed.
- Use issues for concrete problems demonstrated by the execution results.
- Use coverage_warning for concerns that are not demonstrated by the current tests.
- passed_tests and total_tests must match the execution results.
- correctness_score must be a number between 0 and 100.
- confidence must be a number between 0 and 1.
- Return valid JSON only.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a JSON-only response generator. "
                    "Return only valid JSON matching the requested schema. "
                    "Do not use Markdown code fences."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    choice = response.choices[0]
    result = choice.message.content

    print("\n========== RAW CORRECTNESS RESPONSE ==========")
    print(repr(result))
    print("==============================================")

    if not result or not result.strip():
        print("Finish reason:", choice.finish_reason)

        raise ValueError(
            "Correctness agent returned an empty response from Groq."
        )

    try:
        return CorrectnessResult.model_validate_json(result)

    except Exception as error:
        print("\n========== INVALID CORRECTNESS JSON ==========")
        print(result)
        print("==============================================")

        raise ValueError(
            f"Correctness agent returned invalid JSON: {error}"
        ) from error