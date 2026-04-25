"""Binary (alloy) phase diagram — polygon-region rendering."""

from __future__ import annotations

from typing import Iterable

from huitu._common import _draw_regions, finalize, prepare_axes


def plot_phase_diagram(
    data: Iterable[dict],
    ax=None,
    journal: str = "default",
    save=None,
    xlabel: str = "Composition",
    ylabel: str = r"Temperature ($^\circ$C)",
    invariants: Iterable[tuple] | None = None,
    **kwargs,
):
    """Plot a 2-D phase diagram from a list of phase-region dicts.

    data
        Iterable of ``{label, vertices, color}`` dicts. ``vertices`` is a
        list of ``(x, T)`` tuples forming each phase field.
    invariants
        Optional iterable of ``(x, T, label)`` marker points (e.g. eutectic,
        peritectic).
    """
    fig, ax = prepare_axes(ax, journal)

    alpha = kwargs.pop("alpha", 0.4)
    edge_color = kwargs.pop("edgecolor", "black")

    _draw_regions(ax, data, alpha=alpha, edge_color=edge_color, lw=0.7)

    if invariants:
        for x, T, label in invariants:
            ax.plot(x, T, marker="o", color="black", ms=4)
            ax.annotate(label, xy=(x, T), xytext=(4, 4),
                        textcoords="offset points", fontsize=6)

    ax.relim()
    ax.autoscale_view()
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    finalize(fig, save)
    return fig, ax
