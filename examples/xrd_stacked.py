"""Stacked XRD patterns with vertical offset, Nature preset."""

from pathlib import Path

from huitu import plot_xrd

ROOT = Path(__file__).resolve().parent
STACK = sorted((ROOT / "sample_data" / "xrd_stacked").glob("*.txt"))
OUT = ROOT / "output" / "xrd_stacked.png"

fig, ax = plot_xrd(
    STACK,
    labels=[p.stem for p in STACK],
    journal="nature",
    offset=1.1,
    save=OUT,
)
