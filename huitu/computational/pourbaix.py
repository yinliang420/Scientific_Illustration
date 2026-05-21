"""Pourbaix (E-pH) diagram — polygon-region rendering."""

from __future__ import annotations

import re
from typing import Iterable

import numpy as np

from huitu._common import _draw_regions, finalize, prepare_axes

# Nernst slope at 25 degC, 1 atm: (RT/F) * ln(10) in volts per pH unit.
NERNST_25C = 0.05916


_SUBSCRIPT_DIGITS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
_SUPERSCRIPT_DIGITS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")


def _format_species(name: str) -> str:
    """Mathtext-subscript any digit run that follows a letter.

    ``"Fe2O3"`` → ``"Fe$_2$O$_3$"`` so matplotlib renders true subscripts
    instead of leaving "Fe2O3" as plain text (which mpl spaces awkwardly).
    Unicode subscripts (``Fe₂O₃``) and superscripts (``Fe³⁺``) are first
    normalised to ASCII so the same mathtext path applies — many sans-serif
    journal fonts have no glyph for ``₂`` and render it as a visible gap.
    Already-mathtext-formatted labels (those containing ``$``) pass through
    unchanged.
    """
    if not isinstance(name, str) or "$" in name:
        return name
    # 1) unicode subscripts → ``$_n$``
    out = re.sub(
        r"([₀₁₂₃₄₅₆₇₈₉]+)",
        lambda m: "$_" + m.group(1).translate(_SUBSCRIPT_DIGITS) + "$",
        name,
    )
    # 2) unicode superscripts (e.g. ``Fe³⁺`` charge state) → ``$^{n+}$``
    def _sup(m: re.Match) -> str:
        body = m.group(0).translate(_SUPERSCRIPT_DIGITS)
        body = body.replace("⁺", "+").replace("⁻", "-")
        return "$^{" + body + "}$"

    out = re.sub(r"[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]+", _sup, out)
    # 3) raw ASCII digit-runs that sit immediately AFTER a letter or `)` get
    #    subscripted (e.g. Fe2O3 → Fe$_2$O$_3$; Ca(OH)2 → Ca(OH)$_2$).
    #    Then handle trailing charge states like "Fe2+" / "NH4+" → superscript.
    def _ascii_charge(m: re.Match) -> str:
        digits = m.group(1) or ""
        sign = m.group(2)
        body = digits + sign
        return "$^{" + body + "}$"

    # Charge state must run first so e.g. "Fe2+" handles the trailing `+`
    # without the digit `2` getting eaten by the subscript regex below.
    out = re.sub(r"(\d*)([+-])(?=\b|$)", _ascii_charge, out)
    out = re.sub(r"(?<=[A-Za-z\)])(\d+)", r"$_\1$", out)
    return out


def plot_pourbaix(
    data: Iterable[dict],
    ax=None,
    journal: str = "default",
    save=None,
    ph_range: tuple = (0.0, 14.0),
    e_range: tuple = (-1.0, 2.0),
    water_stability: bool = True,
    **kwargs,
):
    """Plot a Pourbaix diagram from a list of stability-region dicts.

    data
        Iterable of ``{label, vertices, color}`` dicts. ``vertices`` is a
        list of ``(pH, E)`` tuples forming a closed polygon (need not repeat
        the first point).
    ph_range, e_range
        Axis limits.
    water_stability
        Overlay the H2 (``E = -0.05916 * pH``) and O2
        (``E = 1.229 - 0.05916 * pH``) dashed lines at 25 degC, 1 atm.
    """
    fig, ax = prepare_axes(ax, journal)

    alpha = kwargs.pop("alpha", 0.45)
    edge_color = kwargs.pop("edgecolor", "black")

    # ``label_position="top"`` anchors centroid labels near the top of each
    # polygon so the diagonally-descending water-stability lines (H2/H2O and
    # O2/H2O) pass *below* the text rather than slicing through it.
    # Pre-format species labels ("Fe2O3" → "Fe$_2$O$_3$") so digits render as
    # subscripts rather than as plain text with an awkward gap.
    formatted = [
        {**r, "label": _format_species(r.get("label", ""))} for r in data
    ]
    _draw_regions(ax, formatted, alpha=alpha, edge_color=edge_color, lw=0.6,
                  label_position="top")

    if water_stability:
        ph = np.linspace(ph_range[0], ph_range[1], 50)
        # zorder=2 puts the dashed water-stability lines *under* region labels
        # (which use zorder=4 + white halo) so the user's "H2/H2O line over the
        # centroid text" complaint can't recur.
        ax.plot(ph, -NERNST_25C * ph, ls="--", color="grey", lw=0.7,
                label=r"H$_2$/H$_2$O", zorder=2)
        ax.plot(ph, 1.229 - NERNST_25C * ph, ls="--", color="grey", lw=0.7,
                label=r"O$_2$/H$_2$O", zorder=2)
        # Opaque white frame keeps the water-stability legend legible even when
        # it lands over a region label at the top-right corner.
        ax.legend(loc="best", fontsize=6, framealpha=0.95,
                  facecolor="white", edgecolor="lightgray")

    ax.set_xlim(*ph_range)
    ax.set_ylim(*e_range)
    ax.set_xlabel("pH")
    ax.set_ylabel("E vs SHE (V)")

    finalize(fig, save)
    return fig, ax
