# CodeAssessment Docker execution architecture

This guide describes the Docker stack, its exact repository locations, service links, ports, execution functions, database storage, backups, and remaining production work.

## 1. Architecture

~~~text
Browser
  | http://localhost:5173
  v
frontend (Vite / React)
  | browser requests beginning with /api
  v
backend (FastAPI) -------------------------> PostgreSQL
  |                                         problems, test cases, submissions
  | POST http://execution-engine:8001/execute
  v
docker-execution-engine (FastAPI)
  | Docker socket + temporary shared volume
  v
short-lived isolated language containers
  | Python / C / C++ / Java
  v
verified result -> backend -> frontend
~~~

Two actions use this path:

~~~text
Run Code  -> public test cases only
Submit    -> public + hidden test cases, then AI assessment workflow
~~~

## 2. Repository map

~~~text
CodeAssessment/
├── docker-compose.yml
├── docker/
│   ├── python.Dockerfile
│   ├── c.Dockerfile
│   ├── cpp.Dockerfile
│   └── java.Dockerfile
├── docker-execution-engine/
│   ├── docker/engine.Dockerfile
│   ├── app/main.py
│   ├── app/schemas.py
│   ├── app/queue_worker.py
│   ├── app/sandbox.py
│   ├── app/languages.py
│   ├── app/models.py
│   ├── tests/
│   └── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── docker_runner/executor.py
│   ├── dataset/
│   └── workflow/
├── frontend/
│   ├── Dockerfile
│   ├── vite.config.js
│   └── src/components/student/ProblemWorkspace.tsx
├── database/
│   ├── README.md
│   └── backups/
└── docs/DOCKER_EXECUTION_ARCHITECTURE.md
~~~

The root docker-compose.yml is the normal startup file. The nested docker-execution-engine/docker-compose.yml is only a standalone engine-development option; do not start both Compose stacks together.

## 3. Services, images, ports, and links

| Compose service | Build or image | Host port | Docker-network port | Purpose |
|---|---|---:|---:|---|
| frontend | frontend/Dockerfile | 5173 | 5173 | React/Vite UI |
| backend | backend/Dockerfile | 8000 | 8000 | FastAPI, database access, judge orchestration |
| postgres | postgres:16-alpine | none | 5432 | Persistent problem/test/submission data |
| execution-engine | docker-execution-engine/docker/engine.Dockerfile | none | 8001 | Sandbox execution API |
| dataset-importer | backend/Dockerfile | none | none | Optional APPS importer |
| dataset-processor | backend/Dockerfile | none | none | Optional APPS processor |
| codecontests-importer | backend/Dockerfile | none | none | Optional CodeContests importer |
| newfacade-importer | backend/Dockerfile | none | none | Optional Newfacade importer |

Only these URLs are visible on the Windows host:

~~~text
http://localhost:5173          frontend UI
http://localhost:8000/health   backend health
~~~

These are private Docker-network addresses and are intentionally not exposed on Windows:

~~~text
http://execution-engine:8001/health
http://execution-engine:8001/execute
postgresql://postgres:5432/codeassessment
~~~

## 4. Each Docker file

### docker-compose.yml

This file connects every service. It:

- starts PostgreSQL before the backend;
- starts the execution engine before the backend;
- maps frontend port 5173 and backend port 8000;
- gives the backend DATABASE_URL and DOCKER_ENGINE_URL;
- mounts /var/run/docker.sock into the execution engine;
- creates named volumes for PostgreSQL and temporary sandbox work;
- defines optional dataset tools.

The engine build location is:

~~~yaml
execution-engine:
  build:
    context: ./docker-execution-engine
    dockerfile: docker/engine.Dockerfile
~~~

### frontend/Dockerfile and frontend/vite.config.js

frontend/Dockerfile uses Node 20, runs npm ci, and starts Vite on port 5173.

frontend/vite.config.js sends browser requests beginning with /api to:

~~~text
http://backend:8000
~~~

The frontend does not contact PostgreSQL or the execution engine directly.

### backend/Dockerfile

backend/Dockerfile uses Python 3.11, installs backend/requirements.txt, and starts:

~~~text
uvicorn main:app --host 0.0.0.0 --port 8000
~~~

### docker-execution-engine/docker/engine.Dockerfile

This image uses Python 3.11, installs FastAPI dependencies and Docker CLI, then starts:

~~~text
uvicorn app.main:app --host 0.0.0.0 --port 8001
~~~

The engine needs Docker CLI because it creates short-lived runner containers.

### docker/python.Dockerfile, docker/c.Dockerfile, docker/cpp.Dockerfile, docker/java.Dockerfile

These optional tool images create a non-root sandbox user with UID 1000.

Their optional image names are:

~~~text
codeassessment-python:latest
codeassessment-c:latest
codeassessment-cpp:latest
codeassessment-java:latest
~~~

The current engine registry directly selects official images instead of these optional image names. The optional images are useful maintenance/prebuild assets but are not the active runtime selection until app/languages.py is changed.

## 5. Frontend, backend, and engine functions

### Frontend requests

File: frontend/src/components/student/ProblemWorkspace.tsx

| User action | Request | Backend function |
|---|---|---|
| Open problem | GET /api/problems/{problem_id} | get_problem() |
| Run Code | POST /api/submissions/run | quick_run_code() |
| Submit Code | POST /api/submissions/submit | submit_and_evaluate_code() |

Run Code loads only public cases. Submit loads all stored cases.

### Backend functions

File: backend/main.py

~~~python
async def quick_run_code(payload: QuickRunRequest, db: Session)
async def submit_and_evaluate_code(payload: SubmissionRequest, db: Session)
def redact_hidden_execution(execution_result)
~~~

File: backend/docker_runner/executor.py

~~~python
async def execute_code_sandboxed(
    source_code: str,
    language: str = "python",
    test_cases: List[Dict[str, Any]] = None,
    stop_on_first_failure: bool = False
) -> Dict[str, Any]
~~~

execute_code_sandboxed() prepares the code/test payload and POSTs it to the address in DOCKER_ENGINE_URL:

~~~text
http://execution-engine:8001/execute
~~~

If the engine cannot be reached, the backend has a limited local fallback. Production judging must use the Docker engine; the fallback is not a secure multi-language judge.

### Execution-engine functions

Files: docker-execution-engine/app/main.py and app/queue_worker.py

~~~python
async def execute_code_endpoint(req: ExecuteRequest)
async def process_execution_request(
    req: ExecuteRequest
) -> ExecutionResultResponse
~~~

Endpoint list:

~~~text
GET  /health
POST /execute
~~~

The engine uses app/sandbox.py:

~~~python
def execute_in_sandbox(
    code: str,
    lang_config: LanguageConfig,
    input_data: str,
    expected_output: str,
    time_limit: int | None = None,
    memory_limit: int | None = None,
    workspace: dict | None = None,
    should_compile: bool = True
) -> SandboxRunResult
~~~

## 6. Engine request and result data

File: docker-execution-engine/app/schemas.py

~~~python
class ExecuteRequest(BaseModel):
    code: str
    language: str
    test_cases: list[TestCaseInput]
    time_limit: int | None = 2
    memory_limit: int | None = 256
    stop_on_first_failure: bool = False
~~~

Every supplied test case has:

~~~text
id
input
expected_output
is_hidden
time_limit
memory_limit
~~~

The engine result is:

~~~python
class ExecutionResultResponse(BaseModel):
    status: str
    runtime_ms: int
    memory_kb: int
    compile_success: bool
    compile_stderr: str | None
    tests_total: int
    tests_passed: int
    tests_failed: int
    results: list[TestCaseResultResponse]
~~~

A per-case TestCaseResultResponse contains test_case_id, verdict, runtime, memory, is_hidden, input, expected_output, actual_output, and stderr.

For hidden cases, the response schema removes input, expected_output, actual_output, and stderr. backend/main.py performs an additional redaction before persistence/API return.

## 7. Current language registry

File: docker-execution-engine/app/languages.py

| Product scope | Runner image | Source file | Compile | Run |
|---|---|---|---|---|
| Python | python:3.11-slim | solution.py | none | python3 solution.py |
| C | gcc:13 | solution.c | gcc -O2 solution.c -o solution | ./solution |
| C++ | gcc:13 | solution.cpp | g++ -O2 solution.cpp -o solution | ./solution |
| Java | eclipse-temurin:17-jdk | Main.java | javac Main.java | java Main |

For compiled languages, the worker compiles once in a disposable workspace, then runs the generated executable for the remaining test cases.

The engine registry currently contains a Node/JavaScript entry, but JavaScript is not a tested/released platform feature. Keep JavaScript disabled in the UI until it is explicitly tested. HTML/CSS/JavaScript projects require a future browser sandbox rather than this stdin/stdout system.

## 8. Sandbox isolation and limits

File: docker-execution-engine/app/sandbox.py

Every compile/run container is created with:

~~~text
--network none
--read-only
--tmpfs /tmp
--pids-limit 64
--memory <limit>
--cpus 1.0
--user 1000:1000
--cap-drop ALL
--security-opt no-new-privileges
--rm
~~~

Current defaults:

| Setting | Value | Configuration |
|---|---:|---|
| Maximum source size | 65,536 bytes | EXECUTION_MAX_SOURCE_BYTES |
| Maximum output size | 1 MiB | EXECUTION_MAX_OUTPUT_BYTES |
| Process limit | 64 | EXECUTION_MAX_PROCESSES |
| CPU limit | 1 CPU | EXECUTION_CPU_LIMIT |
| Default memory | 256 MB | EXECUTION_MEMORY_LIMIT |
| Default timeout | 2 seconds per test case | ExecuteRequest.time_limit |
| Docker scheduling grace | 3 seconds | EXECUTION_DOCKER_SCHEDULING_GRACE_SECONDS |
| Docker startup grace | 20 seconds in main Compose | EXECUTION_DOCKER_STARTUP_GRACE_SECONDS |
| Concurrent cases per submission | 8 | EXECUTION_MAX_CONCURRENT_JOBS |

The engine has the Docker socket:

~~~text
/var/run/docker.sock
~~~

and a shared temporary named volume:

~~~text
codeassessment_execution-work mounted at /sandbox
~~~

The socket is privileged. For production, isolate this engine on a dedicated worker host/VM; never expose the engine or Docker socket to the internet.

## 9. PostgreSQL database and hidden tests

PostgreSQL details:

| Item | Exact value |
|---|---|
| Service | postgres |
| Image | postgres:16-alpine |
| Database | codeassessment |
| User | codeassessment |
| Container data folder | /var/lib/postgresql/data |
| Local named Docker volume | codeassessment_postgres-data |
| Compose volume key | postgres-data |

Important tables:

| Table | Data stored |
|---|---|
| problems | title, statement, difficulty, category, examples, constraints, starter code |
| problem_test_cases | public/hidden inputs, expected outputs, limits |
| submissions | submitted source code, execution result, scores, feedback |
| students | basic student records only |

Hidden test fields:

~~~text
problem_test_cases.problem_id
problem_test_cases.position
problem_test_cases.visibility       PUBLIC or HIDDEN
problem_test_cases.input_data
problem_test_cases.expected_output
problem_test_cases.time_limit_seconds
problem_test_cases.memory_limit_mb
~~~

Some legacy cases may remain in problems.test_cases JSON. problem_test_cases is the preferred normalised judge source.

Current local Docker database count:

~~~text
1,890 problems
5,670 public test cases
186,774 hidden test cases
22 submissions
~~~

Those values are in the local Docker volume, not Git.

### Direct safe database access

~~~powershell
docker compose exec -it postgres psql -U codeassessment -d codeassessment
~~~

Then run:

~~~sql
\dt
SELECT COUNT(*) FROM problems;
SELECT visibility, COUNT(*) FROM problem_test_cases GROUP BY visibility;
SELECT id, title, difficulty, category FROM problems LIMIT 20;
\q
~~~

Do not show hidden input_data or expected_output in student-facing output, logs, screenshots, or a public repository.

## 10. Backup, restore, and dataset import

Files: database/README.md and database/.gitignore

database/backups/ is a local-only backup location. Actual dump, SQL, and DB files are ignored by Git because they can contain hidden tests and student submissions.

Create a trusted private backup:

~~~powershell
docker compose exec postgres pg_dump -U codeassessment -d codeassessment -Fc -f /tmp/codeassessment.dump
docker compose cp postgres:/tmp/codeassessment.dump .\database\backups\codeassessment.dump
~~~

Restore a trusted backup. This replaces the receiver's local tables:

~~~powershell
docker compose up -d postgres
docker compose cp .\database\backups\codeassessment.dump postgres:/tmp/codeassessment.dump
docker compose exec postgres pg_restore -U codeassessment -d codeassessment --clean --if-exists --no-owner --no-privileges /tmp/codeassessment.dump
~~~

Never commit a database dump to GitHub. Share it only through restricted private storage with trusted developers.

Newfacade pipeline files:

~~~text
backend/dataset/normalize_newfacade.py
backend/dataset/import_newfacade.py
~~~

Pipeline:

~~~text
Raw Newfacade data
  -> validate and normalise to platform stdin/stdout format
  -> remove invalid/duplicate data
  -> mark public/hidden cases
  -> import into PostgreSQL
~~~

The newfacade-importer optional tool expects prepared source data at:

~~~text
../datasets/newfacade-staging
~~~

Dataset files are not part of the Git repository.

## 11. Local commands

Start all normal runtime services:

~~~powershell
cd "C:\Users\amani\Downloads\Multiagent framework\CodeAssessment"
docker compose up -d --build
~~~

Check services:

~~~powershell
docker compose ps
Invoke-WebRequest http://localhost:8000/health
docker compose exec execution-engine python -c "from urllib.request import urlopen; print(urlopen('http://127.0.0.1:8001/health').read().decode())"
~~~

Watch relevant logs:

~~~powershell
docker compose logs -f backend execution-engine postgres
~~~

Rebuild after a source change:

~~~powershell
docker compose up -d --build
~~~

docker compose down -v deletes local volumes, including PostgreSQL data. Use it only when data deletion is intended and a backup exists.

## 12. Development status and remaining work

Done:

- one repository now contains the Docker execution engine;
- frontend, backend, PostgreSQL, and engine are linked;
- public/hidden test selection and redaction are linked;
- four current product languages are configured;
- isolated Docker execution, compile errors, verdicts, and bounded concurrency are implemented;
- private backup instructions exist.

Not part of current work:

- a real user/account database; students has only basic records and current login is mock/basic;
- released JavaScript judging;
- HTML/CSS/JavaScript browser project evaluation;
- exact CPU-time/peak-memory complexity measurement.

Production work still needed:

1. Replace the default PostgreSQL password with managed secrets.
2. Store encrypted backups outside Git.
3. Use a dedicated execution worker host because Docker socket access is privileged.
4. Add queue limits, rate limits, metrics, logs, alerts, and cleanup monitoring.
5. Add database migrations before changing production schema.
6. Test every supported language on the deployment runner host.
7. Implement real auth, role permissions, and account management separately.
