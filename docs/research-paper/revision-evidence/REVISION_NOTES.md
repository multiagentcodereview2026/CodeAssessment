# Paper revision and remaining evidence

Prepared 30 October 2026. Application source and frozen research results are
unchanged. The original `paper-artifacts-20261030` tag is preserved.

## Changes in the revised manuscript

- Explains why correctness-only grading cannot distinguish equally correct
  implementations by efficiency, while the mandatory ceiling survives valid
  instructor weight changes.
- Rewrites the abstract around the problem, system, controlled findings, and
  limits. Shortens the system description without dropping the public-test gate,
  input contract, missing-evidence policy, or scoring definition.
- Adds three verified primary references: SPEED, multivariate amortized resource
  analysis, and Jonsson/Svingby's rubric validity review. No borrowed accuracy
  results or claim that these papers justify our exact weights is introduced.
- Adds an editable projection decision table. Candidate measurement remains
  separate from the learner's later official score.
- Reframes AI-label agreement as a diagnostic case study. Shows the unchanged
  original python-S02 fixture and explains why its two dimensions are equal,
  whereas truly independent array dimensions must remain distinct.
- Adds a weight-sensitivity table for the same 28 synthetic vectors per profile.
  No real student grade distribution or optimal-weight result is claimed.

## Reproduce the additional table

From the repository root:

```powershell
python scripts/derive_paper_weight_sensitivity.py --output research-results/weight-sensitivity.json
```

The helper reads the immutable published scoring-rule grid. It independently
recomputes each of the 84 ceiling scores from component values and weights and
checks them against the recorded values. It reports unrounded score summaries.
The manuscript displays mean and median to two decimal places; the JSON retains
three decimal places. Every profile has a range of 0 to 100 on this chosen grid.
These aggregates are sensitive to the chosen synthetic grid and are not
population estimates.

## Human work still pending

No user study was conducted or added by this revision. The existing independent
review forms remain available in `docs/RESEARCH_REVIEW_FORM.md` and the review-pack
generator. A feasible next step is two qualified reviewers independently labeling
the canonical snippets while blinded to platform/AI outputs, then documenting
disagreements and adjudication. A diverse problem-held-out corpus is needed for
broader claims; twenty related snippets alone remain a small diagnostic set.

An instructor-grade study would separately test grading agreement. A student
feedback study would test perceived usefulness and actionability, not complexity
accuracy or learning improvement. Obtain institutional guidance, consent, and
any required ethics approval before recruitment; do not invent approval or label
AI output as human review. Report participant selection, experience, protocol,
sample size, missing responses, and limitations when such work is actually done.

Before submission, obtain all-author/mentor approval and institutional similarity
screening. This revision does not establish plagiarism clearance or acceptance.
