# EmergIN 2027 submission checklist

Verified against the official conference page on 29 October 2026:
https://www.niet.co.in/ieee-conference-2027/

- Submission deadline: 30 October 2026, 23:59 IST.
- Submit through the conference's Microsoft CMT link.
- Prepare six pages in the supplied IEEE Word template, using Times New
  Roman, single spacing and justified text.
- Maximum six authors; include every author's full affiliation, address and
  email, and identify the corresponding author. Omit titles and positions.
- Number and cite tables, figures and references in order. Tables must remain
  editable; figures should meet the venue's 600 dpi requirement and fit the
  text boundary.
- Use one consistent English style, original unpublished work and a final
  spelling/grammar check. Recheck the official page before upload.
- Track V (AI, Machine Learning and Deep Learning) is a plausible fit; the
  authors should select the final CMT track after reviewing the actual scope.

IEEE's conference submission policy requires disclosure of AI-generated
content used in an article, including text, figures and code. Check the
precise disclosure against the actual final contribution and do not claim a
tool-generated passage or fixture was independently human-authored:
https://conferences.ieeeauthorcenter.ieee.org/author-ethics/guidelines-and-policies/submission-policies/

## Content gates before drafting final results

- Freeze a Git commit and a source/configuration manifest.
- Keep regression checks separate from experimental accuracy.
- Describe the deterministic correctness fraction, structural complexity
  estimate, heuristic confidence threshold, private benchmark comparison,
  deterministic style analysis and rubric contributions as distinct steps.
- Present the correctness-ceiling proof, but describe the 30/35/25/10 weights
  as a complexity-focused design hypothesis pending instructor validation.
- Report per-language and joint time/space agreement, coverage/abstention,
  frozen AI predictions, baseline comparisons, sample sizes and uncertainty
  only after independently reviewed labels exist.
- Declare the pilot's AI-assisted synthetic provenance, two-problem grouping
  and limited representativeness. Do not equate translated variants with
  independent problems or real student submissions.
- State that passing finite tests does not prove correctness for all inputs.
  Disclose the deliberate release of one failed private feedback case.
- Distinguish the measured private candidate score from the learner's future
  implementation. No guaranteed score gain or learning-benefit claim.
- Independently verify citations, dataset rights, consent where applicable,
  author details, funding/conflicts and the final rendered six-page layout.

## Remaining author input

Return both completed reviewer forms, adjudicated labels and instructor
grades, plus final author order/affiliations/emails. Genuine feedback ratings
and representative latency/quality measurements remain necessary for strong
claims. A similarity detector score is not plagiarism clearance, and no
Turnitin/iThenticate clearance has been established by this work.
