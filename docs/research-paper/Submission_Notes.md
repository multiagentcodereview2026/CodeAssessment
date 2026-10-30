# CodeVedha manuscript handoff

Prepared for EmergIN 2027, Track V suggested, on 30 October 2026.

## What is delivered

The six-page paper uses the supplied IEEE A4 Word template as its design basis,
Times New Roman, single spacing and justified body text. It contains a confirmed
five-author block and emails, a shared KMIT address, Kura Vignesh Reddy as
corresponding author, four editable tables, native Word equations, a new 600 dpi
architecture figure, nine references and an AI-use acknowledgment.
Every rendered page was inspected. No screenshot is used as an experimental
result. The document is a systems paper with a limited pilot, not a validated
human grading study.

## Evidence behind the results

| Claim | Evidence and scope |
| --- | --- |
| Frozen application | Local source commit d4cdb86; source/prompt SHA-256 manifest |
| Regression checks | 333 backend tests and nine component-rendering checks passed; frontend lint and build passed |
| Execution | Fresh 30 October run: eight live synthetic contracts all met expectations; three cases per contract |
| Candidate score consistency | Fresh isolated in-memory runs: default 85.4 to 97.4; custom 81.9 to 98.7; both candidate scores matched fresh official scores |
| Ceiling property | Mathematical argument under stated assumptions, near-perfect rounding regressions, plus 84 synthetic policy-scenario checks |
| Static complexity pilot | Reproduced on the frozen source: time 19/20, space 20/20, joint 19/20, coverage 20/20 |
| Label provenance | AI-assisted unverified proposals; only two original problem groups; no human expert accuracy claim |
| Guidance alignment | Implemented AI-assisted gate and mocked regression checks; no real-provider success-rate or expert-validated efficacy result |
| Controlled scoring comparison | Analysis commit 7ddc4aa; four rules with 84 identical component/weight configurations each; 49/43/0/0 unrounded ceiling violations; five targeted experiment tests passed |
| Version reconciliation | Fresh archived runs: d4cdb86 passed 333; later 21aa1b7 passed 336. The old GitHub version 317152b passed 324. The paper intentionally cites the frozen d4cdb86 result. |

Do not call 95% label agreement “application accuracy.” Do not call the two AI
outputs human expert reviews. The paper deliberately retains the Python symbolic
bound mismatch. Do not describe the weights as empirically optimal: the proof
concerns the ceiling, while weight selection remains a stated design choice.

## Conference checks

The official page, checked 30 October 2026, gives a full-paper deadline of
30 October 2026 at 23:59 IST, six pages, Microsoft Word IEEE formatting, at most
six authors, full affiliation/address/emails, numbered/cited tables and figures,
editable tables, and figures at least 600 dpi. Submit via its Microsoft CMT link:
https://www.niet.co.in/ieee-conference-2027/

The site does not establish a numeric plagiarism threshold. No acceptance,
indexing, or publication outcome is guaranteed. IEEE's AI-generated-content
disclosure is included, with sections and uses identified:
https://conferences.ieeeauthorcenter.ieee.org/author-ethics/guidelines-and-policies/submission-policies/

## Author checks before upload

1. All five authors should read the paper, confirm the contribution and author
   order, emails, full name spellings (including whether to expand initials),
   affiliation and corresponding-author role.
2. Confirm funding and conflicts. No funding source or ethics approval was
   supplied, so neither was invented. Add a required genuine acknowledgment if
   applicable. The reported evaluation uses synthetic fixtures, not a human
   participant study; any later participant data need an appropriate review.
3. Confirm the rights to disclose the synthetic fixtures and supplied AI review
   files before making the companion evidence package public. It contains no
   real course submissions or imported problem dataset. Keep the live database,
   .env files, credentials and real private judge cases out of supplementary data.
4. Request institution-approved similarity screening if required. A bounded
   exact-token overlap check found no shared windows of 8, 10 or 12 tokens with
   the supplied ten-page base paper when the manuscript bibliography was
   excluded. This is not Turnitin/iThenticate clearance or a plagiarism score.
5. Review the final PDF and Word file together before uploading. Do not modify
   margins or font size to add unsupported claims. All acceptance and numeric
   score claims should keep their current distinction.

## Public artifact release and exact source versions

The immutable release tag is `paper-artifacts-20261030`:
https://github.com/multiagentcodereview2026/CodeAssessment/tree/paper-artifacts-20261030/docs/research-paper/artifacts

It provides pilot.jsonl, normalized proposals-a.jsonl and proposals-b.jsonl,
provenance, test transcripts, synthetic execution reports and reproduction
instructions. This is not an expert-labelled benchmark. Raw review prose,
returned source copies, unsupported metadata assertions and instructor fields
are excluded. The normalized proposals reproduce the 19/20 comparison while
retaining explicit AI-assisted unverified provenance.

`paper-implementation-20261030` identifies d4cdb86 and guidance version 6;
`paper-scoring-experiment-20261030` identifies 7ddc4aa. There is no reason to
change the paper to guidance version 5 or to replace its frozen 333 count with
the older public version's 324 count. Full commit IDs are in the reproduction
guide and transcripts. A 503 means the execution service is unavailable; it
must be resolved before rerunning live contracts, not recorded as a pass.

The conference requires author email addresses but does not explicitly require
institutional addresses. The confirmed Gmail addresses are retained. No
institutional email or mandatory-email rule has been invented.

## Research work still needed for stronger future claims

Independent expert complexity labels, blinded instructor grades, a diverse
problem-held-out corpus, real-provider generation/alignment trials, human
feedback ratings, and repeated latency measurements remain future work. The
paper states these limits explicitly rather than filling missing results.

## Reference checks

Primary records used: Douce et al. DOI 10.1145/1163405.1163409; Keuning et al.
DOI 10.1145/3231711; Piech et al. PMLR 37, pp. 1093–1102; the selected base
paper arXiv:2510.26402; APPS NeurIPS Datasets and Benchmarks 2021 and
arXiv:2105.09938; Chen et al. arXiv:2107.03374; official Docker and Tree-sitter
documentation. The base paper's reported training corpus and numerical
feedback results are not reused as results of this platform.

The release is intended for publication to GitHub with the named tags. No paper
has been submitted to CMT by this work. Author approval and institutional
similarity screening remain necessary; publication of artifacts is not
independent expert validation.
