"""Scatter with error bars + linear fit, default preset."""

from pathlib import Path

from huitu import plot_scatter

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sample_data" / "scatter.csv"
OUT = ROOT / "output" / "scatter.png"

fig, ax = plot_scatter(DATA, journal="default", fit=True, xlabel="x", ylabel="y", label="data", save=OUT)
