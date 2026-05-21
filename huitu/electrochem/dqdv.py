"""Differential capacity (dQ/dV) — battery characterisation companion to GCD.

Given a galvanostatic charge/discharge trace (voltage vs capacity), the
derivative ``dQ/dV`` versus ``V`` exposes redox plateaus as peaks. Each peak
corresponds to a phase-transition or intercalation event; peak shift /
broadening between cycles tracks ageing.

Input
-----
``data`` is one of:

* path to a 2-column file (``V, Q``) or 3-column file (``V, Q_charge,
  Q_discharge``)
* NumPy ndarray with the same column layout
* tuple ``(V, Q)`` or ``(V, Q_charge, Q_discharge)``
* pandas DataFrame
* list of any of the above — overlays multiple cycles on the same axes

Smoothing
---------
``smooth="savgol"`` (default) applies a Savitzky–Golay filter to ``V`` and
``Q`` before differentiation; ``smooth=None`` returns the raw derivative
(noisy on real data — useful for synthetic cycles or pre-smoothed input).
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from huitu._common import finalize, place_legend, prepare_axes
from huitu.style import role


def _coerce_dqdv(data) -> tuple[np.ndarray, np.ndarray] | list[tuple[np.ndarray, np.ndarray]]:
    """Normalise to ``(V, Q)`` or a list of ``(V, Q)`` cycles.

    A 3-column input is split into ``(V, Q_charge)`` and ``(V, Q_discharge)``.
    """
    if isinstance(data, list):
        out: list[tuple[np.ndarray, np.ndarray]] = []
        for d in data:
            out.append(_coerce_dqdv(d))  # type: ignore[arg-type]
        return out

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
        arr = np.column_stack([np.asarray(c, dtype=float) for c in data])
    else:
        raise TypeError(
            f"plot_dqdv expects path/ndarray/DataFrame/tuple/list; "
            f"got {type(data).__name__}"
        )
    if arr.ndim != 2 or arr.shape[1] < 2:
        raise ValueError("dQ/dV data needs ≥2 columns: V, Q")
    return arr[:, 0], arr[:, 1]


def _savgol(y: np.ndarray, window: int, polyorder: int) -> np.ndarray:
    """Light wrapper that gracefully handles short arrays."""
    try:
        from scipy.signal import savgol_filter
    except ImportError as e:
        raise ImportError(
            "smooth='savgol' needs scipy. Install scipy or pass smooth=None."
        ) from e
    # Window must be odd, smaller than len(y), and > polyorder.
    n = len(y)
    w = min(window, n if n % 2 == 1 else n - 1)
    if w <= polyorder:
        return y.copy()
    return savgol_filter(y, w, polyorder)


def _compute_dqdv(
    v: np.ndarray,
    q: np.ndarray,
    smooth: str | None,
    window: int,
    polyorder: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(V_mid, dQ/dV)`` evaluated on the midpoints of ``V``."""
    if smooth == "savgol":
        v_s = _savgol(v, window, polyorder)
        q_s = _savgol(q, window, polyorder)
    elif smooth is None or smooth is False:
        v_s, q_s = v, q
    else:
        raise ValueError(f"smooth must be 'savgol' or None; got {smooth!r}")

    # Numerical derivative on midpoints — robust to non-monotonic V because
    # we divide elementwise. Edges drop one sample (standard).
    dv = np.diff(v_s)
    dq = np.diff(q_s)
    # Guard against division by zero (V plateau): mark as NaN, then forward-fill
    # by taking the local neighbour value.
    with np.errstate(divide="ignore", invalid="ignore"):
        dqdv = np.where(dv != 0, dq / dv, np.nan)
    # Replace NaN by linear interpolation across them (preserves shape).
    nan_mask = np.isnan(dqdv)
    if nan_mask.any() and not nan_mask.all():
        idx = np.arange(len(dqdv))
        dqdv[nan_mask] = np.interp(idx[nan_mask], idx[~nan_mask], dqdv[~nan_mask])
    v_mid = 0.5 * (v_s[:-1] + v_s[1:])
    return v_mid, dqdv


def plot_dqdv(
    data,
    ax=None,
    journal: str = "default",
    save=None,
    labels: Iterable[str] | None = None,
    smooth: str | None = "savgol",
    window: int = 11,
    polyorder: int = 3,
    xlabel: str = "Potential (V vs. ref.)",
    ylabel: str = r"dQ/dV (mAh g$^{-1}$ V$^{-1}$)",
    show_zero: bool = True,
    **kwargs,
):
    """Differential-capacity plot — dQ/dV vs V — with optional smoothing.

    Parameters
    ----------
    data
        ``(V, Q)``, file path, ndarray, DataFrame, or list of these for
        multi-cycle overlay. See module docstring.
    journal
        Journal preset name.
    save
        Optional output path (PNG / PDF / SVG).
    labels
        Per-cycle labels. Used when ``data`` is a list.
    smooth
        ``"savgol"`` (default) applies Savitzky–Golay before differentiating.
        ``None`` returns the raw derivative.
    window
        Savitzky–Golay window length (odd). Default 11.
    polyorder
        Savitzky–Golay polynomial order. Default 3.
    show_zero
        Draw a thin grey ``y=0`` reference line.

    Returns
    -------
    fig, ax : tuple
    """
    fig, ax = prepare_axes(ax, journal)

    # Normalise to a list of cycles.
    coerced = _coerce_dqdv(data)
    cycles: list[tuple[np.ndarray, np.ndarray]]
    if isinstance(coerced, tuple):
        cycles = [coerced]
    else:
        cycles = coerced

    label_iter = list(labels) if labels is not None else []
    # Use the semantic palette so cycle 1 = hero, cycle 2 = baseline, etc.
    role_cycle = [
        role("hero"), role("baseline"), role("positive"),
        role("accent_teal"), role("accent_violet"), role("neutral_dark"),
    ]

    traces: list[tuple[np.ndarray, np.ndarray, str]] = []
    for i, (v, q) in enumerate(cycles):
        v_mid, dqdv = _compute_dqdv(v, q, smooth, window, polyorder)
        color = role_cycle[i % len(role_cycle)]
        label = label_iter[i] if i < len(label_iter) else None
        ax.plot(v_mid, dqdv, color=color, lw=1.1, label=label, **kwargs)
        traces.append((v_mid, dqdv, color))

    if show_zero:
        ax.axhline(0, color=role("neutral"), lw=0.5, ls="--", alpha=0.7)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if label_iter:
        # Route through place_legend so the dQ/dV legend never sits on top of
        # the tallest peak — same automatic inline / pad-top behaviour as the
        # rest of huitu.
        place_legend(ax, label_iter, traces=traces, legend="auto",
                     pad_top=0.18)

    finalize(fig, save)
    return fig, ax
