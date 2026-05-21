"""BET N₂ adsorption isotherm + linear-plot demo (v0.6)."""

from pathlib import Path

import numpy as np

from huitu import plot_bet

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / "bet.png"
OUT.parent.mkdir(exist_ok=True)

# Synthetic Type-IV-ish isotherm: standard BET-shape rise + a desorption
# branch with a thin hysteresis loop.
rng = np.random.default_rng(2026)
p_rel = np.linspace(0.01, 0.99, 35)
# Underlying BET-form with C=80, V_m=12 cm³ g⁻¹.
V_m_true, C_true = 12.0, 80.0
v_ads = (V_m_true * C_true * p_rel) / ((1 - p_rel) * (1 + (C_true - 1) * p_rel))
v_ads += rng.normal(0, 0.4, size=p_rel.size)
v_des = v_ads + 1.5 * np.exp(-((p_rel - 0.7) ** 2) / 0.02)

fig, axes, metrics = plot_bet(
    (p_rel, v_ads, v_des),
    journal="nature",
    label="MnO₂-Cu",
    save=OUT,
)
print(f"Vm = {metrics['V_m']:.2f} cm³ g⁻¹")
print(f"S_BET = {metrics['S_BET']:.1f} m² g⁻¹")
print(f"C = {metrics['C']:.1f}")
print(f"R² = {metrics['R2']:.4f}")
