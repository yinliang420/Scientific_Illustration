"""Demo of share_axes: left column shares x; right column shares y."""

from pathlib import Path

import numpy as np

from huitu import make_subplots, share_axes

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / "shared_axes_demo.png"

rng = np.random.default_rng(0)
fig, axes = make_subplots(2, 2, journal="default", figsize=(5.5, 4))
for i, a in enumerate(axes.ravel()):
    x = rng.normal(i, 1.0, 60)
    y = rng.normal(i, 1.0, 60)
    a.scatter(x, y, s=10)

# Left column: share x only; right column: share y only.
share_axes(axes[:, 0], which="x")
share_axes(axes[:, 1], which="y")

fig.savefig(OUT, bbox_inches="tight")
