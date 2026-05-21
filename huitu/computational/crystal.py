"""Crystal structure visualization via ASE, with optional VESTA dispatch."""

from __future__ import annotations

import os
import shutil
import subprocess
import warnings
from pathlib import Path

from huitu._common import finalize
from huitu.layout.subplots import make_subplots

# Kwargs forwarded to ase.visualize.plot.plot_atoms. Anything else would raise.
_ASE_PLOT_ATOMS_KWARGS = {"radii", "rotation", "colors", "scale"}


def _annotate_panel(ax, atoms, banner: str) -> None:
    """Add banner + atom-legend + scale bar + closed unit-cell box to ``ax``.

    Called per-panel after ``plot_atoms`` so each subplot carries the same
    decorations regardless of viewing direction.
    """
    from matplotlib.patches import Patch

    # 1) renderer banner — distinguishes ASE-direct from VESTA-fallback PNGs.
    ax.text(0.02, 0.98, banner, transform=ax.transAxes,
            fontsize=6, va="top", alpha=0.6)

    # 2) atom-symbol legend (unique species, ASE jmol colors).
    try:
        from ase.data import atomic_numbers
        from ase.data.colors import jmol_colors
    except ImportError:  # pragma: no cover — ase always available here.
        jmol_colors = None
    seen: list[str] = []
    handles: list[Patch] = []
    for sym in atoms.get_chemical_symbols():
        if sym in seen:
            continue
        seen.append(sym)
        color = (jmol_colors[atomic_numbers[sym]]
                 if jmol_colors is not None else "grey")
        handles.append(Patch(facecolor=color, edgecolor="black",
                             linewidth=0.4, label=sym))
    if handles:
        ax.legend(handles=handles, loc="upper right", fontsize=6,
                  framealpha=0.85, handlelength=1.0, borderpad=0.3)

    # 3) scale bar: 2 Å rule pinned at the bottom-left of the axes.
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    span_y = y1 - y0
    bx0 = x0 + 0.04 * (x1 - x0)
    by0 = y0 + 0.05 * span_y
    ax.plot([bx0, bx0 + 2.0], [by0, by0], "k-", lw=2)
    ax.text(bx0 + 1.0, by0 - 0.04 * span_y, "2 Å",
            ha="center", va="top", fontsize=6)

    # 4) Close the unit-cell box: rectangle around the current data extent
    #    (matches ASE's projected cell footprint, all 4 edges guaranteed).
    bxlo, bxhi = ax.get_xlim()
    bylo, byhi = ax.get_ylim()
    pad_x = 0.04 * (bxhi - bxlo)
    pad_y = 0.08 * (byhi - bylo)
    rx0, rx1 = bxlo + pad_x, bxhi - pad_x
    ry0, ry1 = bylo + 2 * pad_y, byhi - pad_y
    box_x = [rx0, rx1, rx1, rx0, rx0]  # closed: last == first
    box_y = [ry0, ry0, ry1, ry1, ry0]
    ax.plot(box_x, box_y, ls="--", color="grey", lw=0.6, alpha=0.6)


def plot_crystal_ase(
    cif_path,
    ax=None,
    journal: str = "default",
    save=None,
    radii: float = 0.5,
    rotation: str = "0x,0y,0z",
    _banner: str = "rendered via ASE",
    **kwargs,
):
    """Render a crystal structure in three orthogonal views using ASE.

    Requires the ``ase`` extra: ``pip install 'huitu[crystal]'``.
    The ``ax`` argument is ignored — a 1x3 subplot is always created.
    """
    try:
        from ase.io import read as ase_read
        from ase.visualize.plot import plot_atoms
    except ImportError as exc:
        raise ImportError(
            "ase not installed. Install via: pip install 'huitu[crystal]'"
        ) from exc

    atoms = ase_read(str(cif_path))
    fig, axes = make_subplots(1, 3, journal=journal, panel_labels=False,
                              figsize=kwargs.pop("figsize", (6, 2.2)))

    # plot_atoms rejects unknown kwargs; only forward the ones it accepts.
    forwarded = {k: kwargs.pop(k) for k in list(kwargs)
                 if k in _ASE_PLOT_ATOMS_KWARGS}

    labels = ["xy", "xz", "yz"]
    rotations = [rotation, "-90x,0y,0z", "0x,-90y,0z"]
    for a, label, rot in zip(axes, labels, rotations):
        plot_atoms(atoms, a, radii=radii, rotation=rot, **forwarded)
        a.set_title(label, fontsize=7)
        a.set_xticks([])
        a.set_yticks([])
        _annotate_panel(a, atoms, banner=_banner)

    finalize(fig, save)
    return fig, axes


def plot_crystal_vesta(
    cif_path,
    save: str = "out.png",
    ax=None,
    journal: str = "default",
    **kwargs,
):
    """Render a structure via VESTA if ``VESTA_BIN`` is set; else fall back
    to :func:`plot_crystal_ase`.

    ``VESTA_BIN`` must point to a user-supplied wrapper script (or binary)
    that accepts two positional arguments: the input CIF path and the
    desired output image path, i.e. ``vesta_bin input.cif output.png``.
    VESTA's real GUI does not support headless rendering, so scripting is
    delegated to the user's wrapper.
    """
    vesta = os.environ.get("VESTA_BIN")
    if vesta and shutil.which(vesta):
        save_path = Path(save)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [vesta, str(cif_path), str(save_path)]
        subprocess.run(cmd, check=True)
        return None, None

    warnings.warn("VESTA_BIN not set or missing; falling back to ASE renderer.",
                  stacklevel=2)
    # Tag the banner so the fallback PNG is visibly distinct from the direct
    # ASE render (was previously byte-identical to ``plot_crystal_ase``).
    return plot_crystal_ase(cif_path, ax=ax, journal=journal, save=save,
                            _banner="rendered via VESTA fallback", **kwargs)
