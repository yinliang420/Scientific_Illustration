"""Crystal dispatcher: falls back to ASE when VESTA_BIN is unset."""

import os
from pathlib import Path

from huitu import plot_crystal_vesta

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sample_data" / "crystal.cif"
OUT = ROOT / "output" / "crystal_vesta.png"

# Force the ASE fallback branch for demo purposes.
os.environ.pop("VESTA_BIN", None)

fig, axes = plot_crystal_vesta(DATA, save=str(OUT))
