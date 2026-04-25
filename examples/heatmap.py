"""Annotated heatmap, default preset."""

from pathlib import Path

from huitu import plot_heatmap

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sample_data" / "heatmap.csv"
OUT = ROOT / "output" / "heatmap.png"

fig, ax = plot_heatmap(DATA, annot=True, cbar_label="value", journal="default", save=OUT)
