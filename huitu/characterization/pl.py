"""Photoluminescence (PL) spectrum plotting."""

from __future__ import annotations

from typing import Iterable

import numpy as np

from huitu._common import (
    coerce_xy, finalize, is_multi_input, place_legend, prepare_axes,
)


def plot_pl(
    data,
    ax=None,
    journal: str = "default",
    save=None,
    labels: Iterable[str] | None = None,
    normalize: bool = False,
    offset: float = 0.0,
    legend: str = "auto",
    **kwargs,
):
    """Plot PL intensity vs wavelength. Multi-spectrum input supported."""
    fig, ax = prepare_axes(ax, journal)

    is_multi = is_multi_input(data)
    items = list(data) if is_multi else [data]
    labels = list(labels) if labels else [None] * len(items)
    if len(labels) < len(items):
        labels = labels + [None] * (len(items) - len(labels))

    traces = []
    for i, item in enumerate(items):
        x, y = coerce_xy(item)
        if normalize:
            ymax = float(np.max(y))
            if ymax > 0:
                y = y / ymax
        yshift = y + i * offset
        (line,) = ax.plot(x, yshift, label=labels[i], **kwargs)
        traces.append((x, yshift, line.get_color()))

    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("PL intensity (a.u.)")

    place_legend(ax, labels, traces=traces, legend=legend)

    finalize(fig, save)
    return fig, ax
