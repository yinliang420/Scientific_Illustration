"""Pourbaix (E-pH) diagram built from inline region dicts."""

from pathlib import Path

from huitu import plot_pourbaix

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / "pourbaix.png"

regions = [
    {"label": "Fe", "color": "tab:blue",
     "vertices": [(0, -1), (14, -1), (14, -0.6), (0, -0.45)]},
    {"label": r"Fe$^{2+}$", "color": "tab:orange",
     "vertices": [(0, -0.45), (0, 0.8), (9, 0.2), (9, -0.6), (0, -0.6)]},
    {"label": r"Fe$_2$O$_3$", "color": "tab:green",
     "vertices": [(9, -0.6), (9, 0.2), (14, 0.2), (14, -0.6)]},
    {"label": r"FeO$_4^{2-}$", "color": "tab:red",
     "vertices": [(0, 0.8), (9, 0.2), (14, 0.2), (14, 2.0), (0, 2.0)]},
]

fig, ax = plot_pourbaix(regions, journal="default", save=OUT)
