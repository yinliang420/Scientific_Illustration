"""Advanced layered chart types: parallel coordinates, waffle, streamgraph,
hexbin-density (premium variant), connected scatter.
"""

from __future__ import annotations

from typing import Iterable, Mapping, Sequence

import numpy as np
import matplotlib.patches as mpatches

from huitu._common import (
    expand_xlim_for_annos,
    finalize,
    marker_clearance_pts,
    prepare_axes,
)
from huitu.style import PALETTES, get_cmap
from ._license import require_pro


# ------------------------------------------------------------------
# Parallel coordinates
# ------------------------------------------------------------------
def plot_parallel(
    df,
    *,
    color_by: str | None = None,
    ax=None,
    journal: str = "default",
    save=None,
    palette: str = "ggsci-nejm",
    alpha: float = 0.7,
    linewidth: float = 1.0,
    normalize: bool = True,
    **kwargs,
):
    """Parallel-coordinates plot for a pandas DataFrame.

    All columns are drawn as parallel axes (in the dataframe order), one
    polyline per row. If ``color_by`` names a column, rows are colored by that
    column's value (categorical -> palette; numeric -> colormap on a normalized
    scale).
    """
    require_pro("plot_parallel")
    import pandas as pd  # local import: avoid hard dep at package import time

    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas.DataFrame")
    data = df.copy()
    color_series = None
    if color_by is not None:
        if color_by not in data.columns:
            raise KeyError(color_by)
        color_series = data[color_by]
        data = data.drop(columns=[color_by])

    # Keep numeric columns only.
    numeric_cols = [c for c in data.columns if np.issubdtype(data[c].dtype, np.number)]
    if len(numeric_cols) < 2:
        raise ValueError("need at least two numeric columns")
    mat = data[numeric_cols].to_numpy(dtype=float)

    # Parallel coordinates need a wider figure than the journal default to
    # leave room for N parallel axes + rotated tick labels.
    if ax is None:
        import matplotlib.pyplot as plt
        from huitu.style import use_journal as _uj
        _uj(journal)
        n_cols = len(numeric_cols)
        width = max(5.0, min(9.0, 1.0 * n_cols + 2.5))
        # Opt out of constrained_layout: the bottom subplots_adjust used when
        # tick labels are rotated is incompatible with constrained layout.
        fig, ax = plt.subplots(figsize=(width, width * 0.55),
                               constrained_layout=False)
    else:
        fig, ax = prepare_axes(ax, journal)
    n_rows, n_cols = mat.shape
    x = np.arange(n_cols)

    # Per-column normalization for plot (but keep original tick labels).
    col_min = np.nanmin(mat, axis=0)
    col_max = np.nanmax(mat, axis=0)
    spans = np.where(col_max - col_min > 0, col_max - col_min, 1.0)
    if normalize:
        plot_mat = (mat - col_min) / spans
    else:
        plot_mat = mat

    # Colors.
    if color_series is None:
        row_colors = [PALETTES.get(palette, PALETTES["ggsci-nejm"])[0]] * n_rows
    elif color_series.dtype.kind in "biufc":
        vals = color_series.to_numpy(dtype=float)
        lo, hi = np.nanmin(vals), np.nanmax(vals)
        norm = (vals - lo) / max(hi - lo, 1e-12)
        try:
            cmap = get_cmap(palette)
        except Exception:
            import matplotlib.cm as cm
            cmap = cm.get_cmap("viridis")
        row_colors = [cmap(n) for n in norm]
    else:
        categories = list(color_series.astype(str).unique())
        src = PALETTES.get(palette, PALETTES["ggsci-nejm"])
        cat_to_col = {c: src[i % len(src)] for i, c in enumerate(categories)}
        row_colors = [cat_to_col[str(v)] for v in color_series]

    for i, row in enumerate(plot_mat):
        if np.isnan(row).any():
            continue
        ax.plot(x, row, color=row_colors[i], alpha=alpha, linewidth=linewidth,
                zorder=2)

    # Vertical axis guides.
    for xi in x:
        ax.axvline(xi, color="#BBBBBB", linewidth=0.5, zorder=1)

    ax.set_xticks(x)
    # Longer labels get wrapped; short ones stay horizontal. 20 chars -> angle 20°.
    max_lab_len = max(len(c) for c in numeric_cols)
    rotation = 0 if max_lab_len <= 8 else (20 if max_lab_len <= 14 else 35)
    ax.set_xticklabels(numeric_cols, rotation=rotation,
                        ha="right" if rotation else "center")
    if normalize:
        ax.set_yticks([0.0, 0.5, 1.0])
        ax.set_ylabel("normalized")
    ax.set_xlim(-0.3, n_cols - 1 + 0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(True)
    ax.tick_params(which="both", top=False, right=False, left=True)
    # Reserve bottom room for rotated labels so they don't clip.
    if rotation:
        fig.subplots_adjust(bottom=0.22)

    # Categorical legend.
    if color_series is not None and color_series.dtype.kind not in "biufc":
        handles = [mpatches.Patch(color=c, label=k) for k, c in cat_to_col.items()]
        ax.legend(handles=handles, frameon=False, fontsize=7,
                  loc="upper right", bbox_to_anchor=(1.0, 1.02),
                  ncol=min(len(handles), 4))

    finalize(fig, save)
    return fig, ax


# ------------------------------------------------------------------
# Waffle chart
# ------------------------------------------------------------------
def plot_waffle(
    values: Mapping[str, float] | Sequence[float],
    labels: Sequence[str] | None = None,
    *,
    ax=None,
    journal: str = "default",
    save=None,
    rows: int = 10,
    cols: int = 10,
    palette: str = "ggsci-observable10",
    gap: float = 0.08,
    **kwargs,
):
    """Waffle chart — rows × cols grid of squares, each worth 1/(rows*cols)
    of the whole.
    """
    require_pro("plot_waffle")
    fig, ax = prepare_axes(ax, journal)

    if isinstance(values, Mapping):
        labels = list(values.keys())
        vals = np.asarray(list(values.values()), dtype=float)
    else:
        vals = np.asarray(values, dtype=float)
        if labels is None:
            labels = [f"cat {i + 1}" for i in range(vals.size)]
        labels = list(labels)
    total = vals.sum()
    if total <= 0:
        raise ValueError("values must sum to a positive number")

    # Cell counts (round, then fix drift to match rows*cols).
    n_cells = rows * cols
    counts = np.round(vals / total * n_cells).astype(int)
    drift = n_cells - counts.sum()
    if drift != 0:
        # adjust the biggest category
        counts[np.argmax(counts)] += drift

    palette_colors = PALETTES.get(palette, PALETTES["ggsci-observable10"])
    cell_colors = []
    for i, c in enumerate(counts):
        cell_colors.extend([palette_colors[i % len(palette_colors)]] * int(c))

    # Layout: fill column-major from bottom-left to match iconography norms.
    idx = 0
    for c in range(cols):
        for r in range(rows):
            if idx >= len(cell_colors):
                break
            x = c + gap / 2
            y = r + gap / 2
            rect = mpatches.Rectangle(
                (x, y), 1 - gap, 1 - gap,
                facecolor=cell_colors[idx], edgecolor="none"
            )
            ax.add_patch(rect)
            idx += 1

    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)

    # Legend
    handles = [mpatches.Patch(color=palette_colors[i % len(palette_colors)],
                              label=f"{labels[i]} ({counts[i]}%)")
               for i in range(len(labels))]
    ax.legend(handles=handles, frameon=False, fontsize=7,
              loc="upper left", bbox_to_anchor=(1.02, 1.0))

    finalize(fig, save)
    return fig, ax


# ------------------------------------------------------------------
# Streamgraph
# ------------------------------------------------------------------
def plot_streamgraph(
    x,
    series: Mapping[str, Sequence[float]],
    *,
    ax=None,
    journal: str = "default",
    save=None,
    palette: str = "met-monet",
    baseline: str = "wiggle",
    alpha: float = 0.9,
    **kwargs,
):
    """Streamgraph (stacked area with a balanced baseline).

    baseline: ``"zero"`` (simple stack), ``"sym"`` (mirror around 0),
    or ``"wiggle"`` (minimize slope, Byron/Wattenberg algorithm).
    """
    require_pro("plot_streamgraph")
    fig, ax = prepare_axes(ax, journal)

    x = np.asarray(x, dtype=float)
    names = list(series.keys())
    Y = np.vstack([np.asarray(series[n], dtype=float) for n in names])
    if Y.shape[1] != x.size:
        raise ValueError("each series must have the same length as x")

    n_layers, n_points = Y.shape
    if baseline == "zero":
        g0 = np.zeros(n_points)
    elif baseline == "sym":
        g0 = -Y.sum(axis=0) / 2.0
    elif baseline == "wiggle":
        # Byron/Wattenberg "wiggle" baseline (minimize squared slope of layers).
        total = Y.sum(axis=0)
        f = np.zeros(n_points)
        for i in range(n_layers):
            w = (n_layers - i) * Y[i]
            f += w
        g0 = -f / max(n_layers, 1)
        # shift so minimum = 0 if that keeps values more positive
    else:
        raise ValueError(f"unknown baseline: {baseline}")

    # Build cumulative upper boundaries.
    cum = np.cumsum(Y, axis=0) + g0[None, :]
    lower = np.vstack([g0, cum[:-1]])
    upper = cum

    palette_colors = PALETTES.get(palette, PALETTES["met-monet"])
    for i, name in enumerate(names):
        col = palette_colors[i % len(palette_colors)]
        ax.fill_between(x, lower[i], upper[i], color=col, alpha=alpha,
                        linewidth=0, label=name)

    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.tick_params(which="both", left=False, top=False, right=False)
    ax.legend(frameon=False, fontsize=7, loc="upper left",
              bbox_to_anchor=(1.01, 1.0))

    finalize(fig, save)
    return fig, ax


# ------------------------------------------------------------------
# Connected scatter — trajectories through 2D space with time-direction.
# ------------------------------------------------------------------
def plot_connected_scatter(
    x,
    y,
    *,
    labels: Iterable[str] | None = None,
    ax=None,
    journal: str = "default",
    save=None,
    palette: str = "met-hiroshige",
    arrow_scale: float = 1.0,
    annotate_first_last: bool = True,
    xlabel: str | None = None,
    ylabel: str | None = None,
    **kwargs,
):
    """Plot a time-ordered trajectory of (x_t, y_t) with direction arrows.

    Accepts a single (x, y) pair (1D arrays) or list of pairs for multi-series.
    """
    require_pro("plot_connected_scatter")
    fig, ax = prepare_axes(ax, journal)

    # Normalize input -> list of trajectories
    def _is_1d(a):
        return np.asarray(a).ndim == 1

    if _is_1d(x) and _is_1d(y):
        series = [(np.asarray(x, dtype=float), np.asarray(y, dtype=float))]
    else:
        series = [(np.asarray(xi, dtype=float), np.asarray(yi, dtype=float))
                  for xi, yi in zip(x, y)]

    labels = list(labels) if labels else [None] * len(series)
    colors_src = PALETTES.get(palette, PALETTES["met-hiroshige"])
    annos: list = []

    for i, ((xs, ys), lab) in enumerate(zip(series, labels)):
        col = colors_src[i % len(colors_src)]
        ax.plot(xs, ys, color=col, linewidth=1.0, zorder=2, label=lab)
        # Points with sequential size = time.
        sizes = np.linspace(10, 55, xs.size)
        ax.scatter(xs, ys, s=sizes, c=col, edgecolor="white",
                   linewidth=0.5, zorder=3)
        if xs.size >= 2:
            # Mid-trajectory arrow.
            mid = xs.size // 2
            ax.annotate(
                "", xy=(xs[mid], ys[mid]),
                xytext=(xs[mid - 1], ys[mid - 1]),
                arrowprops=dict(arrowstyle="-|>", color=col,
                                lw=0.8, shrinkA=0, shrinkB=0,
                                mutation_scale=10 * arrow_scale),
                zorder=4,
            )
        if annotate_first_last:
            # Clear the biggest scatter point (sizes top out at 55) so the
            # "start" / "end" glyphs never sit on top of a marker.
            clear = marker_clearance_pts(55, pad_pts=2.0)
            # Detect closed trajectory (start ≈ end) — collapse to a single
            # combined label so two stacked annotations don't overlay.
            p_start = (xs[0], ys[0])
            p_end = (xs[-1], ys[-1])
            xrange = float(np.nanmax(xs) - np.nanmin(xs)) or 1.0
            yrange = float(np.nanmax(ys) - np.nanmin(ys)) or 1.0
            closed = np.hypot(p_start[0] - p_end[0],
                              p_start[1] - p_end[1]) < 0.02 * np.hypot(xrange, yrange)
            annos.append(ax.annotate(
                "start↔end" if closed else "start", xy=p_start,
                xytext=(clear, clear), textcoords="offset points",
                fontsize=7, color=col, weight="bold",
                annotation_clip=False,
            ))
            if not closed:
                annos.append(ax.annotate(
                    "end", xy=p_end,
                    xytext=(clear, clear), textcoords="offset points",
                    fontsize=7, color=col, weight="bold",
                    annotation_clip=False,
                ))

    if xlabel: ax.set_xlabel(xlabel)
    if ylabel: ax.set_ylabel(ylabel)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(which="both", top=False, right=False)
    if any(lab for lab in labels):
        ax.legend(frameon=False, fontsize=7, loc="best")

    # Strict: extend xlim so boundary start/end annotations never clip.
    if annos:
        expand_xlim_for_annos(ax, annos, pad_px=6.0)

    finalize(fig, save)
    return fig, ax
