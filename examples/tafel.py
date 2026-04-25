"""Tafel plot with linear fit over the main Tafel region."""

from pathlib import Path

from huitu import plot_tafel

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sample_data" / "tafel.txt"
OUT = ROOT / "output" / "tafel.png"

fig, ax = plot_tafel(DATA, fit_range=(0.10, 0.35), journal="acs", save=OUT)
