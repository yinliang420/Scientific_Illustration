"""Scatter plot with optional linear fit and error bars."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from huitu._common import coerce_xy, finalize, prepare_axes


def plot_scatter(
    data,
    ax=None,
    journal: str = "default",
    save=None,
    yerr=None,
    xerr=None,
    fit: bool = False,
    xlabel: str | None = None,
    ylabel: str | None = None,
    label: str | None = None,
    **kwargs,
):
    """Scatter with optional ``fit=True`` linear regression overlay.

    If ``data`` is a DataFrame with a third column, that column is used as
    ``yerr`` when ``yerr`` isn't explicitly passed.
    """
    fig, ax = prepare_axes(ax, journal)

    if isinstance(data, pd.DataFrame) and data.shape[1] >= 3 and yerr is None:
        x = data.iloc[:, 0].to_numpy(dtype=float)
        y = data.iloc[:, 1].to_numpy(dtype=float)
        yerr = data.iloc[:, 2].to_numpy(dtype=float)
    else:
        if isinstance(data, (str, Path)):
            df = pd.read_csv(data, sep=None, engine="python")
            x = df.iloc[:, 0].to_numpy(dtype=float)
            y = df.iloc[:, 1].to_numpy(dtype=float)
            if df.shape[1] >= 3 and yerr is None:
                yerr = df.iloc[:, 2].to_numpy(dtype=float)
        else:
            x, y = coerce_xy(data)

    if yerr is not None or xerr is not None:
        ax.errorbar(
            x, y, yerr=yerr, xerr=xerr, fmt="o", capsize=2, markersize=4, label=label, **kwargs
        )
    else:
        ax.scatter(x, y, s=20, label=label, **kwargs)

    if fit:
        if yerr is not None:
            w = 1.0 / np.asarray(yerr, dtype=float)
            slope, intercept = np.polyfit(x, y, 1, w=w)
        else:
            slope, intercept = np.polyfit(x, y, 1)
        xs = np.linspace(np.min(x), np.max(x), 100)
        y_fit = slope * xs + intercept
        fit_color = "r"
        ax.plot(xs, y_fit, fit_color + "--", lw=1.0,
                label=f"fit: y={slope:.3g}x+{intercept:.3g}")
        # 95% CI band from standard linear-regression SE
        n = x.size
        if n >= 3:
            x_mean = float(np.mean(x))
            Sxx = float(np.sum((x - x_mean) ** 2))
            resid = y - (slope * x + intercept)
            dof = max(n - 2, 1)
            sigma = float(np.sqrt(np.sum(resid ** 2) / dof))
            if Sxx > 0:
                se = sigma * np.sqrt(1.0 / n + (xs - x_mean) ** 2 / Sxx)
                ax.fill_between(xs, y_fit - 1.96 * se, y_fit + 1.96 * se,
                                alpha=0.2, color=fit_color, linewidth=0)

    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel)
    if label or fit:
        ax.legend(loc="best")

    finalize(fig, save)
    return fig, ax
