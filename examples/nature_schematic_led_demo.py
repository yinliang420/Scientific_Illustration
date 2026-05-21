"""End-to-end demo: ``archetype.schematic_led`` + materials-science plot_*.

Reproduces the layout pattern of a Nature-style materials paper Fig 1
(schematic-led composite). The hero panel carries a synthetic mechanism
schematic; the support row carries real materials-characterization
plots driven by ``examples/sample_data/``.

This is the closest huitu has to a one-page "this is what we mean by
*figure archetype*" demo.

Run from repo root::

    python examples/nature_schematic_led_demo.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

import huitu

SAMPLE = Path(__file__).parent / "sample_data"
OUT = Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)


def _draw_hero_schematic(ax) -> None:
    """A simple three-stage 'pristine → activated → cycled' mechanism cartoon."""
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.set_axis_off()

    stages = [
        ("Pristine",   huitu.role("baseline_soft"), 1.5),
        ("Activated",  huitu.role("hero_soft"),     5.0),
        ("Cycled",     huitu.role("hero"),          8.5),
    ]
    box_w, box_h = 1.8, 2.4
    for label, color, cx in stages:
        rect = mpatches.FancyBboxPatch(
            (cx - box_w / 2, 0.8), box_w, box_h,
            boxstyle="round,pad=0.06,rounding_size=0.20",
            linewidth=1.0, edgecolor=huitu.role("neutral_dark"),
            facecolor=color, alpha=0.85,
        )
        ax.add_patch(rect)
        text_color = "white" if color == huitu.role("hero") else huitu.role("neutral_dark")
        ax.text(cx, 0.8 + box_h / 2, label, ha="center", va="center",
                fontsize=10, fontweight="bold", color=text_color)

    # arrows between stages
    for x_from, x_to in [(2.4, 4.1), (5.9, 7.6)]:
        ax.annotate("", xy=(x_to, 2.0), xytext=(x_from, 2.0),
                    arrowprops=dict(arrowstyle="->", lw=1.2,
                                    color=huitu.role("neutral_dark")))

    ax.text(5.0, 3.6, "Design principle: capacity is gained without changing payload identity",
            ha="center", va="center", fontsize=8, color=huitu.role("neutral_dark"))


def main() -> None:
    # 4 support panels in the bottom row.
    fig, ax = huitu.archetype.schematic_led(
        journal="nature", n_supports=4,
    )

    # ── hero ────────────────────────────────────────────────────────────────
    _draw_hero_schematic(ax["hero"])

    # ── supports: real materials-characterization data ─────────────────────
    huitu.plot_xrd(str(SAMPLE / "xrd.txt"), ax=ax["supports"][0])
    ax["supports"][0].set_title("XRD", fontsize=8, pad=4)

    huitu.plot_cv(str(SAMPLE / "cv.txt"), ax=ax["supports"][1])
    ax["supports"][1].set_title("CV", fontsize=8, pad=4)

    huitu.plot_eis(str(SAMPLE / "eis.txt"), ax=ax["supports"][2])
    ax["supports"][2].set_title("EIS", fontsize=8, pad=4)

    # 4th support: synthetic 4-method bar to showcase semantic-palette dogfood.
    sup3 = ax["supports"][3]
    methods = ["Pristine", "Activated", "Cycled"]
    capacity = np.array([85, 142, 168])
    sup3.bar(np.arange(3), capacity,
             color=[huitu.role("baseline_soft"),
                    huitu.role("hero_soft"),
                    huitu.role("hero")],
             edgecolor="white", linewidth=0.4)
    sup3.set_xticks(np.arange(3))
    sup3.set_xticklabels(methods, fontsize=6.5, rotation=0)
    sup3.set_ylabel("Capacity (mAh g⁻¹)", fontsize=7)
    sup3.set_title("Capacity by stage", fontsize=8, pad=4)
    sup3.spines["top"].set_visible(False)
    sup3.spines["right"].set_visible(False)

    fig.savefig(OUT / "nature_schematic_led_demo.png", bbox_inches="tight", dpi=300)
    fig.savefig(OUT / "nature_schematic_led_demo.svg", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT.relative_to(Path.cwd())}/nature_schematic_led_demo.{{png,svg}}")


if __name__ == "__main__":
    main()
