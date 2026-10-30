# Paper readiness — 30 October 2026

This document separates implementation evidence from research evidence.
The final manuscript must describe a frozen Git commit and rubric version.
Do not claim that software regression pass rate is application accuracy.

The paper freezes implementation `d4cdb86` (guidance version 6), not the older
`317152b` public snapshot (guidance version 5). Its archived-snapshot test run
passed 333 tests. The scoring experiment is `7ddc4aa`. See
`research-paper/artifacts/REPRODUCING.md` for release tags, public synthetic
fixtures, normalized AI proposals, reports and exact reproduction commands.

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
6. Final author approval, funding/conflicts, any participant consent/ethics
   approval and data availability. Author order, affiliation and working Gmail
   addresses were supplied. Institutional emails may be used if available;
   the conference's published instructions do not require them.
7. Resolve imported problem/test licensing and verify every reference against
   its original publication. Similarity screening is not plagiarism clearance.
8. Apply the chosen conference's current template, page limit, anonymization
   and AI-disclosure rules. Recheck its official submission page at delivery.
   Inspect every rendered page, citations, equations, tables and figures.

## Integrated projection, with bounded claims

The teammate's private candidate generation is now integrated with the saved
v2 rubric, judge verification, incomplete-score handling, bounded retries and
private evidence storage. A cached candidate cannot override fresh official
results, cross assignment contexts, or match source after changing whitespace
inside a literal. Pending work survives restart with a persisted attempt
budget; unavailable verification ends explicitly and can be retried by the
learner. Historical assessments without a compatible rubric are not regraded.

The displayed number is a measured score for a private candidate implementing
the guided stage. Guidance is not the exact candidate source, so the learner's
implementation may receive a different grade. Do not promise a gain or claim
AI-generation accuracy from the controlled fixtures below. Actual provider
quality and educational benefit still require independent evaluation.

The current contribution can be described as a complexity-focused assessment
system with an auditable correctness ceiling. Strong accuracy or educational
benefit claims require the experiments above; do not invent numbers to fill
the results section. See RESEARCH_EVALUATION_PROTOCOL.md for the protocol.
Use RESEARCH_REVIEW_FORM.md for the independent labeling and feedback review.

## Software verification

- The exact paper implementation, `d4cdb86`, passed 333 tests in a fresh isolated
  archived-snapshot run. Earlier counts refer to different source revisions:
  `41be983` passed 315 and `317152b` passed 324. Separate transcripts identify
  the later source snapshot. Do not add counts across runs or replace the
  frozen paper count with a count from an unrelated HEAD.
- Frontend production build and lint passed.
- Eight live execution checks met their expected outcomes: sum programs in
  Python/C/C++/Java/JavaScript, C++ nested-array Merge Intervals, a changed
  incorrect program rejected on all three cases, then the correct source
  passing again. The contract tool reproduces this matrix.
- The scoring audit checked 28 synthetic scenarios under three weight sets.
  The correctness ceiling held in every scenario; human validation is pending.
- Backend startup recovered after additive schema reconciliation. No database
  reset, volume removal or historical regrading was performed.
- The live synthetic candidate-to-official-score contract matched under both
  default weights (85.4 -> 97.4) and custom weights (81.9 -> 98.7), with 3/3
  candidate cases passing in each. These are original fixtures run with the
  AI provider disabled and an isolated in-memory database, not AI success-rate
  measurements. Reproduce with `analysis.verify_candidate_score_contract`.
- The pilot contains 20 original AI-assisted synthetic snippets across five
  languages and two problem groups. Normalized AI-proposed labels are released
  with explicit unverified provenance; independent human labels remain pending.
  These proposals must not pass a human-reviewed corpus gate. The original
  blank reviewer forms remain available for a genuine independent study.

These are software checks, not evidence of human grading agreement, model
accuracy or improved learning outcomes. No publication-ready accuracy figure
has been established by this batch.

`analysis.research_manifest` records the exact commit, source/prompt hashes,
allowlisted configuration and runtime without exporting keys or datasets.
Use CONFERENCE_SUBMISSION_CHECKLIST.md for the verified venue requirements.
