# CodeAssessment implementation status

Updated: 2026-10-19. Status reflects source inspection and the local checks recorded below. Backend, frontend, and engine unit checks ran successfully. Docker-backed execution and a hosted CI run remain unverified in this environment.

## Workflow status

| Area | Status | Evidence / remaining work |
| --- | --- | --- |
| Frontend build and lint | Verified locally | `npm run lint` and `npm run build` pass. Full browser walkthrough remains necessary. |
| Startup and configuration | Improved; runtime pending | Compose now declares PostgreSQL with persistent storage and health checks, uses required secrets, and waits for backend/database/engine health. Needs a real Docker Desktop startup check. |
| Database and migrations | Backend tests pass; PostgreSQL runtime pending | Backend migration tests pass against SQLite, including repeat application of the current migration head. Clean-volume PostgreSQL migration and external database support need integration verification. |
| Authentication and roles | Partial | Student and instructor APIs use bearer-token/role guards. Quick-run now requires a student token. Backend tests cover registration/login and role-scoped endpoints; browser flows and PostgreSQL-backed identity operations remain to be checked. |
| Problem catalogue and test cases | Partial | Built-in instructor problems and normalized test cases exist; extra catalogue population depends on explicit dataset import. Verify imported source/license and full coverage before research claims. |
| Run and submit gate | Implemented in UI; runtime pending | Workspace enables final submit after a successful run for the current code revision. Backend submit independently runs authoritative stored cases. |
| Execution isolation | Unit checks pass; Docker runtime pending and production limitation remains | Engine tests cover bounded output capture, fail-closed behavior, runner restrictions, and hidden-case redaction. Live tests now assert behavior across Python, C, C++, Java, and JavaScript, but were skipped locally because Docker is unavailable. The engine API itself has no auth and relies on its private Compose network; it must not be exposed publicly. The service mounts the Docker socket; do not use for untrusted multi-tenant workloads without a separate hardened execution host/service. |
| Assessment scoring | Implemented with limits | Correctness is based on engine results; complexity is static/deterministic analysis, while style/recommendations/revision may use Groq or fallback logic. Provider versus fallback provenance is now recorded; output still needs human quality review. |
| Explainable feedback and revised code | Partial | Provider/fallback provenance and unavailable revised-code states are explicit. Revision drafts remain unverified until rejudged; run live provider and browser checks when credentials/service are available. |
| Similarity review | Partial | Same-problem peer comparisons use available stored submissions. No peers and database errors now produce unavailable evidence rather than a fabricated originality score. Instructor review workflow still needs browser and PostgreSQL validation. |
| Student history, dashboard and analytics | Partial | Saved submissions and several analytics routes are API-backed. Needs browser walkthrough against a clean database and multiple accounts. |
| Instructor courses, assignments and analytics | Partial | Core course/enrollment/assignment APIs persist. Some editing and report/analytics features remain incomplete; see README limitations. |
| Benchmarks/research evaluation | Protocol and gate implemented; results pending | See [research evaluation protocol](RESEARCH_EVALUATION_PROTOCOL.md). A reviewed, licensed snippet-level corpus and frozen model/static predictions are still required; no accuracy or research result is claimed. Upstream dataset license metadata conflicts and must be resolved before redistribution. |
| Hidden-test dataset security | Local index removal staged; remote cleanup pending | The large JSONL problem bank is ignored and removed from the local Git index, while its local copy is preserved. The remote still contains the tracked object until a reviewed repository update removes it; do not expose its hidden tests. |
| Automated checks / CI | Configured; hosted execution pending | GitHub Actions runs frontend lint/build, backend pytest, engine unit tests, and Docker-backed tests for each language. A successful hosted run is still needed. |
| Production operations | Pending | Add release deployment, secret management, backups/restore drills, structured monitoring, rate limiting, threat review, and hardened execution boundary. |

## Required local startup check

1. Install and start Docker Desktop with the Linux engine available.
2. Copy `.env.example` to `.env` and replace both placeholder values with distinct random secrets. Do not share or commit them.
3. Copy `backend/.env.example` to `backend/.env`; set a Groq key only if live model responses are wanted.
4. Run `docker compose up --build -d`, then `docker compose ps` and `Invoke-RestMethod http://localhost:8000/health` (or `curl`).
5. Register a fresh student, create or import a problem, run public cases, submit, refresh history, and inspect a second account/role for access control.
6. Run `docker compose down` (without `-v`) and start again to confirm data persists. Test migrations on a disposable volume before any production upgrade.
7. Confirm all five runtime images are available (GCC is shared by C and C++) and test each supported language with success and wrong-answer cases, plus compile error, runtime error, timeout, output cap, and service-unavailable scenarios.

## Environment limits and credential handling

Local verification: backend `pytest -q --tb=short` — **202 passed**; frontend `npm run lint` and `npm run build` — **passed**; execution-engine pytest — **11 passed, 13 skipped** because Docker was not available. `docker compose config --quiet` and `git diff --check` pass. A Docker daemon pipe was not reachable, so engine live execution, Compose startup, PostgreSQL integration, and browser end-to-end flows remain unverified. The backend test suite emits deprecation warnings for Pydantic class-based configs, FastAPI `on_event`, and `datetime.utcnow()`.

During the source/configuration audit, ignored local `.env` files contained credentials that were inadvertently included in tool output. Their values are intentionally not reproduced here. Rotate the affected database and model-provider credentials in their respective services, then update local environment files and deployment secrets. Do not reuse the exposed credentials. Rotation was not performed by this task.
