"""COHP plot with bonding / antibonding fills."""

from pathlib import Path

from huitu import plot_cohp

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sample_data" / "cohp.txt"
OUT = ROOT / "output" / "cohp.png"

fig, ax = plot_cohp(DATA, journal="default", save=OUT)
