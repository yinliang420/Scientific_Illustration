"""Post-training trend curves with alpha-graduated line segments.

Reproduces the visual pattern of ``VIGIL/plot_posttraining.py`` using
huitu's API. The hero method uses ``role("hero")``; baselines map to
``role("baseline")``/``role("positive")``. Each line's alpha fades from
0.3 → 0.9 across the training steps to emphasise the latest checkpoint.

Run from repo root::

    python examples/nature_vigil_trend.py
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgba

import huitu


# ── synthetic post-training curve (DPO / DA-DPO / VIGIL-style "ours") ────────
methods = ["DPO", "DA-DPO", "Ours"]
colors = [huitu.role("baseline"), huitu.role("positive"), huitu.role("hero")]

steps = np.array([0, 200, 400, 600, 800])
results = np.array([
    [22.0, 25.5, 28.2, 29.5, 30.2],   # DPO
    [22.0, 33.5, 38.2, 39.8, 40.5],   # DA-DPO
    [22.0, 52.5, 56.8, 57.9, 58.5],   # Ours
])

# ── plot ────────────────────────────────────────────────────────────────────
huitu.use_journal("nature")
fig, ax = plt.subplots(figsize=(5.0, 3.2), constrained_layout=True)

# Baseline (step=0) as a dashed reference.
ax.axhline(results[0, 0], color=huitu.role("neutral"),
           linestyle="--", linewidth=0.8, alpha=0.6, zorder=1)

x_pos = np.arange(len(steps))
for m, (label, color) in enumerate(zip(methods, colors)):
    y = results[m]

    # Alpha-graduated LineCollection: each segment a touch more saturated
    # than the last, drawing the eye to the final checkpoint.
    pts = np.column_stack([x_pos, y])
    segments = np.stack([pts[:-1], pts[1:]], axis=1)
    rgb = np.array(to_rgba(color))
    alphas = np.linspace(0.35, 0.95, len(segments))
    seg_colors = [(rgb[0], rgb[1], rgb[2], a) for a in alphas]
    ax.add_collection(LineCollection(segments, colors=seg_colors,
                                      linewidths=2.0, capstyle="round",
                                      zorder=2 + m))
    ax.scatter(x_pos, y, color=color, s=18, zorder=4 + m, edgecolor="white",
               linewidth=0.5)
    # Direct end-of-line label (Nature style — fewer legend chores).
    ax.text(x_pos[-1] + 0.12, y[-1], label, color=color,
            fontsize=7, va="center", ha="left", fontweight="bold")

ax.set_xticks(x_pos)
ax.set_xticklabels(steps)
ax.set_xlim(-0.4, x_pos[-1] + 1.4)   # headroom for end labels
ax.set_ylim(15, 65)
ax.set_xlabel("Training step")
ax.set_ylabel("Metric (%)")
ax.set_title("Post-training trajectory (alpha-graduated)", fontsize=8, pad=6)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

huitu._common.finalize(fig, save="examples/output/nature_vigil_trend.png")
fig.savefig("examples/output/nature_vigil_trend.svg", bbox_inches="tight")
plt.close(fig)
print("wrote examples/output/nature_vigil_trend.{png,svg}")
