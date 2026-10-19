# CodeAssessment implementation status

Updated: 2026-10-19. Status is based on source inspection in this checkout. The local Docker daemon and Python runtime were unavailable during this review, so runtime integration and backend tests are not claimed as passing.

## Workflow status

| Area | Status | Evidence / remaining work |
| --- | --- | --- |
| Frontend build and lint | Verified locally | `npm run lint` and `npm run build` are the available client checks. Full browser walkthrough remains necessary. |
| Startup and configuration | Improved; runtime pending | Compose now declares PostgreSQL with persistent storage and health checks, uses required secrets, and waits for backend/database/engine health. Needs a real Docker Desktop startup check. |
| Database and migrations | Implemented; runtime pending | SQLAlchemy, Alembic, readiness endpoint and persisted course/submission models exist. Clean-volume migration and external database support need integration verification. |
| Authentication and roles | Partial | Student and instructor APIs use bearer-token/role guards. Quick-run now requires a student token. Need full registration, login, logout, role-scope, and password-change integration tests. |
| Problem catalogue and test cases | Partial | Built-in instructor problems and normalized test cases exist; extra catalogue population depends on explicit dataset import. Verify imported source/license and full coverage before research claims. |
| Run and submit gate | Implemented in UI; runtime pending | Workspace enables final submit after a successful run for the current code revision. Backend submit independently runs authoritative stored cases. |
| Execution isolation | Improved; production limitation remains | Removed backend-host fallback and engine-host fallback. The engine API itself has no auth and relies on its private Compose network; it must not be exposed publicly. It uses per-runner Docker restrictions but mounts the Docker socket; do not use for untrusted multi-tenant workloads without a separate hardened execution host/service. |
| Assessment scoring | Implemented with limits | Correctness is based on engine results; complexity is static/deterministic analysis, while style/recommendations/revision may use Groq or fallback logic. Inspect agent-specific confidence and fallback labels before treating AI output as ground truth. |
| Explainable feedback and revised code | Partial | Graph generates agent feedback and revision; providers can fail and fallbacks are not necessarily problem-specific or verified. Revised output is not re-executed. |
| Student history, dashboard and analytics | Partial | Saved submissions and several analytics routes are API-backed. Needs browser walkthrough against a clean database and multiple accounts. |
| Instructor courses, assignments and analytics | Partial | Core course/enrollment/assignment APIs persist. Some editing and report/analytics features remain incomplete; see README limitations. |
| Benchmarks/research evaluation | Pending | Need a fixed, licensed benchmark snapshot, reproducible split, baseline scripts, evaluation protocol, and recorded metrics. Dataset import scripts alone do not validate model or agent quality. |
| Automated checks / CI | Added; CI execution pending | GitHub Actions workflow runs frontend lint/build and backend pytest on push/PR. Needs a successful hosted run and repair of any previously unobserved test failures. |
| Production operations | Pending | Add release deployment, secret management, backups/restore drills, structured monitoring, rate limiting, threat review, and hardened execution boundary. |

## Required local startup check

1. Install and start Docker Desktop with the Linux engine available.
2. Copy `.env.example` to `.env` and replace both placeholder values with distinct random secrets. Do not share or commit them.
3. Copy `backend/.env.example` to `backend/.env`; set a Groq key only if live model responses are wanted.
4. Run `docker compose up --build -d`, then `docker compose ps` and `Invoke-RestMethod http://localhost:8000/health` (or `curl`).
5. Register a fresh student, create or import a problem, run public cases, submit, refresh history, and inspect a second account/role for access control.
6. Run `docker compose down` (without `-v`) and start again to confirm data persists. Test migrations on a disposable volume before any production upgrade.
7. Confirm all four runner images are present and test each supported language with success, compile error, runtime error, timeout, output cap, and service-unavailable scenarios.

## Environment limits and credential handling

In this review environment, no Python interpreter was installed/available to the configured launcher and no Docker daemon pipe was reachable. Backend pytest, Alembic/PostgreSQL integration, engine startup, and end-to-end flows therefore remain unverified. Frontend lint/build checks are the local automated checks available here.

During the source/configuration audit, ignored local `.env` files contained credentials that were inadvertently included in tool output. Their values are intentionally not reproduced here. Rotate the affected database and model-provider credentials in their respective services, then update local environment files and deployment secrets. Do not reuse the exposed credentials. Rotation was not performed by this task.
