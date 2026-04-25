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


def plot_crystal_ase(
    cif_path,
    ax=None,
    journal: str = "default",
    save=None,
    radii: float = 0.5,
    rotation: str = "0x,0y,0z",
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
    return plot_crystal_ase(cif_path, ax=ax, journal=journal, save=save, **kwargs)
