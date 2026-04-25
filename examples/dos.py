"""Density of states with s/p/d projections."""

from pathlib import Path

from huitu import plot_dos

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sample_data" / "dos.txt"
OUT = ROOT / "output" / "dos.png"

fig, ax = plot_dos(DATA, journal="default", save=OUT)
