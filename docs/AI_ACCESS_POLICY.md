# AI access policy

The AI provider is an optional text-generation service, not a backend agent.
It has no database connection, Docker socket, filesystem access, credentials,
student roster, hidden tests, hidden expected outputs, or authority to change a
score.

## Enabled capabilities

- `revision`: a student-requested guided learning stage using that student's
  source, public problem content, and public assessment evidence.
- `score_projection`: a student-requested private revision draft using the
  same constrained context. The backend judges the draft; only the aggregate
  verified result is returned to the student.
- `explainability`: sanitized student source, public problem context, and
  public assessment evidence. Deterministic evidence remains authoritative.
- `complexity_review`: sanitized student source and public problem context;
  used when deterministic evidence is insufficient or conflicting. Confident
  AST results bypass AI. Private targets and hidden tests are excluded.

Correctness, style, similarity, recommendations, supervisor validation, and
hints cannot contact AI, even with a legacy environment allowlist. Their
existing deterministic scores and fallbacks remain available. Practice topic
recommendations and roadmap selection use the deterministic recommendation engine.

Explainability requires model-reported confidence of at least 0.85 plus the
existing source/evidence checks. This threshold is a filter, not a measured
accuracy guarantee. Lower-confidence output uses deterministic feedback.

Revision and private projection generation are requested through the guide
button. Projection retries belong to that explicit request. Generation uses
the saved guide steps and outline; only verified improvements are displayed.
Guide and matching private source are generated together in one request.
An independent alignment check remains required before judge execution.
Successful private drafts and alignment results are cached for the same
submission, stage, test context and rubric. Generation is not repeated for a
provider cooldown or a temporary judge outage. HTTP 400 ends the attempt;
HTTP 429 sets an account-wide cooldown and delays the bounded retry.
At most two verification attempts run per submission. After the second failure,
verification stops and no retry action is offered for that submission. Pending clicks
reuse the existing job. Generated guidance is published immediately and remains
available if projection fails or stops. The private source is never published;
its optional measured projection requires independent alignment and execution.

Remove any capability from `AI_ALLOWED_CAPABILITIES` to switch that feature to
its deterministic fallback without affecting the rest of the application.

## Non-negotiable backend controls

- Docker execution decides correctness.
- Deterministic rubric code decides scores and caps them at 100.
- AI output cannot alter correctness, private complexity benchmarks, or hidden
  judge results.
- AI payloads are allowlisted per feature and source comments are sanitized.
- Hidden test values and private execution diagnostics never enter AI payloads.
