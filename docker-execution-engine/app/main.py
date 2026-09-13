from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.queue_worker import process_execution_request
from app.schemas import ExecuteRequest
from app.schemas import ExecutionResultResponse


app = FastAPI(
    title="Docker Code Execution Engine",
    description="Standalone Sandboxed Execution Microservice for CodeAssessment",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "service": "Docker Execution Engine"
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
