import os

from dotenv import load_dotenv
from groq import Groq

from schemas import StyleResult


load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def analyze_style(problem, code, language):

    with open("prompts/style_prompt.txt", "r") as file:
        system_prompt = file.read()

    user_prompt = f"""
Problem:
{problem}

Programming Language:
{language}

Student Code:
{code}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        temperature=0
    )

    result = response.choices[0].message.content

    return StyleResult.model_validate_json(result)