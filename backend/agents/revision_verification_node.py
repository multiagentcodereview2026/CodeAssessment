from agents.revision_verification import summarize_revision_verification, unverified_revision
from docker_runner.executor import execute_code_sandboxed
from workflow.state import EvaluationState


async def revision_verification_node(state: EvaluationState):
    """Verify AI-generated code without passing judge cases to any AI agent."""
    revision = state.get("improved_code") or {}
    if not isinstance(revision, dict) or revision.get("revision_source") != "ai":
        return {"improved_code": revision}
    code = str(revision.get("improved_code") or "").strip()
    test_cases = state.get("revision_test_cases") or []
    safe = dict(revision)
    if not code or not test_cases:
        safe["verification"] = unverified_revision("No judge cases were available to verify this generated draft.")
        return {"improved_code": safe}
    try:
        outcome = await execute_code_sandboxed(
            source_code=code,
            language=(state.get("submission") or {}).get("language", ""),
            test_cases=test_cases,
            stop_on_first_failure=False,
        )
        safe["verification"] = summarize_revision_verification(outcome)
    except Exception:
        safe["verification"] = unverified_revision("The judge was unavailable, so this generated draft could not be verified.")
    return {"improved_code": safe}
