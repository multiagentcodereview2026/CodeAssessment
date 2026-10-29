"""Freeze allowlisted source and prompt hashes without reading datasets or keys."""
import argparse
import hashlib
import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path


def manifest(root: Path, commit: str, scope: str):
    root = root.resolve()
    hashes = {}
    directories = ["backend/agents", "backend/analysis", "backend/prompts", "backend/scoring", "backend/workflow", "backend/config", "frontend/src", ".github/workflows"]
    candidates = [root / "backend" / name for name in ("main.py", "schemas.py", "models.py", "database.py", "requirements.txt")]
    for directory in directories:
        folder = root / directory
        if folder.exists():
            candidates.extend(path for path in folder.rglob("*") if path.suffix in {".py", ".txt", ".ts", ".tsx", ".yml"})
    for path in sorted(set(candidates)):
        if path.is_file() and path.resolve().is_relative_to(root) and "__pycache__" not in path.parts:
            hashes[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    from config.settings import settings
    names = ["GROQ_MODEL", "AI_ALLOWED_CAPABILITIES", "GROQ_TIMEOUT_SECONDS", "GROQ_MIN_REQUEST_INTERVAL_SECONDS",
             "COMPLEXITY_AI_REVIEW_ENABLED", "COMPLEXITY_AST_DIRECT_CONFIDENCE", "COMPLEXITY_AI_MIN_CONFIDENCE",
             "SCORE_PROJECTION_TIMEOUT_SECONDS", "SCORE_PROJECTION_MAX_DRAFT_ATTEMPTS", "SCORE_PROJECTION_BACKGROUND_RETRIES"]
    safe_config = {name: getattr(settings, name) for name in names}
    fingerprint = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    return {"kind": "research_reproducibility_manifest", "commit": commit, "environment_scope": scope,
            "created_at_utc": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
            "platform": platform.system(), "architecture": platform.machine(), "logical_cpus": os.cpu_count(),
            "configuration": safe_config, "provider_configured": bool(settings.GROQ_API_KEY), "source_sha256": fingerprint, "files": hashes,
            "note": "No key, environment file, database or dataset contents are included. This manifest is not an accuracy result."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--scope", required=True, choices=["host_tooling", "running_backend", "isolated_verification_container"])
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = manifest(args.repo_root, args.commit, args.scope)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key not in {"files", "configuration"}}, indent=2))
