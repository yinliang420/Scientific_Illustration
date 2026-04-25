"""Raman spectrum, RSC preset."""

from pathlib import Path

from huitu import plot_raman

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sample_data" / "raman.txt"
OUT = ROOT / "output" / "raman.png"

fig, ax = plot_raman(DATA, journal="rsc", save=OUT)
