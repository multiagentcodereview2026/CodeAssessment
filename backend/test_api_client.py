from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_full_production_suite():
    print("\n--- 1. Testing GET /api/problems ---")
    res = client.get("/api/problems")
    assert res.status_code == 200
    problems = res.json()
    print(f"Loaded {len(problems)} problems from database.")
    assert len(problems) >= 3

    print("\n--- 2. Testing GET /api/problems/two-sum ---")
    p_res = client.get("/api/problems/two-sum")
    assert p_res.status_code == 200
    p_data = p_res.json()
    print("Title:", p_data["title"])
    print("Supported Starter Codes:", list(p_data["starter_codes"].keys()))

    print("\n--- 3. Testing POST /api/submissions/submit (10 Agents) ---")
    sub_payload = {
        "student_id": "24BD1A058Z",
        "problem_id": "two-sum",
        "language": "python",
        "code": "class Solution:\n    def twoSum(self, nums: list[int], target: int) -> list[int]:\n        seen = {}\n        for i, n in enumerate(nums):\n            if target - n in seen:\n                return [seen[target - n], i]\n            seen[n] = i\n        return []"
    }
    sub_res = client.post("/api/submissions/submit", json=sub_payload)
    assert sub_res.status_code == 200
    eval_data = sub_res.json()
    print("Submission ID   :", eval_data["submission_id"])
    print("Overall Score   :", eval_data["overall_score"])
    print("Correctness     :", eval_data["correctness_score"])
    print("Mentor Feedback :", eval_data["feedback"]["mentor_feedback"][:80] + "...")

    print("\n--- 4. Testing GET /api/submissions/{id} ---")
    get_sub = client.get(f"/api/submissions/{eval_data['submission_id']}")
    assert get_sub.status_code == 200
    print("Retrieved saved submission from DB successfully.")

    print("\n--- 5. Testing GET /api/analytics/student/24BD1A058Z ---")
    analytics_res = client.get("/api/analytics/student/24BD1A058Z")
    assert analytics_res.status_code == 200
    a_data = analytics_res.json()
    print("Overall Student Avg:", a_data["overall_score"])
    print("Streak Days        :", a_data["streak_days"])
    print("XP                 :", a_data["xp"])

    print("\n--- 6. Testing GET /api/instructor/overview ---")
    inst_res = client.get("/api/instructor/overview")
    assert inst_res.status_code == 200
    inst_data = inst_res.json()
    print("Total Enrolled Students:", inst_data["total_students"])
    print("Class Avg Score        :", inst_data["class_avg_score"])
    print("\n[ALL 6 PRODUCTION ENDPOINTS PASSED WITH 100% SUCCESS!]")

if __name__ == "__main__":
    test_full_production_suite()
