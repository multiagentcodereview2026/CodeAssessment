# Research evaluation protocol

**Status: protocol and tooling are present; no research result is claimed.**
The current repository does not contain an independently reviewed code-snippet
ground-truth corpus suitable for measuring complexity-agent accuracy or
student-feedback quality. Run the experimental protocol only after the data
and licensing gates below are resolved.

## Frozen scoring policy for the next evaluation

New submissions use `complexity-focused-v2`: C, T, M and Y are percentages
for correctness, time, auxiliary space and style. Default weighted quality is
Q = 0.30C + 0.35T + 0.25M + 0.10Y and the final mark is S = min(Q, C).
The 79-point cap and second correctness multiplication are removed.
Question-specific instructor weights must be nonnegative and total 100%.
The correctness ceiling applies to every custom rubric. Store the version,
weights and component contributions with the assessment; do not regrade old
records or mix rubric versions in research comparisons.

For complete finite components in [0,100], nonnegative normalized weights
imply 0 <= Q <= 100. Therefore 0 <= S <= C <= 100. Increasing a component
cannot lower S, and the formula is continuous in the components. These are
mathematical properties, not evidence that a particular weighting matches
instructor judgment. Complexity receives 60% because it is the platform's
instructional focus; 30/35/25/10 is a prespecified design hypothesis, not a
literature-proven optimum. The correctness ceiling may make improvements in
complexity leave the final mark unchanged until correctness improves.

Unavailable weighted evidence leaves the assessment incomplete with lower
and upper score bounds; never redistribute its weights. Confirmed zero
correctness fixes the mark at zero even when the other analyses are pending.
Acceptance is a separate verdict requiring every evaluated case to pass.
Passing finite tests is not a proof of algorithm correctness on all inputs.

Public-test admission is enforced by the backend on the exact submitted code.
Passing the public cases is required before full assessment; it does not
guarantee passing private cases. One failed private feedback case may be
released for learning, with remaining private cases redacted. State that
release policy explicitly in the paper; do not claim that every hidden case
remains secret. Numerical grades and similarity review are separate.

Run `python -m analysis.scoring_policy_audit --output /tmp/scoring-audit.json`
for synthetic sensitivity checks. With independently reviewed component
percentages and instructor grades, add `--reviews /path/to/reviews.jsonl` to
compare mean absolute error against equal-weight and correctness-heavier
comparators. Each row needs `id`, `correctness`, `time`, `space`, `style`,
`instructor_score`, and two distinct `reviewed_by` identifiers. Preselect
comparators before opening the holdout; compare on matched solutions and
report sample size, uncertainty and disagreements. Reviewer identifiers in a
file are an audit trail, not proof that review was independent.

Run `python -m analysis.verify_execution_contract --output /tmp/execution.json`
inside the backend Compose network for real sandbox smoke checks using
original synthetic programs. The matrix covers five languages, nested array
stdin, unsorted and endpoint-sharing intervals, and changed-source execution.
Report these as software verification, separately from analyzer accuracy.

Score projection is integrated for compatible saved v2 rubrics. A private
candidate must compile, pass all evaluated cases, have complete scored
components and improve the saved grade before a measured gain is displayed.
Unavailable verification ends without an invented number. The learner's
implementation is assessed freshly; private candidate evidence cannot import
an old grade into a new attempt or assignment context. Model-generation
quality is a separate empirical outcome, not established by software tests.

## Research objective

Evaluate whether CodeAssessment's static complexity analysis and assessment
feedback agree with independent human judgments on submitted source code, and
whether the application returns correct, reproducible results across supported
languages. This protocol does not presume that multi-agent assessment is more
accurate than a deterministic baseline.

## Data inventory and limits

The tracked snapshot `codeassessment-problem-bank-verified-20260927.jsonl` was
audited locally before being removed from Git's index. It contains 1,886
problem-level records, 5,658 public cases, and 186,738 hidden cases. It is
retained only in the local working directory and is ignored by Git; do not
commit it, print its test payloads, or publish it. It has problem-level target
complexities and no submitted source snippet or independent snippet label, so
it is not a valid code-complexity accuracy benchmark by itself.

The snapshot's `source_license` metadata says “Apache-2.0”, but the upstream
GitHub repository's `LICENSE` file is MIT while the Hugging Face dataset card
declares Apache-2.0. The upstream project describes a Python LeetCode
problem-solving dataset and supplies a citation. Resolve the discrepancy and
check the provenance/terms for included problem statements, tests, and
solutions before redistribution or external publication. See the upstream
[repository and dataset documentation](https://github.com/newfacade/LeetCodeDataset),
its [LICENSE file](https://github.com/newfacade/LeetCodeDataset/blob/main/LICENSE),
and the [Hugging Face dataset card](https://huggingface.co/datasets/newfacade/LeetCodeDataset).

`backend/tests/style_benchmark_valid.jsonl` is a small regression fixture, not
an independently labeled scientific test set. `backend/analysis/build_stage10_holdouts.py`
generates synthetic fixtures for plumbing checks; synthetic rows are not
evidence of generalization to real student code. Keep those uses separate in
reports.

## Required benchmark corpus

Prepare a separate, access-controlled JSONL dataset outside Git. Every record
must have a stable `problem_id`, unique `solution_id`, language, source code,
time and auxiliary-space labels for that specific snippet, label source,
review date, and provenance. Include only supported languages: Python, C,
C++, Java, and JavaScript. Preserve a record-level license/provenance ledger;
do not assume a problem-set license automatically covers solutions or tests.

Two reviewers should label each evaluation snippet independently using the
problem statement, constraints, and the code. Resolve disagreements before
freezing the labels. Keep an adjudication note and avoid exposing hidden test
cases to the analyzer or model. Require the labels to describe the submitted
snippet, not the problem's optimal solution.

## Splits and leakage control

Group records by original problem ID before splitting. No problem, near
duplicate, or derived solution may appear in more than one split. Freeze a
versioned snapshot and SHA-256 manifest before running analysis. Use a
development split for tuning, a validation split for decisions, and a final
holdout that is not consulted during development. Record the split manifest,
snapshot hash, preprocessing version, and analyzer commit with every result.

The existing Stage 10 validator checks minimum size, language coverage,
duplicate IDs, reviewed labels, and overlap with a baseline. The final gate
also rejects empty or incomplete report artifacts and invalid exact-rate
values. These checks are safeguards, not proof that labels are correct or
that a split is leakage-free.

## Comparators and measures

Compare at least:

1. A simple deterministic baseline (for example, the current static analyzer
   without model review).
2. The existing AST/static analyzer.
3. The configured model reviewer alone, using frozen predictions.
4. The combined AST-plus-review workflow, if that path is the experiment.

Primary complexity outcomes are exact time and space label agreement and
separately reported normalized-label agreement. Also report per-language and
per-complexity-class precision, recall, and F1; unsupported/unavailable rate;
confidence coverage and accuracy on accepted-confidence cases; and latency
with provider configuration. Never silently drop unavailable predictions:
show the denominator and coverage beside conditional accuracy. Use
problem-grouped bootstrap confidence intervals when the corpus is large enough.

For feedback quality, use blinded human ratings with a preregistered rubric
for factual correctness, problem-specific relevance, actionability, and
privacy. Report inter-rater agreement and disagreements. Do not treat LLM
judges as ground truth without human validation.

## Execution and provider manifest

The offline comparison runner uses `analyze_static_complexity` for its AST
baseline, rather than accidentally invoking the production combined workflow.
Its `accuracy` is joint exact agreement among answered rows. Report `coverage`
beside it; `accuracy_all_rows` uses the full denominator with abstentions as
non-successes. `time_accuracy` and `space_accuracy` show the separate dimensions.
REVIEW_REQUIRED/NEEDS_REVIEW rows are abstentions, not confident predictions.
These field definitions are not a substitute for a reviewed evaluation set.
The combined comparator now replays the production orchestration with frozen
provider predictions. In particular, AI disagreement cannot replace a
complete AST formula: it triggers review, following the deployed policy.
The threshold 0.85 is a heuristic configuration value, not an empirically
calibrated 85% probability of correctness; do not describe it as such.

Generate an independent pilot with `python -m analysis.build_research_review_pack
--output-dir <new-folder>`. It supplies separate readable and JSONL forms for
two reviewers with no analyzer labels. The 20 translated variants cover only
two problem groups; do not count them as 20 independent problems or create a
train/test split that shares either problem. Store completed reviews outside
Git and retain the original independent judgments before adjudication.

`python -m analysis.verify_candidate_score_contract --output <report.json>`
compares measured candidates with real fresh official submissions under
default and custom weights. It forces an isolated in-memory database and
disables the provider. This verifies the judge/scorer integration on original
synthetic inputs and must not be labeled AI accuracy or human-grade agreement.

Record the following for each run: repository commit, operating system,
Python version, Docker version, runtime image digests, CPU/memory/time/output
limits, model/provider/model ID, prompt hashes, temperature, retry/timeout
settings, and whether each result came from the provider or a fallback.
Provider runs must fail or be marked unavailable when credentials or network
access are missing; fallback output is not a successful provider observation.
Do not record API keys, private source, or hidden test values in reports.

## Commands

From `backend/`, with dependencies installed and the corpus stored outside Git:

```powershell
python -m analysis.validate_approach_corpus `
  --dataset C:\research-data\snippet-labels.jsonl `
  --minimum 200 `
  --require-reviewed `
  --output C:\research-results\corpus-validation.json

python -m analysis.benchmark_ai_ast `
  --dataset C:\research-data\frozen-test.jsonl `
  --ai-predictions C:\research-results\frozen-provider-predictions.jsonl `
  --output C:\research-results\complexity-report.json
```

Generate a synthetic plumbing fixture only in a temporary output directory:

```powershell
python -m analysis.build_stage10_holdouts --output-dir C:\temp\codeassessment-stage10
```

Do not use that synthetic run as a research result. The final Stage 10 gate
consumes baseline, unseen, and adversarial report JSON files and reports
`HOLD` until each artifact is nonempty, complete, labeled, and has a valid test
metric.

## Findings and threats to validity

No model comparison, accuracy, F1, correlation, latency, or human-feedback
quality result has been produced by this protocol yet. The current status is
**pending data curation and license review**. Main threats include
problem-level labels being mistaken for code-level labels, source/licensing
ambiguity, benchmark contamination, language imbalance, synthetic examples,
provider drift, fallback/provider mixing, and evaluators overfitting to the
static analyzer's own output.
