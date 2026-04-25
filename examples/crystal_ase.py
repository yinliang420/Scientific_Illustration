"""Crystal structure (NaCl) rendered via ASE in three orthogonal views."""

from pathlib import Path

from huitu import plot_crystal_ase

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sample_data" / "crystal.cif"
OUT = ROOT / "output" / "crystal_ase.png"

fig, axes = plot_crystal_ase(DATA, journal="default", radii=0.5, save=OUT)
