"""Operando 2-D evolution map.

Operando experiments (XRD, Raman, FTIR, XAS ...) produce a stack of spectra
acquired across a perturbation axis such as time, potential, or temperature.
``plot_operando`` renders that stack as a perceptually-uniform 2-D heatmap,
with the perturbation axis on ``y`` and the spectral axis on ``x``.

Example
-------
>>> import numpy as np
>>> from huitu import plot_operando
>>> data = np.random.rand(40, 200)
>>> fig, ax = plot_operando(
...     data,
...     x=np.linspace(20, 60, 200),
...     y=np.linspace(0, 3600, 40),
...     xlabel=r"2$\\theta$ ($^\\circ$)",
...     ylabel="time (s)",
...     cbar_label="intensity",
... )
"""

from __future__ import annotations

import numpy as np

from huitu._common import finalize, prepare_axes
from huitu.style import PALETTES, _GRADIENT_PALETTES, get_cmap


def _resolve_cmap(cmap):
    """Return a matplotlib colormap from a huitu palette name or mpl cmap."""
    if cmap is None:
        return None
    if isinstance(cmap, str):
        key = cmap.lower()
        if key in PALETTES and key in _GRADIENT_PALETTES:
            return get_cmap(key)
        if key in PALETTES:
            # Qualitative palette given but gradient needed — build one anyway.
            from matplotlib.colors import LinearSegmentedColormap

            return LinearSegmentedColormap.from_list(f"huitu-{key}", PALETTES[key])
        return cmap  # defer to matplotlib
    return cmap


def plot_operando(
    data,
    x=None,
    y=None,
    ax=None,
    journal: str = "default",
    save=None,
    cmap="crameri-batlow",
    xlabel: str | None = None,
    ylabel: str | None = None,
    cbar_label: str | None = None,
    log_z: bool = False,
    smooth: float = 0,
    contour_levels=None,
    **kwargs,
):
    """2-D evolution map for operando spectroscopy (XRD, Raman, XAS, ...).

    Renders an ``(M, N)`` spectrum stack as an ``imshow`` heatmap with
    perceptually-uniform defaults (Crameri batlow). Optional log colorbar,
    Gaussian smoothing, and overlaid white contour lines for guiding the eye.

    Parameters
    ----------
    data
        2-D ndarray ``(M, N)`` — ``M`` spectra along axis 0, ``N`` x-bins
        along axis 1.
    x
        Length-``N`` x-axis values (e.g. 2theta, cm^-1). Defaults to pixel
        indices.
    y
        Length-``M`` y-axis values (e.g. time, potential, temperature).
    cmap
        Huitu palette name or matplotlib colormap.
    log_z
        Use a logarithmic colorbar norm.
    smooth
        If > 0, apply ``scipy.ndimage.gaussian_filter`` with this sigma before
        plotting. Falls back silently when scipy is missing.
    contour_levels
        Iterable of z-values or int count; overlays thin white contour lines.

    Returns
    -------
    (fig, ax)
        Matplotlib figure and axes.
    """
    Z = np.asarray(data, dtype=float)
    if Z.ndim != 2:
        raise ValueError("plot_operando expects a 2-D array")
    M, N = Z.shape
    if x is None:
        x = np.arange(N)
    if y is None:
        y = np.arange(M)
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.size != N or y.size != M:
        raise ValueError(
            f"x must have length {N} and y length {M}, got {x.size} and {y.size}"
        )

    if smooth and smooth > 0:
        try:
            from scipy.ndimage import gaussian_filter

            Z = gaussian_filter(Z, sigma=float(smooth))
        except Exception:
            import warnings as _w

            _w.warn("scipy not available; skipping gaussian smoothing")

    fig, ax = prepare_axes(ax, journal)

    cmap_obj = _resolve_cmap(cmap)

    norm = None
    if log_z:
        from matplotlib.colors import LogNorm

        zmin = float(np.nanmin(Z[Z > 0])) if np.any(Z > 0) else 1e-12
        zmax = float(np.nanmax(Z))
        norm = LogNorm(vmin=zmin, vmax=zmax)

    extent = [float(x.min()), float(x.max()), float(y.min()), float(y.max())]
    im = ax.imshow(
        Z,
        aspect="auto",
        origin="lower",
        extent=extent,
        cmap=cmap_obj,
        norm=norm,
        **kwargs,
    )

    if contour_levels is not None:
        X, Y = np.meshgrid(x, y)
        ax.contour(
            X,
            Y,
            Z,
            levels=contour_levels,
            colors="white",
            linewidths=0.4,
            alpha=0.6,
        )

    ax.set_xlabel(xlabel if xlabel is not None else r"2$\theta$ ($^\circ$)")
    if ylabel:
        ax.set_ylabel(ylabel)

    cbar = fig.colorbar(im, ax=ax, shrink=0.85, pad=0.02, aspect=25)
    cbar.outline.set_linewidth(0.5)
    cbar.ax.tick_params(width=0.5, length=2)
    label_text = cbar_label if cbar_label else "Intensity (a.u.)"
    cbar.set_label(label_text, rotation=270, labelpad=6)

    finalize(fig, save)
    return fig, ax
