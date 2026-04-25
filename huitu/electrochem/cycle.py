"""Cycling / rate performance plotting with optional Coulombic efficiency twin axis."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from huitu._common import finalize, prepare_axes
from huitu.readers.txt_csv import read_xy


def _to_frame(data: Any) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        return data
    if isinstance(data, (str, Path)):
        p = Path(data)
        # Try full-table parse first (preserves 3rd CE column when present);
        # fall back to the two-column reader on parse failure.
        try:
            df = pd.read_csv(p, sep=None, engine="python", comment="#")
        except (pd.errors.ParserError, ValueError):
            df = None
        if df is not None and df.select_dtypes("number").shape[1] >= 2:
            return df
        x, y = read_xy(p)
        return pd.DataFrame({"cycle": x, "capacity": y})
    if isinstance(data, np.ndarray):
        cols = ["cycle", "capacity", "ce"][: data.shape[1]]
        return pd.DataFrame(data, columns=cols)
    raise TypeError(f"unsupported cycle data: {type(data).__name__}")


def plot_cycle(
    data,
    ax=None,
    journal: str = "default",
    save=None,
    show_efficiency: bool = True,
    **kwargs,
):
    """Plot discharge capacity vs cycle number.

    If the input provides a third column it is treated as Coulombic efficiency
    and drawn on a twin right axis.
    """
    fig, ax = prepare_axes(ax, journal)
    df = _to_frame(data)

    cycle = df.iloc[:, 0].to_numpy(dtype=float)
    capacity = df.iloc[:, 1].to_numpy(dtype=float)
    ax.plot(cycle, capacity, "o-", color="tab:blue", markersize=3, label="Capacity", **kwargs)
    ax.set_xlabel("Cycle number")
    ax.set_ylabel("Specific capacity (mAh g$^{-1}$)", color="tab:blue")
    ax.tick_params(axis="y", colors="tab:blue")

    if show_efficiency and df.shape[1] >= 3:
        ce = df.iloc[:, 2].to_numpy(dtype=float)
        ax2 = ax.twinx()
        ax2.plot(cycle, ce, "s", color="tab:red", markersize=3, label="CE")
        ax2.set_ylabel("Coulombic efficiency (%)", color="tab:red")
        ax2.tick_params(axis="y", colors="tab:red")
        ax2.set_ylim(0, 105)

    finalize(fig, save)
    return fig, ax
