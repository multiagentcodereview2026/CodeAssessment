from langgraph.graph import StateGraph, START, END
from workflow.state import EvaluationState

from agents.supervisor import supervisor_node
from agents.correctness import correctness_node
from agents.complexity import complexity_node
from agents.style import style_node
from agents.aggregation import aggregation_node
from agents.explainability import explainability_node
from agents.recommendation import recommendation_node
from agents.projection import score_projection_node

def check_compilation_failure(state: EvaluationState) -> str:
    """
    Always send execution results through the correctness node.

    The correctness node calculates the score deterministically.
    For compilation errors it will correctly produce 0 correctness.
    """
    return "correctness_node"

def build_graph():
    builder = StateGraph(EvaluationState)

    # 1. Register Nodes
    builder.add_node("supervisor_node", supervisor_node)
    builder.add_node("correctness_node", correctness_node)
    builder.add_node("complexity_node", complexity_node)
    builder.add_node("style_node", style_node)
    builder.add_node("aggregation_node", aggregation_node)
    builder.add_node("explainability_node", explainability_node)
    builder.add_node("recommendation_node", recommendation_node)
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

    # 3. Parallel Fan-Out: student grading uses correctness, complexity, and
    # style only. Similarity is recalculated from latest coursework records in
    # the instructor-only review endpoint.
    builder.add_edge("correctness_node", "complexity_node")
    builder.add_edge("correctness_node", "style_node")

    # 4. Join: both student-grading branches feed into aggregation.
    builder.add_edge("complexity_node", "aggregation_node")
    builder.add_edge("style_node", "aggregation_node")

    # 5. Pedagogical and Revision Flow
    builder.add_edge("aggregation_node", "explainability_node")
    builder.add_edge("explainability_node", "recommendation_node")
    # Official scoring should finish without waiting for optional AI code
    # generation. Students may request a revision from the saved result later.
    builder.add_edge("recommendation_node", "score_projection_node")
    builder.add_edge("score_projection_node", END)

    return builder.compile()

evaluation_graph = build_graph()
