from typing import TypedDict, Optional, List, Dict, Any

class EvaluationState(TypedDict):
    # Core Inputs
    user: Dict[str, Any]
    problem: Dict[str, Any]
    submission: Dict[str, Any]
    execution_result: Optional[Dict[str, Any]]
    
    # Supervisor
    validation_result: Optional[Dict[str, Any]]
    
    # Multi-dimensional Scores & Details
    correctness_score: Optional[float]
    correctness_details: Optional[Dict[str, Any]]
    complexity_score: Optional[float]
    complexity_details: Optional[Dict[str, Any]]
    style_score: Optional[float]
    style_details: Optional[Dict[str, Any]]
    similarity_score: Optional[float]
    similarity_details: Optional[Dict[str, Any]]
    
    # Aggregated & Pedagogical Layers
    overall_score: Optional[float]
    score_breakdown: Optional[Dict[str, Any]]
    confidence: Optional[float]
    feedback: Optional[Dict[str, Any]]
    recommendations: Optional[Dict[str, Any]]
    improved_code: Optional[Dict[str, Any]]
    learning_analytics: Optional[Dict[str, Any]]
    projected_score: Optional[Dict[str, Any]]
    
    # Pipeline Metadata
    status: str
    errors: List[str]
