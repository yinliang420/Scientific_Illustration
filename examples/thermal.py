"""Combined TGA + DSC with twin-axis layout."""

from pathlib import Path

from huitu import plot_thermal

ROOT = Path(__file__).resolve().parent
TGA = ROOT / "sample_data" / "tga.txt"
DSC = ROOT / "sample_data" / "dsc.txt"
OUT = ROOT / "output" / "thermal.png"

fig, ax = plot_thermal(TGA, dsc_data=DSC, mode="both", journal="elsevier", save=OUT)
