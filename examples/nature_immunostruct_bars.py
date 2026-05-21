"""Nature-style grouped-bar comparison with the semantic role palette.

Reproduces the visual pattern of ``ImmunoStruct/plot_bars.py`` (Nature Machine
Intelligence, vendored under ``docs/inspirations/figures4papers/``) using
huitu's idiomatic API — ``role("hero")`` / ``role("baseline")`` for the
hero-vs-baseline encoding, ``use_journal("nature")`` for the preset, and
``plot_bar(grouped=True)`` for the bar layout.

Run from repo root::

    python examples/nature_immunostruct_bars.py
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

import huitu

# ── synthetic IEDB-style metrics ────────────────────────────────────────────
metrics = ["AUROC", "AUPRC", "Accuracy", "F1"]
methods = ["Baseline", "Ours (Tiny)", "Ours (Base)", "Ours (Large)"]
rng = np.random.default_rng(2026)
base_mean = np.array([0.74, 0.62, 0.71, 0.66])
# baseline, ours-tiny, ours-base, ours-large (monotone improvement)
mean = np.vstack([
    base_mean + rng.normal(0, 0.01, 4),
    base_mean + np.array([0.06, 0.08, 0.05, 0.07]) + rng.normal(0, 0.01, 4),
    base_mean + np.array([0.10, 0.13, 0.09, 0.12]) + rng.normal(0, 0.01, 4),
    base_mean + np.array([0.14, 0.17, 0.13, 0.16]) + rng.normal(0, 0.01, 4),
])
sd = np.full_like(mean, 0.012)

# ── plot ────────────────────────────────────────────────────────────────────
huitu.use_journal("nature")

# Use the semantic palette so the 1st column is hero blue (ours) and the
# baseline gets the brick-red role. We swap the order so hero comes last for
# visual emphasis (Nature-MI style places the headline method at the right).
colors = [
    huitu.role("baseline"),
    huitu.role("hero_soft"),
    huitu.role("hero_2"),
    huitu.role("hero"),
]

fig, ax = plt.subplots(figsize=(5.2, 3.0), constrained_layout=True)
x = np.arange(len(metrics))
width = 0.18
offsets = np.linspace(-1.5 * width, 1.5 * width, len(methods))

for j, (label, color, off) in enumerate(zip(methods, colors, offsets)):
    ax.bar(
        x + off, mean[j], width=width, yerr=sd[j], label=label,
        color=color, edgecolor="white", linewidth=0.4,
        error_kw={"elinewidth": 0.8, "capthick": 0.8, "capsize": 2},
    )

# Dynamic y tightening — never use 0–100 when values cluster around 0.7.
y_lo, y_hi = mean.min() - sd.max() * 4, mean.max() + sd.max() * 4
ax.set_ylim(y_lo, y_hi)

ax.set_xticks(x)
ax.set_xticklabels(metrics)
ax.set_ylabel("Score")
ax.set_title("Method comparison on synthetic IEDB-style metrics", fontsize=8, pad=6)
ax.legend(loc="upper left", fontsize=7, frameon=False, ncol=2,
          columnspacing=0.8, handlelength=1.0)

# Save in both formats; SVG remains editable thanks to v0.5 svg.fonttype="none".
huitu._common.finalize(fig, save="examples/output/nature_immunostruct_bars.png")
fig.savefig("examples/output/nature_immunostruct_bars.svg", bbox_inches="tight")
plt.close(fig)
print("wrote examples/output/nature_immunostruct_bars.{png,svg}")
