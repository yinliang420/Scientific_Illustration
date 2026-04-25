"""Main axes with zoomed inset showing a region of the XRD pattern."""

from pathlib import Path

from huitu import add_inset, plot_xrd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sample_data" / "xrd.txt"
OUT = ROOT / "output" / "inset_demo.png"

fig, ax = plot_xrd(DATA, journal="acs")
add_inset(ax, bounds=(0.55, 0.4, 0.4, 0.5), xlim=(27, 34), ylim=(0.2, 1.05))

OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, bbox_inches="tight")
