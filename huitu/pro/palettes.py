"""Premium palette registry for huitu.pro.

Three curated families:

* ``ggsci_*`` — journal-branded palettes ported from the R package
  `ggsci <https://nanx.me/ggsci/>`_ (NPG, AAAS, Lancet, NEJM, JAMA, BMJ, JCO,
  D3, Observable10, Frontiers, UChicago, Simpsons, Futurama, Tron, StarTrek).
* ``met_*`` — Metropolitan Museum-inspired palettes ported from
  `MetBrewer <https://github.com/BlakeRMills/MetBrewer>`_ (Hiroshige, Hokusai,
  Cassatt, Isfahan, VanGogh, Johnson, Derain, Egypt, Archambault, Juarez,
  Renoir, Monet, OKeeffe, Redon, Tam, Tara, Manet, Klimt, Kandinsky).
* ``ft_*`` — Financial Times editorial palettes distilled from FT's
  Visual Vocabulary and web style guide (qualitative + sequential + diverging).

All palettes are registered into ``huitu.style.PALETTES`` when
:func:`register_pro_palettes` runs (called automatically when ``huitu.pro``
is imported after activation).
"""

from __future__ import annotations

from typing import Dict, List

# ------------------------------------------------------------------
# ggsci — journal-branded categorical palettes (hex verified against
# https://github.com/nanxstats/ggsci/blob/master/R/palettes.R)
# ------------------------------------------------------------------
_GGSCI: Dict[str, List[str]] = {
    "ggsci-npg": [
        "#E64B35", "#4DBBD5", "#00A087", "#3C5488", "#F39B7F",
        "#8491B4", "#91D1C2", "#DC0000", "#7E6148", "#B09C85",
    ],
    "ggsci-aaas": [
        "#3B4992", "#EE0000", "#008B45", "#631879", "#008280",
        "#BB0021", "#5F559B", "#A20056", "#808180", "#1B1919",
    ],
    "ggsci-nejm": [
        "#BC3C29", "#0072B5", "#E18727", "#20854E", "#7876B1",
        "#6F99AD", "#FFDC91", "#EE4C97",
    ],
    "ggsci-lancet": [
        "#00468B", "#ED0000", "#42B540", "#0099B4", "#925E9F",
        "#FDAF91", "#AD002A", "#ADB6B6", "#1B1919",
    ],
    "ggsci-jama": [
        "#374E55", "#DF8F44", "#00A1D5", "#B24745",
        "#79AF97", "#6A6599", "#80796B",
    ],
    "ggsci-bmj": [
        "#2A6EBB", "#F0AB00", "#C50084", "#7D5CC6", "#E37222",
        "#69BE28", "#00B2A9", "#CD202C", "#747678",
    ],
    "ggsci-jco": [
        "#0073C2", "#EFC000", "#868686", "#CD534C", "#7AA6DC",
        "#003C67", "#8F7700", "#3B3B3B", "#A73030", "#4A6990",
    ],
    "ggsci-d3": [
        "#1F77B4", "#FF7F0E", "#2CA02C", "#D62728", "#9467BD",
        "#8C564B", "#E377C2", "#7F7F7F", "#BCBD22", "#17BECF",
    ],
    "ggsci-observable10": [
        "#4269D0", "#EFB118", "#FF725C", "#6CC5B0", "#3CA951",
        "#FF8AB7", "#A463F2", "#97BBF5", "#9C6B4E", "#9498A0",
    ],
    "ggsci-frontiers": [
        "#D51317", "#F39200", "#EFD500", "#95C11F", "#007B3D",
        "#31B7BC", "#0094CD", "#164194", "#6F286A", "#706F6F",
    ],
    "ggsci-uchicago": [
        "#800000", "#767676", "#FFA319", "#8A9045", "#155F83",
        "#C16622", "#8F3931", "#58593F", "#350E20",
    ],
    "ggsci-simpsons": [
        "#FED439", "#709AE1", "#8A9197", "#D2AF81", "#FD7446",
        "#D5E4A2", "#197EC0", "#F05C3B", "#46732E", "#71D0F5",
        "#370335", "#075149", "#C80813", "#91331F", "#1A9993", "#FD8CC1",
    ],
    "ggsci-futurama": [
        "#FF6F00", "#C71000", "#008EA0", "#8A4198", "#5A9599",
        "#FF6348", "#84D7E1", "#FF95A8", "#3D3B25", "#ADE2D0",
        "#1A5354", "#3F4041",
    ],
    "ggsci-tron": [
        "#FF410D", "#6EE2FF", "#F7C530", "#95CC5E",
        "#D0DFE6", "#F79D1E", "#748AA6",
    ],
    "ggsci-startrek": [
        "#CC0C00", "#5C88DA", "#84BD00", "#FFCD00",
        "#7C878E", "#00B5E2", "#00AF66",
    ],
}

# ------------------------------------------------------------------
# MetBrewer — art-inspired palettes (hex verified against
# https://github.com/BlakeRMills/MetBrewer/blob/main/Python/met_brewer/palettes.py)
# ------------------------------------------------------------------
_METBREWER: Dict[str, List[str]] = {
    "met-hiroshige": [
        "#E76254", "#EF8A47", "#F7AA58", "#FFD06F", "#FFE6B7",
        "#AADCE0", "#72BCD5", "#528FAD", "#376795", "#1E466E",
    ],
    "met-hokusai1": [
        "#6D2F20", "#B75347", "#DF7E66", "#E09351",
        "#EDC775", "#94B594", "#224B5E",
    ],
    "met-hokusai3": [
        "#D8D97A", "#95C36E", "#74C8C3", "#5A97C1", "#295384", "#0A2E57",
    ],
    "met-cassatt2": [
        "#2D223C", "#574571", "#90719F", "#B695BC", "#DEC5DA",
        "#C1D1AA", "#7FA074", "#466C4B", "#2C4B27", "#0E2810",
    ],
    "met-isfahan1": [
        "#4E3910", "#845D29", "#D8C29D", "#4FB6CA",
        "#178F92", "#175F5D", "#1D1F54",
    ],
    "met-vangogh3": [
        "#E7E5CC", "#C2D6A4", "#9CC184", "#669D62",
        "#447243", "#1F5B25", "#1E3D14", "#192813",
    ],
    "met-johnson": ["#A00E00", "#D04E00", "#F6C200", "#0086A8", "#132B69"],
    "met-derain": [
        "#EFC86E", "#97C684", "#6F9969", "#AAB5D5",
        "#808FE1", "#5C66A8", "#454A74",
    ],
    "met-egypt": ["#DD5129", "#0F7BA2", "#43B284", "#FAB255"],
    "met-archambault": [
        "#88A0DC", "#381A61", "#7C4B73", "#ED968C",
        "#AB3329", "#E78429", "#F9D14A",
    ],
    "met-juarez": ["#A82203", "#208CC0", "#F1AF3A", "#CF5E4E", "#637B31", "#003967"],
    "met-renoir": [
        "#17154F", "#2F357C", "#6C5D9E", "#9D9CD5", "#B0799A", "#F6B3B0",
        "#E48171", "#BF3729", "#E69B00", "#F5BB50", "#ADA43B", "#355828",
    ],
    "met-monet": [
        "#4E6D58", "#749E89", "#ABCCBE", "#E3CACF", "#C399A2",
        "#9F6E71", "#41507B", "#7D87B2", "#C2CAE3",
    ],
    "met-okeeffe2": [
        "#FBE3C2", "#F2C88F", "#ECB27D", "#E69C6B",
        "#D37750", "#B9563F", "#92351E",
    ],
    "met-redon": [
        "#5B859E", "#1E395F", "#75884B", "#1E5A46", "#DF8D71", "#AF4F2F",
        "#D48F90", "#732F30", "#AB84A5", "#59385C", "#D8B847", "#B38711",
    ],
    "met-tam": [
        "#FFD353", "#FFB242", "#EF8737", "#DE4F33",
        "#BB292C", "#9F2D55", "#62205F", "#341648",
    ],
    "met-tara": ["#EAB1C6", "#D35E17", "#E18A1F", "#E9B109", "#829D44"],
    "met-manet": [
        "#3B2319", "#80521C", "#D29C44", "#EBC174", "#EDE2CC", "#7EC5F4",
        "#4585B7", "#225E92", "#183571", "#43429B", "#5E65BE",
    ],
    "met-klimt": ["#DF9ED4", "#C93F55", "#EACC62", "#469D76", "#3C4B99", "#924099"],
    "met-kandinsky": ["#3B7C70", "#CE9642", "#898E9F", "#3B3A3E"],
}

# ------------------------------------------------------------------
# Financial Times editorial palettes (distilled from FT Visual Vocabulary
# and FT web style guide).
# ------------------------------------------------------------------
_FT: Dict[str, List[str]] = {
    # Categorical — FT brand + accessible qualitative set
    "ft-categorical": [
        "#0F5499", "#990F3D", "#0D7680", "#CC0000",
        "#593380", "#FF8833", "#00897B", "#555555",
    ],
    # Sequential — FT single-hue (dark navy -> pale)
    "ft-sequential": [
        "#0A1F44", "#173264", "#1F4287", "#2A5CAA",
        "#4E84C4", "#7FA7D8", "#B0C7E6", "#DCE6F2",
    ],
    # Diverging — oxblood <-> FT teal, balanced through off-white
    "ft-diverging": [
        "#8A0F25", "#B84D5F", "#D9899A", "#F1D5D8",
        "#FFF1E5", "#D1E4E3", "#7FB7B2", "#2E8C8C", "#0D5E5E",
    ],
    # "Night" — dark-mode optimized set, good on dark backgrounds
    "ft-night": [
        "#FF8A8A", "#85D4FF", "#FFD580", "#A0E7A0",
        "#C6A0FF", "#FFC2E8", "#E8E8E8",
    ],
}

# Continuous/gradient-safe palettes (for use with get_cmap in pro plots).
_PRO_GRADIENT_NAMES: tuple = (
    "met-hiroshige", "met-hokusai3", "met-isfahan1", "met-vangogh3",
    "met-cassatt2", "met-okeeffe2", "met-tam",
    "ft-sequential", "ft-diverging",
)


def pro_palettes() -> Dict[str, List[str]]:
    """Return a fresh dict of all pro palette name -> hex list."""
    out: Dict[str, List[str]] = {}
    out.update(_GGSCI)
    out.update(_METBREWER)
    out.update(_FT)
    return out


def register_pro_palettes() -> None:
    """Merge pro palettes into :data:`huitu.style.PALETTES` and the
    gradient-allowed set. Safe to call multiple times."""
    from huitu import style as _style

    pal = pro_palettes()
    for name, colors in pal.items():
        _style.PALETTES[name] = list(colors)
    # allow gradient use for select palettes (style._GRADIENT_PALETTES is a set)
    if hasattr(_style, "_GRADIENT_PALETTES"):
        _style._GRADIENT_PALETTES.update(_PRO_GRADIENT_NAMES)  # type: ignore[attr-defined]


def list_pro_palettes() -> List[str]:
    """Return the sorted list of all premium palette names."""
    return sorted(pro_palettes().keys())
