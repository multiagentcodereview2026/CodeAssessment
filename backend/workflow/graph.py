from langgraph.graph import StateGraph, START, END
from workflow.state import EvaluationState

from agents.supervisor import supervisor_node
from agents.correctness import correctness_node
from agents.complexity import complexity_node
from agents.style import style_node
from agents.similarity import similarity_node
from agents.aggregation import aggregation_node
from agents.explainability import explainability_node
from agents.recommendation import recommendation_node
from agents.revision import revision_node
from agents.projection import score_projection_node

def check_compilation_failure(state: EvaluationState) -> str:
    """Conditional Edge: Skip in-depth complexity/style if compilation broke."""
    exec_res = state.get("execution_result") or {}
    if exec_res.get("compile_status") == "error":
        return "explainability_node"
    return "correctness_node"

def build_graph():
    builder = StateGraph(EvaluationState)

    # 1. Register Nodes
    builder.add_node("supervisor_node", supervisor_node)
    builder.add_node("correctness_node", correctness_node)
    builder.add_node("complexity_node", complexity_node)
    builder.add_node("style_node", style_node)
    builder.add_node("similarity_node", similarity_node)
    builder.add_node("aggregation_node", aggregation_node)
    builder.add_node("explainability_node", explainability_node)
    builder.add_node("recommendation_node", recommendation_node)
    builder.add_node("revision_node", revision_node)
    builder.add_node("score_projection_node", score_projection_node)

    # 2. Sequential & Conditional Flow
    builder.add_edge(START, "supervisor_node")
    builder.add_conditional_edges(
        "supervisor_node",
        check_compilation_failure,
        {
            "correctness_node": "correctness_node",
            "explainability_node": "explainability_node"
        }
    )

    # 3. Parallel Fan-Out: Correctness triggers Complexity, Style, and Similarity concurrently
    builder.add_edge("correctness_node", "complexity_node")
    builder.add_edge("correctness_node", "style_node")
    builder.add_edge("correctness_node", "similarity_node")

    # 4. Join: All 3 parallel branches feed into Aggregation
    builder.add_edge("complexity_node", "aggregation_node")
    builder.add_edge("style_node", "aggregation_node")
    builder.add_edge("similarity_node", "aggregation_node")

    # 5. Pedagogical and Revision Flow
    builder.add_edge("aggregation_node", "explainability_node")
    builder.add_edge("explainability_node", "recommendation_node")
    builder.add_edge("recommendation_node", "revision_node")
    builder.add_edge("revision_node", "score_projection_node")
    builder.add_edge("score_projection_node", END)

    return builder.compile()

evaluation_graph = build_graph()
