"""Render the bug-count and test-coverage charts for the hardening case study.

Uses huitu's own `plot_bar`, `role()`, and `use_journal()` to draw the figures
that ship inside `docs/hardening-case-study.html`. Dogfooding: the writeup
about huitu uses huitu to make its own charts.

Output: two PNG files under `docs/showcase/`:

  hardening-bugs-by-round.png      stacked P0/P1/P2 counts per round (8/7/1)
  hardening-tests-by-round.png     adversarial cases added per round (67/56/100)

Run from repo root:  python tools/render_hardening_charts.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import huitu


OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "showcase"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# Round-by-round bug counts, split by severity (matches the HTML table).
# Round 1: 8 bugs   = 3 P0 + 4 P1 + 1 P2
# Round 2: 7 bugs   = 3 P0 + 2 P1 + 2 P2
# Round 3: 1 bug    = 0 P0 + 1 P1 + 0 P2
_ROUND_LABELS = ["Round 1", "Round 2", "Round 3"]
_P0 = np.array([3, 3, 0], dtype=float)
_P1 = np.array([4, 2, 1], dtype=float)
_P2 = np.array([1, 2, 0], dtype=float)


def _draw_bugs_by_round() -> Path:
    """Stacked-bar chart of bugs found per round, split by severity."""
    huitu.use_journal("default")
    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    x = np.arange(len(_ROUND_LABELS))
    width = 0.55

    # Severity colors use the semantic palette so the chart speaks the
    # same visual language as the rest of huitu.
    c_p0 = huitu.role("negative")        # most severe — red
    c_p1 = huitu.role("baseline")        # brick red — should-fix
    c_p2 = huitu.role("neutral")         # mid grey — nice-to-have

    ax.bar(x, _P0, width, label="P0", color=c_p0, edgecolor="white", linewidth=0.6)
    ax.bar(x, _P1, width, bottom=_P0, label="P1", color=c_p1, edgecolor="white", linewidth=0.6)
    ax.bar(x, _P2, width, bottom=_P0 + _P1, label="P2", color=c_p2, edgecolor="white", linewidth=0.6)

    # Numeric total above each bar.
    totals = _P0 + _P1 + _P2
    for xi, t in zip(x, totals):
        ax.text(xi, t + 0.25, f"{int(t)}", ha="center", va="bottom",
                fontsize=10, fontweight="bold", color=huitu.role("neutral_dark"))

    ax.set_xticks(x)
    ax.set_xticklabels(_ROUND_LABELS)
    ax.set_ylabel("Bugs found / fixed")
    ax.set_ylim(0, 10)
    ax.set_yticks([0, 2, 4, 6, 8, 10])
    ax.set_title("Bugs surfaced per round (by severity)", fontsize=10, pad=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(loc="upper right", frameon=False, fontsize=8, ncol=3,
              handlelength=1.2, columnspacing=1.0)

    out = OUT_DIR / "hardening-bugs-by-round.png"
    fig.savefig(out, bbox_inches="tight", dpi=300)
    plt.close(fig)
    return out


def _draw_tests_by_round() -> Path:
    """Adversarial test cases added per round vs. cumulative coverage."""
    huitu.use_journal("default")
    fig, ax = plt.subplots(figsize=(5.2, 3.2))

    per_round = np.array([67, 56, 100], dtype=float)
    cumulative = np.cumsum(per_round)
    x = np.arange(len(_ROUND_LABELS))
    width = 0.55

    bars = ax.bar(x, per_round, width, label="cases written this round",
                  color=huitu.role("hero"), edgecolor="white", linewidth=0.6)

    # Place per-bar labels INSIDE the top of each bar (white text on hero blue),
    # so they never collide with the cumulative-line twin axis crossing them.
    for xi, val in zip(x, per_round):
        ax.text(xi, val - 4, f"{int(val)}", ha="center", va="top",
                fontsize=11, fontweight="bold", color="white")

    # Cumulative line on a twin axis. Place "Σ N" markers BELOW the line marker
    # (va="top" with negative offset) so the bar tops have clear visual space.
    ax2 = ax.twinx()
    ax2.plot(x, cumulative, color=huitu.role("positive"), marker="o",
             linewidth=1.8, markersize=6, label="cumulative")
    # Anchor each Σ-label below its marker so it stays out of the bar's value.
    for xi, val in zip(x, cumulative):
        ax2.annotate(f"Σ {int(val)}", xy=(xi, val),
                     xytext=(6, 0), textcoords="offset points",
                     ha="left", va="center",
                     fontsize=8.5, color=huitu.role("positive"), fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(_ROUND_LABELS)
    ax.set_ylabel("Cases this round", color=huitu.role("hero"))
    # Generous headroom so the cumulative line never touches the bar tops.
    ax.set_ylim(0, 180)
    ax.tick_params(axis="y", colors=huitu.role("hero"))

    ax2.set_ylabel("Cumulative cases", color=huitu.role("positive"))
    ax2.set_ylim(0, 360)
    ax2.tick_params(axis="y", colors=huitu.role("positive"))

    ax.set_title("Adversarial test cases written per round", fontsize=10, pad=8)
    ax.spines["top"].set_visible(False)
    ax2.spines["top"].set_visible(False)

    out = OUT_DIR / "hardening-tests-by-round.png"
    fig.savefig(out, bbox_inches="tight", dpi=300)
    plt.close(fig)
    return out


def main() -> None:
    bugs_path = _draw_bugs_by_round()
    tests_path = _draw_tests_by_round()
    print(f"wrote {bugs_path.relative_to(Path.cwd())}")
    print(f"wrote {tests_path.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
