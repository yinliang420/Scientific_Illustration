"""FTIR transmittance spectrum, ACS preset."""

from pathlib import Path

from huitu import plot_ftir

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sample_data" / "ftir.txt"
OUT = ROOT / "output" / "ftir.png"

fig, ax = plot_ftir(DATA, journal="acs", save=OUT)
