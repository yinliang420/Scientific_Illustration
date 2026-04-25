"""Grouped/stacked bar plot."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from huitu._common import finalize, prepare_axes


def _to_frame(data):
    if isinstance(data, pd.DataFrame):
        return data
    if isinstance(data, (str, Path)):
        return pd.read_csv(data, sep=None, engine="python")
    if isinstance(data, np.ndarray):
        if data.ndim != 2 or data.shape[1] < 2:
            raise ValueError("ndarray must have shape (N, >=2)")
        cols = ["category"] + [f"v{i}" for i in range(data.shape[1] - 1)]
        return pd.DataFrame(data, columns=cols)
    if isinstance(data, tuple) and len(data) == 2:
        return pd.DataFrame({"category": list(data[0]), "value": list(data[1])})
    raise TypeError("plot_bar expects a DataFrame, CSV path, ndarray, or (categories, values) tuple")


def plot_bar(
    data,
    ax=None,
    journal: str = "default",
    save=None,
    stacked: bool = False,
    width: float = 0.8,
    xlabel: str = "",
    ylabel: str = "Value",
    **kwargs,
):
    """Plot grouped (default) or stacked bars from a DataFrame.

    The first column is treated as the category axis; the remaining numeric
    columns become bar groups.
    """
    fig, ax = prepare_axes(ax, journal)
    df = _to_frame(data)

    categories = df.iloc[:, 0].astype(str).to_numpy()
    value_cols = df.columns[1:]
    n_cat = len(categories)
    n_grp = len(value_cols)
    x = np.arange(n_cat)

    if stacked:
        bottom = np.zeros(n_cat)
        for col in value_cols:
            vals = df[col].to_numpy(dtype=float)
            ax.bar(x, vals, width=width, bottom=bottom, label=col, **kwargs)
            bottom += vals
    else:
        group_w = width / max(n_grp, 1)
        for i, col in enumerate(value_cols):
            vals = df[col].to_numpy(dtype=float)
            offset = (i - (n_grp - 1) / 2) * group_w
            ax.bar(x + offset, vals, width=group_w, label=col, **kwargs)

    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(loc="best")

    finalize(fig, save)
    return fig, ax
