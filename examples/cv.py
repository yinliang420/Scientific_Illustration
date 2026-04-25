"""Cyclic voltammetry, ACS preset."""

from pathlib import Path

from huitu import plot_cv

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sample_data" / "cv.txt"
OUT = ROOT / "output" / "cv.png"

fig, ax = plot_cv(DATA, journal="acs", save=OUT)
