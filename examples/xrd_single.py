"""Single-sample XRD pattern, ACS-style preset."""

from pathlib import Path

from huitu import plot_xrd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sample_data" / "xrd.txt"
OUT = ROOT / "output" / "xrd_single.png"

fig, ax = plot_xrd(
    DATA,
    journal="acs",
    hkl={28.4: "(111)", 32.9: "(200)", 47.3: "(220)", 56.5: "(311)"},
    save=OUT,
)
