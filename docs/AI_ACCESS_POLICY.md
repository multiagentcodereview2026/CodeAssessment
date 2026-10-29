# AI access policy

The AI provider is an optional text-generation service, not a backend agent.
It has no database connection, Docker socket, filesystem access, credentials,
student roster, hidden tests, hidden expected outputs, or authority to change a
score.

## Enabled capabilities

- `hints`: on-demand hints built only from public problem content.
- `revision`: a student-requested guided learning stage using that student's
  source, public problem content, and public assessment evidence.
- `score_projection`: a student-requested private revision draft using the
  same constrained context. The backend judges the draft; only the aggregate
  verified result is returned to the student.
- `supervisor`: public problem context and language only; no student identity
  or source code.
- `correctness`: redacted execution verdicts and public problem context; the
  backend always calculates the correctness score.
- `explainability`: sanitized student source, public problem context, and
  public assessment evidence. Deterministic evidence remains authoritative.
- `recommendation`: already-saved feedback and complexity summaries only.
- `similarity`: sanitized current source plus aggregate similarity facts; peer
  source code is never sent.
- `complexity_review`: sanitized student source and public problem context;
  private complexity targets and hidden tests are excluded.

Remove any capability from `AI_ALLOWED_CAPABILITIES` to switch that feature to
its deterministic fallback without affecting the rest of the application.

## Non-negotiable backend controls

- Docker execution decides correctness.
- Deterministic rubric code decides scores and caps them at 100.
- AI output cannot alter correctness, private complexity benchmarks, or hidden
  judge results.
- AI payloads are allowlisted per feature and source comments are sanitized.
- Hidden test values and private execution diagnostics never enter AI payloads.
