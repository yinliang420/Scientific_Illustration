"""Internal helpers shared across plot modules."""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from huitu.readers.txt_csv import read_xy
from huitu.style import use_journal


def coerce_xy(data: Any) -> Tuple[np.ndarray, np.ndarray]:
    """Normalize supported inputs into `(x, y)` numpy arrays."""
    if isinstance(data, (str, Path)):
        return read_xy(data)
    if isinstance(data, tuple) and len(data) == 2:
        return np.asarray(data[0], dtype=float), np.asarray(data[1], dtype=float)
    if isinstance(data, np.ndarray):
        if data.ndim != 2 or data.shape[1] < 2:
            raise ValueError("ndarray must have shape (N, >=2)")
        return data[:, 0].astype(float), data[:, 1].astype(float)
    if isinstance(data, pd.DataFrame):
        if data.shape[1] < 2:
            raise ValueError("DataFrame must have at least two columns")
        return (
            data.iloc[:, 0].to_numpy(dtype=float),
            data.iloc[:, 1].to_numpy(dtype=float),
        )
    raise TypeError(f"unsupported data type: {type(data).__name__}")


def is_multi_input(data: Any) -> bool:
    """Decide whether ``data`` is a collection of multiple curves.

    A 2-tuple of 1-D equal-length numeric arrays is treated as a single
    ``(x, y)`` sample; anything else that is a list/tuple is "multi".
    """
    if not isinstance(data, (list, tuple)):
        return False
    if len(data) == 2:
        a, b = data
        if isinstance(a, (str, Path, pd.DataFrame)) or isinstance(
            b, (str, Path, pd.DataFrame)
        ):
            return True
        if isinstance(a, np.ndarray) and a.ndim == 2:
            return True
        if isinstance(b, np.ndarray) and b.ndim == 2:
            return True
        try:
            aa = np.asarray(a)
            bb = np.asarray(b)
        except Exception:
            return True
        if aa.ndim != 1 or bb.ndim != 1:
            return True
        if aa.shape != bb.shape:
            return True
        if not (np.issubdtype(aa.dtype, np.number) and np.issubdtype(bb.dtype, np.number)):
            return True
        return False
    return True


def prepare_axes(ax, journal: str):
    """Apply journal style if no axes provided, then return (fig, ax)."""
    if ax is None:
        use_journal(journal)
        fig, ax = plt.subplots()
    else:
        fig = ax.figure
    return fig, ax


def _draw_regions(ax, regions, alpha: float = 0.5, edge_color: str = "black",
                  lw: float = 0.6):
    """Draw labelled polygon regions on ``ax``.

    Each region is a dict with ``vertices`` (Nx2 iterable of ``(x, y)``),
    optional ``label`` (drawn at centroid), and optional ``color``. Used by
    Pourbaix and phase-diagram plots.
    """
    from matplotlib.patches import Polygon

    for i, region in enumerate(regions):
        verts = np.asarray(region["vertices"], dtype=float)
        color = region.get("color") or f"C{i}"
        poly = Polygon(verts, closed=True, facecolor=color,
                       edgecolor=edge_color, lw=lw, alpha=alpha)
        ax.add_patch(poly)
        cx = float(np.mean(verts[:, 0]))
        cy = float(np.mean(verts[:, 1]))
        ax.text(cx, cy, region.get("label", ""), ha="center", va="center",
                fontsize=7)


def place_legend(ax, labels, traces=None, legend="auto", pad_top=0.18,
                 fontsize=None, label_pad_frac: float = 0.22):
    """Attach a legend to ``ax`` without overlapping data traces.

    Parameters
    ----------
    ax
        Target axes.
    labels
        Iterable of per-trace labels (``None`` entries are skipped).
    traces
        Optional list of ``(x, y_plotted, color)`` tuples. Required for
        ``legend="inline"`` — each label is pinned at the right end of its
        trace in the matching color, so no stacked line is ever covered.
    legend
        One of:
          * ``"auto"`` — inline if ``traces`` + 3+ labelled curves, else ``"best"``
          * ``"inline"`` — annotate labels next to each trace's right edge
          * ``"best"``, ``"upper right"``, ``"upper left"`` … — mpl ``loc``
          * ``"outside"`` — box legend to the right of the axes
          * ``"none"`` / ``False`` — no legend
    pad_top
        Fractional headroom (of current y-span) to reserve above the top
        plotted value, so an inside legend never sits on top of a trace.
    label_pad_frac
        When ``legend="inline"`` and inline annotations extend past the right
        edge of the axes, expand ``xlim`` by this fraction of the current
        x-span so labels remain visible. Used as a fallback when per-annotation
        bbox extents are unavailable.
    """
    labels = list(labels) if labels is not None else []
    has_labels = any(l for l in labels)
    if legend in (None, False, "none") or not has_labels:
        return

    # Always reserve a bit of vertical breathing room above the data.
    ymin, ymax = ax.get_ylim()
    span = ymax - ymin
    if span > 0:
        ax.set_ylim(ymin, ymax + pad_top * span)

    n_labelled = sum(1 for l in labels if l)
    mode = legend

    # Demote inline -> best on very narrow axes (inline is illegible).
    if mode in ("auto", "inline"):
        try:
            width_px = ax.get_window_extent().width
        except Exception:
            width_px = 400  # assume fine
        if width_px < 220 and mode == "auto":
            mode = "best"
        elif width_px < 220 and mode == "inline":
            mode = "best"

    if mode == "auto":
        mode = "inline" if (traces and n_labelled >= 3) else "best"

    if mode == "inline" and traces:
        import matplotlib as mpl

        fs = fontsize or mpl.rcParams.get("legend.fontsize", 7)
        xlo, xhi = ax.get_xlim()
        inverted = xlo > xhi  # FTIR/XPS use reversed axes
        annos = []
        for (x, y, color), label in zip(traces, labels):
            if not label:
                continue
            xi = np.asarray(x)
            yi = np.asarray(y)
            if xi.size == 0:
                continue
            # Pick the trace end that corresponds to the plot's right edge.
            if inverted:
                idx = int(np.argmin(xi))
            else:
                idx = int(np.argmax(xi))
            ha = "left"
            dx = 3
            a = ax.annotate(
                label,
                xy=(float(xi[idx]), float(yi[idx])),
                xytext=(dx, 0),
                textcoords="offset points",
                va="center",
                ha=ha,
                color=color,
                fontsize=fs,
                clip_on=False,
            )
            annos.append(a)

        # Expand x-axis so inline labels don't overflow the axes.
        fig = ax.figure
        xlo, xhi = ax.get_xlim()
        span_x = xhi - xlo
        try:
            fig.canvas.draw()
            inv = ax.transData.inverted()
            if inverted:
                # right edge is the smaller x (xhi); labels extend toward smaller x
                min_x_data = xhi
                for a in annos:
                    try:
                        bb = a.get_window_extent()
                        # label's leftmost pixel -> data x
                        x_data, _ = inv.transform((bb.x0, bb.y0))
                        if x_data < min_x_data:
                            min_x_data = x_data
                    except Exception:
                        pass
                # inverted axis: xlo > xhi; extend xhi downward a bit
                target = min(min_x_data, xhi - abs(span_x) * 0.01)
                if target < xhi:
                    ax.set_xlim(xlo, target)
            else:
                max_x_data = xhi
                for a in annos:
                    try:
                        bb = a.get_window_extent()
                        x_data, _ = inv.transform((bb.x1, bb.y1))
                        if x_data > max_x_data:
                            max_x_data = x_data
                    except Exception:
                        pass
                target = max(max_x_data, xhi + abs(span_x) * 0.01)
                if target > xhi:
                    ax.set_xlim(xlo, target * 1.01)
        except Exception:
            # Fallback: blindly pad by label_pad_frac of x-span.
            pad = abs(span_x) * float(label_pad_frac)
            if inverted:
                ax.set_xlim(xlo, xhi - pad)
            else:
                ax.set_xlim(xlo, xhi + pad)
        return

    if mode == "outside":
        ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5),
                  frameon=False, fontsize=fontsize)
        return

    ax.legend(loc=mode, frameon=False, fontsize=fontsize)


def panel_tag(ax, letter, loc: str = "outside-left", size: int = 8,
              weight: str = "bold"):
    """Place a panel tag like ``(a)`` on ``ax``.

    Parameters
    ----------
    ax
        Matplotlib axes.
    letter
        Letter for the tag. If the string already contains ``(``, it is used
        verbatim; otherwise it is wrapped in parentheses.
    loc
        ``"outside-left"`` (default, Nature style) places at
        ``(-0.12, 1.02)`` with right/bottom alignment. ``"inside-top-left"``
        puts the tag inside the panel at ``(0.02, 0.96)``.
    size, weight
        Font size / weight for the tag.
    """
    text = letter if "(" in letter else f"({letter})"
    if loc == "inside-top-left":
        ax.text(0.02, 0.96, text, transform=ax.transAxes,
                fontsize=size, fontweight=weight, va="top", ha="left")
    else:  # outside-left
        ax.text(-0.12, 1.02, text, transform=ax.transAxes,
                fontsize=size, fontweight=weight, va="bottom", ha="right")


def supertitle(fig, text, y: float = 0.98, size=None):
    """Thin wrapper around ``fig.suptitle`` with a consistent size.

    Uses ``axes.labelsize + 1`` (i.e. preset base + 2) unless overridden.
    """
    import matplotlib as mpl

    if size is None:
        base = mpl.rcParams.get("axes.labelsize", 8)
        try:
            base = float(base)
        except Exception:
            base = 8.0
        size = base + 1
    return fig.suptitle(text, y=y, fontsize=size)


def marker_clearance_pts(marker_size: float, pad_pts: float = 4.0) -> float:
    """Offset (in points) guaranteeing text clears a scatter marker.

    ``marker_size`` is matplotlib's ``scatter(s=...)`` in points². Returns
    ``marker_radius + pad_pts`` — the minimum horizontal offset from the
    marker *center* to the nearest text edge, so an annotation never kisses
    the marker outline at the default size.
    """
    import math

    radius = math.sqrt(max(float(marker_size), 1.0) / math.pi)
    return radius + float(pad_pts)


def expand_xlim_for_annos(ax, annos, pad_px: float = 6.0) -> None:
    """Widen ``ax.xlim`` so every annotation sits strictly inside the axes.

    Call *after* every artist has been added; a ``fig.canvas.draw()`` is
    forced so text window-extents are realised. Only ever widens — never
    shrinks. Keeps end-of-line labels from overlapping the spine or being
    clipped by ``bbox_inches="tight"`` at save time.

    Parameters
    ----------
    ax
        Axes whose x-limits may need widening.
    annos
        Iterable of :class:`matplotlib.text.Annotation` (or any artist with
        ``get_window_extent``) whose extents must fit inside the final axes.
    pad_px
        Extra pixels of breathing room around every annotation, in display
        coordinates. Defaults to 6 px.
    """
    if not annos:
        return
    fig = ax.figure
    try:
        fig.canvas.draw()
        ax_bbox = ax.get_window_extent()
        inv = ax.transData.inverted()
    except Exception:
        return
    min_px = ax_bbox.x0
    max_px = ax_bbox.x1
    for a in annos:
        try:
            bb = a.get_window_extent()
            if bb.width <= 0 or bb.height <= 0:
                continue
            min_px = min(min_px, bb.x0 - pad_px)
            max_px = max(max_px, bb.x1 + pad_px)
        except Exception:
            continue
    if min_px >= ax_bbox.x0 and max_px <= ax_bbox.x1:
        return
    xlo_cur, xhi_cur = ax.get_xlim()
    try:
        new_xlo = inv.transform((min_px, ax_bbox.y0))[0]
        new_xhi = inv.transform((max_px, ax_bbox.y0))[0]
    except Exception:
        return
    if xlo_cur <= xhi_cur:
        ax.set_xlim(min(new_xlo, xlo_cur), max(new_xhi, xhi_cur))
    else:  # reversed axis (e.g. XPS, FTIR)
        ax.set_xlim(max(new_xlo, xlo_cur), min(new_xhi, xhi_cur))


def finalize(fig, save):
    # constrained_layout manages spacing itself; tight_layout fights with twins.
    if not fig.get_constrained_layout():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            try:
                fig.tight_layout()
            except Exception:
                pass
    if save is not None:
        import matplotlib as mpl

        Path(save).parent.mkdir(parents=True, exist_ok=True)
        # Respect the active journal preset's savefig.dpi. If it's the
        # sentinel "figure" value (matplotlib default) fall back to 600 so
        # raster output is always publication-ready.
        dpi = mpl.rcParams.get("savefig.dpi", 600)
        if isinstance(dpi, str):
            dpi = 600
        fig.savefig(save, bbox_inches="tight", dpi=dpi)
