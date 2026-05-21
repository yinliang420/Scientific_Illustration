"""Rietveld refinement result plot (observed, calculated, difference)."""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from huitu._common import finalize
from huitu.layout.subplots import make_subplots
from huitu.style import use_journal


def _to_rietveld_array(data):
    if isinstance(data, pd.DataFrame):
        return data.to_numpy(dtype=float)
    if isinstance(data, (str, Path)):
        df = pd.read_csv(data, sep=None, engine="python", comment="#")
        df = df.apply(pd.to_numeric, errors="coerce").dropna(how="all")
        return df.to_numpy(dtype=float)
    if isinstance(data, np.ndarray):
        return data.astype(float)
    raise TypeError(f"plot_rietveld expects path/DataFrame/ndarray; got {type(data).__name__}")


def plot_rietveld(
    data,
    ax=None,
    journal: str = "default",
    save=None,
    hkl_positions: Iterable[float] | None = None,
    bragg_label: str = "",
    **kwargs,
):
    """Two-panel Rietveld refinement plot (main + difference).

    data
        3-column ``(2theta, I_obs, I_calc)`` or 4-column
        ``(2theta, I_obs, I_calc, I_bkg)`` path/array/DataFrame.
    hkl_positions
        Optional sequence of 2theta positions; short vertical tick marks are
        drawn at the bottom of the main panel.
    bragg_label
        Legend label for the Bragg tick marks.

    ``ax`` is ignored — this plot always creates its own 2-row layout.
    """
    if ax is not None:
        warnings.warn("plot_rietveld builds its own layout; ax ignored",
                      stacklevel=2)
    arr = _to_rietveld_array(data)
    if arr.shape[1] < 3:
        raise ValueError("plot_rietveld needs >=3 columns: 2theta, I_obs, I_calc")

    tt = arr[:, 0]
    iobs = arr[:, 1]
    icalc = arr[:, 2]
    ibkg = arr[:, 3] if arr.shape[1] >= 4 else None

    use_journal(journal)
    fig, axes = make_subplots(
        2, 1, journal=journal, panel_labels=False,
        sharex=True, gridspec_kw={"height_ratios": [3, 1]},
    )
    ax_main, ax_diff = axes[0], axes[1]

    obs_color = kwargs.pop("obs_color", "black")
    calc_color = kwargs.pop("calc_color", "tab:red")
    bkg_color = kwargs.pop("bkg_color", "tab:blue")
    diff_color = kwargs.pop("diff_color", "tab:green")

    ax_main.plot(tt, iobs, ls="none", marker="o", mfc="none", mec=obs_color,
                 ms=2.5, mew=0.4, label=r"$I_{obs}$")
    ax_main.plot(tt, icalc, color=calc_color, lw=0.8, label=r"$I_{calc}$")
    if ibkg is not None:
        ax_main.plot(tt, ibkg, color=bkg_color, lw=0.6, ls="--", label="bkg")
    ax_main.set_ylabel("Intensity (a.u.)")

    if hkl_positions is not None:
        hkl = np.asarray(list(hkl_positions), dtype=float)
        y0 = float(np.min(iobs))
        span = float(np.max(iobs) - y0)
        tick_y = y0 - 0.05 * span
        tick_h = 0.04 * span
        ax_main.vlines(hkl, tick_y - tick_h, tick_y, color="black", lw=0.6,
                       label=bragg_label or None)

    ax_main.margins(y=0.05)
    ax_main.legend(loc="best")

    diff = iobs - icalc
    ax_diff.plot(tt, diff, color=diff_color, lw=0.6,
                 label=r"$I_{obs} - I_{calc}$")
    ax_diff.axhline(0.0, color="grey", lw=0.4, ls="--")
    ax_diff.set_xlabel(r"2$\theta$ ($^{\circ}$)")
    ax_diff.set_ylabel("diff")

    finalize(fig, save)
    return fig, ax_main
