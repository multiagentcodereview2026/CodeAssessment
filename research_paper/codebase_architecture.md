# CodeAssessment System Architecture & Implementation Specification

**Verified Repository Commit:** `034c5fe61481e32156aecd4666cad847b9dd8957`  
**Framework Version:** CodeAssessment v2.4 (October 2026)  
**Primary Tech Stack:** Python 3.13 / FastAPI, LangGraph, Tree-Sitter, SQLAlchemy, PostgreSQL (Supabase Mumbai), React 18, Docker

---

## 1. System Overview & Architectural Paradigm

CodeAssessment implements a **Principled Mixed-Evidence Multi-Agent Architecture** for automated programming assessment. It is engineered to solve the fundamental flaw of holistic LLM autograders—namely, the conflation of generative natural language fluency with deterministic grading authority.

```
+-----------------------------------------------------------------------------------+
|                                STUDENT WORKSPACE (React 18)                       |
|   - Monaco Editor (Python, C, C++, Java, JS)  - Interactive Hint-First Scaffolding|
|   - Real-time Public Test Runner             - Stepwise Guided Revision Diff View |
+------------------------------------------+----------------------------------------+
                                           | HTTP POST /api/submissions/submit
                                           v
+-----------------------------------------------------------------------------------+
|                             FASTAPI BACKEND SERVICE                               |
|   - JWT Auth & Ownership Verification         - Course & Deadline Gatekeeper      |
|   - Problem & Judge Test Case Retrieval      - Hidden-Data Redaction Engine       |
+-------------------+---------------------------------------+-----------------------+
                    |                                       |
                    v (Concurrent Task 1)                   v (Concurrent Task 2)
+---------------------------------------+   +---------------------------------------+
|        DOCKER EXECUTION ENGINE        |   |     HYBRID COMPLEXITY ANALYZER        |
|  - Isolated Containers (c, cpp, py, j)|   |  - Tree-sitter AST Pattern Matching   |
|  - CPU: 1.0 core, Mem: 256MB, Time: 5s|   |  - Loop / Recursion / DP / Graph IR   |
|  - Public & Hidden Judge Evaluation   |   |  - Dynamic Profiling (Low Conf Fall)  |
|  - Subprocess Verdict / Exit Tracking |   |  - Private Benchmark Normalization    |
+-------------------+-------------------+   +-------------------+-------------------+
                    |                                       |
                    +-------------------+-------------------+
                                        | Initial State Injection
                                        v
+-----------------------------------------------------------------------------------+
|                           LANGGRAPH EVALUATION GRAPH                              |
|                                                                                   |
|                               +------------------+                                |
|                               |  START / SUPERV  |                                |
|                               +--------+---------+                                |
|                                        |                                          |
|                               v--------v---------+                                |
|                               | CORRECTNESS NODE | (Deterministic Case Ratio)     |
|                               +---+----------+---+                                |
|                                   |          |                                    |
|                    +--------------+          +--------------+                     |
|                    | Parallel Fan-Out                       |                     |
|                    v                                        v                     |
|       +-------------------------+              +-------------------------+        |
|       |     COMPLEXITY NODE     |              |       STYLE NODE        |        |
|       |  - 10-Level Rank Ladder |              |  - AST Structural Rules |        |
|       |  - Scaled Worse Penalty |              |  - Naming, Mod, Read, M |        |
|       +------------+------------+              +------------+------------+        |
|                    |                                        |                     |
|                    +------------------+---------------------+                     |
|                                       | Join at Barrier                           |
|                                       v                                           |
|                           +-----------------------+                               |
|                           |   AGGREGATION NODE    | (Deterministic Rubric Math)   |
|                           |   - 20C / 30K / 30S / 20T| - 79.0 Non-Accepted Cap    |
|                           +-----------+-----------+                               |
|                                       |                                           |
|                                       v                                           |
|                           +-----------------------+                               |
|                           |  EXPLAINABILITY NODE  | (Structural AST Fallback)     |
|                           +-----------+-----------+                               |
|                                       |                                           |
|                                       v                                           |
|                           +-----------------------+                               |
|                           |  RECOMMENDATION NODE  | (Deterministic DSA Graph)     |
|                           +-----------+-----------+                               |
|                                       |                                           |
|                                       v                                           |
|                           +-----------------------+                               |
|                           | SCORE PROJECTION NODE | (Verified vs Hypothetical)    |
|                           +-----------+-----------+                               |
|                                       |                                           |
|                                       v                                           |
|                                     [END]                                         |
+---------------------------------------+-------------------------------------------+
                                        |
                                        v
+-----------------------------------------------------------------------------------+
|                       PERSISTENCE & REVEALED FEEDBACK                             |
|   - Atomic PostgreSQL Write (SUB-XXXXXXXX)                                        |
|   - Single Hidden Feedback Case Reveal (Input, Expected, Actual Output)           |
|   - Sanitized Response (All Remaining Hidden Cases Permanently Redacted)          |
+-----------------------------------------------------------------------------------+
```

---

## 2. Core State Contracts & Data Models

### 2.1 State Definition (`backend/workflow/state.py`)
```python
class EvaluationState(TypedDict):
    user: Dict[str, Any]                      # student_id, name, role
    problem: Dict[str, Any]                   # title, statement, constraints, category, difficulty
    submission: Dict[str, Any]                # source_code, language
    execution_result: Dict[str, Any]          # compile_status, stdout, runtime_ms, results[]
    validation_result: Optional[Dict[str, Any]]
    correctness_score: Optional[float]        # 0.0 to 100.0 (deterministic)
    correctness_details: Optional[Dict[str, Any]]
    complexity_score: Optional[float]         # 0.0 to 100.0 (deterministic rank penalty)
    complexity_details: Optional[Dict[str, Any]]
    complexity_target: Optional[Dict[str, Any]] # Private: optimal_time, optimal_space, constraints
    precomputed_complexity_analysis: Optional[Dict[str, Any]]
    style_score: Optional[float]              # 0.0 to 100.0 (deterministic AST checks)
    style_details: Optional[Dict[str, Any]]
    overall_score: Optional[float]            # 0.0 to 100.0 (gated composite)
    score_breakdown: Optional[Dict[str, Any]] # auditable weights and raw values
    feedback: Optional[Dict[str, Any]]        # pedagogical strengths, weaknesses, steps
    recommendations: Optional[Dict[str, Any]] # curated roadmap topics
    projected_score: Optional[Dict[str, Any]] # verified vs hypothetical improvement
    status: str
    errors: List[str]
```

---

## 3. Mathematical Foundations & Scoring Policy

### 3.1 Functional Correctness
Let $\mathcal{T} = \mathcal{T}_{\text{public}} \cup \mathcal{T}_{\text{hidden}}$ be the set of authoritative test cases, with $|\mathcal{T}| = N$.
Each test $t_i \in \mathcal{T}$ yields verdict $v_i \in \{\text{ACCEPTED}, \text{WRONG\_ANSWER}, \text{TIME\_LIMIT}, \text{RUNTIME\_ERROR}, \text{MEMORY\_LIMIT}\}$.
Let $\mathbb{I}_{\text{accepted}}(t_i) = 1$ if $v_i = \text{ACCEPTED}$, else $0$.
Let $\mathbb{I}_{\text{compile}} \in \{0, 1\}$ indicate compilation success.

$$C = \begin{cases} 
0.0, & \text{if } \mathbb{I}_{\text{compile}} = 0 \\
\displaystyle \frac{\sum_{i=1}^N \mathbb{I}_{\text{accepted}}(t_i)}{N} \times 100.0, & \text{if } \mathbb{I}_{\text{compile}} = 1 
\end{cases}$$

### 3.2 Algorithmic Complexity Scoring
Let the discrete asymptotic rank hierarchy be defined as:
$$\mathcal{R} = \big[ O(1), O(\log n), O(\sqrt{n}), O(n), O(n \log n), O(n^2), O(n^3), O(n^{4+}), O(2^n), O(n!) \big]$$
with ordinal ranks $r: \mathcal{R} \to \{1, 2, \dots, 10\}$.

Let $r(e) \in \{1, \dots, 10\}$ be the curated benchmark target rank, and $r(p) \in \{1, \dots, 10\}$ be the inferred rank of the student's solution.
The rank discrepancy is:
$$\Delta = r(p) - r(e)$$

If $\Delta \le 0$, the student's algorithm matches or outperforms the benchmark; $\text{penalty} = 0.0$.
If $\Delta > 0$, the penalty scales relative to the remaining worse ranks available from the benchmark:
$$W(e) = |\mathcal{R}| - r(e) = 10 - r(e)$$
$$\text{Penalty}(e, p) = \min\left(25.0, \; \Delta \times \frac{25.0}{\max(1, 10 - r(e))}\right)$$
$$\text{Marks}_{\text{dim}} = \max\Big(0.0, \; 25.0 - \text{Penalty}(e, p)\Big)$$
$$\text{Percentage}_{\text{dim}} = \text{Marks}_{\text{dim}} \times 4 \in [0.0, 100.0]$$

This formulation ensures that a 1-rank regression from an $O(n)$ benchmark ($W(e) = 6$, penalty $\approx 4.17$) is penalized more strictly than a 1-rank regression from an $O(1)$ benchmark ($W(e) = 9$, penalty $\approx 2.78$), reflecting that higher baseline algorithms have narrower acceptable margins of inefficiency.

When student algorithm outperforms the benchmark ($\Delta < 0$):
$$\text{Marks}_{\text{dim}} = 25.0, \quad \text{Flag: } \texttt{benchmark\_review\_required} = \text{True}$$

### 3.3 Code Style & Maintainability
Style analysis evaluates four orthogonal dimensions using language-specific AST and structural heuristics:
$$T = \sum_{k \in \{\text{naming}, \text{modularity}, \text{readability}, \text{maintainability}\}} S_k, \quad S_k \in [0, 25]$$

### 3.4 Student Composite Rubric & Correctness Gating
Let the active student dimensions be $D = \{\text{correctness}, \text{time}, \text{space}, \text{style}\}$ with base weights:
$$w_{\text{base}} = \big(w_C, w_{K_{\text{time}}}, w_{K_{\text{space}}}, w_T\big) = (0.20, 0.30, 0.30, 0.20)$$

When dimension $j \in D$ is unavailable or unconfigured, weights are dynamically renormalized over available dimensions $A \subseteq D$:
$$\hat{w}_j = \frac{w_j}{\sum_{k \in A} w_k}$$
$$S_{\text{raw}} = \sum_{j \in A} \hat{w}_j \cdot X_j$$

**Pedagogical Correctness Gate:**  
To prevent syntactically polished or efficient but functionally incorrect code from receiving an honor-roll grade:
$$S_{\text{final}} = \begin{cases}
S_{\text{raw}}, & \text{if } C \ge 100.0 \\
\min(S_{\text{raw}}, \; 79.0), & \text{if } C < 100.0
\end{cases}$$

### 3.5 Instructor Review Rubric
For faculty auditing and plagiarism triage, similarity is computed via token 3-gram Jaccard overlap against the 50 most recent peer submissions:
$$\text{Originality} = \max(0.0, \; 100.0 - \text{SimilarityRisk})$$
$$w_{\text{instructor}} = (0.20, 0.25, 0.25, 0.20, 0.10) \quad \text{for } (C, K_{\text{time}}, K_{\text{space}}, T, O)$$

---

## 4. Multi-Agent Graph Lifecycle & Failure Isolation

### 4.1 Supervisor Node (`backend/agents/supervisor.py`)
Validates execution state structure. Executes prior to graph fan-out and routes directly to `correctness_node`. Compilation failures are processed by `correctness_node` to assign a deterministic zero score.

### 4.2 Parallel Fan-Out
`correctness_node` acts as a fan-out barrier:
- Dispatches `complexity_node` (consuming precomputed Tree-sitter / AST analysis).
- Dispatches `style_node` (evaluating AST / linting rules).
Both branches execute independently and rejoin at `aggregation_node`.

### 4.3 Pedagogical Feedback & Staged Coaching
1. **`explainability_node`**:
   - Generates constructive pedagogical diagnoses.
   - Guaranteed deterministic fallback (`build_evidence_feedback`): Parses compilation stderr, failed public test cases, loop nesting counts, and AST signals directly into structured advice if the LLM provider fails.
2. **`recommendation_node`**:
   - Traverses a curated DAG of 14 Data Structures and Algorithms topics.
   - Maps student weaknesses to prerequisite concepts.
3. **`score_projection_node`**:
   - Evaluates hypothetical improvement scenarios assuming 100% correctness under existing complexity/style.
   - Explicitly flags predictions as *hypothetical* unless backed by a judge-evaluated revision stage (`verified_revision_stage`).

---

## 5. Security & Isolation Architecture

1. **Docker Execution Sandbox**:
   - Compiles and runs student code under dedicated non-root users (`runner`) in isolated disposable containers.
   - Resource enforcement: 1.0 vCPU, 256MB RAM, 5-second CPU timeout.
   - Network access is denied (`--net=none`) on runner containers.
2. **Hidden Test Privacy Preservation**:
   - Stored judge test cases are partitioned into `PUBLIC` and `HIDDEN`.
   - `redact_hidden_execution()` strips all inputs, expected outputs, and actual outputs of hidden tests before responses leave the backend.
   - Single-Case Learning Disclosure: `revealed_feedback_case()` permits exactly one failed hidden test case to be revealed to the student as a debugging aid, while all other hidden cases remain permanently redacted.
3. **Identified Architectural Caveats**:
   - *Benchmark Exposure*: `target_time_complexity` and `target_space_complexity` are visible in the `GET /api/problems/{id}` response payload.
   - *Executor Fallback*: `backend/docker_runner/executor.py` contains a local subprocess execution fallback (`execute_locally()`) if the Docker daemon cannot be contacted.
