# AI-assisted pilot label comparison — 30 October 2026

This is model agreement on a small synthetic pilot, not independent human
expert validation or a measured application-wide accuracy result.

## Inputs and provenance

The submitted files each contain all 20 solution IDs from the original pack.
They self-report reviewer IDs `gemini-3-flash` and `claude-sonnet-5-5` and
correctly retain `ai_assisted_unverified` provenance. These model identities,
prompts, review independence and model settings have not been verified.
No instructor grades or executed correctness evidence were supplied.

Canonical source bytes and problem IDs come from the original pilot pack.
The first review returns no source text, so its source association is by ID.
The second returns every snippet with extra ending newlines; its declared
hashes match the canonical originals, rather than those returned bytes,
despite asserting a recomputed match. It also replaces the original two
problem-group IDs with variant IDs. Preserve the submitted files unchanged;
record these metadata discrepancies and use canonical original grouping.

## Observed results

- Reviewer-to-reviewer time label agreement: 20/20.
- Reviewer-to-reviewer auxiliary-space agreement: 20/20.
- Static platform time label agreement with those proposals: 19/20.
- Static platform auxiliary-space agreement: 20/20.
- Joint exact label agreement: 19/20 (95%); analyzer coverage: 20/20.

| Language | Snippets | Joint exact label matches |
| --- | ---: | ---: |
| Python | 4 | 3 |
| C | 4 | 4 |
| C++ | 4 | 4 |
| Java | 4 | 4 |
| JavaScript | 4 | 4 |

## The remaining exact-label mismatch

`python-S02` resets a scalar accumulator in an outer loop over `range(len(a))`
and recomputes the sum in an inner loop over `a`. Both iteration counts are
the same input length n, giving n*n additions and worst-case O(n²) time under
the unit-cost arithmetic assumption. It uses O(1) auxiliary space.

The static analyzer emits O(m*n) time and O(1) space. O(m*n) specializes to
O(n²) when m=n, but the source has one array-length bound, not two independent
sizes. This is a symbolic bound/variable association issue to investigate
with the analyzer maintainer, not evidence of a failing runtime test.
Keep it as a mismatch in the strict label comparison; do not globally turn
every O(m*n) result into O(n²) or tune the reported result on this pilot.

## Appropriate paper claim and remaining work

Report this as a 20-snippet, five-language, two-problem-group AI-assisted
pilot. Translated variants are not independent problems. Do not report 95%
as expert-ground-truth accuracy, or 100% reviewer agreement as proof of
correctness. Retain both submitted outputs, file hashes, canonical source
hashes, preprocessing notes and the analyzer commit.

Human adjudication, a more diverse held-out corpus, instructor-grade/weight
validation and feedback-quality evaluation remain separate requirements for
stronger claims. Do not feed these outputs into a combined-method evaluation
by inventing confidence values or provider parameters that were not supplied.

Reproduce the comparison with `analysis.compare_ai_reviews --analyze` using
the original pack and the two submitted files. Generated inputs and reports
remain in ignored `research-results/`; do not commit private review files.
