"""Differential capacity (dQ/dV) demo (v0.6).

Synthesises a two-cycle GCD and renders dQ/dV — illustrates peak shift /
broadening on the second cycle (typical ageing signature).
"""

from pathlib import Path

import numpy as np

from huitu import plot_dqdv

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / "dqdv.png"
OUT.parent.mkdir(exist_ok=True)


def _cycle(v0_shift: float, broaden: float) -> tuple[np.ndarray, np.ndarray]:
    """Synthesise a two-plateau charge curve (V grows, Q grows)."""
    v = np.linspace(2.5, 4.4, 400)
    # Two sigmoid-like plateaus: V₁ ≈ 3.5 (broadened by Sn-Mn redox), V₂ ≈ 3.7
    q = 150.0 * (
        1.0 / (1.0 + np.exp(-(30.0 - broaden) * (v - (3.7 + v0_shift))))
        + 0.4 / (1.0 + np.exp(-(25.0 - broaden) * (v - (3.5 + v0_shift))))
    )
    return v, q


cycle_1 = _cycle(v0_shift=0.00, broaden=0.0)   # fresh cell
cycle_50 = _cycle(v0_shift=0.04, broaden=8.0)  # aged, peaks shifted + broadened

fig, ax = plot_dqdv(
    [cycle_1, cycle_50],
    labels=["cycle 1", "cycle 50"],
    journal="nature",
    save=OUT,
)
print(f"wrote {OUT}")
