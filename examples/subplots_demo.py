"""2x2 panel layout with (a)(b)(c)(d) labels, Nature preset."""

from pathlib import Path

from huitu import make_subplots, plot_xrd, plot_raman, plot_cv, plot_eis

ROOT = Path(__file__).resolve().parent
SAMPLES = ROOT / "sample_data"
OUT = ROOT / "output" / "subplots_demo.png"

fig, axes = make_subplots(2, 2, journal="nature", figsize=(7, 5))

plot_xrd(SAMPLES / "xrd.txt", ax=axes[0, 0])
plot_raman(SAMPLES / "raman.txt", ax=axes[0, 1])
plot_cv(SAMPLES / "cv.txt", ax=axes[1, 0])
plot_eis(SAMPLES / "eis.txt", ax=axes[1, 1])

fig.tight_layout()
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, bbox_inches="tight")
