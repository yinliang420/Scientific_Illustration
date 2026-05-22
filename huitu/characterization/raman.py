"""Raman spectrum plotting."""

from __future__ import annotations

from typing import Iterable

import numpy as np

from huitu._common import (
    coerce_xy, finalize, is_multi_input, place_legend, prepare_axes,
)


def plot_raman(
    data,
    ax=None,
    journal: str = "default",
    save=None,
    labels: Iterable[str] | None = None,
    offset: float = 1.05,
    normalize: bool = True,
    legend: str = "auto",
    label_trim: int | None = 24,
    xlim: tuple | None = None,
    smart_xlim: bool = True,
    **kwargs,
):
    """Plot one or more Raman spectra (stacked if list).

    label_trim
        If set, truncate each label to this many characters with a trailing
        ``"…"`` ellipsis (unicode, not ``"..."``). Default 24. Pass ``None``
        to disable trimming.
    """
    fig, ax = prepare_axes(ax, journal)

    is_stacked = is_multi_input(data)
    items = list(data) if is_stacked else [data]
    labels = list(labels) if labels else [None] * len(items)
    if len(labels) < len(items):
        labels = labels + [None] * (len(items) - len(labels))

    if label_trim is not None and label_trim > 0:
        trimmed = []
        for lab in labels:
            if not isinstance(lab, str) or len(lab) <= label_trim:
                trimmed.append(lab)
                continue
            # Mathtext-aware trim: if label contains '$', skip trimming entirely
            # rather than risk chopping inside $...$ and corrupting mathtext.
            # Users can pre-shorten their mathtext labels if needed.
            if "$" in lab:
                trimmed.append(lab)
            else:
                trimmed.append(lab[: max(label_trim - 1, 1)] + "\u2026")
        labels = trimmed

    traces = []
    all_x = []
    for i, item in enumerate(items):
        x, y = coerce_xy(item)
        all_x.append(x)
        if normalize:
            span = np.max(y) - np.min(y)
            y = (y - np.min(y)) / span if span > 0 else y
        yshift = y + i * offset
        (line,) = ax.plot(x, yshift, label=labels[i], **kwargs)
        traces.append((x, yshift, line.get_color()))

    ax.set_xlabel(r"Raman shift (cm$^{-1}$)")
    ax.set_ylabel("Intensity (a.u.)")
    ax.set_yticks([])
    ax.margins(y=0.08)

    if xlim is not None:
        ax.set_xlim(*xlim)
    elif smart_xlim and all_x:
        cat_x = np.concatenate(all_x)
        if cat_x.size:
            p1, p99 = np.percentile(cat_x, [1, 99])
            dmin = float(np.min(cat_x))
            dmax = float(np.max(cat_x))
            lo = max(dmin, float(p1) - 50.0)
            hi = min(dmax, float(p99) + 50.0)
            if hi > lo:
                ax.set_xlim(lo, hi)

    place_legend(ax, labels, traces=traces, legend=legend)

    finalize(fig, save)
    return fig, ax
