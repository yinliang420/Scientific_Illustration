"""TGA/DSC thermal analysis plotting."""

from __future__ import annotations

from huitu._common import coerce_xy, finalize, prepare_axes


def plot_thermal(
    data,
    ax=None,
    journal: str = "default",
    save=None,
    mode: str = "tga",
    dsc_data=None,
    **kwargs,
):
    """Plot TGA, DSC, or both on shared temperature x-axis.

    Single-sample only; overlay multiple samples by calling twice on the same
    ``ax``. When ``mode='both'``, use ``ax.figure.axes[-1]`` to access the twin
    DSC axis.

    mode
        ``'tga'`` -> weight % on y.
        ``'dsc'`` -> heat flow on y.
        ``'both'`` -> TGA on left, DSC on twin right. ``data`` is TGA and
        ``dsc_data`` is the DSC 2-column input.
    """
    if mode not in ("tga", "dsc", "both"):
        raise ValueError("mode must be 'tga', 'dsc', or 'both'")

    fig, ax = prepare_axes(ax, journal)

    x, y = coerce_xy(data)

    if mode == "tga":
        color = kwargs.pop("color", "tab:blue")
        ax.plot(x, y, color=color, **kwargs)
        ax.set_ylabel("Weight (%)")
    elif mode == "dsc":
        color = kwargs.pop("color", "tab:red")
        ax.plot(x, y, color=color, **kwargs)
        ax.set_ylabel("Heat flow (mW mg$^{-1}$)")
    else:
        if dsc_data is None:
            raise ValueError("mode='both' requires dsc_data")
        color = kwargs.pop("color", "tab:blue")
        ax.plot(x, y, color=color, label="TGA", **kwargs)
        ax.set_ylabel("Weight (%)", color="tab:blue")
        ax.tick_params(axis="y", colors="tab:blue")

        dx, dy = coerce_xy(dsc_data)
        ax2 = ax.twinx()
        ax2.plot(dx, dy, color="tab:red", label="DSC")
        ax2.set_ylabel("Heat flow (mW mg$^{-1}$)", color="tab:red")
        ax2.tick_params(axis="y", colors="tab:red")

    ax.set_xlabel(r"Temperature ($^{\circ}$C)")

    finalize(fig, save)
    return fig, ax
