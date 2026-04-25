"""Grouped violin plot from long-format CSV."""

from pathlib import Path

from huitu import plot_box_violin

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sample_data" / "boxviolin.csv"
OUT = ROOT / "output" / "box_violin.png"

fig, ax = plot_box_violin(
    DATA, kind="violin", x="sample", y="value",
    xlabel="Sample", ylabel="Value", journal="rsc", save=OUT,
)
