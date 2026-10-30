# Guided score projection

The learner's official saved grade is never replaced by a candidate score.
Projection uses the submission's saved rubric and weights. The generated
candidate must pass all evaluated cases and have complete weighted assessment
evidence before a measured score can appear.

## Guidance alignment

Guidance version 6 passes the exact displayed goal, actions, outline, and
explanation to private candidate generation. A separate AI-assisted review
checks the source basis for the guidance, candidate adherence, and stage scope.
Missing evidence, provider fallback, or an inconclusive review withholds the
projection. It does not mark the learner's submission wrong. The review receives
no hidden test data and is not a formal proof of semantic equivalence or of
complexity. Judge execution and scoring remain separate mandatory steps.

Prompts prohibit treating container nesting as proof of cubic work or rewriting
code merely to influence the analyzer. The complexity analyzer is unchanged.
AI review may still make mistakes; independently labelled evaluation is needed
before making an accuracy claim about this safeguard. The additional provider
call can increase verification latency.

## Public states

- Pending: a spinner and explanation, with no fabricated progress percentage.
- Slow: after 30 seconds on the page, explain that verification is taking longer.
- Paused: after three failed refreshes or 360 checks, offer **Check again**.
  This resumes status reads and does not generate another candidate.
- Verified improvement: measured candidate score and signed difference.
- Verified no increase: a completed result, including zero or negative difference,
  without treating it as a provider failure or suggesting an automatic retry.
- Unavailable: explain that no reliable projection is available and allow an
  explicit retry through the revision endpoint.

Polling is sequential, every ten seconds after the preceding request finishes.
Requests time out after 30 seconds and are cancelled on navigation. A page-side
timeout does not cancel the backend verification task.

The expandable calculation table shows current and candidate percentages,
saved weights, and weighted contributions. The final mark applies the
correctness ceiling and conservative rounding. Historical records with missing
comparison evidence display a dash rather than a reconstructed score.

Historical projections are not regraded or modified on deployment. Their
**Recheck with current guidance** action requests updated guidance and the new
alignment verification; guidance version 5 is not reused as version 6.

## Checks

Backend regression coverage includes saved rubric scoring, incomplete evidence,
no gain, rejected alignment, stale request protection, and private-data isolation.
Provider responses are mocked in tests; no paid provider review is an accuracy
benchmark. Run the normal backend pytest suite in its Linux environment.

Frontend component checks: `node --test scripts/projection-status.test.mjs`
from the frontend directory. Also run `npm run lint` and `npm run build`.
