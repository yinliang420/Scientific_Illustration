"""Grouped bar plot, RSC preset."""

from pathlib import Path

from huitu import plot_bar

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sample_data" / "bar.csv"
OUT = ROOT / "output" / "bar.png"

fig, ax = plot_bar(DATA, journal="rsc", ylabel="Capacity (mAh g$^{-1}$)", save=OUT)
