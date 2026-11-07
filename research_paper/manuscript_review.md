# Manuscript Review & Gap Analysis: Draft 1 vs. Latest Codebase

**Document Reviewed:** `/Users/nayaneeshcherry/Desktop/CodeAssessment-conference-draft1.pdf`  
**Companion Artifact:** `.build_conference_paper.py` (Script generating IEEE conference draft at commit `7bb4a44`)  
**Current Codebase State:** Commit `034c5fe` (October 2026)

---

## 1. Executive Summary of the Existing Manuscript

The existing 6-page draft, titled *"Multi-Agent Code Assessment through Implementation Analysis and Evaluation Design"*, was written primarily as a **critical source audit** of an early prototype (commit `c37de11` and `811842c`). 

While the draft demonstrated intellectual honesty by refusing to claim unearned educational gains, its primary posture was reactive: it documented numerous architectural flaws, broken control flows, missing features, and unvalidated LLM outputs. In Table III of Draft 1, **every single empirical outcome was marked as `[RESULT REQUIRED]`**.

Between the writing of Draft 1 and the current commit (`034c5fe`), the CodeAssessment platform underwent substantial refactoring and hardening. Major engineering improvements directly addressed the deficiencies identified in Draft 1. A new, authoritative IEEE research paper must transition from an audit of a broken prototype to a rigorous, evidence-based scientific contribution evaluating a **principled mixed-evidence multi-agent assessment architecture**.

---

## 2. Section-by-Section Critical Review of Draft 1

### Title & Abstract
- **Draft 1 Formulation:** *"Multi-Agent Code Assessment through Implementation Analysis and Evaluation Design"*. The abstract characterized the system as an early prototype where authentication was demonstrative, execution fell back to host, similarity was imputed without peers, and score projections were unverified.
- **Current Reality:** Authentication is fully functional with JWT, role-based access, and salted password hashes. Similarity has been completely removed from student grades. Revision and score projection have been separated into verified re-execution vs. explicit hypothetical scenarios.
- **Required Update:** The title and abstract must present the actual novel contribution: a mixed-evidence architecture that enforces deterministic guardrails on grading while leveraging multi-agent LLMs for scaffolded, explainable pedagogical guidance.

### Section I: Introduction
- **Draft 1 Formulation:** Stated that the study answers two audit questions: AQ1 (which proposed capabilities are implemented) and AQ2 (how scoring behaves on synthetic inputs).
- **Shortcomings:** Framing the paper primarily around "audit questions" reads like an internal software QA report rather than an academic research paper in computer science education and software engineering.
- **Required Update:** Frame the paper around foundational research questions (RQs):
  - **RQ1 (Architectural Integrity & Separation of Evidence):** How can automated assessment separate deterministic verification (correctness, algorithmic complexity, maintainability) from generative natural language feedback to eliminate LLM grade hallucination?
  - **RQ2 (Algorithmic Complexity Reasoning):** Can a hybrid analysis pipeline (Tree-sitter AST pattern matching + runtime profiling + constrained LLM review) accurately evaluate time/space asymptotic complexity across multiple languages without benchmark contamination?
  - **RQ3 (Pedagogical Feedback Fidelity & Actionability):** Does evidence-grounded multi-stage coaching prevent cognitive offloading compared to holistic solution generation?
  - **RQ4 (Empirical Robustness & System Performance):** What are the latency, throughput, and error boundaries of the multi-agent graph across containerized judge workloads?

### Section II: Background and Related Work
- **Draft 1 Content:** Cited Keuning et al. (2018), Autograder+ (Sahu et al., 2025/2026), SARFGEN (Wang et al., 2017), JPlag (Prechelt et al., 2002), and AutoGen (Wu et al., 2023).
- **Critique:** The related work was selective (only 5 prior works in Table I). It lacked deep engagement with recent 2023–2026 computing education literature on generative AI in programming education (e.g., SIGCSE, ITiCSE, IEEE Transactions on Learning Technologies), recent multi-agent software engineering frameworks (MetaGPT, ChatDev), and modern program analysis / complexity benchmarks.
- **Required Update:** Expand the taxonomy of related work into three distinct paradigms:
  1. Traditional unit-test autograders (Web-CAT, Gradescope, Autolab).
  2. Pure generative / holistic LLM evaluators and their vulnerabilities (hallucination, grading drift, answer disclosure).
  3. Hybrid multi-agent and program-analysis systems (Autograder+, SARFGEN).

### Section III: Proposed Framework and Verified Implementation
- **Draft 1 Description:**
  - Figure 1: Handled code execution, redacted fields, and ran an 8-node LangGraph.
  - Figure 2: The graph had `similarity` feeding into `aggregation`, and `revision` directly preceding `projection`.
  - Equation (1): Rank penalty $q(e, p) = \max\{0, 100 - 20 \max[0, r(p) - r(e)]\}$.
  - Equation (2): Composite score $S = \text{round}_1[(\sum w_i x_i)/(\sum w_i)]$ with $w = (0.40, 0.20, 0.20, 0.10, 0.10)$.
- **Obsolete vs. Active Code:**
  - *Obsolete:* Similarity is **no longer in the student rubric** (`backend/scoring/rubric.py`). Active student weights are $w = (0.20, 0.30, 0.30, 0.20)$ for Correctness, Time Complexity, Space Complexity, and Style.
  - *Obsolete:* Revision is **no longer inside the synchronous graph** (`backend/workflow/graph.py`). It is an asynchronous on-demand endpoint.
  - *Active:* Complexity scoring uses a refined 10-level rank ladder with a relative penalty scaled to available worse ranks: $\text{penalty} = \min(25, \Delta \cdot \frac{25}{\max(1, 10 - r(e))})$.
  - *Active:* Non-accepted score cap ($79.0$) prevents incorrect programs from receiving high scores on style/complexity alone.

### Section IV: Dataset and Evaluation Corpus
- **Draft 1 Content:** Inventoried LeetCodeDataset v0.3.1 (2,641 train, 228 test problems) and constructed a 12-problem pilot with 24 synthetic mutants.
- **Shortcomings:** The 12-problem pilot was synthetic and not executed against the live platform. The license conflict (Apache-2.0 in metadata vs MIT upstream) was flagged but left unanalyzed.
- **Required Update:** Detail the active production catalog (1,890 problems, 192,425 test cases) in PostgreSQL, the verified problem bank `complexity_analysis.json` (1,886 problems with audited time/space provenance), and the experimental holdout protocol.

### Section V: Experimental Methodology
- **Draft 1 Content:** Outlined a planned study with two blinded human graders, Holm-adjusted alpha, and planned significance testing.
- **Shortcomings:** Outlined only what *should* be done in a future human trial, without presenting concrete empirical measurements of the software itself.
- **Required Update:** Present actual, reproducible software engineering experiments:
  1. Static vs Hybrid Complexity accuracy across algorithm categories.
  2. Latency and resource profiling across multi-agent graph nodes.
  3. Fault injection and fallback resilience (Groq offline, rate limits, compile failures).
  4. Full test suite execution across 265 test cases.

### Section VI: Results & Section VII: Discussion
- **Draft 1 Content:**
  - Documented `UnboundLocalError` at commit `811842c` (Figure 3).
  - All empirical outcomes in Table III were `[RESULT REQUIRED]`.
- **Status in Latest Code:**
  - The `UnboundLocalError` bug is completely fixed.
  - Automated tests pass 100% (265/265).
  - Database latency reduced by 92% (from 553.9 ms to 43.18 ms) via Mumbai migration.
- **Required Update:** Remove the obsolete bug documentation as a primary figure; replace with verified architecture diagrams, actual performance benchmarks, and empirical analysis of the hybrid analyzer.

### Section VIII & IX: Threats to Validity, Ethics, Security
- **Draft 1 Content:** Identified host fallback in executor, benchmark target exposure in problem detail API, absence of real peer corpus for similarity, and prompt injection risks.
- **Assessment:** These remain legitimate, highly perceptive observations that demonstrate genuine scientific maturity. They must be preserved and formalized in the new paper.

---

## 3. Discrepancy Reconciliation Table

| Dimension | Draft 1 Audit (Commit c37de11 / 811842c) | Current Codebase (Commit 034c5fe) | Action for New Paper |
| :--- | :--- | :--- | :--- |
| **Student Rubric** | Included Originality (10%) with imputed 10% similarity fallback. | Similarity strictly excluded from student score. $w = (0.20, 0.30, 0.30, 0.20)$. | Present active rubric; document elimination of imputed similarity. |
| **Score Cap** | None. Flawed code could score high. | `NON_ACCEPTED_SCORE_CAP = 79.0` enforced if correctness < 100%. | Detail correctness gating formula and pedagogical rationale. |
| **Assessment Graph** | 10 nodes including synchronous Revision and Similarity. | 8 nodes. Synchronous revision decoupled; similarity moved to instructor route. | Present updated graph topology and explain latency/reliability benefits. |
| **Revision Agent** | Fixed C++ Two Sum fallback on AI failure. | Problem-specific, language-preserving staged guidance or explicit unavailable status. | Detail staged coaching hierarchy (Local, Data Structure, Refinement). |
| **Score Projection** | Fixed fallback (+7 points up to 100). | `verified_revision_projection` (re-executed code) vs `hypothetical_projection`. | Formalize mathematical distinction between verified vs hypothetical projection. |
| **Submit Handler** | Failed with `UnboundLocalError` at line 311. | Fully asynchronous, robust task gathering, proper error status (502/503). | Confirm handler stability and test coverage. |
| **Benchmark Targets** | Exposed in `GET /api/problems/{id}`. | Still exposed in `ProblemDetail` payload. | Accurately report as an active security limitation / threat to validity. |
| **Execution Fallback** | Local subprocess fallback when Docker fails. | Still present in `backend/docker_runner/executor.py`. | Accurately report as an operational security limitation. |
| **Empirical Results** | All `[RESULT REQUIRED]`. | 265 automated test cases, latency benchmarks, AST complexity evaluations. | Report actual observed measurements, test metrics, and runtime latency. |
