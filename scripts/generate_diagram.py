"""
Generate the VibeFinder AI system architecture diagram.
Output: assets/architecture.png

Usage: python scripts/generate_diagram.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUTPUT = Path(__file__).parent.parent / "assets" / "architecture.png"

# ── Color palette ─────────────────────────────────────────────────────────────
BG = "#0d1117"
CLAUDE = "#1f6feb"       # blue — Claude API calls
LOGIC = "#238636"        # green — rule-based logic
RELIABILITY = "#6e40c9"  # purple — reliability/guardrail
IO = "#21262d"           # dark — I/O boxes
DATA = "#b45309"         # amber — data source
WHITE = "#e6edf3"
GRAY = "#8b949e"
ARROW = "#58a6ff"


def box(ax, x, y, w, h, text, color, fontsize=10, text_color=WHITE):
    patch = FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.12",
        facecolor=color, edgecolor="#30363d", linewidth=1.5, zorder=3,
    )
    ax.add_patch(patch)
    ax.text(
        x, y, text,
        ha="center", va="center", fontsize=fontsize,
        color=text_color, fontweight="bold", zorder=4,
        multialignment="center", linespacing=1.4,
    )


def arrow(ax, x1, y1, x2, y2, label=""):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="-|>", color=ARROW, lw=1.8,
            connectionstyle="arc3,rad=0.0",
        ),
        zorder=2,
    )
    if label:
        mx, my = (x1 + x2) / 2 + 0.08, (y1 + y2) / 2
        ax.text(mx, my, label, fontsize=8, color=GRAY, zorder=5,
                ha="left", va="center", fontstyle="italic")


def main():
    fig, ax = plt.subplots(figsize=(13, 10))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # Title
    ax.text(6.5, 9.55, "VibeFinder AI — System Architecture",
            ha="center", va="center", fontsize=15, color=WHITE,
            fontweight="bold", fontfamily="monospace")

    # ── Boxes (x, y, w, h) ────────────────────────────────────────────────────

    # User I/O
    box(ax, 6.5, 8.85, 4.5, 0.75, "User  —  Natural Language Query", IO, fontsize=10)

    # Guardrails (left column)
    box(ax, 2.2, 7.5, 2.6, 0.8, "Input Guardrails\n(length · sanitize)", RELIABILITY, 9)

    # Step 1 — Claude extract
    box(ax, 6.5, 7.5, 5.0, 0.8,
        "Claude Agent  ·  Step 1\nextract_music_preferences  (tool call)", CLAUDE, 9)

    # Step 2 — optional refine
    box(ax, 6.5, 6.35, 5.0, 0.8,
        "Claude Agent  ·  Step 2  (if confidence < 0.6)\nrefine_preferences  (tool call)", CLAUDE, 9)

    # Structured prefs label (between steps)
    ax.text(6.5, 6.9, "structured preferences  +  confidence score",
            ha="center", va="center", fontsize=8, color=GRAY, fontstyle="italic", zorder=5)

    # Recommender
    box(ax, 6.5, 5.2, 4.5, 0.8,
        "Rule-Based Recommender\nscore_song( )  →  rank  →  top-K", LOGIC, 9)

    # Song catalog (right column)
    box(ax, 11.2, 5.2, 2.4, 0.8, "Song Catalog\n(18 tracks, CSV)", DATA, 9)

    # Step 3 — Claude explain
    box(ax, 6.5, 4.05, 5.0, 0.8,
        "Claude Agent  ·  Step 3\nGenerate natural language explanation", CLAUDE, 9)

    # Evaluation harness (left column, lower)
    box(ax, 2.2, 4.05, 2.6, 0.8, "Evaluation\nHarness", RELIABILITY, 9)

    # Output
    box(ax, 6.5, 2.9, 4.5, 0.75,
        "Recommendations  +  Explanation  →  User", IO, fontsize=10)

    # Logging (right column, lower)
    box(ax, 11.0, 3.5, 2.6, 0.65, "Structured\nLogging", RELIABILITY, 9)

    # ── Arrows ────────────────────────────────────────────────────────────────
    arrow(ax, 6.5, 8.48, 6.5, 7.90)                         # query → step1
    arrow(ax, 3.50, 7.5, 4.0, 7.5)                          # guardrails → step1
    arrow(ax, 6.5, 7.10, 6.5, 6.75)                         # step1 → step2
    arrow(ax, 6.5, 5.95, 6.5, 5.60)                         # step2 → recommender
    arrow(ax, 10.0, 5.2, 8.75, 5.2, label="reads")         # catalog → recommender
    arrow(ax, 6.5, 4.80, 6.5, 4.45)                         # recommender → step3
    arrow(ax, 3.50, 4.05, 4.0, 4.05)                        # eval → step3
    arrow(ax, 6.5, 3.65, 6.5, 3.28)                         # step3 → output
    arrow(ax, 10.05, 4.05, 9.85, 3.7)                       # logging connection

    # ── Legend ────────────────────────────────────────────────────────────────
    legend_handles = [
        mpatches.Patch(facecolor=CLAUDE, edgecolor="#30363d", label="Claude API calls"),
        mpatches.Patch(facecolor=LOGIC, edgecolor="#30363d", label="Rule-based logic"),
        mpatches.Patch(facecolor=RELIABILITY, edgecolor="#30363d", label="Reliability layer"),
        mpatches.Patch(facecolor=IO, edgecolor="#30363d", label="I/O"),
        mpatches.Patch(facecolor=DATA, edgecolor="#30363d", label="Data source"),
    ]
    leg = ax.legend(
        handles=legend_handles,
        loc="lower left", bbox_to_anchor=(0.01, 0.01),
        framealpha=0.4, facecolor="#161b22", edgecolor="#30363d",
        labelcolor=WHITE, fontsize=9,
    )

    plt.tight_layout(pad=0.3)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUTPUT, dpi=160, bbox_inches="tight", facecolor=BG)
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
