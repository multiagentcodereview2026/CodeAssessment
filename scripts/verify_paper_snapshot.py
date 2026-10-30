"""Test an exact Git snapshot without checking it out or accessing the app DB.

Requires Git, Docker, and a backend image built with backend/requirements.txt.
The archived backend runs in a disposable container with no network or mounts.
"""
import argparse
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image", default="ai_codeassessment-backend")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    commit = subprocess.run(["git", "rev-parse", "--verify", args.commit + "^{commit}"],
                            cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    archive = subprocess.run(["git", "archive", commit, "backend"], cwd=root,
                             capture_output=True, check=True).stdout
    command = ["docker", "run", "--rm", "-i", "--network", "none", "--entrypoint", "sh",
               "-e", "DATABASE_URL=sqlite:////tmp/frozen-ci.db", "-e", "GROQ_API_KEY=",
               "-e", "GROQ_MIN_REQUEST_INTERVAL_SECONDS=0", args.image, "-c",
               "mkdir -p /tmp/frozen-source && tar -xf - -C /tmp/frozen-source "
               "&& cd /tmp/frozen-source/backend "
               "&& python -m pytest -q -p no:cacheprovider --disable-warnings --tb=short"]
    result = subprocess.run(command, input=archive, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    transcript = ("Frozen commit: " + commit + "\n"
                  "Scope: isolated container; no network, mounts, or application database access.\n"
                  + result.stdout.decode("utf-8", errors="replace"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(transcript, encoding="utf-8", newline="\n")
    print(transcript)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
