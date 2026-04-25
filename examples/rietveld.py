"""Rietveld refinement plot: observed, calculated, background, difference."""

from pathlib import Path

from huitu import plot_rietveld

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sample_data" / "rietveld.txt"
OUT = ROOT / "output" / "rietveld.png"

fig, ax = plot_rietveld(
    DATA,
    journal="acs",
    hkl_positions=[28.4, 47.3, 56.5],
    bragg_label="Bragg",
    save=OUT,
)
