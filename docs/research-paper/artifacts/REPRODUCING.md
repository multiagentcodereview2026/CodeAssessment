# Paper artifact release

Use the immutable tag `paper-artifacts-20261030` for the manuscript, synthetic
data and evidence. Clone the repository with full history; a shallow checkout
may omit the earlier snapshots needed by the verification helper.

## Exact versions

| Purpose | Git commit | Release tag | Verified backend result |
| --- | --- | --- | --- |
| Earlier public version | 317152b61c4aad89eac9962470a0582595751df1 | Not the paper snapshot | 324 passed in its recorded run |
| Paper implementation | d4cdb86aa95d99f544d5e3253bf116eeeac87b24 | paper-implementation-20261030 | 333 passed in a fresh archived-snapshot run |
| Scoring-rule experiment | 7ddc4aa08e4ff3a7a0d4c2701c44fe41121042f0 | paper-scoring-experiment-20261030 | Five targeted experiment/audit tests passed |
| Later source snapshot | 21aa1b7e18ca035407ff7580abf37b3311ae5ae6 | Included in release history | 336 passed in its separate archived-snapshot run |

The manuscript's 333 count belongs to the specified implementation commit.
The 315 count in older development notes belongs to 41be983; do not combine
test counts across revisions or treat them as research accuracy.

## Data and provenance

`pilot.jsonl` contains twenty original AI-assisted synthetic function snippets
from two problem groups across five languages. Input arrays are supplied by a
caller; auxiliary space excludes the input and includes stack use. Search inputs
are sorted ascending. This is not a real-student or expert-reviewed benchmark.

`proposals-a.jsonl` and `proposals-b.jsonl` export only normalized AI-proposed
time and space labels with canonical identifiers and hashes. They are not raw
review files or authenticated independent expert labels. Source identities,
prompts, and model settings were not verified. `provenance.json` retains source
file hashes and preprocessing details. Raw rationale text and duplicate source
copies are not published. No learner records, credentials, database files, or
real private judge cases are included.

The release adds no new license for third-party datasets. Imported problem
collections are not part of this release. Contact the authors about reuse terms.

## Build the verification environment

Requirements: Git, Docker Desktop/Engine, Python 3 on the host, and the normal
local Compose configuration described by the project. Compose requires its
root environment values even for a verification-only service. Do not publish
your environment files. The verification commands below explicitly use a
temporary SQLite database rather than the application's configured database.

From the repository root:

```powershell
docker compose build backend execution-engine
docker compose up -d --no-deps execution-engine
python scripts/verify_paper_snapshot.py --commit paper-implementation-20261030 --output research-results/frozen-tests.txt
```

The snapshot helper archives that exact Git commit and tests it in a disposable
container with no network and no mounts. It cannot connect to the application
database. Published test transcripts record the full commit and actual pytest
result.

## Reproduce the synthetic results

Run these from the repository root. Results are written to each temporary
container's stdout; save them to a local file if desired.

```powershell
docker compose run --rm --no-deps --entrypoint python -e DATABASE_URL=sqlite:////tmp/research.db -e GROQ_API_KEY= -e AI_ALLOWED_CAPABILITIES= backend -m analysis.verify_execution_contract --output /tmp/execution.json
docker compose run --rm --no-deps --entrypoint python -e DATABASE_URL=sqlite:////tmp/research.db -e GROQ_API_KEY= -e AI_ALLOWED_CAPABILITIES= backend -m analysis.verify_candidate_score_contract --output /tmp/candidate.json
docker compose run --rm --no-deps --entrypoint python backend -m analysis.scoring_policy_ablation --output /tmp/ablation.json
docker compose run --rm --no-deps --entrypoint python -v "${PWD}/docs/research-paper/artifacts:/data:ro" backend -m analysis.compare_ai_reviews --original /data/pilot.jsonl --review-a /data/proposals-a.jsonl --review-b /data/proposals-b.jsonl --output-dir /tmp/pilot-comparison --analyze
```

Expected outcomes are recorded in the accompanying JSON reports: all eight
execution contracts meet their stated outcomes; the intentionally incorrect
program passes zero cases. Candidate and fresh official scores match at 97.4
under default weights and 98.7 under the documented custom weights. The pilot
gives 19/20 joint exact agreement and 20/20 coverage. Four rules on the same
84 configurations yield 49/43/0/0 unrounded correctness-ceiling violations.

A 503 indicates an unavailable execution service, not a reproduced score. Check
`docker compose ps`, execution-service health, Docker socket access, and supported
language images. Record outages separately; do not replace missing runs with
the expected numbers. Host timings and image availability may differ.

## Interpretation

These checks establish the stated synthetic contracts and policy properties.
They do not establish application-wide accuracy, empirically optimal weights,
independent human grading agreement, live-provider reliability, or learning gains.
