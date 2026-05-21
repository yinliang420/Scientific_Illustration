"""Electronic band structure plotting.

Accepts four input forms:

* A plain text file whose first column is the k-path coordinate and every
  remaining column is one band (energy in eV, Fermi-shifted so E_F = 0).
* A NumPy ndarray with the same column layout.
* A pandas DataFrame with the same column layout.
* ✨ v0.6: A pymatgen ``BSVasprun`` *or* ``BandStructureSymmLine`` object —
  high-symmetry k-points are auto-extracted from the band structure's
  ``branches`` so callers don't have to pass ``kpoints=`` manually.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence, Tuple

import numpy as np
import pandas as pd

from huitu._common import finalize, prepare_axes


# Sentinel returned by _try_pymatgen — None if pymatgen isn't available
# OR if the input isn't a pymatgen object. (band_array, kpoints) otherwise.
def _try_pymatgen(data) -> tuple[np.ndarray, list[tuple[str, float]]] | None:
    """If ``data`` is a pymatgen band-structure object, convert to
    ``(band_array, kpoints)``; else return ``None``.

    ``band_array`` has shape ``(n_kpoints, 1 + n_bands)`` matching the
    same layout as the text/DataFrame loaders. ``kpoints`` is the list
    of high-symmetry tick marks in ``[(label, kpath_value), ...]`` form.
    """
    # Quickly reject the common cases before paying the pymatgen import.
    if isinstance(data, (str, Path, np.ndarray, pd.DataFrame)):
        return None
    try:
        from pymatgen.electronic_structure.bandstructure import (  # noqa
            BandStructureSymmLine,
        )
        from pymatgen.io.vasp.outputs import BSVasprun  # noqa
    except ImportError:
        return None

    # BSVasprun → BandStructureSymmLine
    if isinstance(data, BSVasprun):
        bs = data.get_band_structure(line_mode=True)
    elif isinstance(data, BandStructureSymmLine):
        bs = data
    else:
        return None

    # Construct the kpath coordinate by accumulating the cartesian distance
    # between consecutive kpoints inside each segment, and inserting hard
    # discontinuities (so a discontinuous segment renders as a real break in
    # the visual).
    kpts = bs.kpoints
    distances = [0.0]
    branches = bs.branches  # list of {'start_index', 'end_index', 'name'}
    branch_starts = {b["start_index"] for b in branches}
    for i in range(1, len(kpts)):
        if i in branch_starts:
            # Branch boundary — keep the same x so the next branch begins
            # right against the previous one (Nature / pymatgen convention).
            distances.append(distances[-1])
        else:
            step = np.linalg.norm(np.array(kpts[i].cart_coords)
                                  - np.array(kpts[i - 1].cart_coords))
            distances.append(distances[-1] + float(step))
    kpath = np.asarray(distances, dtype=float)

    # bs.bands: dict {Spin.up: ndarray(n_bands, n_kpoints), Spin.down: ...}
    # We concatenate spin channels (if present) into the column list, so a
    # spin-polarised band structure shows up as the union of both channels.
    from pymatgen.electronic_structure.core import Spin

    band_cols: list[np.ndarray] = []
    for spin in (Spin.up, Spin.down):
        if spin in bs.bands:
            mat = bs.bands[spin] - bs.efermi  # Fermi-shift so E_F = 0
            band_cols.extend(mat[i, :] for i in range(mat.shape[0]))
    if not band_cols:
        return None

    band_array = np.column_stack([kpath] + band_cols)

    # High-symmetry kpoints — at every branch start (and the final endpoint).
    seen_positions: set[float] = set()
    kpoint_labels: list[tuple[str, float]] = []
    for b in branches:
        for idx_key in ("start_index", "end_index"):
            idx = b[idx_key]
            pos = float(kpath[idx])
            if pos in seen_positions:
                continue
            seen_positions.add(pos)
            # Branch names look like "\\Gamma-X" — split on dash so we
            # tick at the right endpoint with the appropriate label.
            name = b["name"]
            label = name.split("-")[0 if idx_key == "start_index" else -1]
            label = label.replace("\\", "")  # strip LaTeX backslash
            kpoint_labels.append((label, pos))

    return band_array, kpoint_labels


def _to_band_array(data):
    pmg = _try_pymatgen(data)
    if pmg is not None:
        return pmg  # (array, kpoints)
    if isinstance(data, pd.DataFrame):
        return data.to_numpy(dtype=float), None
    if isinstance(data, (str, Path)):
        df = pd.read_csv(data, sep=None, engine="python", comment="#")
        df = df.apply(pd.to_numeric, errors="coerce").dropna(how="all")
        return df.to_numpy(dtype=float), None
    if isinstance(data, np.ndarray):
        return data.astype(float), None
    raise TypeError(
        f"plot_band expects path/DataFrame/ndarray/pymatgen-BSVasprun; "
        f"got {type(data).__name__}"
    )


def plot_band(
    data,
    ax=None,
    journal: str = "default",
    save=None,
    kpoints: Sequence[Tuple[str, float]] | None = None,
    k_labels: Sequence[str] | None = None,
    k_ticks: Sequence[float] | None = None,
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
    k_labels, k_ticks
        Convenience pair: list of high-symmetry labels (e.g. ``["Γ", "X", "M",
        "Γ"]``) and matching tick positions along the k-path. When both are
        supplied, used in place of ``kpoints`` and a faint vertical line is
        drawn at each tick to mark the segment boundaries.
    """
    fig, ax = prepare_axes(ax, journal)
    arr, auto_kpoints = _to_band_array(data)
    if arr.shape[1] < 2:
        raise ValueError("band data needs >=2 columns (kpath + at least one band)")
    # If the caller did not pass `kpoints=` and a pymatgen object surfaced
    # high-symmetry points, use those automatically.
    if kpoints is None and auto_kpoints:
        kpoints = auto_kpoints

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

    if k_labels is not None and k_ticks is not None:
        ax.set_xticks(list(k_ticks))
        ax.set_xticklabels(list(k_labels))
        for t in k_ticks:
            ax.axvline(t, color="gray", lw=0.5, alpha=0.5)
    elif kpoints:
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
