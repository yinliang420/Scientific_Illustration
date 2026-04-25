"""Advanced in-situ / operando characterization plots (premium).

These chart types are staples of operando-spectroscopy papers:

* :func:`plot_operando_waterfall` — stagger-stacked spectra colored by a
  perturbation axis (time, potential, temperature).
* :func:`plot_operando_xrd_echem` — the canonical operando-battery figure:
  XRD / Raman heatmap on the left, galvanostatic (or CV) profile on the right,
  sharing the perturbation axis.
* :func:`plot_operando_3d_surface` — 3-D waterfall surface over
  ``(x, perturbation, intensity)``.
* :func:`plot_operando_diffmap` — Δ-intensity heatmap (each spectrum minus
  a reference), highlighting what changed.
* :func:`plot_operando_peak_evolution` — track fit-parameter evolution
  (peak position, FWHM, area) across the perturbation axis as multi-curve.
"""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np
import matplotlib.pyplot as plt

from huitu._common import finalize, prepare_axes
from huitu.style import PALETTES, get_cmap, _GRADIENT_PALETTES
from ._license import require_pro


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _resolve_cmap(cmap):
    """Return a matplotlib colormap from a palette name or cmap."""
    if cmap is None:
        return None
    if isinstance(cmap, str):
        key = cmap.lower()
        if key in PALETTES:
            try:
                return get_cmap(key)
            except Exception:
                from matplotlib.colors import LinearSegmentedColormap
                return LinearSegmentedColormap.from_list(
                    f"huitu-{key}", PALETTES[key])
        return cmap
    return cmap


# ------------------------------------------------------------------
# Waterfall (stagger-stacked spectra with time-gradient coloring)
# ------------------------------------------------------------------
def plot_operando_waterfall(
    data,
    x=None,
    y=None,
    *,
    ax=None,
    journal: str = "default",
    save=None,
    cmap: str = "met-hiroshige",
    stagger: float = 0.08,
    linewidth: float = 0.9,
    fill: bool = False,
    fill_alpha: float = 0.25,
    xlabel: str | None = None,
    ylabel: str | None = None,
    cbar_label: str | None = None,
    every: int = 1,
    **kwargs,
):
    """Stagger-stacked operando spectra, colored by the perturbation axis.

    Parameters
    ----------
    data
        2-D array (M, N) — M spectra acquired at M perturbation values.
    x
        Length-N spectral x-axis (e.g. 2theta, cm^-1, energy).
    y
        Length-M perturbation values (time, potential, temperature).
    stagger
        Vertical offset per spectrum, as a fraction of the spectrum's peak.
    fill
        If True, fill under each curve.
    every
        Plot every k-th spectrum (useful when M is large).
    """
    require_pro("plot_operando_waterfall")
    Z = np.asarray(data, dtype=float)
    if Z.ndim != 2:
        raise ValueError("data must be 2-D (M spectra x N bins)")
    M, N = Z.shape
    if x is None:
        x = np.arange(N)
    if y is None:
        y = np.arange(M)
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    fig, ax = prepare_axes(ax, journal)
    cmap_obj = _resolve_cmap(cmap)
    peak = float(np.nanmax(Z))
    if peak <= 0:
        peak = 1.0

    idxs = list(range(0, M, max(int(every), 1)))
    n_plot = len(idxs)
    for k, i in enumerate(idxs):
        frac = i / max(M - 1, 1)
        col = cmap_obj(frac) if cmap_obj is not None else None
        z = n_plot - k  # earlier spectra drawn behind
        offset = k * stagger * peak
        curve = Z[i] + offset
        if fill:
            ax.fill_between(x, offset, curve, color=col, alpha=fill_alpha,
                            linewidth=0, zorder=z)
        ax.plot(x, curve, color=col, linewidth=linewidth, zorder=z + 0.3)

    # Colorbar encoding the perturbation axis.
    import matplotlib as mpl
    norm = mpl.colors.Normalize(vmin=float(y.min()), vmax=float(y.max()))
    sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap_obj)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, shrink=0.85, pad=0.02, aspect=25)
    cbar.set_label(cbar_label or (ylabel or "perturbation"),
                   rotation=270, labelpad=8)

    if xlabel:
        ax.set_xlabel(xlabel)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(which="both", left=False, top=False, right=False)
    finalize(fig, save)
    return fig, ax


# ------------------------------------------------------------------
# XRD + galvanostatic 2-panel (THE canonical operando-battery figure)
# ------------------------------------------------------------------
def plot_operando_xrd_echem(
    data,
    x,
    y,
    *,
    echem: Sequence[float],
    journal: str = "default",
    save=None,
    cmap: str = "crameri-batlow",
    xlabel: str | None = None,
    ylabel: str = "time / capacity",
    echem_xlabel: str = "E (V)",
    cbar_label: str | None = None,
    width_ratios=(3.0, 1.0),
    echem_color: str = "#BC3C29",
    contour_levels=None,
    log_z: bool = False,
    **kwargs,
):
    """Two-panel operando figure: spectral heatmap on the left, electrochemical
    profile on the right — both sharing the perturbation axis (y).

    ``data`` is an (M, N) heatmap. ``echem`` must be length-M.
    """
    require_pro("plot_operando_xrd_echem")
    Z = np.asarray(data, dtype=float)
    if Z.ndim != 2:
        raise ValueError("data must be 2-D")
    M, N = Z.shape
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    e = np.asarray(echem, dtype=float)
    if x.size != N or y.size != M or e.size != M:
        raise ValueError("shape mismatch between data, x, y, echem")

    from huitu.style import use_journal as _uj
    _uj(journal)
    fig, axes = plt.subplots(
        1, 2, sharey=True,
        gridspec_kw={"width_ratios": list(width_ratios)},
        figsize=(4.8, 3.6),
    )
    ax_map, ax_ec = axes

    cmap_obj = _resolve_cmap(cmap)
    norm = None
    if log_z:
        from matplotlib.colors import LogNorm
        zmin = float(np.nanmin(Z[Z > 0])) if np.any(Z > 0) else 1e-12
        zmax = float(np.nanmax(Z))
        norm = LogNorm(vmin=zmin, vmax=zmax)
    extent = [float(x.min()), float(x.max()), float(y.min()), float(y.max())]
    im = ax_map.imshow(Z, aspect="auto", origin="lower", extent=extent,
                       cmap=cmap_obj, norm=norm)
    if contour_levels is not None:
        X, Y = np.meshgrid(x, y)
        ax_map.contour(X, Y, Z, levels=contour_levels, colors="white",
                       linewidths=0.4, alpha=0.6)
    if xlabel:
        ax_map.set_xlabel(xlabel)
    ax_map.set_ylabel(ylabel)
    ax_map.spines["top"].set_visible(False)
    ax_map.spines["right"].set_visible(False)
    ax_map.tick_params(which="both", top=False, right=False)

    # Colorbar inside map panel bounds (via dedicated axes to avoid squeezing).
    cbar = fig.colorbar(im, ax=ax_map, shrink=0.85, pad=0.02, aspect=25,
                        location="top")
    cbar.set_label(cbar_label or "Intensity", labelpad=4)
    cbar.outline.set_linewidth(0.5)
    cbar.ax.tick_params(width=0.5, length=2)

    # Electrochemistry panel
    ax_ec.plot(e, y, color=echem_color, linewidth=1.2)
    ax_ec.set_xlabel(echem_xlabel)
    ax_ec.spines["top"].set_visible(False)
    ax_ec.spines["right"].set_visible(False)
    ax_ec.tick_params(which="both", top=False, right=False, labelleft=False)

    fig.subplots_adjust(wspace=0.05, top=0.82)
    if save is not None:
        fig.savefig(save, bbox_inches="tight")
    return fig, (ax_map, ax_ec)


# ------------------------------------------------------------------
# 3-D waterfall surface
# ------------------------------------------------------------------
def plot_operando_3d_surface(
    data,
    x=None,
    y=None,
    *,
    journal: str = "default",
    save=None,
    cmap: str = "crameri-batlow",
    elev: float = 30,
    azim: float = -60,
    xlabel: str | None = None,
    ylabel: str | None = None,
    zlabel: str = "Intensity",
    stride: int = 1,
    **kwargs,
):
    """3-D surface / waterfall for operando spectra.

    Uses an ``Axes3D`` with ``plot_surface`` + thin wireframe overlay.
    """
    require_pro("plot_operando_3d_surface")
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers 3d proj)

    Z = np.asarray(data, dtype=float)
    if Z.ndim != 2:
        raise ValueError("data must be 2-D")
    M, N = Z.shape
    if x is None:
        x = np.arange(N)
    if y is None:
        y = np.arange(M)
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    X, Y = np.meshgrid(x, y)

    from huitu.style import use_journal as _uj
    _uj(journal)
    fig = plt.figure(figsize=(5.2, 4.0))
    ax = fig.add_subplot(111, projection="3d")
    cmap_obj = _resolve_cmap(cmap)
    surf = ax.plot_surface(X, Y, Z, cmap=cmap_obj, linewidth=0.15,
                           edgecolor="#444444", rstride=max(1, M // 30),
                           cstride=stride, antialiased=True, alpha=0.92)
    ax.view_init(elev=elev, azim=azim)
    if xlabel:
        ax.set_xlabel(xlabel, labelpad=6)
    if ylabel:
        ax.set_ylabel(ylabel, labelpad=6)
    ax.set_zlabel(zlabel, labelpad=4)
    # Lighten grid background
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor("white")
        axis.pane.set_edgecolor("#DDDDDD")
    if save is not None:
        fig.savefig(save, bbox_inches="tight", dpi=220)
    return fig, ax


# ------------------------------------------------------------------
# Difference map (each spectrum minus reference)
# ------------------------------------------------------------------
def plot_operando_diffmap(
    data,
    x=None,
    y=None,
    *,
    reference: int | Sequence[float] = 0,
    ax=None,
    journal: str = "default",
    save=None,
    cmap: str = "ft-diverging",
    xlabel: str | None = None,
    ylabel: str | None = None,
    cbar_label: str = "$\\Delta$ Intensity",
    symmetric: bool = True,
    **kwargs,
):
    """Δ-intensity heatmap: each row is (spectrum − reference_spectrum).

    ``reference`` may be an integer index into ``data`` (default 0 = first
    spectrum) or a length-N array used as the reference baseline.
    """
    require_pro("plot_operando_diffmap")
    Z = np.asarray(data, dtype=float)
    if Z.ndim != 2:
        raise ValueError("data must be 2-D")
    M, N = Z.shape
    if x is None:
        x = np.arange(N)
    if y is None:
        y = np.arange(M)
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    if isinstance(reference, int):
        ref = Z[reference]
    else:
        ref = np.asarray(reference, dtype=float)
        if ref.size != N:
            raise ValueError(f"reference length {ref.size} != N={N}")
    dZ = Z - ref[None, :]

    fig, ax = prepare_axes(ax, journal)
    cmap_obj = _resolve_cmap(cmap)

    vmax = float(np.nanmax(np.abs(dZ)))
    vmin = -vmax if symmetric else float(np.nanmin(dZ))
    extent = [float(x.min()), float(x.max()), float(y.min()), float(y.max())]
    im = ax.imshow(dZ, aspect="auto", origin="lower", extent=extent,
                   cmap=cmap_obj, vmin=vmin, vmax=vmax)
    cbar = fig.colorbar(im, ax=ax, shrink=0.85, pad=0.02, aspect=25)
    cbar.set_label(cbar_label, rotation=270, labelpad=8)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(which="both", top=False, right=False)
    finalize(fig, save)
    return fig, ax


# ------------------------------------------------------------------
# Peak-evolution multi-curve
# ------------------------------------------------------------------
def plot_operando_peak_evolution(
    y,
    series,
    *,
    ax=None,
    journal: str = "default",
    save=None,
    palette: str = "ggsci-npg",
    markers: bool = True,
    marker_size: float = 20,
    linewidth: float = 1.4,
    xlabel: str | None = None,
    ylabel: str | None = None,
    legend_loc: str = "best",
    **kwargs,
):
    """Evolution of fit parameters (peak position, FWHM, area, ...) across
    a perturbation axis.

    ``series`` is a mapping ``{name: values}`` where each ``values`` array has
    the same length as ``y`` (the perturbation / time axis).
    """
    require_pro("plot_operando_peak_evolution")
    fig, ax = prepare_axes(ax, journal)
    y = np.asarray(y, dtype=float)
    colors = PALETTES.get(palette, PALETTES["ggsci-npg"])

    for i, (name, vals) in enumerate(series.items()):
        v = np.asarray(vals, dtype=float)
        if v.size != y.size:
            raise ValueError(f"series '{name}' length {v.size} != {y.size}")
        c = colors[i % len(colors)]
        ax.plot(y, v, color=c, linewidth=linewidth, label=name,
                zorder=2 + i)
        if markers:
            ax.scatter(y, v, color=c, s=marker_size, edgecolor="white",
                       linewidth=0.5, zorder=3 + i)

    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(which="both", top=False, right=False)
    ax.legend(frameon=False, fontsize=7, loc=legend_loc)
    finalize(fig, save)
    return fig, ax


# ------------------------------------------------------------------
# Contour-style evolution map with spectral-reference overlay
# ------------------------------------------------------------------
def plot_operando_contour(
    data,
    x=None,
    y=None,
    *,
    ax=None,
    journal: str = "default",
    save=None,
    cmap: str = "met-hiroshige",
    levels: int = 14,
    filled: bool = True,
    reference_peaks: Iterable[float] | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
    cbar_label: str = "Intensity",
    **kwargs,
):
    """Contour / filled-contour evolution map.

    ``reference_peaks`` — iterable of spectral-axis positions drawn as thin
    vertical dashed reference lines (e.g. expected Bragg positions).
    """
    require_pro("plot_operando_contour")
    Z = np.asarray(data, dtype=float)
    if Z.ndim != 2:
        raise ValueError("data must be 2-D")
    M, N = Z.shape
    if x is None:
        x = np.arange(N)
    if y is None:
        y = np.arange(M)
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    fig, ax = prepare_axes(ax, journal)
    cmap_obj = _resolve_cmap(cmap)
    X, Y = np.meshgrid(x, y)
    if filled:
        cs = ax.contourf(X, Y, Z, levels=levels, cmap=cmap_obj)
    else:
        cs = ax.contour(X, Y, Z, levels=levels, cmap=cmap_obj, linewidths=0.6)
    cbar = fig.colorbar(cs, ax=ax, shrink=0.85, pad=0.02, aspect=25)
    cbar.set_label(cbar_label, rotation=270, labelpad=8)
    if reference_peaks is not None:
        for rp in reference_peaks:
            ax.axvline(rp, color="#FFFFFF", linewidth=0.6,
                       linestyle=(0, (3, 2)), alpha=0.75, zorder=5)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(which="both", top=False, right=False)
    finalize(fig, save)
    return fig, ax
