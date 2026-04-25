"""UV-Vis absorbance with accompanying Tauc plot output."""

from pathlib import Path

from huitu import make_subplots, plot_uvvis

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sample_data" / "uvvis.txt"
OUT = ROOT / "output" / "uvvis.png"

fig, axes = make_subplots(1, 2, journal="wiley")
plot_uvvis(DATA, ax=axes[0])
plot_uvvis(DATA, ax=axes[1], tauc="direct")
fig.savefig(OUT)
