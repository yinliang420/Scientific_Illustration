"""Radar / spider chart for multi-axis comparison."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from huitu._common import finalize
from huitu.style import use_journal


def _to_radar_frame(data, categories: Sequence[str] | None):
    if isinstance(data, pd.DataFrame):
        return data
    if isinstance(data, (str, Path)):
        df = pd.read_csv(data, sep=None, engine="python", index_col=0)
        return df
    if isinstance(data, dict):
        if categories is None:
            raise ValueError("categories= must be provided when data is a dict")
        rows = {name: list(vals) for name, vals in data.items()}
        return pd.DataFrame(rows, index=list(categories)).T
    if isinstance(data, np.ndarray):
        if categories is None:
            categories = [f"axis{i}" for i in range(data.shape[1])]
        return pd.DataFrame(data, columns=list(categories))
    raise TypeError("plot_radar expects DataFrame, CSV path, dict, or ndarray")


def _normalize(arr: np.ndarray, mode):
    if mode is None:
        return arr
    if mode == "per_axis":
        mn = np.min(arr, axis=0, keepdims=True)
        mx = np.max(arr, axis=0, keepdims=True)
        span = np.where(mx - mn == 0, 1.0, mx - mn)
        return (arr - mn) / span
    if mode == "global":
        mn = float(np.min(arr))
        mx = float(np.max(arr))
        span = mx - mn if mx > mn else 1.0
        return (arr - mn) / span
    raise ValueError("normalize must be None, 'per_axis', or 'global'")


def plot_radar(
    data,
    ax=None,
    journal: str = "default",
    save=None,
    categories: Sequence[str] | None = None,
    normalize: str | None = "per_axis",
    fill_alpha: float = 0.2,
    **kwargs,
):
    """Radar chart comparing multiple samples across several axes.

    data
        DataFrame whose columns are axis categories and rows are samples,
        a dict ``{sample: [values]}`` paired with ``categories=[...]``, or a
        2-D ndarray with optional ``categories=``.
    normalize
        ``'per_axis'`` (default), ``'global'``, or ``None`` for no scaling.
    """
    if ax is not None and ax.name != "polar":
        raise ValueError("plot_radar requires a polar axes")

    df = _to_radar_frame(data, categories)
    axes_labels = list(df.columns)
    sample_names = list(df.index)
    values = df.to_numpy(dtype=float)
    values = _normalize(values, normalize)

    n = len(axes_labels)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles_closed = angles + [angles[0]]

    if ax is None:
        use_journal(journal)
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="polar")
    else:
        fig = ax.figure

    for i, row in enumerate(values):
        row_closed = np.concatenate([row, row[:1]])
        ax.plot(angles_closed, row_closed, lw=1.0, label=sample_names[i], **kwargs)
        ax.fill(angles_closed, row_closed, alpha=fill_alpha)

    ax.set_xticks(angles)
    ax.set_xticklabels(axes_labels, fontsize=7)
    ax.tick_params(axis="y", labelsize=6, colors="#666666")

    # Place the radial tick labels midway between two category angles so they
    # don't collide with category text. Use half the angular spacing.
    if n >= 2:
        half_step_deg = float(np.degrees(angles[1] - angles[0]) / 2.0)
        ax.set_rlabel_position(half_step_deg)

    # Clamp radial axis when per-axis normalization puts everything in [0, 1].
    if normalize == "per_axis":
        ax.set_rlim(0, 1.0)

    ax.legend(loc="upper left", bbox_to_anchor=(1.1, 1.0), frameon=False,
              fontsize=6)

    finalize(fig, save)
    return fig, ax
