"""Pourbaix (E-pH) diagram — polygon-region rendering."""

from __future__ import annotations

from typing import Iterable

import numpy as np

from huitu._common import _draw_regions, finalize, prepare_axes

# Nernst slope at 25 degC, 1 atm: (RT/F) * ln(10) in volts per pH unit.
NERNST_25C = 0.05916


def plot_pourbaix(
    data: Iterable[dict],
    ax=None,
    journal: str = "default",
    save=None,
    ph_range: tuple = (0.0, 14.0),
    e_range: tuple = (-1.0, 2.0),
    water_stability: bool = True,
    **kwargs,
):
    """Plot a Pourbaix diagram from a list of stability-region dicts.

    data
        Iterable of ``{label, vertices, color}`` dicts. ``vertices`` is a
        list of ``(pH, E)`` tuples forming a closed polygon (need not repeat
        the first point).
    ph_range, e_range
        Axis limits.
    water_stability
        Overlay the H2 (``E = -0.05916 * pH``) and O2
        (``E = 1.229 - 0.05916 * pH``) dashed lines at 25 degC, 1 atm.
    """
    fig, ax = prepare_axes(ax, journal)

    alpha = kwargs.pop("alpha", 0.45)
    edge_color = kwargs.pop("edgecolor", "black")

    _draw_regions(ax, data, alpha=alpha, edge_color=edge_color, lw=0.6)

    if water_stability:
        ph = np.linspace(ph_range[0], ph_range[1], 50)
        ax.plot(ph, -NERNST_25C * ph, ls="--", color="grey", lw=0.7,
                label=r"H$_2$/H$_2$O")
        ax.plot(ph, 1.229 - NERNST_25C * ph, ls="--", color="grey", lw=0.7,
                label=r"O$_2$/H$_2$O")
        ax.legend(loc="best", fontsize=6)

    ax.set_xlim(*ph_range)
    ax.set_ylim(*e_range)
    ax.set_xlabel("pH")
    ax.set_ylabel("E vs SHE (V)")

    finalize(fig, save)
    return fig, ax
