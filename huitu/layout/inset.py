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
        for (xd, yd), (xf, yf) in [((xlim[1], ylim[1]), (0, 1)), ((xlim[1], ylim[0]), (0, 0))]:
            cp = ConnectionPatch(
                xyA=(xd, yd), coordsA=ax.transData,
                xyB=(xf, yf), coordsB=inset.transAxes,
                linestyle="--", color="grey", lw=0.5,
            )
            ax.add_artist(cp)

    return inset
