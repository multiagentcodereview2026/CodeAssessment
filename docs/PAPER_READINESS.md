# Paper readiness — 29 October 2026

This document separates implementation evidence from research evidence.
The final manuscript must describe a frozen Git commit and rubric version.
Do not claim that software regression pass rate is application accuracy.

## Implemented for the next study

- Versioned shared default rubric: correctness/time/space/style = 30/35/25/10;
  final mark is min(weighted quality, correctness). Optional per-question
  instructor overrides total 100%; correctness ceiling is mandatory.
- Assignment-context overrides do not mutate the shared practice question.
  Weights are frozen after submissions and snapshotted in the assessment.
- Unknown analysis remains incomplete with bounds; it does not earn marks
  through weight redistribution. Old saved grades remain unchanged.
- Public tests gate submission at the server; every evaluation test must pass
  for acceptance. A failed submission cannot receive an Excellent label.
- Private complexity targets are withheld from student question responses.
  One failed private feedback case can be intentionally revealed for learning.
- Unmeasured memory is labeled honestly instead of displaying a constant.
- Reproducible scoring sensitivity and live execution contract tools exist.
  The teammate's analyzer implementation is unchanged by this batch.

## Evidence the team still needs to supply

1. Independently reviewed code-level time and auxiliary-space labels,
   provenance and publication rights. Problem-optimal targets are not labels
   for an arbitrary submitted solution. Use two reviewers and adjudication.
2. Blinded instructor grades and component judgments on matched submissions
   to evaluate the default weights, including alternatives and sensitivity.
   Keep the selected holdout untouched during tuning.
3. A frozen model/provider/prompt configuration with real prediction runs.
   Report unavailable/fallback cases separately and give coverage as well as
   exact time/space/joint agreement, per-language metrics and uncertainty.
4. Human feedback ratings: factuality, relevance, actionability and privacy.
   Include wrong answers, timeout, compile failure and unavailable analysis.
   Do not use a model's self-rating as human ground truth.
5. Repeated end-to-end latency measurements (median and p95), hardware and
   database region, warm/cold runs, source snapshot hashes and image digests.
6. Final author affiliations, institutional emails, author order, funding,
   conflicts, any participant consent/ethics approval and data availability.
7. Resolve imported problem/test licensing and verify every reference against
   its original publication. Similarity screening is not plagiarism clearance.
8. Apply the chosen conference's current template, page limit, anonymization
   and AI-disclosure rules. Recheck its official submission page at delivery.
   Inspect every rendered page, citations, equations, tables and figures.

## Separate pending feature

Score projection and its verification remain the teammate's unfinished work.
Do not claim a verified gain, improved-code score guarantee or projection
accuracy until that work is integrated and tested with custom saved rubrics.
Existing historical artifacts are not regraded by this change.

The current contribution can be described as a complexity-focused assessment
system with an auditable correctness ceiling. Strong accuracy or educational
benefit claims require the experiments above; do not invent numbers to fill
the results section. See RESEARCH_EVALUATION_PROTOCOL.md for the protocol.
Use RESEARCH_REVIEW_FORM.md for the independent labeling and feedback review.

## Software verification observed in this batch

- 142 selected backend regressions passed in the final combined run; the
  unfinished projection suite was intentionally excluded.
- Frontend production build and lint passed.
- Eight live execution checks met their expected outcomes: sum programs in
  Python/C/C++/Java/JavaScript, C++ nested-array Merge Intervals, a changed
  incorrect program rejected on all three cases, then the correct source
  passing again. The contract tool reproduces this matrix.
- The scoring audit checked 28 synthetic scenarios under three weight sets.
  The correctness ceiling held in every scenario; human validation is pending.
- Backend startup recovered after additive schema reconciliation. No database
  reset, volume removal or historical regrading was performed.

These are software checks, not evidence of human grading agreement, model
accuracy or improved learning outcomes. No publication-ready accuracy figure
has been established by this batch.
