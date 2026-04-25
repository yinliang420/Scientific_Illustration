"""Bode plot for EIS (|Z| and phase vs log frequency)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from huitu._common import finalize, prepare_axes


def _to_three_cols(data):
    if isinstance(data, pd.DataFrame):
        arr = data.to_numpy(dtype=float)
    elif isinstance(data, (str, Path)):
        df = pd.read_csv(data, sep=None, engine="python", comment="#")
        df = df.apply(pd.to_numeric, errors="coerce").dropna(how="all")
        arr = df.to_numpy(dtype=float)
    elif isinstance(data, np.ndarray):
        arr = data.astype(float)
    elif isinstance(data, tuple) and len(data) == 3:
        arr = np.column_stack([np.asarray(c, dtype=float) for c in data])
    else:
        raise TypeError(f"plot_bode expects 3-column data; got {type(data).__name__}")
    if arr.ndim != 2 or arr.shape[1] < 3:
        raise ValueError("plot_bode expects at least 3 columns: freq, |Z|, phase (or freq, Zr, Zi)")
    return arr


def plot_bode(
    data,
    ax=None,
    journal: str = "default",
    save=None,
    input_format: str = "magphase",
    **kwargs,
):
    """Bode plot: |Z| (log) on left y, phase (deg) on right y, log frequency x.

    ``**kwargs`` are forwarded to the |Z| curve; pass ``phase_kwargs=`` dict
    for phase-specific styling.

    input_format
        ``'magphase'`` (default): columns are ``(freq, |Z|, phase_deg)``.
        ``'complex'``: columns are ``(freq, Z', Z'')``; |Z| and phase are
        derived.
    """
    phase_kwargs = kwargs.pop("phase_kwargs", {})

    fig, ax = prepare_axes(ax, journal)
    arr = _to_three_cols(data)

    freq = arr[:, 0]
    if input_format == "magphase":
        mag = arr[:, 1]
        phase = arr[:, 2]
    elif input_format == "complex":
        zr, zi = arr[:, 1], arr[:, 2]
        mag = np.hypot(zr, zi)
        phase = np.degrees(np.arctan2(zi, zr))
    else:
        raise ValueError("input_format must be 'magphase' or 'complex'")

    mag_style = dict(marker="o", linestyle="-", color="tab:blue", markersize=3)
    mag_style.update(kwargs)
    ax.plot(freq, mag, label="|Z|", **mag_style)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel(r"|Z| ($\Omega$)", color="tab:blue")
    ax.tick_params(axis="y", colors="tab:blue")

    ax2 = ax.twinx()
    phase_style = dict(marker="s", linestyle="-", color="tab:red", markersize=3)
    phase_style.update(phase_kwargs)
    ax2.plot(freq, phase, label="phase", **phase_style)
    ax2.set_ylabel("Phase (deg)", color="tab:red")
    ax2.tick_params(axis="y", colors="tab:red")

    finalize(fig, save)
    return fig, ax
