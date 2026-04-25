"""XPS raw spectrum with Shirley baseline and three fitted components, Wiley preset."""

from pathlib import Path

import numpy as np

from huitu import plot_xps, read_xy

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sample_data" / "xps.txt"
OUT = ROOT / "output" / "xps_fitting.png"


def lorentz(x, c, w, a):
    return a * (w ** 2) / ((x - c) ** 2 + w ** 2)


x, y = read_xy(DATA)
baseline = 0.05 * (x - x.min()) + 0.5
fits = [
    (x, baseline + lorentz(x, 711.0, 1.4, 3.0), "Fe 2p$_{3/2}$"),
    (x, baseline + lorentz(x, 724.2, 1.5, 1.8), "Fe 2p$_{1/2}$"),
    (x, baseline + lorentz(x, 713.3, 1.8, 1.2), "satellite"),
]

fig, ax = plot_xps(
    DATA,
    journal="wiley",
    baseline=(x, baseline),
    fits=fits,
    save=OUT,
)
