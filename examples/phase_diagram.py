"""Binary phase diagram from inline region dicts (Pb-Sn style)."""

from pathlib import Path

from huitu import plot_phase_diagram

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / "phase_diagram.png"

regions = [
    {"label": "Liquid", "color": "tab:red",
     "vertices": [(0, 327), (1, 232), (0.62, 183), (0, 327)]},
    {"label": r"$\alpha$", "color": "tab:blue",
     "vertices": [(0, 183), (0.19, 183), (0, 327)]},
    {"label": r"$\beta$", "color": "tab:green",
     "vertices": [(0.975, 183), (1, 183), (1, 232)]},
    {"label": r"$\alpha$ + $\beta$", "color": "tab:orange",
     "vertices": [(0.19, 183), (0.975, 183), (0.975, 20), (0.19, 20)]},
    {"label": r"$\alpha$ + L", "color": "#ddddff",
     "vertices": [(0, 327), (1, 232), (0.62, 183), (0.19, 183)]},
]

invariants = [(0.62, 183, "eutectic")]

fig, ax = plot_phase_diagram(
    regions,
    journal="default",
    xlabel="Sn mole fraction",
    invariants=invariants,
    save=OUT,
)
