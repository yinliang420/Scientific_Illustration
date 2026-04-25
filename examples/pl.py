"""Photoluminescence spectrum, Nature preset."""

from pathlib import Path

from huitu import plot_pl

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sample_data" / "pl.txt"
OUT = ROOT / "output" / "pl.png"

fig, ax = plot_pl(DATA, journal="nature", normalize=True, save=OUT)
