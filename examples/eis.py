"""Nyquist plot, IEEE preset."""

from pathlib import Path

from huitu import plot_eis

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sample_data" / "eis.txt"
OUT = ROOT / "output" / "eis.png"

fig, ax = plot_eis(DATA, labels=["sample"], journal="ieee", save=OUT)
