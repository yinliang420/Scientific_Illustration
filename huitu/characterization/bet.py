"""BET (Brunauer–Emmett–Teller) N₂ adsorption isotherm + linear-plot panel.

Standard analysis of a porous-material gas-sorption isotherm. Two-panel
layout, Nature/Cell-Press style:

* **Left panel** — raw adsorption / desorption isotherm: volume adsorbed
  ``V_ads`` (cm³ STP g⁻¹) versus relative pressure ``P/P₀``.
* **Right panel** — BET linear plot: ``1 / [V_ads · (P₀/P − 1)]`` versus
  ``P/P₀`` over the conventional ``0.05 ≤ P/P₀ ≤ 0.30`` BET range, with
  the linear fit overlaid and the derived monolayer capacity ``V_m`` and
  specific surface area ``S_BET`` annotated inline.

The BET equation rearranged into linear form is::

    1 / [V (P₀/P − 1)]  =  (C − 1) / (V_m C) · (P/P₀)  +  1 / (V_m C)

Slope ``m`` and intercept ``b`` of that line give::

    V_m   =  1 / (m + b)
    C     =  1 + m / b
    S_BET =  V_m · N_A · σ_N2 / V_STP

with ``σ_N2 = 0.162 nm² = 16.2 Å²`` (cross-section of an N₂ molecule)
and ``V_STP = 22414 cm³ mol⁻¹``.

Input
-----
``data`` is one of:

* path to a two- or three-column whitespace/CSV file (``P/P₀, V_ads``;
  optional third column = ``V_des``)
* NumPy ndarray shape ``(N, 2)`` or ``(N, 3)``
* tuple ``(P_over_P0, V_ads)`` or ``(P_over_P0, V_ads, V_des)``
* pandas DataFrame
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from huitu._common import finalize
from huitu.style import role, use_journal


# Physical constants for the BET surface-area calculation.
_AVOGADRO = 6.02214076e23                # mol⁻¹
_N2_CROSS_SECTION_M2 = 0.162e-18         # m² per N₂ molecule (= 0.162 nm²)
_V_STP_CM3_PER_MOL = 22414.0             # cm³ STP per mol


def _coerce_bet(data) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    """Normalise the four supported input forms to (p_rel, v_ads, v_des|None)."""
    if isinstance(data, (str, Path)):
        df = pd.read_csv(data, sep=None, engine="python", comment="#",
                         header=None)
        df = df.apply(pd.to_numeric, errors="coerce").dropna(how="all")
        arr = df.to_numpy(dtype=float)
    elif isinstance(data, np.ndarray):
        arr = np.asarray(data, dtype=float)
    elif isinstance(data, pd.DataFrame):
        arr = data.to_numpy(dtype=float)
    elif isinstance(data, tuple):
        cols = [np.asarray(c, dtype=float) for c in data]
        arr = np.column_stack(cols)
    else:
        raise TypeError(
            f"plot_bet expects path/ndarray/DataFrame/tuple; "
            f"got {type(data).__name__}"
        )
    if arr.ndim != 2 or arr.shape[1] < 2:
        raise ValueError("BET data needs at least 2 columns: P/P0, V_ads")
    p_rel = arr[:, 0]
    v_ads = arr[:, 1]
    v_des = arr[:, 2] if arr.shape[1] >= 3 else None
    return p_rel, v_ads, v_des


def _bet_linear_fit(
    p_rel: np.ndarray,
    v_ads: np.ndarray,
    fit_range: tuple[float, float] = (0.05, 0.30),
) -> tuple[float, float, float, np.ndarray, np.ndarray]:
    """Return ``(slope, intercept, r_squared, x_fit, y_fit)`` of the BET line.

    The BET-linear variable ``y = 1 / [V (P0/P − 1)]`` is regressed against
    ``x = P/P0`` over the conventional ``0.05 ≤ P/P0 ≤ 0.30`` window.
    """
    p_lo, p_hi = fit_range
    mask = (p_rel >= p_lo) & (p_rel <= p_hi) & (v_ads > 0)
    if mask.sum() < 3:
        raise ValueError(
            f"BET fit requires ≥3 points in {fit_range}; got {int(mask.sum())}."
        )
    x = p_rel[mask]
    y = 1.0 / (v_ads[mask] * (1.0 / x - 1.0))   # = 1 / [V (P0/P − 1)]
    # Least-squares slope+intercept.
    slope, intercept = np.polyfit(x, y, 1)
    y_hat = slope * x + intercept
    ss_res = float(np.sum((y - y_hat) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return float(slope), float(intercept), float(r2), x, y


def _bet_surface_area(slope: float, intercept: float) -> tuple[float, float]:
    """Derived monolayer capacity Vₘ (cm³ STP g⁻¹) and BET surface area
    S_BET (m² g⁻¹) from the linear-fit slope+intercept."""
    if slope + intercept <= 0:
        # Degenerate (typically a sign of poor fit window).
        return float("nan"), float("nan")
    v_m = 1.0 / (slope + intercept)
    s_bet = v_m * _AVOGADRO * _N2_CROSS_SECTION_M2 / _V_STP_CM3_PER_MOL
    return v_m, s_bet


def plot_bet(
    data,
    journal: str = "default",
    save=None,
    fit_range: Tuple[float, float] = (0.05, 0.30),
    figsize: Tuple[float, float] | None = None,
    annotate: bool = True,
    show_desorption: bool = True,
    label: str | None = None,
    **kwargs,
):
    """Two-panel BET isotherm + linear-plot figure.

    Parameters
    ----------
    data
        ``(P/P0, V_ads)`` or ``(P/P0, V_ads, V_des)`` — see module docstring
        for accepted input forms.
    journal
        Journal preset name.
    save
        Optional path to write the figure as PNG (extension respected).
    fit_range
        BET-linear regression window in ``P/P0``. Default ``(0.05, 0.30)``
        matches IUPAC convention.
    figsize
        Override figsize. Defaults to ``(6.6, 2.8)`` — a wide 2-panel page.
    annotate
        Whether to print ``V_m``, ``S_BET``, and ``R²`` on the linear panel.
    show_desorption
        If a desorption branch is supplied, render it on the isotherm panel
        with an open marker. No effect if ``data`` has only two columns.
    label
        Optional dataset name (rendered in the isotherm-panel legend).

    Returns
    -------
    fig, (ax_iso, ax_lin), metrics : tuple
        ``metrics`` is a dict with keys ``V_m`` (cm³ STP g⁻¹), ``S_BET``
        (m² g⁻¹), ``C`` (BET constant), ``slope``, ``intercept``, ``R2``.
    """
    p_rel, v_ads, v_des = _coerce_bet(data)
    use_journal(journal)
    if figsize is None:
        figsize = (6.6, 2.8)
    fig, (ax_iso, ax_lin) = plt.subplots(
        1, 2, figsize=figsize, constrained_layout=True,
    )

    # ── Left: raw isotherm ──────────────────────────────────────────────────
    hero = role("hero")
    base = role("baseline")
    iso_label = label or "adsorption"
    ax_iso.plot(p_rel, v_ads, color=hero, lw=1.0, marker="o",
                markersize=3.5, label=iso_label, **kwargs)
    if show_desorption and v_des is not None:
        ax_iso.plot(p_rel, v_des, color=base, lw=1.0, marker="o",
                    markersize=3.5, mfc="white",
                    label=f"{iso_label} (desorption)")
    ax_iso.set_xlabel(r"$P/P_0$")
    ax_iso.set_ylabel(r"$V_{ads}$ (cm$^{3}$ STP g$^{-1}$)")
    ax_iso.set_xlim(0, 1)
    ax_iso.set_ylim(bottom=0)
    if v_des is not None or label:
        ax_iso.legend(loc="upper left", fontsize=7, frameon=False)
    ax_iso.set_title("Isotherm", fontsize=8, pad=4)

    # ── Right: BET linear ───────────────────────────────────────────────────
    slope, intercept, r2, x_fit, y_fit = _bet_linear_fit(p_rel, v_ads, fit_range)
    v_m, s_bet = _bet_surface_area(slope, intercept)
    c_const = 1.0 + slope / intercept if intercept != 0 else float("nan")

    # All in-window points (filled) and the regression line.
    ax_lin.plot(x_fit, y_fit, color=hero, lw=0, marker="o", markersize=4)
    x_line = np.linspace(x_fit.min(), x_fit.max(), 50)
    y_line = slope * x_line + intercept
    ax_lin.plot(x_line, y_line, color=role("neutral_dark"), lw=1.0, ls="--",
                label=f"y = {slope:.3g}x + {intercept:.3g}")
    ax_lin.set_xlabel(r"$P/P_0$")
    ax_lin.set_ylabel(r"$1 / [V_{ads}(P_0/P - 1)]$  (g cm$^{-3}$)")
    ax_lin.set_title("BET linear plot", fontsize=8, pad=4)
    ax_lin.legend(loc="upper left", fontsize=6.5, frameon=False)

    if annotate:
        if np.isfinite(s_bet):
            annotation = (
                f"$V_m$ = {v_m:.2f} cm$^{{3}}$ g$^{{-1}}$\n"
                f"$S_{{BET}}$ = {s_bet:.1f} m$^{{2}}$ g$^{{-1}}$\n"
                f"$C$ = {c_const:.1f}\n"
                f"$R^2$ = {r2:.4f}"
            )
        else:
            annotation = f"BET fit degenerate\n$R^2$ = {r2:.4f}"
        ax_lin.text(
            0.96, 0.05, annotation, transform=ax_lin.transAxes,
            ha="right", va="bottom", fontsize=7,
            color=role("neutral_dark"),
            bbox=dict(boxstyle="round,pad=0.35", fc="white",
                      ec=role("neutral_light"), lw=0.6, alpha=0.95),
        )

    metrics = {
        "V_m": v_m,
        "S_BET": s_bet,
        "C": c_const,
        "slope": slope,
        "intercept": intercept,
        "R2": r2,
    }

    finalize(fig, save)
    return fig, (ax_iso, ax_lin), metrics
