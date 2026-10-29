# Independent review form

Complete one copy per solution per reviewer before seeing analyzer output or
the other reviewer's answers. Keep private code and participant identities
outside Git. Use pseudonymous reviewer and solution IDs.

| Field | Reviewer entry |
| --- | --- |
| Solution ID and problem ID | |
| Source SHA-256 / dataset version | |
| Language / compiler version | |
| Reviewer ID and date | |
| Code provenance and permission to use it | |
| Input-size variables and relevant constraints | |
| Time complexity of this exact source | |
| Auxiliary space, including recursion stack | |
| Source-based justification and dominant operation | |
| Ambiguous cases / assumptions | |
| Correctness evidence and known failing cases | |
| Independently assigned overall grade, 0–100 | |
| Independently assigned C/T/M/Y percentages, if grading weights | |

For feedback review, score each criterion 0 (incorrect or absent), 1
(substantial problems), 2 (mixed), 3 (minor problems), or 4 (fully supported).
Give concrete evidence for each rating. Unavailable output is recorded as
unavailable and included in coverage, not silently dropped.

| Feedback criterion | Rating | Evidence |
| --- | --- | --- |
| Factual correctness against code and observed execution | | |
| Relevance to this problem and submission | | |
| Actionability for a learner | | |
| Correctness issues prioritized ahead of cosmetic style | | |
| No unsupported score promise or complexity claim | | |
| Privacy follows the declared one-case release policy | | |

Missing comments alone must not lower the judgment. Compilation failures,
wrong answers, partially passing submissions, timeouts, good algorithms with
poor formatting and uncertain complexity estimates should all be represented.

After both reviews are locked, adjudicate discrepancies and retain both
original judgments. Record adjudicator, rationale and final labels separately.
Do not replace independent answers with the platform's own predictions.
Agree how instructor grades are formed before comparing weight alternatives.

For the scoring audit tool, export adjudicated rows as JSONL with fields:
`id`, `correctness`, `time`, `space`, `style`, `instructor_score`, and
`reviewed_by` (two distinct pseudonymous reviewer IDs). Do not submit blank
forms as evaluated data. Keep the raw reviews to substantiate independence.
