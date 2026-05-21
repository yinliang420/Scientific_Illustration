"""Galvanostatic charge-discharge plotting."""

from __future__ import annotations

from typing import Iterable

from huitu._common import coerce_xy, finalize, is_multi_input, prepare_axes


def plot_gcd(
    data,
    ax=None,
    journal: str = "default",
    save=None,
    labels: Iterable[str] | None = None,
    **kwargs,
):
    """Plot GCD curves: capacity (mAh/g) vs potential (V). Accepts list for multi-rate overlay."""
    fig, ax = prepare_axes(ax, journal)

    is_multi = is_multi_input(data)
    items = list(data) if is_multi else [data]
    labels = list(labels) if labels else [None] * len(items)
    if len(labels) < len(items):
        labels = labels + [None] * (len(items) - len(labels))

    for item, lab in zip(items, labels):
        x, y = coerce_xy(item)
        ax.plot(x, y, label=lab, **kwargs)

    ax.set_xlabel("Specific capacity (mAh g$^{-1}$)")
    ax.set_ylabel("Potential (V)")
    if any(l for l in labels):
        ax.legend(loc="best")

    finalize(fig, save)
    return fig, ax
