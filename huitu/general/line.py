"""Multi-curve line plot with optional twin Y axis."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

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
        cols = [f"col{i}" for i in range(data.shape[1])]
        return pd.DataFrame(data, columns=cols)
    if isinstance(data, tuple) and len(data) == 2:
        x = np.asarray(data[0], dtype=float)
        y = np.asarray(data[1], dtype=float)
        return pd.DataFrame({"x": x, "y": y})
    raise TypeError("plot_line expects a DataFrame, CSV path, ndarray, or (x, y) tuple")


def plot_line(
    data,
    ax=None,
    journal: str = "default",
    save=None,
    twin_cols: Iterable[str] | None = None,
    xlabel: str = "",
    ylabel: str = "",
    ylabel_right: str = "",
    **kwargs,
):
    """Plot every numeric column (other than the first) as a line vs the first.

    Columns listed in ``twin_cols`` are drawn on a twin right Y axis.
    """
    fig, ax = prepare_axes(ax, journal)
    df = _to_frame(data)

    xcol = df.columns[0]
    x = df[xcol].to_numpy(dtype=float)
    twin_set = set(twin_cols or [])

    ax2 = ax.twinx() if twin_set else None

    # Pick contrasting colors when twin axes are used, using huitu's curated
    # nature-cat palette (deep blue vs brick red) so the two y-axes read as
    # distinct at a glance.
    left_color = None
    right_color = None
    if ax2 is not None:
        try:
            from huitu.style import PALETTES

            left_color = PALETTES["nature-cat"][0]
            right_color = PALETTES["nature-cat"][1]
        except Exception:
            left_color = "#0C5DA5"
            right_color = "#D1362F"

    for col in df.columns[1:]:
        y = df[col].to_numpy(dtype=float)
        target = ax2 if col in twin_set else ax
        if ax2 is not None:
            c = right_color if col in twin_set else left_color
            target.plot(x, y, label=col, color=c, **kwargs)
        else:
            target.plot(x, y, label=col, **kwargs)

    ax.set_xlabel(xlabel or xcol)
    ax.set_ylabel(ylabel)
    if ax2 is not None:
        ax2.set_ylabel(ylabel_right)
        # Color-code the axis labels / tick labels to match their traces.
        if left_color:
            ax.yaxis.label.set_color(left_color)
            ax.tick_params(axis="y", colors=left_color)
        if right_color:
            ax2.yaxis.label.set_color(right_color)
            ax2.tick_params(axis="y", colors=right_color)

    lines, labels = ax.get_legend_handles_labels()
    if ax2 is not None:
        l2, lb2 = ax2.get_legend_handles_labels()
        lines += l2
        labels += lb2
    if labels:
        ax.legend(lines, labels, loc="best")

    finalize(fig, save)
    return fig, ax
