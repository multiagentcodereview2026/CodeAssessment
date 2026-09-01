import os
from dotenv import load_dotenv
from groq import Groq

from schemas import CorrectnessResult


load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)




def analyze_correctness(
    problem: str,
    code: str,
    execution_results: str,
    language: str = "Python"
) -> CorrectnessResult:

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

- 100: All tests pass and no correctness issue is evident.
- 80-99: Mostly correct with minor edge-case failures.
- 50-79: Partially correct with significant failures.
- 1-49: Mostly incorrect.
- 0: Completely incorrect or unable to execute.

Return ONLY valid JSON matching this structure:

{{
    "passed_tests": integer,
    "total_tests": integer,
    "correctness_score": number,
    "is_correct": boolean,
    "issues": ["issue 1", "issue 2"],
    "explanation": "explanation",
    "confidence": number
}}
Important rules:

- Base correctness_score primarily on the observed execution results.
- Do not invent failed tests.
- If all observed tests pass, do not reduce the correctness score merely because
  you suspect an untested edge case.
- Instead, mention possible insufficient test coverage in coverage_warning.
- is_correct should indicate whether all observed tests passed.
- Use issues for concrete problems demonstrated by the execution results.
- Use coverage_warning for concerns that are not demonstrated by the current tests.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    result = response.choices[0].message.content

    return CorrectnessResult.model_validate_json(result)