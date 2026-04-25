"""2-D density / joint-distribution plots.

Shows where points concentrate in a 2-D scatter using kernel density estimation
or hexbin. Optional marginal histograms build a joint (seaborn-style) plot.

Example
-------
>>> import numpy as np
>>> from huitu import plot_density
>>> rng = np.random.default_rng(0)
>>> x = rng.normal(0, 1, 2000)
>>> y = 0.5 * x + rng.normal(0, 0.5, 2000)
>>> fig, ax = plot_density(x, y, kind="kde", marginal=True)
"""

from __future__ import annotations

import warnings

import numpy as np

from huitu._common import finalize, prepare_axes
from huitu.style import PALETTES, _GRADIENT_PALETTES, get_cmap


def _resolve_cmap(cmap):
    if cmap is None:
        return None
    if isinstance(cmap, str):
        key = cmap.lower()
        if key in PALETTES and key in _GRADIENT_PALETTES:
            return get_cmap(key)
        if key in PALETTES:
            from matplotlib.colors import LinearSegmentedColormap

            return LinearSegmentedColormap.from_list(f"huitu-{key}", PALETTES[key])
        return cmap
    return cmap


def _kde_grid(x, y, bw_method=None, gridsize=200):
    """Return (xx, yy, zz) KDE grid. Uses scipy when available, histogram2d else."""
    xmin, xmax = float(np.min(x)), float(np.max(x))
    ymin, ymax = float(np.min(y)), float(np.max(y))
    # Pad by 5% so contours close away from the data.
    dx = (xmax - xmin) * 0.05 or 1.0
    dy = (ymax - ymin) * 0.05 or 1.0
    xs = np.linspace(xmin - dx, xmax + dx, gridsize)
    ys = np.linspace(ymin - dy, ymax + dy, gridsize)
    xx, yy = np.meshgrid(xs, ys)
    try:
        from scipy.stats import gaussian_kde

        kde = gaussian_kde(np.vstack([x, y]), bw_method=bw_method)
        zz = kde(np.vstack([xx.ravel(), yy.ravel()])).reshape(xx.shape)
    except Exception:
        warnings.warn("scipy not available; using histogram fallback")
        H, xedges, yedges = np.histogram2d(
            x, y, bins=min(gridsize // 4, 60),
            range=[[xmin - dx, xmax + dx], [ymin - dy, ymax + dy]],
        )
        # Interpolate coarse histogram onto the fine grid (nearest-neighbor).
        xi = np.clip(
            np.searchsorted(xedges, xx.ravel()) - 1, 0, H.shape[0] - 1
        )
        yi = np.clip(
            np.searchsorted(yedges, yy.ravel()) - 1, 0, H.shape[1] - 1
        )
        zz = H[xi, yi].reshape(xx.shape).astype(float)
        if zz.max() > 0:
            zz = zz / zz.max()
    return xx, yy, zz


def plot_density(
    x,
    y,
    ax=None,
    journal: str = "default",
    save=None,
    kind: str = "kde",
    cmap="crameri-batlow",
    levels: int = 12,
    gridsize: int = 50,
    bw_method=None,
    marginal: bool = False,
    scatter_alpha: float = 0.3,
    xlabel: str | None = None,
    ylabel: str | None = None,
    **kwargs,
):
    """2-D density / joint-distribution plot.

    Parameters
    ----------
    x, y
        1-D arrays of equal length.
    kind
        ``"kde"`` (filled contour via ``scipy.stats.gaussian_kde``),
        ``"hex"`` (``ax.hexbin``), or ``"scatter_kde"`` (semi-transparent
        scatter + KDE contour lines).
    cmap
        Huitu palette name or matplotlib colormap.
    levels
        Number of KDE contour levels.
    gridsize
        Hexbin resolution (only used for ``kind="hex"``).
    marginal
        Add top and right marginal histograms (joint-plot style). The returned
        ``ax`` is still the main 2-D axes.

    Returns
    -------
    (fig, ax)
        Matplotlib figure and main axes.
    """
    if kind not in ("kde", "hex", "scatter_kde"):
        raise ValueError("kind must be 'kde', 'hex', or 'scatter_kde'")

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.shape != y.shape or x.ndim != 1:
        raise ValueError("x and y must be 1-D arrays of equal length")

    cmap_obj = _resolve_cmap(cmap)

    if marginal and ax is None:
        # Build a joint layout with top / right marginal histograms.
        from huitu.style import use_journal
        import matplotlib.pyplot as plt

        use_journal(journal)
        # Disable constrained_layout so explicit cbar axes place reliably.
        fig = plt.figure(
            figsize=plt.rcParams["figure.figsize"], constrained_layout=False,
        )
        mosaic = fig.subplot_mosaic(
            [["top", "."], ["main", "right"]],
            width_ratios=[4, 1],
            height_ratios=[1, 4],
            gridspec_kw={"wspace": 0.03, "hspace": 0.05},
        )
        # Leave room on the right for the colorbar.
        fig.subplots_adjust(left=0.12, right=0.9, top=0.95, bottom=0.12)
        ax = mosaic["main"]
        ax_top = mosaic["top"]
        ax_right = mosaic["right"]
        ax_top.hist(x, bins=30, color="#4A6C8C", edgecolor="white", linewidth=0.4)
        ax_right.hist(
            y, bins=30, orientation="horizontal",
            color="#4A6C8C", edgecolor="white", linewidth=0.4,
        )
        for side in (ax_top, ax_right):
            side.tick_params(
                which="both", labelbottom=False, labelleft=False,
                bottom=False, left=False, top=False, right=False, length=0,
            )
            for spine in side.spines.values():
                spine.set_visible(False)
    else:
        fig, ax = prepare_axes(ax, journal)

    mappable = None
    if kind == "kde":
        xx, yy, zz = _kde_grid(x, y, bw_method=bw_method, gridsize=200)
        mappable = ax.contourf(xx, yy, zz, levels=levels, cmap=cmap_obj, **kwargs)
    elif kind == "hex":
        mappable = ax.hexbin(
            x, y, gridsize=gridsize, cmap=cmap_obj, mincnt=1, **kwargs
        )
    else:  # scatter_kde
        ax.scatter(
            x, y, s=10, alpha=scatter_alpha, color="#4A6C8C",
            edgecolors="none", rasterized=True,
        )
        xx, yy, zz = _kde_grid(x, y, bw_method=bw_method, gridsize=200)
        ax.contour(xx, yy, zz, levels=levels, cmap=cmap_obj, linewidths=0.6)

    if mappable is not None and kind in ("kde", "hex"):
        if marginal:
            cax = fig.add_axes([0.92, 0.12, 0.02, 0.6])
            cbar = fig.colorbar(mappable, cax=cax)
        else:
            cbar = fig.colorbar(mappable, ax=ax)
        cbar.set_label("density" if kind == "kde" else "count")
        cbar.outline.set_linewidth(0.5)
        cbar.ax.tick_params(width=0.5, length=2)

    # Apply user-supplied labels on the main axes (marginal path suppresses
    # inherited rcParams labels otherwise).
    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel)

    # Hide top/right spines on the main panel for density plots and suppress
    # stray minor ticks that would float over the resulting whitespace.
    if marginal:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(top=False, right=False, which="both")

    finalize(fig, save)
    return fig, ax
