# CodeAssessment Academic Evaluation Rubric Mapping

**Project Title:** CodeAssessment (*CodeVedha*) — Architecting Mixed-Evidence Automated Programming Assessment  
**Authors:** A. Manigreeva, D. Nayaneesh, Kantam Pavan Sai Reddy, Kura Vignesh Reddy, Vitta Karthikeya  
**Document Lead:** Kantam Pavan Sai Reddy (DevOps & Infrastructure Lead)  
**Date:** November 2026  

---

## Parameter 1: Base Paper & Domain Comprehension

| Sub-criterion | Requirement / Expected Evidence | Project Implementation Evidence |
| :--- | :--- | :--- |
| **1.1 Base Paper Comprehension** | Problem statement, research objectives, scope and domain context | Base Paper: Sahu et al. (*Autograder+*, ACM IKDD CoDS-COMAD 2026) & Keuning et al. (*Systematic Review*, ACM TOCE 2018). Addresses black-box test autograders vs. unstable LLM graders in CS1/CS2 pedagogy. |
| **1.2 Methodology Understanding** | Algorithms, models, and techniques used in base paper | Multi-agent state orchestration (LangGraph), static syntax trees (Tree-sitter AST), and dynamic test execution inside isolated Linux cgroups. |
| **1.3 Existing Solution Analysis** | Proposed solution, architecture, datasets and experimental results | Analyzed Web-CAT, Autolab, JPlag, AutoGen, and Autograder+. Found that allowing LLMs to directly alter student grades introduces severe variance ($\sigma^2 = 14.8$). |
| **1.4 Research Gap Identification** | Limitations, shortcomings, assumptions, unexplored areas | Four identified gaps: (1) Stochastic grade drift, (2) Cognitive offloading when LLMs disclose full answers, (3) Inability to prove Big-O from wall-clock runtime, (4) Cloud API outage vulnerability. |
| **1.5 Literature Review** | Survey of related papers and alternative approaches | Detailed survey across 10+ papers documented in `research_paper/literature_review.md` and `research_paper/references.bib`. |

---

## Parameter 2: Project Idea & Innovation

| Sub-criterion | Requirement / Expected Evidence | Project Implementation Evidence |
| :--- | :--- | :--- |
| **2.1 Proposed Idea & Innovation** | Clarity of idea and how it differs from base paper | **Mixed-Evidence Model**: Strictly decouples deterministic grading authority from generative pedagogical guidance. LLM has zero numerical grade authority. |
| **2.2 Project Objectives & Scope** | Objectives, deliverables, boundaries, expected outcomes | Zero score variance ($\sigma^2 = 0.0$), 10-level asymptotic complexity ladder ($O(1)$ to $O(n!)$), 79.0% non-accepted gating cap, and sub-1.5s turnaround. |
| **2.3 Stakeholder Identification** | End users, beneficiaries, administrators | Students (instant hints, roadmap), Instructors (assignments, analytics, CSV exports), Institution (KMIT academic integrity and automated lab grading). |
| **2.4 Benefits & Value Proposition** | Real-world applicability, benefits, usability, impact | Eliminates faculty grading burnout; provides 24/7 guided debugging; stops code copy-pasting through 3-tier staged hints. |
| **2.5 Feasibility & Differentiation** | Technical feasibility, data availability, measurable gains | Evaluated across 1,890 algorithmic problems, 192,425 test cases, and 1,886 audited complexity records. 90.8% exact complexity match; 92.2% DB latency reduction in Mumbai. |

---

## Parameter 3: Solution Design

| Sub-criterion | Requirement / Expected Evidence | Project Implementation Evidence |
| :--- | :--- | :--- |
| **3.1 Solution Architecture** | Components, layers, modules, and interactions | React 18 frontend $\to$ FastAPI backend (:8000) $\to$ Docker execution engine (:8001) $\to$ PostgreSQL 16 (Mumbai `ap-south-1`). See `research_paper/figures/fig1_architecture.pdf`. |
| **3.2 Technology Stack Selection** | Languages, frameworks, databases, AI models | React 18 / Vite / Monaco, FastAPI, SQLAlchemy 2.0, Tree-sitter AST, LangGraph StateGraph, Groq LPU (LLaMA-3.3-70B), Docker. |
| **3.3 Workflow & Process Design** | End-to-end workflows, use cases, data flow | Public Run (fast lightweight testing) vs. Submit (isolated judge execution + AST complexity analysis + 8-node LangGraph scoring). |
| **3.4 Database & Data Design** | Schema, ER diagrams, data structures, datasets | 14 normalized entities in `backend/models.py` with Alembic head `20261016_0006`. Clear partitioning of public vs. hidden test cases. |
| **3.5 Interface & Integration Design** | UI/UX, API interfaces, module integration | Obsidian dark theme, split-pane Monaco code editor, test verdict tabs, Recharts multi-metric score breakdown, RESTful FastAPI endpoints. |
| **3.6 Design Documentation** | Architecture specifications, UML diagrams, SRS | Documented in `research_paper/codebase_architecture.md`, `docs/DOCKER_EXECUTION_ARCHITECTURE.md`, and `research_paper/main.tex`. |

---

## Parameter 4: Implementation & Engineering Rigor

| Sub-criterion | Requirement / Expected Evidence | Project Implementation Evidence |
| :--- | :--- | :--- |
| **4.1 Functional Implementation** | Implementation of planned modules, security, reliability | Polyglot execution (Python, C, C++, Java, JS) under non-root runner (`--net=none`, 1.0 vCPU, 256MB RAM). Redaction of private tests (`redact_hidden_execution`). |
| **4.2 Coding Quality & Understanding** | Code structure, readability, modularity, best practices | Modular structure across `backend/agents/`, `backend/analysis/`, `backend/execution/`. Over 3,700 lines of Tree-sitter AST parsing in `static_analyzer.py`. |
| **4.3 Database Implementation** | Creation, schema, CRUD operations, data management | PostgreSQL 16 managed via Alembic; connection pooling with pre-ping in `database.py`; CRUD for courses, enrollments, assignments, submissions. |
| **4.4 Testing & Validation** | Test cases, unit/integration testing, performance metrics | 202 backend unit tests + 20 fallback/revision tests + 23 Docker runner tests = 245+ automated tests passing (100% compliance). |
| **4.5 Technical Integration** | Integration of UI, backend, database, APIs, AI components | Seamless data flow between Monaco Editor $\leftrightarrow$ FastAPI $\leftrightarrow$ Docker Socket $\leftrightarrow$ LangGraph $\leftrightarrow$ PostgreSQL. |
| **4.6 Implementation Documentation** | Version control, progress tracking, technical records | Git commit history, AWS EC2 deployment scripts, and complete research manuscript. |

---

## Parameter 5: Demo and Presentation

| Sub-criterion | Requirement / Expected Evidence | Project Implementation Evidence |
| :--- | :--- | :--- |
| **5.1 End-to-End Demonstration** | Successful demonstration through actual use cases | Interactive walkthrough: Submit suboptimal $O(n^2)$ code $\to$ see complexity deduction $\to$ reveal 1 hidden test case $\to$ request Stage 1 hint $\to$ verify 79% cap. |
| **5.2 Functional Completeness** | Achievement of objectives, practical usability | Complete dual-role system (Student and Instructor portals) operating live with persistent PostgreSQL records. |
| **5.3 Presentation & Communication** | Clarity, structure, confidence, time management | Clean 8-slide presentation deck (`CodeAssessment_Final_Review_Presentation.pptx`) with empirical data and system figures. |
| **5.4 Technical Explanation & Q&A** | Answering research, design, and implementation questions | See `docs/TECHNICAL_VIVA_QA.md` for complete technical defense answers. |
| **5.5 Teamwork & Contribution** | Participation, role clarity, responsibilities | K. Pavan Sai Reddy: DevOps, AWS EC2 / Docker infrastructure, Nginx configuration, and database connectivity. |
| **5.6 Future Enhancements** | Limitations and future improvements | Transparently documented benchmark exposure and subprocess fallback; future longitudinal classroom trial at KMIT. |
