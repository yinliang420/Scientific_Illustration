"""Band structure, default preset."""

from pathlib import Path

from huitu import plot_band

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sample_data" / "band.txt"
OUT = ROOT / "output" / "band.png"

fig, ax = plot_band(
    DATA,
    kpoints=[("$\\Gamma$", 0.0), ("X", 0.5), ("M", 1.0)],
    ylim=(-5, 5),
    journal="default",
    save=OUT,
)
