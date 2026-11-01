# Revision and score projection contract

The official submission pipeline and saved score are unchanged. A learner click
creates one optional revision job. AI receives AST identifiers and line locations
and returns a guide plus at most six exact replacement patches. The backend
assembles the complete private candidate from the original source, validates it,
reviews alignment, then sends it through the existing
Docker judge and scoring pipeline. Candidate source and private tests never enter
student responses. Private test inputs, expected outputs and diagnostics never
enter AI retry prompts.

## Release policy

Publish a measured candidate score and its guide only when the gain is at least
`SCORE_PROJECTION_MIN_GAIN` (default 1), every evaluated case passes, correctness,
time and space scores do not decrease, and structural complexity evidence supports
the claims. Incidental style variance of at most one percentage point is permitted
for non-style stages (`SCORE_PROJECTION_STYLE_TOLERANCE`, configurable 0–1). A
style-focused stage cannot use that tolerance. Scores
remain capped by the existing rubric. AI approval alone cannot pass the gate.

After projection failure, the independently schema/target-validated revision
guide remains visible with a **Not verified** warning and no candidate score.
Candidate alignment failure does not hide supported guidance. Malformed or
explicitly unsupported guidance remains private. This is supporting
evidence, not a proof that every student implementation will achieve the score.

## Durable jobs and budgets

`revision_jobs` is a transactional outbox with historical snapshots, private
candidate cache, deadlines, leases and independent counters. The dispatcher uses
Postgres row/advisory locks; the worker also checks the current submission job ID
before publishing. Worker restarts preserve cooldowns and candidate drafts.

- Two substantive candidate attempts per job, including invalid candidates and
  alignment rejections. Attempts are reserved before judging; infrastructure
  failures refund the reservation.
- One automatic infrastructure retry, reusing a saved candidate and alignment.
- A provider minute limit with a reliable cooldown waits without consuming a
  candidate attempt. Daily or unknown quota limits stop automatic retries and
  show no invented countdown. Invalid keys/bad requests do not loop.
- Three new jobs per learner/problem/local day (Asia/Kolkata). Repeated pending
  clicks and resuming a transient failure reuse the existing job.
- One running job by default, configurable up to two. A one-hour job expiry
  prevents unbounded quota waits. No broad Docker cleanup is performed.
- Cache compatibility includes exact source hash, language, rubric, tests and
  limits, analyzer version, benchmark targets and space definition. The original
  baseline must have compatible saved analyzer/judge evidence.

Only explicit learner requests create new work; status polling cannot regenerate
a candidate. Cancellation fences publication and survives restart.

## Operation

Apply migrations before starting the updated backend (`alembic upgrade head`;
the existing Compose entrypoint already does this). Settings are documented in
`backend/.env.example`. No real keys belong in committed files.

Run `docker compose exec -T backend python -m revision_job_report` for an aggregate
24-hour status/failure/attempt/token/latency report without source or test data.
Provider failures log safe exception categories; detailed private attempt history
is stored with the job. API usage metrics are present only when the provider
reports them; they are not estimates.

## Exact-edit generation

Each edit carries a guided step ID and a unique old/new substring. The source
hash must match, edits resolve against the original source, and overlapping,
ambiguous, whole-file, unrelated-target and no-op edits are rejected. Required
standard-library includes may be added without replacing existing headers.
Untouched source is preserved, including CRLF line endings. Candidate patches
and assembled code remain private. The usual sandbox, correctness and scoring
checks still apply; syntactically valid patches alone cannot release a score.

A supported guide is saved separately from candidate attempts. A later invalid
target, bad patch or provider response cannot erase that guide. Retry prompts
repair generation/alignment errors instead of inventing a different optimization;
a genuinely measured no-gain result may justify a different stage action.

## Deliberate plan adjustments

- Do not format every candidate silently: style is a scored component and all
  candidate changes must match the displayed stage.
- Judge once normally. Repeated timing is supporting evidence, not proof of an
  asymptotic bound. The existing structural analyzer confirms complexity claims.
- Use the language-specific AST parsers; Python parsing/formatters do not apply
  to C++ or Java.
- Do not send hidden failing cases to AI. Retry feedback contains safe validation
  codes and aggregate scoring evidence.
- End the job after two substantive failures. Starting a fresh job is subject to
  the daily limit; it cannot silently reset the same job's budget.

The deterministic rewrite catalog and cross-provider failover remain future
extensions. No unreviewed source rewrite or new provider is enabled here.
Offline regression tests cover quota classifications, cached Docker recovery,
privacy, release rules and daily quotas. A live 20–30-submission benchmark is
still required before claiming a production pass-rate or accuracy percentage.
