"""Tafel plot with optional slope fitting."""

from __future__ import annotations

import numpy as np

from huitu._common import coerce_xy, finalize, prepare_axes


def plot_tafel(
    data,
    ax=None,
    journal: str = "default",
    save=None,
    fit_range: tuple | None = None,
    label: str | None = None,
    **kwargs,
):
    """Tafel plot: log|j| x vs overpotential eta y.

    Data format: 2 columns (log|j| in A/cm^2, eta in V). If your file has
    columns swapped, transpose via ``DataFrame.iloc[:, [1, 0]]`` first.

    fit_range
        ``(eta_min, eta_max)`` in V (y-axis units). Within this window the
        Tafel slope mV/dec is fitted and overlaid.
    """
    fig, ax = prepare_axes(ax, journal)
    x, y = coerce_xy(data)

    style = dict(marker="o", markersize=3, linestyle="none")
    style.update(kwargs)
    ax.plot(x, y, label=label, **style)
    ax.set_xlabel("log |j| (A cm⁻²)")
    ax.set_ylabel(r"$\eta$ (V vs RHE)")

    if fit_range is not None:
        lo, hi = fit_range
        mask = (y >= lo) & (y <= hi)
        if mask.sum() >= 2:
            # Fit eta = slope * log|j| + intercept; slope has units V/dec.
            slope, intercept = np.polyfit(x[mask], y[mask], 1)
            xs = np.linspace(np.min(x[mask]), np.max(x[mask]), 50)
            ax.plot(xs, slope * xs + intercept, "r--", lw=1.0,
                    label=f"{slope*1000:.0f} mV/dec")

    if label or fit_range is not None:
        ax.legend(loc="best")

    finalize(fig, save)
    return fig, ax
