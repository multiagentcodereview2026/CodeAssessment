#!/usr/bin/env python3
"""
Generate publication-quality vector and high-DPI figures for IEEE paper.
"""
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

OUTPUT_DIR = Path(__file__).resolve().parent / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif", "Times"],
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "figure.autolayout": True,
})

# -------------------------------------------------------------
# Figure 3: Empirical Latency & Performance Comparison
# -------------------------------------------------------------
def generate_figure3():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 2.8), dpi=300)

    # Subplot 1: Latency (ms)
    metrics = ["TLS Handshake", "Query Round-Trip\n(SELECT 1)", "Problem Query\n(1,890 Rows)"]
    us_east = [2198.4, 553.90, 1842.1]
    mumbai = [240.2, 43.18, 406.2]

    x = np.arange(len(metrics))
    width = 0.35

    rects1 = ax1.bar(x - width/2, us_east, width, label="US-East (us-east-1)", color="#c0392b", alpha=0.85, edgecolor="black", linewidth=0.8)
    rects2 = ax1.bar(x + width/2, mumbai, width, label="Mumbai (ap-south-1)", color="#27ae60", alpha=0.85, edgecolor="black", linewidth=0.8)

    ax1.set_ylabel("Latency (ms, log scale)")
    ax1.set_title("(a) Infrastructure Round-Trip Latency")
    ax1.set_xticks(x)
    ax1.set_xticklabels(metrics, fontsize=8)
    ax1.set_yscale("log")
    ax1.set_ylim(10, 5000)
    ax1.grid(True, which="both", ls="--", alpha=0.4, axis="y")
    ax1.legend(loc="upper right", fontsize=8)

    # Add data labels
    for rect in rects1:
        h = rect.get_height()
        ax1.annotate(f"{h:.0f}ms", xy=(rect.get_x() + rect.get_width()/2, h),
                     xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontsize=7)
    for rect in rects2:
        h = rect.get_height()
        ax1.annotate(f"{h:.0f}ms", xy=(rect.get_x() + rect.get_width()/2, h),
                     xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontsize=7, fontweight="bold")

    # Subplot 2: Automated Test Suite Runtime (seconds)
    categories = ["Test Suite Runtime\n(251+ Pytest Tests)"]
    suite_us = [28.5]
    suite_mum = [4.70]

    x2 = np.arange(len(categories))
    r1 = ax2.bar(x2 - width/2, suite_us, width, label="US-East Database", color="#c0392b", alpha=0.85, edgecolor="black", linewidth=0.8)
    r2 = ax2.bar(x2 + width/2, suite_mum, width, label="Mumbai Database", color="#27ae60", alpha=0.85, edgecolor="black", linewidth=0.8)

    ax2.set_ylabel("Execution Time (seconds)")
    ax2.set_title("(b) Test Suite Execution Wall-Clock")
    ax2.set_xticks(x2)
    ax2.set_xticklabels(categories, fontsize=8)
    ax2.set_ylim(0, 35)
    ax2.grid(True, ls="--", alpha=0.4, axis="y")
    ax2.legend(loc="upper right", fontsize=8)

    for r in r1:
        h = r.get_height()
        ax2.annotate(f"{h:.1f}s", xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=8)
    for r in r2:
        h = r.get_height()
        ax2.annotate(f"{h:.2f}s (-83.5%)", xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=8, fontweight="bold")

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "fig3_latency_comparison.pdf", format="pdf")
    fig.savefig(OUTPUT_DIR / "fig3_latency_comparison.png", format="png", dpi=300)
    plt.close(fig)
    print("Generated Figure 3 (Latency Comparison)")

# -------------------------------------------------------------
# Figure 2: Complexity Rank Discrepancy & Scaled Worse Penalty
# -------------------------------------------------------------
def generate_figure2():
    fig, ax = plt.subplots(figsize=(6.8, 3.0), dpi=300)

    discrepancies = [0, 1, 2, 3, 4, 5, 6]
    labels = ["Exact Match (0)", "+1 Rank", "+2 Ranks", "+3 Ranks", "+4 Ranks", "+5 Ranks", ">= +6 Ranks"]

    # Targets: O(1) [r=1, W=9], O(n) [r=4, W=6], O(n^2) [r=6, W=4]
    scores_on = []
    scores_o1 = []
    scores_on2 = []

    for d in discrepancies:
        # O(n)
        p_on = min(25.0, d * (25.0 / 6.0))
        scores_on.append((25.0 - p_on) * 4)

        # O(1)
        p_o1 = min(25.0, d * (25.0 / 9.0))
        scores_o1.append((25.0 - p_o1) * 4)

        # O(n^2)
        p_on2 = min(25.0, d * (25.0 / 4.0))
        scores_on2.append((25.0 - p_on2) * 4)

    x = np.arange(len(discrepancies))
    ax.plot(x, scores_o1, marker="o", linewidth=2.0, color="#2980b9", label="Target: O(1) [9 worse ranks available]")
    ax.plot(x, scores_on, marker="s", linewidth=2.2, color="#27ae60", label="Target: O(n) [6 worse ranks available]")
    ax.plot(x, scores_on2, marker="^", linewidth=2.0, color="#d35400", label="Target: O(n²) [4 worse ranks available]")

    # Add shaded regions for classification
    ax.axhspan(80, 100, color="#2ecc71", alpha=0.15, label="Optimal / Near-Optimal (>=80%)")
    ax.axhspan(40, 80, color="#f39c12", alpha=0.15, label="Moderate Efficiency (40–80%)")
    ax.axhspan(0, 40, color="#e74c3c", alpha=0.15, label="Inefficient (<40%)")

    ax.set_xlabel("Asymptotic Rank Regression from Benchmark Target (Δ = r(p) - r(e))")
    ax.set_ylabel("Complexity Dimension Score (0–100%)")
    ax.set_title("Relative Penalty Decay Across Curated Complexity Baselines")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(-2, 105)
    ax.grid(True, ls="--", alpha=0.4)
    ax.legend(loc="upper right", fontsize=8)

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "fig2_complexity_decay.pdf", format="pdf")
    fig.savefig(OUTPUT_DIR / "fig2_complexity_decay.png", format="png", dpi=300)
    plt.close(fig)
    print("Generated Figure 2 (Complexity Decay)")

# -------------------------------------------------------------
# Figure 1: Architectural Workflow Diagram
# -------------------------------------------------------------
def generate_figure1():
    fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    def draw_box(x, y, w, h, text, color="#ecf0f1", edgecolor="#2c3e50", title=None):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=1.2,rounding_size=2",
                                      facecolor=color, edgecolor=edgecolor, linewidth=1.2)
        ax.add_patch(rect)
        if title:
            ax.text(x + w/2, y + h - 4.5, title, ha="center", va="center", fontsize=8, fontweight="bold", color="#2c3e50")
            ax.text(x + w/2, y + h/2 - 2, text, ha="center", va="center", fontsize=7.5, color="#34495e")
        else:
            ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=8, fontweight="bold", color="#2c3e50")

    def draw_arrow(x1, y1, x2, y2, text=None):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", lw=1.2, color="#2c3e50", shrinkA=2, shrinkB=2))
        if text:
            ax.text((x1+x2)/2, (y1+y2)/2 + 2, text, ha="center", va="bottom", fontsize=6.5, color="#7f8c8d")

    # Ingest Layer
    draw_box(4, 76, 22, 18, "React 18 / Monaco Editor\nLanguage & Source Ingest", color="#d4e6f1", title="Student Client")
    draw_arrow(26, 85, 34, 85, "POST /submit")

    # Gateway Layer
    draw_box(34, 76, 28, 18, "JWT Auth & Role Gate\nPublic/Hidden Case Loader", color="#d5f5e3", title="FastAPI API Gateway")

    # Concurrent Execution & AST
    draw_box(68, 86, 28, 12, "Docker Sandbox\n1.0 CPU, 256MB, 5s timeout", color="#fcf3cf", title="Execution Engine")
    draw_box(68, 68, 28, 12, "Tree-sitter AST & Dynamic IR\nPattern & Loop Depth Extraction", color="#fcf3cf", title="Static Analyzer")

    draw_arrow(62, 88, 68, 92)
    draw_arrow(62, 82, 68, 74)

    # LangGraph Container
    graph_box = patches.FancyBboxPatch((4, 20), 92, 42, boxstyle="round,pad=1.5,rounding_size=3",
                                       facecolor="#f8f9f9", edgecolor="#7f8c8d", linestyle="--", linewidth=1.2)
    ax.add_patch(graph_box)
    ax.text(50, 59, "LangGraph Evaluation StateGraph (Mixed-Evidence Pipeline)", ha="center", va="center", fontsize=8.5, fontweight="bold", color="#2c3e50")

    # Nodes in LangGraph
    draw_box(8, 40, 15, 14, "Correctness\nDeterministic Pass %", color="#ebdef0", title="Node 1")
    draw_arrow(82, 68, 15.5, 54, "State Init")

    draw_box(29, 47, 16, 11, "Complexity\n10-Level Rank Penalty", color="#ebdef0", title="Node 2a")
    draw_box(29, 33, 16, 11, "Code Style\nAST Heuristics (0-100)", color="#ebdef0", title="Node 2b")
    draw_arrow(23, 47, 29, 52)
    draw_arrow(23, 47, 29, 38)

    draw_box(50, 40, 16, 14, "Aggregation\n20C / 30K / 30S / 20T\n[79.0 Non-Accepted Cap]", color="#fadbd8", title="Node 3: Rubric")
    draw_arrow(45, 52, 50, 47)
    draw_arrow(45, 38, 50, 47)

    draw_box(70, 47, 12, 11, "Explainability\nEvidence Fallback", color="#ebdef0", title="Node 4")
    draw_box(84, 47, 10, 11, "DSA Path\nDAG Roadmap", color="#ebdef0", title="Node 5")
    draw_box(70, 33, 24, 11, "Score Projection\nVerified vs Hypothetical", color="#ebdef0", title="Node 6")

    draw_arrow(66, 47, 70, 52)
    draw_arrow(82, 52, 84, 52)
    draw_arrow(89, 47, 82, 44)

    # Output & Persistence Layer
    draw_box(10, 2, 38, 14, "Atomic Transaction (PostgreSQL Mumbai)\n194k Records, Alembic Head 20261022", color="#d5f5e3", title="Supabase Database")
    draw_box(54, 2, 42, 14, "Redact Remaining Hidden Cases\nSingle Feedback Case Disclosed", color="#d4e6f1", title="Sanitized Response")

    draw_arrow(70, 33, 30, 16)
    draw_arrow(82, 33, 75, 16)

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "fig1_architecture.pdf", format="pdf")
    fig.savefig(OUTPUT_DIR / "fig1_architecture.png", format="png", dpi=300)
    plt.close(fig)
    print("Generated Figure 1 (System Architecture)")

if __name__ == "__main__":
    generate_figure1()
    generate_figure2()
    generate_figure3()
    print("All figures successfully created in:", OUTPUT_DIR)
