"""Density of states (total + projected) plotting."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from huitu._common import coerce_xy, finalize, prepare_axes


def _read_dos(data):
    if isinstance(data, pd.DataFrame):
        return data.to_numpy(dtype=float), list(data.columns)
    if isinstance(data, (str, Path)):
        df = pd.read_csv(data, sep=None, engine="python", comment="#")
        df = df.apply(pd.to_numeric, errors="coerce").dropna(how="all")
        return df.to_numpy(dtype=float), list(df.columns)
    if isinstance(data, np.ndarray):
        return data.astype(float), [f"col{i}" for i in range(data.shape[1])]
    return None, None


def plot_dos(
    data,
    ax=None,
    journal: str = "default",
    save=None,
    projections: dict | None = None,
    orientation: str = "horizontal",
    fill_total: bool = True,
    **kwargs,
):
    """Plot DOS. Energy on one axis, DOS on the other.

    data
        Two-column (E, total_DOS) path/array/DataFrame, or wider table whose
        columns are auto-treated as total + projections when ``projections``
        is not explicitly passed.
    projections
        Optional ``{label: dos_array}`` mapping; each is plotted as a line.
    orientation
        ``'horizontal'`` (default): energy on x, DOS on y.
        ``'vertical'``: DOS on x, energy on y (useful alongside band plots).
    """
    if orientation not in ("horizontal", "vertical"):
        raise ValueError("orientation must be 'horizontal' or 'vertical'")

    fig, ax = prepare_axes(ax, journal)

    arr, cols = _read_dos(data)
    if arr is not None and arr.shape[1] >= 2:
        energy = arr[:, 0]
        total = arr[:, 1]
        extras = {cols[i]: arr[:, i] for i in range(2, arr.shape[1])} if cols else {}
    else:
        energy, total = coerce_xy(data)
        extras = {}

    if projections is None:
        projections = extras

    def _plot(x, y, **kw):
        if orientation == "horizontal":
            ax.plot(x, y, **kw)
        else:
            ax.plot(y, x, **kw)

    if fill_total:
        if orientation == "horizontal":
            ax.fill_between(energy, 0, total, color="grey", alpha=0.3, label="total")
        else:
            ax.fill_betweenx(energy, 0, total, color="grey", alpha=0.3, label="total")
    _plot(energy, total, color="black", lw=1.0, label=None if fill_total else "total", **kwargs)

    for label, vals in projections.items():
        if str(label).lower() == "total":
            continue
        _plot(energy, np.asarray(vals, dtype=float), lw=1.0, label=label)

    if orientation == "horizontal":
        ax.axvline(0.0, color="grey", lw=0.6, ls="--")
        ax.set_xlabel(r"E - E$_F$ (eV)")
        ax.set_ylabel("DOS (states/eV)")
    else:
        ax.axhline(0.0, color="grey", lw=0.6, ls="--")
        ax.set_xlabel("DOS (states/eV)")
        ax.set_ylabel(r"E - E$_F$ (eV)")

    handles, labels = ax.get_legend_handles_labels()
    if labels:
        ax.legend(loc="best")

    finalize(fig, save)
    return fig, ax
