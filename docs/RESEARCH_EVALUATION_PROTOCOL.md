# Research evaluation protocol

**Status: protocol and tooling are present; no research result is claimed.**
The current repository does not contain an independently reviewed code-snippet
ground-truth corpus suitable for measuring complexity-agent accuracy or
student-feedback quality. Run the experimental protocol only after the data
and licensing gates below are resolved.

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
