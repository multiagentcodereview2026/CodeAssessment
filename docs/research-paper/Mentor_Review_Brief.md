# CodeVedha Mentor Review Brief

**Review version:** artifact release `paper-artifacts-20261030`, including
experiment `7ddc4aa` and application snapshot `d4cdb86`. Prepared 30 October 2026 for
EmergIN 2027; Track V is the proposed fit.

## Contribution to assess

CodeVedha connects three assessment decisions: a versioned grade bounded by
observed correctness, explicit incompleteness when weighted evidence is missing,
and an executed private candidate projection that cannot replace a learner's
fresh official assessment. The contribution is the integrated evidence contract
and its characterization, not a new general complexity-inference algorithm.

Default component weights are correctness/time/space/style = 30/35/25/10.
The final policy is the smaller of weighted quality and correctness, with
rounding that cannot cross the exact correctness bound. The bound has a
mathematical argument; the exact weights are a design choice awaiting instructor
validation.

## Evidence presently available

- Frozen application: 333 backend tests, nine projection-render checks, frontend
  lint and build passed. These are regression checks, not measured accuracy.
- Eight live synthetic execution contracts met expectations across five
  languages. Two weight configurations gave candidate scores identical to
  fresh official scores for the same candidate.
- Four scoring rules were compared on the same 28 component vectors and three
  weight profiles. Weighted-only and fixed-cap rules exceeded correctness in
  49/84 and 43/84 configurations; multiplication and the ceiling did so in 0/84.
  Five targeted experiment tests passed. These vectors are policy stress probes,
  not necessarily attainable submissions or historical application errors.
- The static complexity pilot has 20 synthetic snippets but only two problem
  groups. Joint exact agreement is 19/20 with AI-proposed labels. No independent
  expert accuracy, learning benefit, or optimal-weight result is asserted.

## Decisions requested from the mentor

1. Is the integrated systems contribution sufficiently distinct from the cited
   feedback platforms for this venue, or should the paper await a broader study?
2. What minimum independent evaluation is needed? We propose two qualified
   complexity reviewers with adjudication, blinded instructor grades, and a
   diverse set of held-out problems. Guidance quality also needs human review.
3. Is the complexity-focused weighting and partial-credit preference appropriate
   for the intended course? Neither lower grade error nor fairness is established
   by the synthetic constraint comparison.
4. Please review the released synthetic fixtures, normalized AI proposals and
   provenance, and arrange institutional similarity screening. Raw model review
   prose and real learner data are excluded from the public artifact package.
5. Please confirm author contributions, funding/conflicts, institutional naming,
   and whether the manuscript is ready for submission after your corrections.

## Material to read first

Read the latest six-page PDF, especially Sections IV, VI-D and VII. The editable
Word file and evidence archive are included for checking equations and results.
The manuscript includes AI-use disclosure. No database-wide plagiarism clearance
has been obtained, and conference acceptance is not assured.

**Public evaluation artifacts and reproduction guide:**
https://github.com/multiagentcodereview2026/CodeAssessment/tree/paper-artifacts-20261030/docs/research-paper/artifacts

Named release tags identify the application snapshot and controlled experiment.
