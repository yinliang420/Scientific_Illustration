"""huitu: materials-science plotting helpers."""

from importlib.metadata import PackageNotFoundError, version

from huitu.style import PALETTES, get_cmap, list_palettes, register_cjk, use_journal, use_palette
from huitu._common import panel_tag, supertitle
from huitu.readers.txt_csv import read_xy
from huitu.characterization.xrd import plot_xrd
from huitu.characterization.xps import plot_xps
from huitu.characterization.raman import plot_raman
from huitu.characterization.ftir import plot_ftir
from huitu.characterization.uvvis import plot_uvvis
from huitu.characterization.pl import plot_pl
from huitu.characterization.thermal import plot_thermal
from huitu.characterization.rietveld import plot_rietveld
from huitu.characterization.operando import plot_operando
from huitu.electrochem.cv import plot_cv
from huitu.electrochem.gcd import plot_gcd
from huitu.electrochem.cycle import plot_cycle
from huitu.electrochem.eis import plot_eis
from huitu.electrochem.bode import plot_bode
from huitu.electrochem.tafel import plot_tafel
from huitu.computational.band import plot_band
from huitu.computational.dos import plot_dos
from huitu.computational.cohp import plot_cohp
from huitu.computational.pourbaix import plot_pourbaix
from huitu.computational.phase_diagram import plot_phase_diagram
from huitu.computational.crystal import plot_crystal_ase, plot_crystal_vesta
from huitu.general.bar import plot_bar
from huitu.general.scatter import plot_scatter
from huitu.general.line import plot_line
from huitu.general.heatmap import plot_heatmap
from huitu.general.box_violin import plot_box_violin
from huitu.general.radar import plot_radar
from huitu.general.density import plot_density
from huitu.general.shap_like import plot_shap
from huitu.layout.subplots import make_subplots
from huitu.layout.inset import add_inset
from huitu.layout.shared_axes import share_axes

# Formerly-premium plot helpers — now part of the standard API. The
# ``huitu.pro`` namespace is still importable as a backward-compatible
# alias; see ``huitu/pro/__init__.py``.
from huitu import pro  # noqa: F401
from huitu.pro import (
    plot_ridgeline,
    plot_dumbbell,
    plot_slope,
    plot_bump,
    plot_parallel,
    plot_waffle,
    plot_streamgraph,
    plot_connected_scatter,
    plot_operando_waterfall,
    plot_operando_xrd_echem,
    plot_operando_3d_surface,
    plot_operando_diffmap,
    plot_operando_peak_evolution,
    plot_operando_contour,
)

try:
    __version__ = version("huitu")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__ = [
    "use_journal",
    "use_palette",
    "list_palettes",
    "register_cjk",
    "get_cmap",
    "PALETTES",
    "read_xy",
    "plot_xrd",
    "plot_xps",
    "plot_raman",
    "plot_ftir",
    "plot_uvvis",
    "plot_pl",
    "plot_thermal",
    "plot_rietveld",
    "plot_operando",
    "plot_cv",
    "plot_gcd",
    "plot_cycle",
    "plot_eis",
    "plot_bode",
    "plot_tafel",
    "plot_band",
    "plot_dos",
    "plot_cohp",
    "plot_pourbaix",
    "plot_phase_diagram",
    "plot_crystal_ase",
    "plot_crystal_vesta",
    "plot_bar",
    "plot_scatter",
    "plot_line",
    "plot_heatmap",
    "plot_box_violin",
    "plot_radar",
    "plot_density",
    "plot_shap",
    "make_subplots",
    "add_inset",
    "share_axes",
    "panel_tag",
    "supertitle",
    # Advanced/statistical helpers (formerly huitu.pro.*)
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
