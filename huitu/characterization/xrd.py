"""XRD pattern plotting."""

from __future__ import annotations

from typing import Iterable

import numpy as np

from huitu._common import (
    coerce_xy, finalize, is_multi_input, place_legend, prepare_axes,
)


def _normalize(y: np.ndarray) -> np.ndarray:
    ymin, ymax = float(np.min(y)), float(np.max(y))
    span = ymax - ymin
    if span <= 0:
        return np.zeros_like(y)
    return (y - ymin) / span


def plot_xrd(
    data,
    ax=None,
    journal: str = "default",
    save=None,
    labels: Iterable[str] | None = None,
    offset: float = 1.05,
    hkl: dict | None = None,
    normalize: bool = True,
    legend: str = "auto",
    xlim: tuple[float, float] | None = None,
    hkl_stagger: bool = True,
    **kwargs,
):
    """Plot an XRD pattern.

    data
        Two-column file/array/DataFrame for a single pattern, or a list of
        those for a stacked plot.
    labels
        Per-pattern legend labels when stacking.
    offset
        Vertical offset multiplier between stacked patterns (of normalized unit).
    hkl
        Optional ``{two_theta: "(hkl)"}`` mapping; labels are drawn above the
        highest pattern.
    normalize
        If True, patterns are min-max normalized before stacking.
    xlim
        Explicit ``(xmin, xmax)`` in 2θ degrees. If ``None`` and multiple
        patterns are stacked, auto-selects the **intersection** of per-pattern
        ranges (falls back to the union when the intersection is empty or
        smaller than half the union span).
    hkl_stagger
        When two adjacent hkl annotations fall within ~3% of the x-range,
        stagger their vertical placement to avoid overlap.
    """
    fig, ax = prepare_axes(ax, journal)

    is_stacked = is_multi_input(data)
    items = list(data) if is_stacked else [data]
    labels = list(labels) if labels else [None] * len(items)
    if len(labels) < len(items):
        labels = labels + [None] * (len(items) - len(labels))

    top = 0.0
    traces = []
    ranges = []
    for i, item in enumerate(items):
        x, y = coerce_xy(item)
        ranges.append((float(np.min(x)), float(np.max(x))))
        yp = _normalize(y) if normalize else y
        shift = i * offset if is_stacked else 0.0
        yshift = yp + shift
        (line,) = ax.plot(x, yshift, label=labels[i], **kwargs)
        traces.append((x, yshift, line.get_color()))
        top = max(top, float(np.max(yshift)))

    # Smart x-limit selection for heterogeneous stacks.
    if xlim is not None:
        ax.set_xlim(*xlim)
    elif is_stacked and len(ranges) > 1:
        mins = [r[0] for r in ranges]
        maxs = [r[1] for r in ranges]
        inter_lo, inter_hi = max(mins), min(maxs)
        union_lo, union_hi = min(mins), max(maxs)
        union_span = union_hi - union_lo
        inter_span = inter_hi - inter_lo
        if inter_span > 0 and union_span > 0 and inter_span >= 0.5 * union_span:
            ax.set_xlim(inter_lo, inter_hi)
        # else leave autoscale (effectively the union)

    ax.set_xlabel(r"2$\theta$ ($^{\circ}$)")
    ax.set_ylabel("Intensity (a.u.)")
    ax.set_yticks([])

    if hkl:
        # Sort by 2theta so stagger walks left-to-right.
        xlo, xhi = ax.get_xlim()
        x_range = abs(xhi - xlo) or 1.0
        items_hkl = sorted(hkl.items(), key=lambda kv: float(kv[0]))
        prev_pos = None
        prev_high = False
        for pos, tag in items_hkl:
            pos_f = float(pos)
            ax.axvline(pos_f, color="grey", lw=0.4, ls="--", alpha=0.6)
            high = False
            if hkl_stagger and prev_pos is not None:
                if abs(pos_f - prev_pos) < 0.03 * x_range and not prev_high:
                    high = True
            y_txt = top * (1.10 if high else 1.02)
            ax.annotate(
                tag, xy=(pos_f, y_txt), xytext=(0, 4),
                textcoords="offset points",
                ha="center", va="bottom", fontsize=6,
                bbox=dict(facecolor="white", edgecolor="none",
                          alpha=0.85, pad=0.3),
            )
            prev_pos = pos_f
            prev_high = high
        # Expand y-limit so labels don't clip at the top of the axes.
        ax.margins(y=0.08)

    place_legend(ax, labels, traces=traces, legend=legend)

    finalize(fig, save)
    return fig, ax
