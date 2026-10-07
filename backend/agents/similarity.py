import re
from typing import List, Dict, Any, Set
from pydantic import BaseModel
from agents.base import load_prompt, invoke_agent
from workflow.state import EvaluationState


class SimilarityOutput(BaseModel):
    similarity_score: float
    originality_score: float
    risk_level: str
    similar_submission_ids: List[str]
    reasoning: str
    flag_for_review: bool


def tokenize_code(code: str) -> Set[str]:
    """Tokenize and extract normalized 3-grams for robust structural similarity."""
    if not code:
        return set()
    # Remove single and multi-line comments
    cleaned = re.sub(r"//.*|/\*[\s\S]*?\*/|#.*", "", code)
    # Extract identifiers, operators, and literals
    tokens = re.findall(r"[A-Za-z_]\w*|[0-9]+|[^\s\w]", cleaned)
    if len(tokens) < 3:
        return set(tokens)
    # Generate 3-grams
    return {f"{tokens[i]}_{tokens[i+1]}_{tokens[i+2]}" for i in range(len(tokens) - 2)}


def calculate_jaccard_similarity(code_a: str, code_b: str) -> float:
    """Compute Jaccard similarity index percentage between two code snippets."""
    tokens_a = tokenize_code(code_a)
    tokens_b = tokenize_code(code_b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    if union == 0:
        return 0.0
    return round((intersection / union) * 100.0, 2)


def get_peer_submissions(problem_id: str, current_student_id: str | None = None, limit: int = 50) -> List[Dict[str, str]]:
    """Query recent peer submissions from the database for the given problem."""
    try:
        from database import SessionLocal
        import models

        db = SessionLocal()
        try:
            query = db.query(models.Submission.submission_id, models.Submission.code, models.Submission.student_id).filter(
                models.Submission.problem_id == problem_id
            )
            if current_student_id:
                query = query.filter(models.Submission.student_id != current_student_id)
            records = query.order_by(models.Submission.created_at.desc()).limit(limit).all()
            return [{"submission_id": r.submission_id, "code": r.code or ""} for r in records]
        finally:
            db.close()
    except Exception:
        return []


async def similarity_node(state: EvaluationState) -> Dict[str, Any]:
    prompt = load_prompt("similarity")
    source_code = state.get("submission", {}).get("source_code", "")
    language = state.get("submission", {}).get("language", "python")
    problem_id = str(state.get("problem", {}).get("id") or state.get("problem", {}).get("title") or "")
    current_student = state.get("user", {}).get("student_id")

    # Fetch peer submissions from database
    peers = get_peer_submissions(problem_id, current_student)

    max_sim = 0.0
    matching_ids: List[str] = []

    for peer in peers:
        sim = calculate_jaccard_similarity(source_code, peer["code"])
        if sim > max_sim:
            max_sim = sim
        if sim >= 65.0:
            matching_ids.append(peer["submission_id"])

    # Determine risk level and scores based on concrete comparison
    similarity_score = max_sim if peers else 10.0
    originality_score = max(0.0, round(100.0 - similarity_score, 2))

    if similarity_score >= 80.0:
        risk_level = "High"
        flag_for_review = True
        reasoning = f"High structural similarity ({similarity_score:.1f}%) detected with {len(matching_ids)} peer submission(s)."
    elif similarity_score >= 50.0:
        risk_level = "Medium"
        flag_for_review = False
        reasoning = f"Moderate code pattern overlap ({similarity_score:.1f}%) with common algorithmic structure."
    else:
        risk_level = "Low"
        flag_for_review = False
        reasoning = "Solution exhibits unique variable naming, logic flow, and structure with low peer similarity."

    fallback = {
        "similarity_score": similarity_score,
        "originality_score": originality_score,
        "risk_level": risk_level,
        "similar_submission_ids": matching_ids,
        "reasoning": reasoning,
        "flag_for_review": flag_for_review
    }

    payload = {
        "source_code": source_code,
        "language": language,
        "computed_similarity_score": similarity_score,
        "computed_risk_level": risk_level,
        "peer_matches_count": len(matching_ids),
    }

    result = await invoke_agent(prompt, payload, SimilarityOutput, fallback)
    # Ensure scores stay anchored to deterministic computation
    result["similarity_score"] = similarity_score
    result["originality_score"] = originality_score
    result["similar_submission_ids"] = matching_ids
    result["flag_for_review"] = flag_for_review

    return {
        "similarity_score": similarity_score,
        "similarity_details": result
    }
