import re
from datasets import load_dataset
from database import SessionLocal, engine, Base
import models

def clean_problem_name(name: str) -> str:
    """Creates a URL-safe ID from problem name."""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name.lower().strip())

def import_deepmind_code_contests(target_count=4000):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print(f"Connecting to Hugging Face 'deepmind/code_contests'...")
    # 'streaming=True' streams data on the fly without needing 30GB local disk space
    dataset = load_dataset("deepmind/code_contests", split="train", streaming=True)

    imported = 0
    for problem in dataset:
        if imported >= target_count:
            break

        name = problem.get("name", f"problem_{imported + 1}")
        prob_id = clean_problem_name(name)
        description = problem.get("description", "")
        
        if not description.strip():
            continue

        # Extract Public Test Cases (For Frontend Examples)
        public_tests = problem.get("public_tests", {})
        pub_inputs = public_tests.get("input", [])
        pub_outputs = public_tests.get("output", [])

        # Extract Private & Generated Hidden Test Cases (For Backend Sandbox)
        private_tests = problem.get("private_tests", {})
        priv_inputs = private_tests.get("input", [])
        priv_outputs = private_tests.get("output", [])

        gen_tests = problem.get("generated_tests", {})
        gen_inputs = gen_tests.get("input", [])
        gen_outputs = gen_tests.get("output", [])

        # Combine all test cases
        all_test_cases = []
        frontend_examples = []

        # 1. Add Public Tests (is_hidden = False)
        for idx, (inp, out) in enumerate(zip(pub_inputs, pub_outputs)):
            all_test_cases.append({
                "input": str(inp).strip(),
                "expected_output": str(out).strip(),
                "is_hidden": False
            })
            frontend_examples.append({
                "input": str(inp).strip(),
                "output": str(out).strip(),
                "explanation": f"Sample test case {idx + 1}"
            })

        # 2. Add Private & Generated Tests (is_hidden = True)
        all_hidden_inputs = priv_inputs + gen_inputs
        all_hidden_outputs = priv_outputs + gen_outputs

        for inp, out in zip(all_hidden_inputs, all_hidden_outputs):
            all_test_cases.append({
                "input": str(inp).strip(),
                "expected_output": str(out).strip(),
                "is_hidden": True
            })

        # Skip if no test cases exist
        if not all_test_cases:
            continue

        # Create database entry
        problem_entry = models.Problem(
            id=prob_id,
            title=name.replace("_", " ").title(),
            difficulty="Medium",
            category="Competitive Programming",
            description=description,
            examples=frontend_examples[:3] if frontend_examples else [{"input": "N/A", "output": "N/A", "explanation": "See problem statement"}],
            constraints=["Time limit: 2.0s", "Memory limit: 256MB"],
            starter_codes={
                "python": "# Write your Python solution here\n",
                "cpp": "// Write your C++ solution here\n#include <iostream>\nusing namespace std;\n\nint main() {\n    return 0;\n}\n"
            },
            test_cases=all_test_cases
        )

        db.merge(problem_entry)
        imported += 1

        if imported % 100 == 0:
            db.commit()
            print(f"Loaded {imported}/{target_count} problems into Databank...")

    db.commit()
    db.close()
    print(f" Successfully loaded {imported} problems from deepmind/code_contests into your Databank!")

if __name__ == "__main__":
    import_deepmind_code_contests(target_count=4000)