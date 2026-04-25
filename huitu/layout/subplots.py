"""Subplot factory with journal styling and (a)(b)(c) panel labels."""

from __future__ import annotations

from string import ascii_lowercase

import matplotlib.pyplot as plt

from huitu.style import use_journal


def make_subplots(
    nrows: int = 1,
    ncols: int = 1,
    journal: str = "default",
    panel_labels: bool = True,
    label_style: str = "({letter})",
    figsize=None,
    **kwargs,
):
    """Thin wrapper over ``plt.subplots`` that applies a journal preset and
    (optionally) draws (a), (b), ... panel labels in each axes.
    """
    use_journal(journal)
    # Passing figsize=None to plt.subplots overrides the rc preset; only forward
    # it when explicitly provided.
    if figsize is not None:
        kwargs["figsize"] = figsize
    fig, axes = plt.subplots(nrows, ncols, **kwargs)

    if panel_labels:
        flat = axes.flatten() if hasattr(axes, "flatten") else [axes]
        for ax, letter in zip(flat, ascii_lowercase):
            ax.annotate(
                label_style.format(letter=letter),
                xy=(0, 1),
                xycoords="axes fraction",
                xytext=(2, -2),
                textcoords="offset points",
                ha="left",
                va="top",
                fontweight="bold",
            )

    return fig, axes
