"""Box plot / violin plot."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from huitu._common import finalize, prepare_axes


def _to_groups(data, x=None, y=None):
    """Return a list of (label, values) pairs."""
    if isinstance(data, pd.DataFrame):
        if x is not None and y is not None:
            groups = []
            for key, sub in data.groupby(x, sort=False):
                groups.append((str(key), sub[y].to_numpy(dtype=float)))
            return groups
        # Wide: each numeric column is a group.
        numeric = data.select_dtypes("number")
        return [(c, numeric[c].to_numpy(dtype=float)) for c in numeric.columns]
    if isinstance(data, (str, Path)):
        df = pd.read_csv(data)
        return _to_groups(df, x=x, y=y)
    if isinstance(data, (list, tuple)):
        return [(f"g{i+1}", np.asarray(v, dtype=float)) for i, v in enumerate(data)]
    if isinstance(data, np.ndarray):
        if data.ndim == 1:
            return [("g1", data.astype(float))]
        return [(f"g{i+1}", data[:, i].astype(float)) for i in range(data.shape[1])]
    raise TypeError(f"plot_box_violin expects DataFrame/CSV/list/ndarray; got {type(data).__name__}")


def plot_box_violin(
    data,
    ax=None,
    journal: str = "default",
    save=None,
    kind: str = "box",
    x: str | None = None,
    y: str | None = None,
    xlabel: str = "",
    ylabel: str = "Value",
    **kwargs,
):
    """Box or violin plot. ``kind='box'|'violin'``.

    For a long-format DataFrame pass ``x=`` (group column) and ``y=`` (value).

    ``**kwargs`` flow through to the underlying matplotlib call
    (``ax.boxplot`` when ``kind='box'``, ``ax.violinplot`` when
    ``kind='violin'``); pass kind-appropriate kwargs accordingly.
    """
    if kind not in ("box", "violin"):
        raise ValueError("kind must be 'box' or 'violin'")

    fig, ax = prepare_axes(ax, journal)
    groups = _to_groups(data, x=x, y=y)
    labels = [g[0] for g in groups]
    values = [g[1] for g in groups]
    positions = np.arange(1, len(groups) + 1)

    if kind == "box":
        ax.boxplot(values, positions=positions, widths=0.6, patch_artist=True, **kwargs)
    else:
        ax.violinplot(values, positions=positions, widths=0.8, showmeans=True, **kwargs)

    ax.set_xticks(positions)
    ax.set_xticklabels(labels)
    ax.set_xlabel(xlabel or (x or ""))
    ax.set_ylabel(ylabel if ylabel != "Value" else (y or ylabel))

    finalize(fig, save)
    return fig, ax
