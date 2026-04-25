"""Post-hoc axis-sharing helper."""

from __future__ import annotations

import numpy as np


def share_axes(axes, which: str = "x"):
    """Link limits on an existing axes grid and hide inner tick labels.

    Parameters
    ----------
    axes
        Array of axes (as returned by ``make_subplots``) or any iterable.
    which
        ``'x'``, ``'y'``, or ``'both'``.
    """
    if which not in ("x", "y", "both"):
        raise ValueError("which must be 'x', 'y', or 'both'")

    flat = np.asarray(axes).ravel() if hasattr(axes, "ravel") else list(axes)
    flat = list(flat)
    if not flat:
        return axes

    ref = flat[0]
    if which in ("x", "both"):
        xlims = [a.get_xlim() for a in flat]
        lo = min(l[0] for l in xlims)
        hi = max(l[1] for l in xlims)
        for a in flat:
            a.set_xlim(lo, hi)
            if a is ref:
                continue
            a.sharex(ref)
    if which in ("y", "both"):
        ylims = [a.get_ylim() for a in flat]
        lo = min(l[0] for l in ylims)
        hi = max(l[1] for l in ylims)
        for a in flat:
            a.set_ylim(lo, hi)
            if a is ref:
                continue
            a.sharey(ref)

    arr = np.asarray(axes)
    if arr.ndim == 2:
        nrows, ncols = arr.shape
        for i in range(nrows):
            for j in range(ncols):
                a = arr[i, j]
                if which in ("x", "both") and i < nrows - 1:
                    a.tick_params(labelbottom=False)
                if which in ("y", "both") and j > 0:
                    a.tick_params(labelleft=False)
    return axes
