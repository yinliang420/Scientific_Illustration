"""Zoom inset with dashed connector rectangle."""

from __future__ import annotations

from typing import Sequence

from matplotlib.patches import ConnectionPatch, Rectangle


def add_inset(
    ax,
    bounds: Sequence[float] = (0.55, 0.55, 0.4, 0.4),
    xlim: Sequence[float] | None = None,
    ylim: Sequence[float] | None = None,
    copy_lines: bool = True,
    connect: bool = True,
):
    """Add an inset axes to ``ax`` showing the region ``(xlim, ylim)``.

    Parameters
    ----------
    bounds
        ``(x0, y0, w, h)`` in axes fraction coordinates.
    copy_lines
        Redraw every line already on ``ax`` into the inset.
    connect
        Draw a dashed rectangle around the zoom region plus two connecting
        lines from opposite corners to the inset.
    """
    inset = ax.inset_axes(bounds)

    if copy_lines:
        for line in ax.get_lines():
            inset.plot(line.get_xdata(), line.get_ydata(), color=line.get_color(), lw=line.get_linewidth())

    if xlim is not None:
        inset.set_xlim(xlim)
    if ylim is not None:
        inset.set_ylim(ylim)

    inset.tick_params(labelsize=6)

    if connect and xlim is not None and ylim is not None:
        rect = Rectangle(
            (xlim[0], ylim[0]),
            xlim[1] - xlim[0],
            ylim[1] - ylim[0],
            fill=False,
            ls="--",
            ec="grey",
            lw=0.6,
        )
        ax.add_patch(rect)
        # Pick the two rectangle corners that maximise euclidean distance to
        # the inset's near corners — so connectors stay visibly long even when
        # the inset abuts/overlaps the zoom rectangle in axes-fraction coords.
        x0, y0, w, h = bounds
        ix1 = x0 + w
        iy1 = y0 + h
        # Inset corners in axes-fraction coords.
        inset_corners_frac = {
            (0, 0): (x0, y0),
            (1, 0): (ix1, y0),
            (0, 1): (x0, iy1),
            (1, 1): (ix1, iy1),
        }
        # Rectangle corners in data + axes-fraction coords.
        rect_corners_data = [
            (xlim[0], ylim[0]),
            (xlim[1], ylim[0]),
            (xlim[0], ylim[1]),
            (xlim[1], ylim[1]),
        ]
        ax_x0, ax_x1 = ax.get_xlim()
        ax_y0, ax_y1 = ax.get_ylim()
        def _to_frac(xd, yd):
            return ((xd - ax_x0) / (ax_x1 - ax_x0),
                    (yd - ax_y0) / (ax_y1 - ax_y0))
        rect_corners_frac = [_to_frac(xd, yd) for (xd, yd) in rect_corners_data]
        # Each inset corner connects to one rectangle corner; pick a pairing
        # that maximises total distance. Use two inset corners that lie on
        # the inset edge facing the rectangle. Default: top/bottom of inset's
        # near-rectangle side.
        # Determine which side of the inset faces the rectangle.
        rect_cx = 0.5 * (rect_corners_frac[0][0] + rect_corners_frac[3][0])
        rect_cy = 0.5 * (rect_corners_frac[0][1] + rect_corners_frac[3][1])
        inset_cx = x0 + 0.5 * w
        inset_cy = y0 + 0.5 * h
        # Decide near-edge of inset (the one closest to rect centre).
        if abs(rect_cx - inset_cx) >= abs(rect_cy - inset_cy):
            # Horizontal pairing: inset's left or right edge faces the rect.
            ix_near = 0 if inset_cx > rect_cx else 1
            inset_pair = [(ix_near, 0), (ix_near, 1)]
        else:
            iy_near = 0 if inset_cy > rect_cy else 1
            inset_pair = [(0, iy_near), (1, iy_near)]
        # For each inset corner in the pair, choose the NEAREST rectangle
        # corner — the conventional zoom-indicator idiom (matches matplotlib's
        # ``mark_inset``) so connectors don't cross the rectangle.  When the
        # inset abuts the zoom region the user should nudge the inset bounds
        # so the connectors have visible length.
        used = set()
        pairs = []
        for fk in inset_pair:
            ix_frac = inset_corners_frac[fk]
            best_idx = None
            best_d = float("inf")
            for idx, rf in enumerate(rect_corners_frac):
                if idx in used:
                    continue
                d = (rf[0] - ix_frac[0]) ** 2 + (rf[1] - ix_frac[1]) ** 2
                if d < best_d:
                    best_d = d
                    best_idx = idx
            used.add(best_idx)
            pairs.append((rect_corners_data[best_idx], fk))
        for (xd, yd), (xf, yf) in pairs:
            cp = ConnectionPatch(
                xyA=(xd, yd), coordsA=ax.transData,
                xyB=(xf, yf), coordsB=inset.transAxes,
                linestyle="--", color="grey", lw=0.5,
            )
            ax.add_artist(cp)

    return inset
