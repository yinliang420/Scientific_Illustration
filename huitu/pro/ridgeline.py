"""Ridgeline / joyplot — stacked KDE distributions."""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np

from huitu._common import finalize, prepare_axes
from huitu.style import get_cmap
from ._license import require_pro


def _kde(values: np.ndarray, grid: np.ndarray, bw: float | None) -> np.ndarray:
    from scipy.stats import gaussian_kde

    if values.size < 2:
        return np.zeros_like(grid)
    kde = gaussian_kde(values, bw_method=bw)
    return kde(grid)


def plot_ridgeline(
    distributions: Sequence[np.ndarray],
    labels: Iterable[str] | None = None,
    *,
    ax=None,
    journal: str = "default",
    save=None,
    palette: str = "met-hiroshige",
    overlap: float = 0.7,
    bw: float | None = None,
    fill: bool = True,
    line_color: str | None = None,
    show_points: bool = False,
    xlabel: str | None = None,
    **kwargs,
):
    """Overlapping KDE densities (Joy Division / joyplot style).

    Parameters
    ----------
    distributions
        Sequence of 1D arrays — one distribution per row.
    overlap
        0 = rows never overlap; 0.9 = heavy overlap (classic joyplot).
    palette
        Any huitu or pro palette name (sampled evenly across rows).
    """
    require_pro("plot_ridgeline")
    fig, ax = prepare_axes(ax, journal)

    dists = [np.asarray(d, dtype=float) for d in distributions]
    dists = [d[np.isfinite(d)] for d in dists]
    n = len(dists)
    if n == 0:
        raise ValueError("distributions is empty")

    labels = list(labels) if labels else [f"row {i + 1}" for i in range(n)]
    if len(labels) < n:
        labels = labels + [f"row {i + 1}" for i in range(len(labels), n)]

    cmap = get_cmap(palette) if palette in _gradient_set() else None
    if cmap is None:
        # Sample from discrete palette evenly.
        from huitu.style import PALETTES

        colors = PALETTES.get(palette, PALETTES["met-hiroshige"])
        idx = np.linspace(0, len(colors) - 1, n).round().astype(int)
        row_colors = [colors[i] for i in idx]
    else:
        row_colors = [cmap(i / max(n - 1, 1)) for i in range(n)]

    xmin = min(float(d.min()) for d in dists if d.size)
    xmax = max(float(d.max()) for d in dists if d.size)
    pad = 0.05 * (xmax - xmin + 1e-12)
    grid = np.linspace(xmin - pad, xmax + pad, 512)

    densities = [_kde(d, grid, bw) for d in dists]
    peak = max((np.max(k) for k in densities if k.size), default=1.0)
    if peak <= 0:
        peak = 1.0

    step = (1.0 - overlap)  # vertical advance per row, in normalized density units
    # Stack top-down: the first row (top of the list) is drawn first (behind),
    # and each subsequent row overlays on top of the one above it. This way
    # lower rows visually sit in front of upper rows — a "cascading" joyplot.
    for i, (k, col, lab) in enumerate(zip(densities, row_colors, labels)):
        y_offset = (n - 1 - i) * step
        y = k / peak + y_offset
        baseline = np.full_like(y, y_offset)
        z = i + 2  # i=0 (top) lowest, i=n-1 (bottom) highest
        if fill:
            ax.fill_between(grid, baseline, y, color=col, alpha=0.85,
                            linewidth=0, zorder=z)
        edge = line_color or "#222222"
        ax.plot(grid, y, color=edge, linewidth=0.6, zorder=z + 0.5)
        if show_points:
            ax.scatter(dists[i], np.full_like(dists[i], y_offset),
                       s=2, c=edge, alpha=0.35, zorder=z + 0.6)

    # Row labels on the left.
    ax.set_yticks([(n - 1 - i) * step for i in range(n)])
    ax.set_yticklabels(labels)
    ax.set_ylim(-step * 0.2, (n - 1) * step + 1.15)
    if xlabel:
        ax.set_xlabel(xlabel)
    ax.spines["left"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    # Kill floating minor ticks on hidden spines (both major + minor, all 3 sides).
    ax.tick_params(which="both", left=False, right=False, top=False)
    # Nudge y-tick labels slightly right to avoid sitting on top of ridge baselines.
    ax.tick_params(axis="y", pad=4)

    finalize(fig, save)
    return fig, ax


def _gradient_set() -> set:
    from huitu.style import _GRADIENT_PALETTES
    return set(_GRADIENT_PALETTES)
