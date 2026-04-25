"""Comparison plots: dumbbell, slope, bump.

These chart types come from the Financial Times Visual Vocabulary:
- Dumbbell  — highlight gap between two values per category
- Slope     — show ranking / value change between two (or few) time points
- Bump      — show ranking evolution across many time points
"""

from __future__ import annotations

from typing import Iterable, Mapping, Sequence

import numpy as np

from huitu._common import (
    expand_xlim_for_annos,
    finalize,
    marker_clearance_pts,
    place_legend,
    prepare_axes,
)
from huitu.style import PALETTES
from ._license import require_pro


# ------------------------------------------------------------------
# Dumbbell
# ------------------------------------------------------------------
def plot_dumbbell(
    categories: Sequence[str],
    start: Sequence[float],
    end: Sequence[float],
    *,
    ax=None,
    journal: str = "default",
    save=None,
    start_color: str = "#8491B4",
    end_color: str = "#E64B35",
    start_label: str = "before",
    end_label: str = "after",
    connector_color: str = "#BBBBBB",
    marker_size: int = 60,
    sort_by: str | None = "delta",
    xlabel: str | None = None,
    **kwargs,
):
    """Category-wise dumbbell of start vs end values.

    sort_by: ``"delta"`` (default), ``"start"``, ``"end"``, or ``None``.
    """
    require_pro("plot_dumbbell")
    fig, ax = prepare_axes(ax, journal)

    cats = list(categories)
    s = np.asarray(start, dtype=float)
    e = np.asarray(end, dtype=float)
    if not (len(cats) == len(s) == len(e)):
        raise ValueError("categories, start, end must all have the same length")

    if sort_by == "delta":
        order = np.argsort(e - s)
    elif sort_by == "start":
        order = np.argsort(s)
    elif sort_by == "end":
        order = np.argsort(e)
    else:
        order = np.arange(len(cats))

    cats = [cats[i] for i in order]
    s = s[order]
    e = e[order]
    y = np.arange(len(cats))

    # Connectors first so markers draw on top.
    for yi, a, b in zip(y, s, e):
        ax.plot([a, b], [yi, yi], color=connector_color, linewidth=2.0,
                solid_capstyle="round", zorder=1)

    ax.scatter(s, y, s=marker_size, color=start_color, zorder=3,
               edgecolor="white", linewidth=0.8, label=start_label)
    ax.scatter(e, y, s=marker_size, color=end_color, zorder=3,
               edgecolor="white", linewidth=0.8, label=end_label)

    ax.set_yticks(y)
    ax.set_yticklabels(cats)
    ax.invert_yaxis()  # first category on top
    if xlabel:
        ax.set_xlabel(xlabel)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(which="both", right=False, top=False)

    place_legend(ax, [start_label, end_label], traces=None, legend="best")
    finalize(fig, save)
    return fig, ax


# ------------------------------------------------------------------
# Slope
# ------------------------------------------------------------------
def plot_slope(
    data: Mapping[str, Sequence[float]],
    x_labels: Sequence[str],
    *,
    ax=None,
    journal: str = "default",
    save=None,
    palette: str = "ggsci-npg",
    highlight: Iterable[str] | None = None,
    muted_color: str = "#C8C8C8",
    linewidth: float = 1.2,
    marker_size: int = 40,
    annotate_ends: bool = True,
    ylabel: str | None = None,
    **kwargs,
):
    """Slope chart of series at a few categorical x positions.

    data
        Mapping ``{series_name: [y_at_x0, y_at_x1, ...]}``. Every series must
        have the same length as ``x_labels``.
    highlight
        Iterable of series names to render in palette colors; all others are
        drawn in ``muted_color``. If ``None``, every series is colored.
    """
    require_pro("plot_slope")
    fig, ax = prepare_axes(ax, journal)

    x_labels = list(x_labels)
    n_x = len(x_labels)
    if n_x < 2:
        raise ValueError("slope charts need at least two x positions")
    x = np.arange(n_x)

    series = list(data.items())
    colors_src = PALETTES.get(palette, PALETTES["ggsci-npg"])
    if highlight is None:
        highlight_set = {name for name, _ in series}
    else:
        highlight_set = set(highlight)

    color_idx = 0
    offset = marker_clearance_pts(marker_size, pad_pts=3.0)
    annos: list = []
    for name, values in series:
        yv = np.asarray(values, dtype=float)
        if yv.size != n_x:
            raise ValueError(f"series '{name}' length {yv.size} != {n_x}")
        if name in highlight_set:
            col = colors_src[color_idx % len(colors_src)]
            color_idx += 1
            zorder = 3
            lw = linewidth
        else:
            col = muted_color
            zorder = 1
            lw = linewidth * 0.7
        ax.plot(x, yv, color=col, linewidth=lw, marker="o",
                markersize=np.sqrt(marker_size), markeredgecolor="white",
                markeredgewidth=0.6, zorder=zorder, label=name)
        if annotate_ends and name in highlight_set:
            annos.append(ax.annotate(
                name, xy=(x[-1], yv[-1]),
                xytext=(offset, 0), textcoords="offset points",
                va="center", ha="left", color=col, fontsize=7,
                zorder=zorder, annotation_clip=False,
            ))

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    right_pad = 0.7 if annotate_ends else 0.3
    ax.set_xlim(-0.3, n_x - 1 + right_pad)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(which="both", top=False, right=False)

    # Strict: ensure no end-label touches the right spine / figure bbox.
    if annotate_ends and annos:
        expand_xlim_for_annos(ax, annos, pad_px=6.0)

    finalize(fig, save)
    return fig, ax


# ------------------------------------------------------------------
# Bump chart — ranking evolution over many periods
# ------------------------------------------------------------------
def plot_bump(
    data: Mapping[str, Sequence[float]],
    x_labels: Sequence[str],
    *,
    ax=None,
    journal: str = "default",
    save=None,
    palette: str = "met-archambault",
    higher_is_better: bool = True,
    linewidth: float = 1.6,
    marker_size: int = 70,
    annotate_ends: bool = True,
    **kwargs,
):
    """Bump chart showing rank changes over time.

    data maps series_name -> list of numeric values (one per period).
    The function converts values into per-period ranks and plots the rank
    trajectories.
    """
    require_pro("plot_bump")
    fig, ax = prepare_axes(ax, journal)

    x_labels = list(x_labels)
    n_x = len(x_labels)
    if n_x < 2:
        raise ValueError("bump charts need at least two periods")

    names = list(data.keys())
    mat = np.asarray([list(data[n]) for n in names], dtype=float)
    if mat.shape[1] != n_x:
        raise ValueError("series length must match len(x_labels)")
    n_series = len(names)

    # Per-column ranks: 1 = best
    if higher_is_better:
        order = (-mat).argsort(axis=0).argsort(axis=0) + 1
    else:
        order = mat.argsort(axis=0).argsort(axis=0) + 1

    colors_src = PALETTES.get(palette, PALETTES["met-archambault"])
    x = np.arange(n_x)
    # Text offset in points must clear the scatter marker so the glyph
    # never overlaps the last/first dot on the trajectory.
    offset = marker_clearance_pts(marker_size, pad_pts=4.0)
    annos: list = []
    for i, name in enumerate(names):
        col = colors_src[i % len(colors_src)]
        ax.plot(x, order[i], color=col, linewidth=linewidth,
                marker="o", markersize=np.sqrt(marker_size),
                markeredgecolor="white", markeredgewidth=0.8,
                zorder=3, label=name)
        if annotate_ends:
            annos.append(ax.annotate(
                name, xy=(x[-1], order[i, -1]),
                xytext=(offset, 0), textcoords="offset points",
                va="center", ha="left", color=col, fontsize=7,
                annotation_clip=False,
            ))
            annos.append(ax.annotate(
                name, xy=(x[0], order[i, 0]),
                xytext=(-offset, 0), textcoords="offset points",
                va="center", ha="right", color=col, fontsize=7,
                annotation_clip=False,
            ))

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    # Preliminary data-unit padding — a measurement pass below enlarges
    # this further if the longest label is wider than we estimated.
    left_pad = 0.9 if annotate_ends else 0.3
    right_pad = 1.1 if annotate_ends else 0.3
    ax.set_xlim(-left_pad, n_x - 1 + right_pad)
    ax.set_yticks(np.arange(1, n_series + 1))
    ax.set_ylabel("Rank")
    ax.invert_yaxis()  # rank 1 on top
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(which="both", top=False, right=False)

    # Strict guarantee: expand xlim so no annotation touches either
    # the plot spine, the tick labels, or the saved figure's bbox edge.
    if annotate_ends and annos:
        expand_xlim_for_annos(ax, annos, pad_px=6.0)

    finalize(fig, save)
    return fig, ax
