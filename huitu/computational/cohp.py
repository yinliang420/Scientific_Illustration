"""COHP / ICOHP plotting.

Convention: raw COHP. Bonding states are negative (left of x=0, filled with
``bonding_color``); antibonding states are positive (right, filled with
``antibonding_color``). This is the opposite of the LOBSTER ``-COHP`` display.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from huitu._common import coerce_xy, finalize, prepare_axes


def _read_cohp(data):
    if isinstance(data, pd.DataFrame):
        return data.to_numpy(dtype=float), list(data.columns)
    if isinstance(data, (str, Path)):
        df = pd.read_csv(data, sep=None, engine="python", comment="#")
        df = df.apply(pd.to_numeric, errors="coerce").dropna(how="all")
        return df.to_numpy(dtype=float), list(df.columns)
    if isinstance(data, np.ndarray):
        return data.astype(float), [f"col{i}" for i in range(data.shape[1])]
    return None, None


def plot_cohp(
    data,
    ax=None,
    journal: str = "default",
    save=None,
    projections: dict | None = None,
    show_icohp: bool = False,
    **kwargs,
):
    """Plot a COHP curve.

    data
        2-column ``(energy, COHP)`` path/array/DataFrame, or wider table whose
        third column is treated as ICOHP (used when ``show_icohp=True``).
    projections
        Optional ``{label: cohp_array}`` mapping for per-bond projections.
    show_icohp
        If True, overlay the integrated COHP on a twin x-axis. When enabled,
        the returned ``ax`` is the primary COHP axes; the ICOHP twin is
        ``ax.figure.axes[1]``.
    """
    fig, ax = prepare_axes(ax, journal)

    arr, cols = _read_cohp(data)
    if arr is not None and arr.shape[1] >= 2:
        energy = arr[:, 0]
        cohp = arr[:, 1]
        icohp = arr[:, 2] if arr.shape[1] >= 3 else None
    else:
        energy, cohp = coerce_xy(data)
        icohp = None

    bonding_color = kwargs.pop("bonding_color", "tab:blue")
    antibonding_color = kwargs.pop("antibonding_color", "tab:red")
    line_color = kwargs.pop("color", "black")

    ax.fill_betweenx(energy, 0, cohp, where=(cohp <= 0),
                     color=bonding_color, alpha=0.35, label="bonding")
    ax.fill_betweenx(energy, 0, cohp, where=(cohp >= 0),
                     color=antibonding_color, alpha=0.35, label="antibonding")
    ax.plot(cohp, energy, color=line_color, lw=1.0, **kwargs)

    if projections:
        for label, vals in projections.items():
            ax.plot(np.asarray(vals, dtype=float), energy, lw=0.8, label=label)

    ax.axhline(0.0, color="grey", lw=0.6, ls="--")
    ax.axvline(0.0, color="black", lw=0.5)
    ax.set_xlabel("COHP (states/eV)")
    ax.set_ylabel(r"E - E$_F$ (eV)")

    if show_icohp and icohp is not None:
        ax2 = ax.twiny()
        ax2.plot(icohp, energy, color="tab:green", lw=1.0, ls="-.", label="ICOHP")
        ax2.set_xlabel("ICOHP (eV)")
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, loc="best")
    else:
        ax.legend(loc="best")

    finalize(fig, save)
    return fig, ax
