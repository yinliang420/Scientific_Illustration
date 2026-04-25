"""huitu.pro — legacy namespace (kept for backward compatibility).

All former "Pro" features are now part of the standard huitu API and can be
imported directly from :mod:`huitu`:

    >>> import huitu
    >>> huitu.plot_ridgeline(...)
    >>> huitu.plot_operando_waterfall(...)

The ``huitu.pro.*`` names below continue to resolve to the same functions
so existing code does not need to change. The ``activate`` / ``is_active``
/ ``require_pro`` helpers are no-ops (see :mod:`huitu.pro._license`).
"""

from __future__ import annotations

from ._license import (
    ProLicenseError,
    activate,
    deactivate,
    is_active,
    require_pro,
)
from .palettes import list_pro_palettes, pro_palettes, register_pro_palettes

# Register the premium palette names so ``list_palettes`` reflects the full
# catalog on import.
register_pro_palettes()

from .ridgeline import plot_ridgeline
from .comparison import plot_dumbbell, plot_slope, plot_bump
from .advanced import (
    plot_parallel,
    plot_waffle,
    plot_streamgraph,
    plot_connected_scatter,
)
from .operando_pro import (
    plot_operando_waterfall,
    plot_operando_xrd_echem,
    plot_operando_3d_surface,
    plot_operando_diffmap,
    plot_operando_peak_evolution,
    plot_operando_contour,
)

__all__ = [
    # license (no-op, kept for back-compat)
    "ProLicenseError",
    "activate",
    "deactivate",
    "is_active",
    "require_pro",
    # palettes
    "list_pro_palettes",
    "pro_palettes",
    "register_pro_palettes",
    # plot functions
    "plot_ridgeline",
    "plot_dumbbell",
    "plot_slope",
    "plot_bump",
    "plot_parallel",
    "plot_waffle",
    "plot_streamgraph",
    "plot_connected_scatter",
    "plot_operando_waterfall",
    "plot_operando_xrd_echem",
    "plot_operando_3d_surface",
    "plot_operando_diffmap",
    "plot_operando_peak_evolution",
    "plot_operando_contour",
]
