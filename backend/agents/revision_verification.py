"""Safe, student-facing verification metadata for generated revisions."""

from __future__ import annotations

from typing import Any, Dict


def summarize_revision_verification(execution: Dict[str, Any] | None) -> Dict[str, Any]:
    """Return allowlisted metadata only; never persist a judge test's values."""
    execution = execution or {}
    compile_success = str(execution.get("compile_status") or "").lower() == "success"
    passed = int(execution.get("passed_cases") or 0)
    total = int(execution.get("total_cases") or 0)
    all_passed = compile_success and total > 0 and passed == total

    if all_passed:
        return {"status": "verified_passed", "verified": True, "compile_success": True, "passed_cases": passed, "total_cases": total, "message": "This suggested revision compiled and passed every evaluated case. Submit your own revision to receive an official score."}
    if not compile_success:
        return {"status": "verification_failed", "verified": True, "compile_success": False, "passed_cases": 0, "total_cases": total, "message": "This suggested revision did not compile, so it is not shown as a verified solution."}
    return {"status": "verification_failed", "verified": True, "compile_success": True, "passed_cases": passed, "total_cases": total, "message": "This suggested revision did not pass every evaluated case, so it is not shown as a verified solution."}


def unverified_revision(reason: str = "Verification was unavailable.") -> Dict[str, Any]:
    return {"status": "verification_unavailable", "verified": False, "compile_success": None, "passed_cases": None, "total_cases": None, "message": reason}
