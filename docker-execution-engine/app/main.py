from fastapi import FastAPI
from fastapi import HTTPException

from app.queue_worker import process_execution_request
from app.schemas import ExecuteRequest
from app.schemas import ExecutionResultResponse
from app.sandbox import is_docker_available


app = FastAPI(
    title="Docker Code Execution Engine",
    description="Standalone Sandboxed Execution Microservice for CodeAssessment",
    version="1.0.0"
)

@app.get("/health")
def health_check():
    # The API server alone is not enough: compiled submissions require the
    # Docker daemon to start isolated language-runner containers.  Reporting
    # healthy before that connection exists lets the backend accept a C/C++
    # submission and fall back to this compiler-less service image.
    if not is_docker_available():
        raise HTTPException(
            status_code=503,
            detail="Docker execution sandbox is not ready"
        )
    return {
        "status": "healthy",
        "service": "Docker Execution Engine",
        "sandbox": "ready"
    }


@app.post(
    "/execute",
    response_model=ExecutionResultResponse
)
async def execute_code_endpoint(req: ExecuteRequest):

    if not req.code.strip():
        raise HTTPException(
            status_code=400,
            detail="Source code cannot be empty"
        )

    if not req.test_cases:
        raise HTTPException(
            status_code=400,
            detail="At least one test case must be provided"
        )

    result = await process_execution_request(req)
    return result
