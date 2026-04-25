"""Multi-curve line plot with temperature on twin Y axis, Wiley preset."""

from pathlib import Path

from huitu import plot_line

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sample_data" / "line.csv"
OUT = ROOT / "output" / "line.png"

fig, ax = plot_line(
    DATA,
    journal="wiley",
    twin_cols=["temperature"],
    xlabel="Time (s)",
    ylabel="V, I",
    ylabel_right=r"Temperature ($^{\circ}$C)",
    save=OUT,
)
