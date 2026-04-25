"""Electronic band structure plotting.

Accepts a plain text file whose first column is the k-path coordinate and
every remaining column is one band (energy in eV, Fermi-shifted so
E_F = 0). TODO: add pymatgen BSVasprun / BandStructureSymmLine support (P2).
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence, Tuple

import numpy as np
import pandas as pd

from huitu._common import finalize, prepare_axes


def _to_band_array(data):
    if isinstance(data, pd.DataFrame):
        return data.to_numpy(dtype=float)
    if isinstance(data, (str, Path)):
        df = pd.read_csv(data, sep=None, engine="python", comment="#")
        df = df.apply(pd.to_numeric, errors="coerce").dropna(how="all")
        return df.to_numpy(dtype=float)
    if isinstance(data, np.ndarray):
        return data.astype(float)
    raise TypeError(f"plot_band expects path/DataFrame/ndarray; got {type(data).__name__}")


def plot_band(
    data,
    ax=None,
    journal: str = "default",
    save=None,
    kpoints: Sequence[Tuple[str, float]] | None = None,
    ylim: tuple | None = None,
    color: str = "#262626",
    linewidth: float = 0.6,
    **kwargs,
):
    """Plot band structure. First column is k-path, remaining are bands (eV).

    Tuple input is not accepted — bands are N-column by nature; pass
    ndarray/DataFrame/path instead.

    kpoints
        Sequence of ``(label, kpath_value)`` for high-symmetry tick marks.
        Vertical solid lines are drawn at each position.
    """
    fig, ax = prepare_axes(ax, journal)
    arr = _to_band_array(data)
    if arr.shape[1] < 2:
        raise ValueError("band data needs >=2 columns (kpath + at least one band)")

    color = kwargs.pop("color", color)
    lw = kwargs.pop("lw", linewidth)
    kpath = arr[:, 0]
    for i in range(1, arr.shape[1]):
        ax.plot(kpath, arr[:, i], color=color, lw=lw, **kwargs)

    ax.axhline(0.0, color="grey", lw=0.6, ls="--")
    ax.set_ylabel(r"E - E$_F$ (eV)")
    ax.set_xlim(kpath.min(), kpath.max())
    if ylim is not None:
        ax.set_ylim(*ylim)

    if kpoints:
        positions = [p for _, p in kpoints]
        labels = [l for l, _ in kpoints]
        for p in positions:
            ax.axvline(p, color="black", lw=0.5)
        ax.set_xticks(positions)
        ax.set_xticklabels(labels)
    else:
        ax.set_xlabel("k-path")

    finalize(fig, save)
    return fig, ax
