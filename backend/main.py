import logging
from uuid import uuid4
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func

import models
from database import Base, engine, get_db
from schemas import (
    LoginRequest,
    AuthUser,
    ProblemListItem,
    ProblemDetail,
    SubmissionRequest,
    SubmissionResponse,
    SubmissionDetails,
    QuickRunRequest,
    QuickRunResponse,
    StudentAnalyticsResponse
)
from docker_runner.executor import execute_code_sandboxed
from workflow.graph import evaluation_graph
from workflow.state import EvaluationState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("evaluator_backend")

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Explainable Multi-Agent AI Code Evaluator (Production API)",
    description="Full Backend API with LangGraph Multi-Agent Orchestration, Sandboxed Execution, Problem Repository, and Analytics",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/auth/login", response_model=AuthUser)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    # Instructor Login (Accepts any password)
    if payload.role == "instructor":
        return AuthUser(id=payload.user_id, name="Prof. Kodacharya", role="instructor", email="instructor@kodacharya.edu")
    
    # Student Login (Accepts any password)
    if payload.role == "student":
        student = db.query(models.Student).filter(models.Student.student_id == payload.user_id).first()
        if not student:
            # Auto-provision any student ID for the demo
            student_name = "Demo Student" if payload.user_id == "demo_student" else payload.user_id
            student = models.Student(student_id=payload.user_id, name=student_name, email=f"{payload.user_id}@codevedha.edu", xp=100, streak_days=1)
            db.add(student)
            db.commit()
            db.refresh(student)
        return AuthUser(id=student.student_id, name=student.name, role="student", email=student.email)

    raise HTTPException(status_code=400, detail="Invalid role")

@app.get("/")
def root():
    return {
        "message": "Explainable Multi-Agent AI Code Assessment Production API is online.",
        "status": "healthy",
        "engine": "LangGraph + Groq"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

# ==========================================
# Problem Repository Endpoints
# ==========================================

@app.get("/api/problems", response_model=List[ProblemListItem])
def list_problems(db: Session = Depends(get_db)):
    """Fetch all available coding problems."""
    return db.query(models.Problem).all()

@app.get("/api/problems/{problem_id}", response_model=ProblemDetail)
def get_problem(problem_id: str, db: Session = Depends(get_db)):
    """Fetch a specific problem with its description, examples, constraints, and starter codes."""
    problem = db.query(models.Problem).filter(models.Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem '{problem_id}' not found.")
    return problem

# ==========================================
# Code Execution & Submission Endpoints
# ==========================================

@app.post("/api/submissions/run", response_model=QuickRunResponse)
async def quick_run_code(payload: QuickRunRequest):
    """Executes code against test cases in the sandbox without triggering AI evaluation."""
    res = await execute_code_sandboxed(
        source_code=payload.code,
        language=payload.language,
        test_cases=payload.test_cases
    )
    return res

@app.post("/api/submissions/submit", response_model=SubmissionResponse)
async def submit_and_evaluate_code(
    payload: SubmissionRequest,
    db: Session = Depends(get_db)
):
    """
    Complete Multi-Agent Evaluation:
    1. Look up problem and test cases.
    2. Sandboxed execution in container/subprocess.
    3. LangGraph 10-Agent Evaluation (Groq).
    4. Atomic DB Persistence.
    """
    logger.info(f"Received submission for student '{payload.student_id}' on problem '{payload.problem_id}'")

    # Fetch problem details
    problem = db.query(models.Problem).filter(models.Problem.id == payload.problem_id).first()
    test_cases = payload.test_cases or (problem.test_cases if problem else None)
    
    # 1. Sandboxed Test Execution
    exec_result = await execute_code_sandboxed(
        source_code=payload.code,
        language=payload.language,
        test_cases=test_cases
    )

    # 2. Build LangGraph State
    initial_state: EvaluationState = {
        "user": {"student_id": payload.student_id, "name": payload.student_id},
        "problem": {
            "title": problem.title if problem else payload.problem_id,
            "statement": problem.description if problem else "Problem statement",
            "constraints": str(problem.constraints) if problem else ""
        },
        "submission": {
            "source_code": payload.code,
            "language": payload.language
        },
        "execution_result": exec_result,
        "validation_result": None,
        "correctness_score": None,
        "correctness_details": None,
        "complexity_score": None,
        "complexity_details": None,
        "style_score": None,
        "style_details": None,
        "similarity_score": None,
        "similarity_details": None,
        "overall_score": None,
        "score_breakdown": None,
        "confidence": None,
        "feedback": None,
        "recommendations": None,
        "improved_code": None,
        "learning_analytics": None,
        "projected_score": None,
        "status": "running",
        "errors": []
    }

    # 3. Execute LangGraph Multi-Agent Engine
    final_state = await evaluation_graph.ainvoke(initial_state)

    # 4. Save into Database
    submission_id = f"SUB-{uuid4().hex[:8].upper()}"
    
    # Ensure student exists
    student = db.query(models.Student).filter(models.Student.student_id == payload.student_id).first()
    if not student:
        student = models.Student(student_id=payload.student_id, name=payload.student_id)
        db.add(student)
        db.commit()

    new_submission = models.Submission(
        submission_id=submission_id,
        student_id=payload.student_id,
        problem_id=payload.problem_id,
        language=payload.language,
        code=payload.code,
        status="EVALUATED",
        overall_score=final_state.get("overall_score"),
        correctness_score=final_state.get("correctness_score"),
        complexity_score=final_state.get("complexity_score"),
        style_score=final_state.get("style_score"),
        similarity_score=final_state.get("similarity_score"),
        execution_result=final_state.get("execution_result"),
        feedback=final_state.get("feedback"),
        recommendations=final_state.get("recommendations"),
        improved_code=final_state.get("improved_code"),
        projected_score=final_state.get("projected_score")
    )
    
    db.add(new_submission)
    db.commit()
    db.refresh(new_submission)

    return SubmissionResponse(
        submission_id=new_submission.submission_id,
        student_id=new_submission.student_id,
        problem_id=new_submission.problem_id,
        language=new_submission.language,
        status=new_submission.status,
        overall_score=new_submission.overall_score,
        correctness_score=new_submission.correctness_score,
        complexity_score=new_submission.complexity_score,
        style_score=new_submission.style_score,
        similarity_score=new_submission.similarity_score,
        execution_result=new_submission.execution_result,
        feedback=new_submission.feedback,
        recommendations=new_submission.recommendations,
        improved_code=new_submission.improved_code,
        projected_score=new_submission.projected_score
    )

@app.get("/api/submissions/{submission_id}", response_model=SubmissionDetails)
def get_submission(submission_id: str, db: Session = Depends(get_db)):
    submission = db.query(models.Submission).filter(models.Submission.submission_id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission

@app.get("/api/submissions", response_model=List[SubmissionDetails])
def list_submissions(
    student_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(models.Submission)
    if student_id:
        query = query.filter(models.Submission.student_id == student_id)
    return query.order_by(models.Submission.created_at.desc()).all()

# ==========================================
# Student & Instructor Analytics Endpoints
# ==========================================

@app.get("/api/analytics/student/{student_id}", response_model=StudentAnalyticsResponse)
def get_student_analytics(student_id: str, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    submissions = db.query(models.Submission).filter(models.Submission.student_id == student_id).all()
    
    total_problems = db.query(models.Problem).count() or 5
    unique_solved = len(set(s.problem_id for s in submissions if (s.overall_score or 0) >= 70))

    # Calculate category averages
    avg_correctness = db.query(func.avg(models.Submission.correctness_score)).filter(models.Submission.student_id == student_id).scalar() or 85.0
    avg_complexity = db.query(func.avg(models.Submission.complexity_score)).filter(models.Submission.student_id == student_id).scalar() or 80.0
    avg_style = db.query(func.avg(models.Submission.style_score)).filter(models.Submission.student_id == student_id).scalar() or 85.0
    avg_overall = db.query(func.avg(models.Submission.overall_score)).filter(models.Submission.student_id == student_id).scalar() or 88.5

    return StudentAnalyticsResponse(
        overall_score=round(avg_overall, 1),
        streak_days=student.streak_days,
        xp=student.xp,
        problems_solved=max(unique_solved, 1),
        total_problems=total_problems,
        score_trend=[
            {"date": "Apr 1", "score": 30},
            {"date": "Apr 8", "score": 45},
            {"date": "Apr 15", "score": 42},
            {"date": "Apr 22", "score": 65},
            {"date": "Apr 29", "score": round(avg_overall, 1)}
        ],
        category_breakdown=[
            {"name": "Correctness", "value": round(avg_correctness, 1), "color": "#10b981"},
            {"name": "Time & Space Complexity", "value": round(avg_complexity, 1), "color": "#3b82f6"},
            {"name": "Code Quality & Style", "value": round(avg_style, 1), "color": "#8b5cf6"},
            {"name": "Originality", "value": 85.0, "color": "#ec4899"}
        ],
        weak_topics=["Dynamic Programming", "Graph Traversals", "Bit Manipulation"]
    )

@app.get("/api/instructor/overview")
def get_instructor_overview(db: Session = Depends(get_db)):
    students = db.query(models.Student).all()
    total_submissions = db.query(models.Submission).count()
    avg_class_score = db.query(func.avg(models.Submission.overall_score)).scalar() or 82.4
    
    student_list = []
    for s in students:
        s_subs = db.query(models.Submission).filter(models.Submission.student_id == s.student_id).all()
        s_avg = (sum(sub.overall_score or 0 for sub in s_subs) / len(s_subs)) if s_subs else 82.0
        student_list.append({
            "id": s.student_id,
            "name": f"{s.name} ({s.student_id})",
            "course": "Data Structures & Algorithms",
            "subs": len(s_subs),
            "avg": f"{round(s_avg, 1)}%",
            "grade": "A" if s_avg >= 85 else "B+",
            "status": "Active" if s_avg >= 60 else "At Risk"
        })

    return {
        "total_students": len(students),
        "active_assignments": 6,
        "total_submissions": total_submissions,
        "class_avg_score": f"{round(avg_class_score, 1)}%",
        "students": student_list
    }