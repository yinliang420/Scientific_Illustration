"""Galvanostatic charge-discharge, Elsevier preset."""

from pathlib import Path

from huitu import plot_gcd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sample_data" / "gcd.txt"
OUT = ROOT / "output" / "gcd.png"

fig, ax = plot_gcd(DATA, journal="elsevier", save=OUT)
