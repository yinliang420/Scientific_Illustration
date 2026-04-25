"""Radar chart comparing 4 materials across 6 property axes."""

from pathlib import Path

from huitu import plot_radar

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sample_data" / "radar.csv"
OUT = ROOT / "output" / "radar.png"

fig, ax = plot_radar(DATA, journal="default", save=OUT)
