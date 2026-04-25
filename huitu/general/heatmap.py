"""2-D heatmap / contour plot."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from huitu._common import finalize, prepare_axes
from huitu.style import PALETTES, _GRADIENT_PALETTES, get_cmap


def _resolve_cmap(cmap):
    if cmap is None or not isinstance(cmap, str):
        return cmap
    key = cmap.lower()
    if key in PALETTES and key in _GRADIENT_PALETTES:
        return get_cmap(key)
    if key in PALETTES:
        from matplotlib.colors import LinearSegmentedColormap

        return LinearSegmentedColormap.from_list(f"huitu-{key}", PALETTES[key])
    return cmap


def _to_matrix(data):
    if isinstance(data, pd.DataFrame):
        return data.to_numpy(dtype=float), list(data.index), list(data.columns)
    if isinstance(data, (str, Path)):
        df = pd.read_csv(data, index_col=0)
        return df.to_numpy(dtype=float), list(df.index), list(df.columns)
    if isinstance(data, np.ndarray):
        if data.ndim != 2:
            raise ValueError("heatmap ndarray must be 2-D")
        m = data.astype(float)
        return m, list(range(m.shape[0])), list(range(m.shape[1]))
    raise TypeError(f"plot_heatmap expects DataFrame/CSV/ndarray; got {type(data).__name__}")


def plot_heatmap(
    data,
    ax=None,
    journal: str = "default",
    save=None,
    mode: str = "heatmap",
    cmap: str = "viridis",
    annot: bool = False,
    fmt: str = ".2g",
    cbar_label: str = "",
    center: float | None = None,
    **kwargs,
):
    """2-D heatmap, contour, or filled contour.

    mode
        ``'heatmap'`` (default, imshow), ``'contour'``, ``'contourf'``.
    annot
        If True, overlay cell values (heatmap mode only).
    center
        If set, apply a diverging normalization centered on this value. When
        ``center == 0`` the range is symmetrized around zero
        (``vmin = -vmax``); otherwise :class:`matplotlib.colors.TwoSlopeNorm`
        is used with the data's min/max.
    """
    if mode not in ("heatmap", "contour", "contourf"):
        raise ValueError("mode must be 'heatmap', 'contour', or 'contourf'")

    fig, ax = prepare_axes(ax, journal)
    mat, rows, cols = _to_matrix(data)
    cmap = _resolve_cmap(cmap)

    # Build an optional diverging norm. Pop user-provided vmin/vmax so they
    # don't collide with the norm.
    norm = None
    if center is not None:
        import matplotlib.colors as mcolors

        user_vmin = kwargs.pop("vmin", None)
        user_vmax = kwargs.pop("vmax", None)
        dmin = float(np.nanmin(mat)) if user_vmin is None else float(user_vmin)
        dmax = float(np.nanmax(mat)) if user_vmax is None else float(user_vmax)
        if center == 0:
            m = max(abs(dmin), abs(dmax), 1e-12)
            norm = mcolors.TwoSlopeNorm(vcenter=0.0, vmin=-m, vmax=m)
        else:
            lo = min(dmin, center - 1e-12)
            hi = max(dmax, center + 1e-12)
            norm = mcolors.TwoSlopeNorm(vcenter=float(center), vmin=lo, vmax=hi)

    if mode == "heatmap":
        if norm is not None:
            im = ax.imshow(mat, cmap=cmap, aspect="auto", norm=norm, **kwargs)
        else:
            im = ax.imshow(mat, cmap=cmap, aspect="auto", **kwargs)
        ax.set_xticks(np.arange(len(cols)))
        ax.set_xticklabels(cols, rotation=45, ha="right")
        ax.set_yticks(np.arange(len(rows)))
        ax.set_yticklabels(rows)
        if annot:
            # Auto white/black text based on |value| relative to range magnitude.
            try:
                _vmin = float(np.nanmin(mat))
                _vmax = float(np.nanmax(mat))
                _mag = max(abs(_vmin), abs(_vmax), 1e-12)
            except Exception:
                _mag = 1.0
            for i in range(mat.shape[0]):
                for j in range(mat.shape[1]):
                    val = mat[i, j]
                    if np.isnan(val):
                        continue
                    text_color = "white" if abs(val) > 0.55 * _mag else "black"
                    ax.text(j, i, format(val, fmt),
                            ha="center", va="center", fontsize=6,
                            color=text_color)
    else:
        xs = np.arange(mat.shape[1])
        ys = np.arange(mat.shape[0])
        X, Y = np.meshgrid(xs, ys)
        plotter = ax.contour if mode == "contour" else ax.contourf
        if norm is not None:
            im = plotter(X, Y, mat, cmap=cmap, norm=norm, **kwargs)
        else:
            im = plotter(X, Y, mat, cmap=cmap, **kwargs)
        ax.set_aspect("auto")

    cbar = fig.colorbar(im, ax=ax)
    if cbar_label:
        cbar.set_label(cbar_label)

    finalize(fig, save)
    return fig, ax
