"""Cycling performance with Coulombic efficiency twin axis, Nature preset."""

from pathlib import Path

from huitu import plot_cycle

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sample_data" / "cycle.txt"
OUT = ROOT / "output" / "cycle.png"

fig, ax = plot_cycle(DATA, journal="nature", save=OUT)
