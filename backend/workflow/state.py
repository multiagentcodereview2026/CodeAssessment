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
    # Private targets are read from the backend problem record only. They are
    # never included in the public problem payload, AI payload, or API result.
    complexity_target: Optional[Dict[str, Any]]
    # This analysis can be started alongside Docker execution before the graph
    # reaches the complexity node.
    precomputed_complexity_analysis: Optional[Dict[str, Any]]
    # Backend-only signals such as a benchmark that should be re-verified.
    assessment_flags: Optional[Dict[str, Any]]
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
