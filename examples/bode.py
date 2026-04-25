"""Bode plot (|Z| and phase) for an RC-like EIS response."""

from pathlib import Path

from huitu import plot_bode

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sample_data" / "bode.txt"
OUT = ROOT / "output" / "bode.png"

fig, ax = plot_bode(DATA, journal="rsc", save=OUT)
