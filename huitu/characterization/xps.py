"""XPS spectrum plotting with optional fitted peak overlay."""

from __future__ import annotations

from typing import Iterable, Tuple

import numpy as np

from huitu._common import coerce_xy, finalize, prepare_axes


def plot_xps(
    data,
    ax=None,
    journal: str = "default",
    save=None,
    fits: Iterable[Tuple[np.ndarray, np.ndarray, str]] | None = None,
    baseline: Tuple[np.ndarray, np.ndarray] | None = None,
    label: str = "raw",
    **kwargs,
):
    """Plot an XPS spectrum.

    fits
        Iterable of ``(x, y, label)`` tuples; drawn as dashed filled
        components on top of the raw signal.
    baseline
        Optional ``(x, y)`` background (e.g. Shirley).
    """
    fig, ax = prepare_axes(ax, journal)

    x, y = coerce_xy(data)
    ax.plot(x, y, "k-", label=label, **kwargs)

    if baseline is not None:
        bx, by = np.asarray(baseline[0]), np.asarray(baseline[1])
        ax.plot(bx, by, color="grey", lw=0.8, ls="--", label="baseline")

    if fits:
        for fx, fy, flabel in fits:
            ax.fill_between(fx, fy, alpha=0.25)
            ax.plot(fx, fy, lw=0.9, label=flabel)

    ax.invert_xaxis()
    ax.set_xlabel("Binding energy (eV)")
    ax.set_ylabel("Intensity (CPS)")
    ax.legend(loc="best")

    finalize(fig, save)
    return fig, ax
