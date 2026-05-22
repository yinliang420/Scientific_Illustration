"""FTIR spectrum plotting (reversed wavenumber axis)."""

from __future__ import annotations

from typing import Iterable

import numpy as np

from huitu._common import (
    coerce_xy, finalize, is_multi_input, place_legend, prepare_axes,
)


def plot_ftir(
    data,
    ax=None,
    journal: str = "default",
    save=None,
    labels: Iterable[str] | None = None,
    mode: str = "transmittance",
    offset: float = 0.0,
    legend: str = "auto",
    xlim: tuple | None = None,
    smart_xlim: bool = True,
    **kwargs,
):
    """Plot FTIR spectra with wavenumber x-axis (high to low).

    mode
        ``'transmittance'`` (default) or ``'absorbance'`` sets the y label only.
    offset
        Vertical offset applied between stacked spectra.
    """
    if mode not in ("transmittance", "absorbance"):
        raise ValueError("mode must be 'transmittance' or 'absorbance'")

    fig, ax = prepare_axes(ax, journal)

    is_multi = is_multi_input(data)
    items = list(data) if is_multi else [data]
    labels = list(labels) if labels else [None] * len(items)
    if len(labels) < len(items):
        labels = labels + [None] * (len(items) - len(labels))

    traces = []
    all_x = []
    for i, item in enumerate(items):
        x, y = coerce_xy(item)
        all_x.append(x)
        yshift = y + i * offset
        (line,) = ax.plot(x, yshift, label=labels[i], **kwargs)
        traces.append((x, yshift, line.get_color()))

    ax.set_xlabel(r"Wavenumber (cm$^{-1}$)")
    ax.set_ylabel("Transmittance (%)" if mode == "transmittance" else "Absorbance (a.u.)")
    ax.invert_xaxis()

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
                # FTIR uses reversed (high-to-low) axis.
                ax.set_xlim(hi, lo)

    place_legend(ax, labels, traces=traces, legend=legend)

    finalize(fig, save)
    return fig, ax
