# CodeAssessment Research & Codebase Audit Report

**Date of Audit:** October 27, 2026  
**Auditor:** Senior Research Scientist & Lead Software Architect  
**Audit Target:** CodeAssessment Platform & Research Manuscript  
**Repository Remote:** `https://github.com/multiagentcodereview2026/CodeAssessment.git`  
**Verified Git Commit:** `034c5fe61481e32156aecd4666cad847b9dd8957` (Branch: `main`, Fast-forwarded from `0902307`)  
**Database Host:** PostgreSQL on Supabase Mumbai (`aws-0-ap-south-1.pooler.supabase.com` / `db.dhwlihkkrtpviubkpsoy.supabase.co`)  
**Database Schema Head:** Alembic revision `20261022_0008` (14 tables, 194,550 total rows verified)

---

## 1. Audit Scope & Methodology

This audit establishes the empirical, software architectural, and research foundations of the **CodeAssessment** project. We conducted an end-to-end, file-by-file inspection of the active codebase, executed the complete automated test suite against the live PostgreSQL database, analyzed the existing manuscript draft (`CodeAssessment-conference-draft1.pdf`), and traced all data and control flows from submission ingest to persistence and feedback presentation.

### Inspected Codebase Inventory

| Subsystem | Key Files Inspected | Line Range / Scope | Audit Findings |
| :--- | :--- | :--- | :--- |
| **LangGraph Workflow** | `backend/workflow/graph.py`<br>`backend/workflow/state.py` | Full (Lines 1–66)<br>Full (Lines 1–45) | Active 8-node stategraph. Removed similarity from student scoring; removed synchronous revision from submit flow. |
| **Scoring Engine** | `backend/scoring/rubric.py`<br>`backend/scoring/complexity.py` | Full (Lines 1–139)<br>Full (Lines 1–601) | Deterministic rubric: $w = (0.20, 0.30, 0.30, 0.20)$ for C, K_time, K_space, T. 79.0 non-accepted score cap. 10-level rank ladder with scaled penalty. |
| **Multi-Agent Implementations** | `backend/agents/supervisor.py`<br>`backend/agents/correctness.py`<br>`backend/agents/complexity.py`<br>`backend/agents/style.py`<br>`backend/agents/aggregation.py`<br>`backend/agents/explainability.py`<br>`backend/agents/recommendation.py`<br>`backend/agents/revision.py`<br>`backend/agents/projection.py` | Full modules | Correctness: deterministic pass ratio. Style: deterministic heuristic scoring. Aggregation: strict rubric enforcement. Explainability: structural AST + test diagnostics fallback. Revision: language-preserving staged coaching. Projection: verified vs hypothetical distinction. |
| **Static & Hybrid Complexity Analysis** | `backend/analysis/static_analyzer.py`<br>`backend/analysis/analyzer_service.py`<br>`backend/analysis/ast_parser.py`<br>`backend/analysis/ast_engine.py`<br>`backend/analysis/confidence_policy.py` | 3,713 lines<br>241 lines<br>Tree-sitter AST | 3-tier analysis: (1) Tree-sitter AST pattern engine, (2) runtime measurement profiling, (3) rate-limited AI review with conflict mitigation. |
| **API & Routing** | `backend/main.py` | 3,730 lines | Resolved `UnboundLocalError` from earlier commit. Authenticated submit endpoint `POST /api/submissions/submit` executes sandboxed test runner and launches graph. Identified `target_time_complexity` exposure in `GET /api/problems/{id}`. |
| **Authentication & AuthZ** | `backend/auth.py`<br>`backend/models.py` | Full modules | PBKDF2/bcrypt password hashing, JWT bearer tokens, role-based authorization (Student vs Instructor), course enrollment gates. |
| **Execution Sandboxing** | `backend/docker_runner/executor.py`<br>`backend/execution/sandbox.py`<br>`docker-execution-engine/` | Full modules | Isolated container execution for Python, C, C++, Java. Fallback execution mechanism in `executor.py` flagged as security risk if Docker is offline. |
| **Test Suite** | `backend/tests/` (36 test suites) | 265 test cases | **265 passed**, 0 failed, 218 deprecation warnings (Pydantic/FastAPI). Test runtime: 4.55s. |

---

## 2. Completed Verification Checks

1. **Automated Test Suite Execution**:
   - Command: `pytest backend/tests`
   - Output: `265 passed, 218 warnings in 4.55s`
   - Covers: Auth API, hybrid complexity analysis, guided revision verification, score projection, recommendation engine, similarity clustering, AST pattern fixtures, and rubric scoring.
2. **Database Verification (Supabase Mumbai `ap-south-1`)**:
   - Connection verified via direct port 5432 and connection pooler.
   - Row counts verified:
     - `problem_test_cases`: 192,425 rows
     - `problems`: 1,890 rows
     - `submissions`: 93 rows
     - `notifications`: 61 rows
     - `users`: 21 rows
     - `students`: 16 rows
     - `courses`: 8 rows
     - `enrollments`: 8 rows
     - `assignments`: 7 rows
     - `assignment_problems`: 7 rows
     - `enrollment_requests`: 7 rows
     - `instructors`: 5 rows
     - `student_roadmaps`: 1 rows
     - `alembic_version`: 1 rows (`20261022_0008`)
     - **Total: 194,550 rows** (100% data integrity).
   - Sequence counters updated and aligned.
3. **Round-Trip Query Latency**:
   - Measured latency to Supabase Mumbai: **43.18 ms** (vs 553.90 ms previously to US-East).

---

## 3. Scope Exclusions & Operational Constraints

1. **Live Model Calls**: Live Groq LLM API calls were not flooded during the audit to avoid incurring third-party token consumption. Deterministic fallback paths (`build_evidence_feedback`, `guided_revision_fallback`, `unavailable_revision`) were thoroughly inspected and validated.
2. **Docker Daemon in Sandbox**: The audit ran on macOS where the local Docker Desktop engine was not running. Sandboxing logic and container commands were evaluated via code and unit test fixtures.
3. **Third-Party Libraries**: Upstream libraries (`psycopg`, `pydantic`, `fastapi`, `langgraph`, `tree-sitter`) were audited at their interface boundaries rather than reading internal library codebases.

---

## 4. Key Architectural Discoveries & Critical Findings

1. **Resolution of UnboundLocalError**: The submit handler bug identified in the earlier manuscript draft at commit `811842c` (where `exec_result` was referenced before assignment) has been completely resolved. `execution_task` is awaited, and `exec_result` is assigned before `redact_hidden_execution` is invoked.
2. **Decoupling of Similarity from Student Grades**: In the earlier draft, similarity was factored into student grades with an imputed 10% similarity (90% originality) when no peer submissions existed. In the current implementation, student rubric weights are strictly $(0.20, 0.30, 0.30, 0.20)$ for correctness, time complexity, space complexity, and style. Similarity is strictly an instructor review signal.
3. **Decoupling of Revision from Submit Path**: Synchronous revision generation was removed from the submit latency path to prevent LLM timeouts from blocking student grading. Revision is now an on-demand, staged coaching workflow (`backend/agents/revision.py`).
4. **Verified vs. Hypothetical Score Projection**: The earlier draft criticized score projection for replacing false-valued scores with 85 and adding +7. The current system introduces `verified_revision_projection`, which recalculates the exact rubric over re-executed code, while `score_projection_node` produces an explicit hypothetical scenario under clear assumptions.
5. **Remaining Benchmark Exposure Risk**: In `backend/main.py` lines 1139, 1157, and 1379, `target_time_complexity` and `target_space_complexity` are included in the problem detail payload returned by `GET /api/problems/{id}`. While hidden test cases are properly redacted, a savvy student inspecting network requests could read the target complexity before submitting.
6. **Host Execution Fallback Risk**: In `backend/docker_runner/executor.py`, if the Docker engine is unreachable, the system attempts `execute_locally()`, which runs student code as a local host subprocess. In production, this fallback poses a severe security risk and should be disabled in untrusted multi-tenant environments.
