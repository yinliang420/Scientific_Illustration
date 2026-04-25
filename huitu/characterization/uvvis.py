"""UV-Vis absorbance and Tauc plot."""

from __future__ import annotations

from typing import Iterable

import numpy as np

from huitu._common import coerce_xy, finalize, is_multi_input, prepare_axes

# Planck * c in eV*nm: hc = 1239.841984 eV*nm.
_HC_EV_NM = 1239.841984


def plot_uvvis(
    data,
    ax=None,
    journal: str = "default",
    save=None,
    labels: Iterable[str] | None = None,
    tauc: bool | str = False,
    xlim: tuple | None = None,
    smart_xlim: bool = True,
    **kwargs,
):
    """Plot UV-Vis absorbance, or a Tauc plot when ``tauc`` is given.

    tauc
        ``False`` (default) for raw wavelength-vs-absorbance.
        ``'direct'`` plots (alpha*h*nu)^2 vs photon energy (eV).
        ``'indirect'`` plots (alpha*h*nu)^0.5 vs photon energy (eV).
        ``tauc=True`` is an alias for ``'direct'``.
        The input y column is used as alpha proxy (typical for thin-film
        absorbance data where alpha proportional to A).
    """
    fig, ax = prepare_axes(ax, journal)

    is_multi = is_multi_input(data)
    items = list(data) if is_multi else [data]
    labels = list(labels) if labels else [None] * len(items)
    if len(labels) < len(items):
        labels = labels + [None] * (len(items) - len(labels))

    if tauc:
        if tauc not in ("direct", "indirect", True):
            raise ValueError("tauc must be False, 'direct', or 'indirect'")
        exponent = 2.0 if tauc in ("direct", True) else 0.5

    all_x = []
    for i, item in enumerate(items):
        wl, a = coerce_xy(item)
        if tauc:
            hv = _HC_EV_NM / wl
            y = (a * hv) ** exponent
            ax.plot(hv, y, label=labels[i], **kwargs)
            all_x.append(hv)
        else:
            ax.plot(wl, a, label=labels[i], **kwargs)
            all_x.append(wl)

    if tauc:
        ax.set_xlabel("Photon energy (eV)")
        if exponent == 2.0:
            ax.set_ylabel(r"($\alpha h\nu$)$^{2}$ (a.u.)")
        else:
            ax.set_ylabel(r"($\alpha h\nu$)$^{1/2}$ (a.u.)")
    else:
        ax.set_xlabel("Wavelength (nm)")
        ax.set_ylabel("Absorbance (a.u.)")

    if xlim is not None:
        ax.set_xlim(*xlim)
    elif smart_xlim and all_x:
        cat_x = np.concatenate(all_x)
        if cat_x.size:
            p1, p99 = np.percentile(cat_x, [1, 99])
            dmin = float(np.min(cat_x))
            dmax = float(np.max(cat_x))
            # Use much smaller pad for tauc (eV scale), 50 for wavelength.
            pad = 0.2 if tauc else 50.0
            lo = max(dmin, float(p1) - pad)
            hi = min(dmax, float(p99) + pad)
            if hi > lo:
                ax.set_xlim(lo, hi)

    if any(l for l in labels):
        ax.legend(loc="best")

    finalize(fig, save)
    return fig, ax
