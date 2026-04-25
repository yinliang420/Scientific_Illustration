"""Electrochemical impedance Nyquist plot."""

from __future__ import annotations

from typing import Iterable

from huitu._common import coerce_xy, finalize, is_multi_input, prepare_axes


def plot_eis(
    data,
    ax=None,
    journal: str = "default",
    save=None,
    labels: Iterable[str] | None = None,
    negate_imag: bool = False,
    equal_aspect: bool = True,
    **kwargs,
):
    """Nyquist plot (Z' vs -Z''). Accepts a list for multi-sample overlay.

    Parameters
    ----------
    negate_imag
        If ``True``, the second column is interpreted as raw Z'' (typically
        negative for a capacitive response) and flipped before plotting so the
        y-axis correctly reads -Z''. If ``False`` (default), the data is
        assumed to already carry -Z'' values (common in exported EIS files).
    """
    fig, ax = prepare_axes(ax, journal)

    is_multi = is_multi_input(data)
    items = list(data) if is_multi else [data]
    labels = list(labels) if labels else [None] * len(items)
    if len(labels) < len(items):
        labels = labels + [None] * (len(items) - len(labels))

    for item, lab in zip(items, labels):
        zr, zi = coerce_xy(item)
        if negate_imag:
            zi = -zi
        ax.plot(zr, zi, "o-", markersize=3, label=lab, **kwargs)

    ax.set_xlabel(r"Z$^{\prime}$ ($\Omega$)")
    ax.set_ylabel(r"-Z$^{\prime\prime}$ ($\Omega$)")
    if equal_aspect:
        ax.set_aspect("equal", adjustable="box")
    if any(l for l in labels):
        ax.legend(loc="best")

    finalize(fig, save)
    return fig, ax
