"""Cyclic voltammetry plotting."""

from __future__ import annotations

from typing import Iterable

from huitu._common import coerce_xy, finalize, is_multi_input, prepare_axes


def plot_cv(
    data,
    ax=None,
    journal: str = "default",
    save=None,
    labels: Iterable[str] | None = None,
    **kwargs,
):
    """Plot CV curves. Pass a single two-column source or a list for multi-cycle overlay."""
    fig, ax = prepare_axes(ax, journal)

    is_multi = is_multi_input(data)
    items = list(data) if is_multi else [data]
    labels = list(labels) if labels else [None] * len(items)
    if len(labels) < len(items):
        labels = labels + [None] * (len(items) - len(labels))

    for item, lab in zip(items, labels):
        x, y = coerce_xy(item)
        ax.plot(x, y, label=lab, **kwargs)

    ax.axhline(0, color="grey", lw=0.5, ls="--", alpha=0.6)
    ax.set_xlabel("Potential (V vs. ref.)")
    ax.set_ylabel("Current density (A g$^{-1}$)")
    if any(l for l in labels):
        ax.legend(loc="best")

    finalize(fig, save)
    return fig, ax
