"""Journal style presets.

``use_journal(name)`` mutates matplotlib's rcParams. It tries to apply a
scienceplots style stack and falls back to a plain-matplotlib preset when
scienceplots or its LaTeX dependency is unavailable.

Note
----
``use_journal`` calls ``matplotlib.rcdefaults()`` before applying the preset,
so any user-set rcParams for the current session are discarded. Re-apply your
custom rcParams after calling ``use_journal`` if needed.

Trust roots (Round 3)
---------------------
* ``_PALETTES_BACKING`` (a :class:`_DefensivePaletteDict`) is the *documented*
  trust root for the ``PALETTES`` registry. It is intentionally writable so
  that :func:`huitu.pro.register_pro_palettes` can extend it at import time.
  Inner values are stored as ``tuple`` and ``__getitem__`` hands out fresh
  ``list`` copies, so even direct mutation of the backing cannot poison a
  subscript read through ``huitu.PALETTES``.
* ``SEMANTIC_PALETTE`` is the public role -> hex view. It is sealed via a
  tuple-backed :class:`_FrozenStrMap` so neither ``__setitem__`` nor
  ``gc.get_referents(...)`` can surface a mutable inner dict.
"""

from __future__ import annotations

from collections.abc import Mapping as _AbcMapping
from types import MappingProxyType
from typing import Mapping

from cycler import cycler
import matplotlib as mpl
import matplotlib.pyplot as plt


# Active preset cache: lets ``prepare_axes`` skip re-applying ``use_journal``
# when the caller already picked one. Without this guard, every ``plot_*``
# call resets rcParams via ``rcdefaults()``, which silently clobbers any
# user-set rc overrides (e.g. ``mpl.rcParams['font.family']='Times'``) that
# were applied *after* ``use_journal``. Read directly through the
# ``huitu.style._ACTIVE_PRESET`` attribute so callers see the latest value.
_ACTIVE_PRESET: str | None = None

# Patch sentinel — set once :func:`use_journal` installs the SVG-savefig
# post-processing hook that rewrites mathtext fallback (STIX) font-family
# attributes to match the active body font. The hook makes the mathtext
# label `r"2$\theta$ ($^\circ$)"` render with a single ``font-family`` in
# the saved SVG even when ``\circ`` is missing from Helvetica and matplotlib
# silently falls back to STIXGeneral. Without this, the user sees a
# Helvetica '2θ' next to a serif '∘' — the "好奇怪整个字体形式" complaint.
_SVG_FONT_UNIFY_INSTALLED = False


def _install_svg_font_unify_hook() -> None:
    """Monkey-patch ``Figure.savefig`` to unify mathtext STIX fallback fonts
    with the body family in SVG output.

    Runs once. Idempotent (guarded by ``_SVG_FONT_UNIFY_INSTALLED``). Only
    rewrites files when:
      * ``svg.fonttype == "none"`` (text stays as <text>/<tspan>)
      * Output path ends with ``.svg``
      * Saved file contains a ``'STIXGeneral'`` etc. fragment

    Why monkey-patch rather than a wrapper utility: the polish tests (and a
    fair amount of user code) call ``fig.savefig`` directly, bypassing
    ``huitu._common.finalize``. A pre-save hook is the only intercept point
    that catches both code paths.
    """
    global _SVG_FONT_UNIFY_INSTALLED
    if _SVG_FONT_UNIFY_INSTALLED:
        return
    import os
    import re

    from matplotlib.figure import Figure

    _orig_savefig = Figure.savefig

    def _patched_savefig(self, fname, *args, **kwargs):
        result = _orig_savefig(self, fname, *args, **kwargs)
        try:
            if not isinstance(fname, (str, os.PathLike)):
                return result
            path = os.fspath(fname)
            if not path.lower().endswith(".svg"):
                return result
            if str(mpl.rcParams.get("svg.fonttype", "")).lower() != "none":
                return result
            with open(path, "rb") as f:
                head = f.read(2048)
            if b"STIX" not in head:
                with open(path, "rb") as f:
                    if b"STIX" not in f.read():
                        return result
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if "STIX" not in content:
                return result
            stack = mpl.rcParams.get("font.family", [])
            if isinstance(stack, str):
                stack = [stack]
            if not stack:
                return result
            body_family = ", ".join(repr(f) for f in stack)
            new_content = re.sub(
                r"'STIX[A-Za-z]+'", body_family, content
            )
            if new_content != content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
        except Exception:
            # Never break savefig because of the hook.
            pass
        return result

    Figure.savefig = _patched_savefig
    _SVG_FONT_UNIFY_INSTALLED = True


class _DefensivePaletteDict(dict):
    """Backing storage that hands out **defensive list copies** of inner values.

    Wrapped in :class:`types.MappingProxyType` to form the public ``PALETTES``
    registry, so users see a ``mappingproxy`` (preserving the documented
    "frozen at top level + cannot pickle" contract) AND ``PALETTES['nord']``
    returns a fresh ``list`` on every access. That means
    ``huitu.PALETTES['nord'][0] = '#000'`` mutates a throwaway list rather
    than the live registry, while ``dict(huitu.PALETTES)`` still hands out
    mutable lists for downstream consumption (pickle / deepcopy / json round-
    trip).
    """

    def __getitem__(self, key):
        return list(super().__getitem__(key))


class _FrozenStrMap(_AbcMapping):
    """Tuple-backed read-only str -> str map.

    Round 3 found that ``MappingProxyType(some_dict)`` is not a complete
    freeze: the wrapped dict is still reachable via ``gc.get_referents``,
    where ``inner = [o for o in gc.get_referents(proxy) if isinstance(o, dict)]``
    surfaces the mutable backing dict in one line. Anyone who can run that
    snippet can corrupt ``role()`` lookups for the rest of the session.

    This class closes that channel by storing the snapshot in a single
    immutable ``tuple`` slot. ``gc.get_referents`` on a ``_FrozenStrMap``
    instance returns only the tuple and the class object, never a writable
    dict. ``__setitem__`` is not defined (raises ``TypeError`` like
    ``mappingproxy``), and ``__reduce_ex__`` raises ``TypeError`` to match
    ``MappingProxyType``'s "frozen at top level + cannot pickle" contract.

    Subclasses :class:`collections.abc.Mapping` so user code that wants a
    type-name-agnostic immutability check can write::

        isinstance(huitu.SEMANTIC_PALETTE, collections.abc.Mapping)  # True

    instead of pinning on the exact class name.
    """

    __slots__ = ("_items",)

    def __init__(self, mapping):
        # Snapshot into a sorted tuple — no live dict ever lives on the instance.
        self._items = tuple(sorted(mapping.items()))

    def __getitem__(self, key):
        for k, v in self._items:
            if k == key:
                return v
        raise KeyError(key)

    def __contains__(self, key):
        return any(k == key for k, _ in self._items)

    def __iter__(self):
        return (k for k, _ in self._items)

    def __len__(self):
        return len(self._items)

    def keys(self):
        return [k for k, _ in self._items]

    def items(self):
        return list(self._items)

    def values(self):
        return [v for _, v in self._items]

    def get(self, key, default=None):
        for k, v in self._items:
            if k == key:
                return v
        return default

    def copy(self):
        return dict(self._items)

    def __eq__(self, other):
        if isinstance(other, _FrozenStrMap):
            return self._items == other._items
        if isinstance(other, dict):
            return dict(self._items) == other
        return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __hash__(self):
        return hash(self._items)

    def __repr__(self):
        return f"_FrozenStrMap({dict(self._items)!r})"

    def __reduce_ex__(self, protocol):  # noqa: D401 — pickle hook
        # Match ``MappingProxyType``'s "frozen ≠ shippable backdoor" contract:
        # refuse to pickle so users cannot accidentally ship a copy and call
        # it frozen. ``dict(huitu.SEMANTIC_PALETTE)`` remains the documented
        # escape hatch for serialization.
        raise TypeError("cannot pickle '_FrozenStrMap' object")

    def __reduce__(self):
        raise TypeError("cannot pickle '_FrozenStrMap' object")

# Widths in inches; journals typically specify mm. 1 inch = 25.4 mm.
_MM = 1.0 / 25.4

# Curated qualitative palettes. All colorblind-checked on white background.
#
# Sources:
#   Paul Tol       — https://personal.sron.nl/~pault/
#   Okabe-Ito      — https://jfly.uni-koeln.de/color/ (Nature Methods 2011)
#   CARTOColors    — https://carto.com/carto-colors/
#   Nord           — https://www.nordtheme.com/
#   Editorial      — custom, inspired by Financial Times & Economist palettes
#   Viridis6       — six evenly-spaced samples of matplotlib's viridis
_TOL_BRIGHT = ["#4477AA", "#EE6677", "#228833", "#CCBB44", "#66CCEE", "#AA3377", "#BBBBBB"]
_TOL_MUTED = ["#332288", "#117733", "#44AA99", "#88CCEE", "#DDCC77", "#CC6677", "#AA4499", "#882255"]
_TOL_VIBRANT = ["#0077BB", "#EE7733", "#33BBEE", "#EE3377", "#009988", "#CC3311", "#BBBBBB"]
_OKABE_ITO = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E6B800", "#56B4E9", "#E69F00", "#000000"]
_CARTO_SAFE = ["#88CCEE", "#CC6677", "#DDCC77", "#117733", "#332288", "#AA4499", "#44AA99"]
_CARTO_BOLD = ["#7F3C8D", "#11A579", "#3969AC", "#F2B701", "#E73F74", "#80BA5A", "#E68310", "#008695"]
_NORD = ["#5E81AC", "#BF616A", "#A3BE8C", "#D08770", "#B48EAD", "#88C0D0", "#EBCB8B", "#8FBCBB"]
_EDITORIAL = ["#1F4E79", "#C44536", "#4E7C5A", "#E0A458", "#6B4C7A", "#8A7B6F", "#2F6E8F", "#A83232"]
_VIRIDIS6 = ["#440154", "#414487", "#2A788E", "#22A884", "#7AD151", "#FDE725"]

# Nature-style qualitative: deep blue, brick red, forest green, burnt amber,
# violet, slate, oxblood. Low-saturation, earthy hues common in Nature figures.
_NATURE_CAT = ["#0C5DA5", "#D1362F", "#00882B", "#E68310", "#5F4690", "#4A6C8C", "#94484B"]
# Nature-muted: low-saturation earth-tones for Nature's production style.
_NATURE_MUTED = ["#3E5C76", "#B0413E", "#4E7C5A", "#C79A3C", "#6B4C7A", "#4A4A4A"]
# Science magazine categorical (warmer, more saturated reds and ochres).
_SCIENCE_CAT = ["#B4223B", "#33649F", "#E09B14", "#2E7D6C", "#6D2E78", "#9C6C2F", "#3F3F3F"]
# Fabio Crameri's batlow — perceptually uniform, robust to greyscale conversion.
# Nature Communications recommended Crameri scientific colormaps post-2020.
_CRAMERI_BATLOW = ["#011959", "#143262", "#30506A", "#506E66", "#788D55", "#B6A747", "#E8B254", "#FACA85"]
# Crameri roma — diverging (bluegreen <-> orange).
_CRAMERI_ROMA = ["#7E1900", "#A4521A", "#C7923A", "#DFCE73", "#B8CEA7", "#6EA4A8", "#26678B", "#1A3668"]
# Matte/low-saturation upgrade of tab10 for presentation slides.
_BOLD_QUALITATIVE = ["#2E5E84", "#E8893C", "#3B8B43", "#C93F3F", "#8E5BA8", "#805845", "#C771A6"]

# ── Semantic / role-based palette (inspired by `nature-figure`'s PALETTE) ────
# Colors are mapped to *semantic roles*, not "first/second/third category".
# Use this when the figure is a hero-vs-baseline comparison, or when you need
# directional (gain / drop) cues instead of arbitrary category identity.
#
#   hero / hero_2     — your method / your sample (deep + medium blue)
#   baseline / baseline_2 — control / reference (dark + soft red)
#   positive          — improvement / gain / above mean (green)
#   negative          — degradation / drop / below mean (red)
#   neutral / neutral_light / neutral_mid / neutral_dark — context / scaffolding
#   accent_*          — sparingly used callouts (gold / teal / violet)
#
# Reserve ``positive``/``negative`` for **directional cues** (arrows, deltas,
# sign-of-effect) — never for category identity. That keeps green/red free as
# universal "good/bad" signals, the way Nature/Science figures use them.
SEMANTIC_PALETTE: dict[str, str] = {
    "hero":         "#0F4D92",  # deep blue — proposed method / your sample
    "hero_2":       "#3775BA",  # medium blue — secondary hero / variant
    "hero_soft":    "#B4C0E4",  # soft blue — third-tier hero variant
    "baseline":     "#B64342",  # brick red — reference / control
    "baseline_2":   "#E9A6A1",  # soft red — secondary reference
    "baseline_soft":"#F6CFCB",  # palest red — tertiary reference / band
    "positive":     "#2E9E44",  # green — gain / improvement / above mean
    "positive_soft":"#AADCA9",  # pale green — softer positive shade
    "negative":     "#E53935",  # saturated red — drop / degradation / below
    "negative_soft":"#F0A0A0",  # pale red — softer negative shade
    "neutral":      "#767676",  # mid grey — neutral reference
    "neutral_light":"#CFCECE",  # light grey — context fill
    "neutral_dark": "#4D4D4D",  # dark grey — emphasis text
    "neutral_black":"#272727",  # near-black — frames / dark text
    "accent_gold":  "#FFD700",  # gold — sparing callout
    "accent_teal":  "#42949E",  # teal — secondary accent
    "accent_violet":"#9A4D8E",  # violet — tertiary accent
    "accent_magenta":"#EA84DD", # magenta — fluorescence channel
}

# When applied as a categorical color cycle, follow the standard hero→
# baseline→positive→negative→neutral→accents ordering.
_SEMANTIC = [
    SEMANTIC_PALETTE["hero"],          # 1st category = your method
    SEMANTIC_PALETTE["baseline"],      # 2nd = baseline / control
    SEMANTIC_PALETTE["accent_teal"],   # 3rd = secondary cool accent
    SEMANTIC_PALETTE["accent_violet"], # 4th = tertiary accent
    SEMANTIC_PALETTE["neutral"],       # 5th = neutral reference
    SEMANTIC_PALETTE["accent_gold"],   # 6th = highlight callout
]

# Freeze SEMANTIC_PALETTE so downstream code can't mutate the role → hex
# mapping in place (which would silently corrupt every figure in a session).
# ``_SEMANTIC`` is a snapshot list of plain hex strings, so the freeze does
# not affect the categorical cycle assembled above.
#
# Round 3: use a tuple-backed :class:`_FrozenStrMap` rather than
# :class:`MappingProxyType`. The proxy form left the inner dict reachable via
# ``gc.get_referents``, which a hostile/sloppy caller could mutate to corrupt
# subsequent ``role()`` lookups. ``_FrozenStrMap`` stores items in an
# immutable tuple slot, so ``gc.get_referents`` only surfaces the tuple — no
# writable dict — and ``role()`` reads stay reproducible across the session.
SEMANTIC_PALETTE = _FrozenStrMap(SEMANTIC_PALETTE)

# Two-level freeze (preserves the ``type(PALETTES).__name__ == "mappingproxy"``
# contract and the "cannot pickle the proxy" contract while sealing the inner
# escape hatch from Round 1):
#   * ``_PALETTES_BACKING`` is a :class:`_DefensivePaletteDict` (a ``dict``
#     subclass). Inner values are stored as ``tuple`` so the backing itself
#     can't be poisoned, and ``__getitem__`` hands out a fresh ``list`` on
#     every access. ``huitu.pro`` writes to this backing at import time.
#   * ``PALETTES`` is :class:`types.MappingProxyType` over the backing — it
#     blocks ``__setitem__`` / ``__delitem__`` / ``pickle`` and is the public
#     read-only view. Indexing via the proxy forwards to the backing's
#     ``__getitem__`` so ``PALETTES['nord'][0] = '#000'`` mutates a throwaway
#     list rather than the registry. ``dict(PALETTES)['nord']`` is therefore
#     a fresh ``list`` that round-trips cleanly through pickle / deepcopy.
_PALETTES_BACKING: _DefensivePaletteDict = _DefensivePaletteDict({
    "tol-bright": tuple(_TOL_BRIGHT),
    "tol-muted": tuple(_TOL_MUTED),
    "tol-vibrant": tuple(_TOL_VIBRANT),
    "okabe-ito": tuple(_OKABE_ITO),
    "carto-safe": tuple(_CARTO_SAFE),
    "carto-bold": tuple(_CARTO_BOLD),
    "nord": tuple(_NORD),
    "editorial": tuple(_EDITORIAL),
    "viridis6": tuple(_VIRIDIS6),
    "nature-cat": tuple(_NATURE_CAT),
    "nature-muted": tuple(_NATURE_MUTED),
    "science-cat": tuple(_SCIENCE_CAT),
    "crameri-batlow": tuple(_CRAMERI_BATLOW),
    "crameri-roma": tuple(_CRAMERI_ROMA),
    "bold-qualitative": tuple(_BOLD_QUALITATIVE),
    "semantic": tuple(_SEMANTIC),
})
PALETTES: Mapping[str, list[str]] = MappingProxyType(_PALETTES_BACKING)

# Palettes whose hex lists are ordered in a perceptually meaningful way and
# therefore make sense as smooth LinearSegmentedColormap gradients.
_GRADIENT_PALETTES = {"crameri-batlow", "crameri-roma", "viridis6"}

# Font stacks used by individual presets. Helvetica chain is the default
# sans choice (Nature/ACS/Wiley/Elsevier/RSC house style); a serif stack is
# used for Science / IEEE which traditionally typeset body text in Times.
_SANS_FAMILY = ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"]
_SERIF_FAMILY = ["Times New Roman", "Liberation Serif", "DejaVu Serif", "serif"]

# Per-journal defaults — palette choice reflects each house's published style.
_PRESETS = {
    "default": {
        "styles": [],
        "palette": "editorial",
        "rc": {
            "figure.figsize": (3.5, 2.8),
            "font.size": 8,
            "axes.linewidth": 0.8,
            "lines.linewidth": 1.2,
            # High-res default; matches most journal minimums.
            "savefig.dpi": 600,
            "font.family":      list(_SANS_FAMILY),
            "font.sans-serif":  list(_SANS_FAMILY),
            "mathtext.fontset": "dejavusans",
        },
    },
    "nature": {
        "styles": ["science", "nature"],
        "palette": "nature-cat",
        "rc": {
            "figure.figsize": (89 * _MM, 70 * _MM),
            "font.size": 7,
            "axes.linewidth": 0.6,
            "lines.linewidth": 1.0,
            # Nature: 300 dpi colour, 600 dpi halftone, 1200 dpi line art.
            # 600 dpi is a safe default for mixed raster/vector panels.
            "savefig.dpi": 600,
            "font.family":      list(_SANS_FAMILY),
            "font.sans-serif":  list(_SANS_FAMILY),
            "mathtext.fontset": "dejavusans",
        },
    },
    "science": {
        "styles": ["science"],
        "palette": "science-cat",
        "rc": {
            "figure.figsize": (55 * _MM * 2, 55 * _MM * 1.6),
            "font.size": 7,
            "axes.linewidth": 0.7,
            "lines.linewidth": 1.0,
            # Science/AAAS: minimum 300 dpi colour / 600 dpi line at final size.
            "savefig.dpi": 600,
            # Science magazine typesets body text in serif.
            "font.family":      list(_SERIF_FAMILY),
            "font.serif":       list(_SERIF_FAMILY),
            "mathtext.fontset": "stix",
        },
    },
    "acs": {
        "styles": ["science", "notebook"],
        "palette": "bold-qualitative",
        "rc": {
            "figure.figsize": (3.33, 2.5),
            "font.size": 8,
            "axes.linewidth": 0.8,
            "lines.linewidth": 1.1,
            # ACS: 300 dpi minimum for colour/halftone; 1200 dpi for line art.
            "savefig.dpi": 600,
            "font.family":      list(_SANS_FAMILY),
            "font.sans-serif":  list(_SANS_FAMILY),
            "mathtext.fontset": "dejavusans",
        },
    },
    "rsc": {
        "styles": ["science"],
        "palette": "tol-vibrant",
        "rc": {
            "figure.figsize": (3.26, 2.6),
            "font.size": 8,
            "axes.linewidth": 0.7,
            "lines.linewidth": 1.0,
            # RSC: 600 dpi required for bitmap figures.
            "savefig.dpi": 600,
            "font.family":      list(_SANS_FAMILY),
            "font.sans-serif":  list(_SANS_FAMILY),
            "mathtext.fontset": "dejavusans",
        },
    },
    "wiley": {
        "styles": ["science"],
        "palette": "nord",
        "rc": {
            "figure.figsize": (3.35, 2.6),
            "font.size": 8,
            "axes.linewidth": 0.8,
            "lines.linewidth": 1.1,
            # Wiley: 300–600 dpi raster; bump to 600 for safety.
            "savefig.dpi": 600,
            "font.family":      list(_SANS_FAMILY),
            "font.sans-serif":  list(_SANS_FAMILY),
            "mathtext.fontset": "dejavusans",
        },
    },
    "elsevier": {
        "styles": ["science"],
        "palette": "okabe-ito",
        "rc": {
            "figure.figsize": (90 * _MM, 70 * _MM),
            "font.size": 8,
            "axes.linewidth": 0.8,
            "lines.linewidth": 1.0,
            # Elsevier: 300 dpi colour/halftone, 500–1000 for line.
            "savefig.dpi": 600,
            "font.family":      list(_SANS_FAMILY),
            "font.sans-serif":  list(_SANS_FAMILY),
            "mathtext.fontset": "dejavusans",
        },
    },
    "ieee": {
        "styles": ["science", "ieee"],
        "palette": "carto-safe",
        "rc": {
            "figure.figsize": (3.5, 2.5),
            "font.size": 8,
            "axes.linewidth": 0.8,
            "lines.linewidth": 1.0,
            # IEEE: 300 dpi minimum for photos, 600 dpi for halftone/combo.
            "savefig.dpi": 600,
            # IEEE Transactions body text is serif.
            "font.family":      list(_SERIF_FAMILY),
            "font.serif":       list(_SERIF_FAMILY),
            "mathtext.fontset": "stix",
        },
    },
}

# rcParams shared across every preset. Tuned to Nature/Science print aesthetics:
# sans-serif Helvetica stack, all four spines visible, thinner axes, tighter
# legends/ticks, and minor ticks on by default.
_COMMON_RC = {
    # Helvetica Neue / Helvetica resolve on macOS desktop work; DejaVu Sans is
    # matplotlib's bundled fallback (Linux CI / vanilla Windows). Arial covers
    # most Windows boxes.
    "font.family": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "mathtext.default": "regular",
    "savefig.dpi": 600,
    "savefig.bbox": "tight",
    # Editable text in vector exports (Nature/Cell/Illustrator/Inkscape).
    # ``svg.fonttype='none'`` keeps text as <text> nodes, so reviewers/editors
    # can re-align labels post-hoc instead of receiving outlined glyphs.
    # ``pdf.fonttype=42`` and ``ps.fonttype=42`` embed TrueType outlines so
    # selecting/searching text in the saved PDF/PS still works.
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "figure.dpi": 120,
    "figure.constrained_layout.use": True,
    "figure.constrained_layout.h_pad": 0.04,
    "figure.constrained_layout.w_pad": 0.04,
    "axes.edgecolor": "black",
    "axes.labelcolor": "black",
    "axes.labelpad": 3.0,
    "axes.linewidth": 0.7,
    "axes.spines.top": True,
    "axes.spines.right": True,
    "axes.spines.left": True,
    "axes.spines.bottom": True,
    "axes.grid": False,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.top": False,
    "ytick.right": False,
    "xtick.major.width": 0.7,
    "ytick.major.width": 0.7,
    "xtick.minor.width": 0.5,
    "ytick.minor.width": 0.5,
    "xtick.major.size": 3.0,
    "ytick.major.size": 3.0,
    "xtick.minor.size": 1.5,
    "ytick.minor.size": 1.5,
    "xtick.major.pad": 3,
    "ytick.major.pad": 3,
    "xtick.minor.visible": True,
    "ytick.minor.visible": True,
    "legend.frameon": False,
    "legend.handlelength": 1.6,
    "legend.columnspacing": 1.0,
    "legend.labelspacing": 0.35,
    # Disable TeX so scienceplots runs without a LaTeX install.
    "text.usetex": False,
}


def _apply_scienceplots(styles: list[str]) -> bool:
    if not styles:
        return True
    try:
        import scienceplots  # noqa: F401

        plt.style.use(styles)
        return True
    except Exception:
        return False


_CJK_FAMILIES = [
    "Noto Sans CJK SC",
    "PingFang SC",
    "Heiti SC",
    "Songti SC",
    "STHeiti",
    "Arial Unicode MS",
    "Microsoft YaHei",
    "SimHei",
]


def register_cjk() -> str | None:
    """Probe available system fonts and return the first CJK font found.

    Returns the resolved font family name so callers can set
    ``font.family`` explicitly, or ``None`` if no CJK-capable font was
    detected. Has no side effect beyond the font-manager probe.
    """
    try:
        from matplotlib import font_manager as fm
    except Exception:
        return None
    try:
        available = {fm.FontProperties(fname=p).get_name()
                     for p in fm.findSystemFonts()}
    except Exception:
        available = set()
    for fam in _CJK_FAMILIES:
        if fam in available:
            return fam
    return None


def use_journal(name: str = "default", cjk: bool = False) -> None:
    """Apply a journal preset to matplotlib rcParams.

    This resets matplotlib rcParams to defaults before applying the preset, so
    any previous user-set rcParams are discarded for the current session.

    Parameters
    ----------
    name
        Journal preset key (see :data:`_PRESETS`).
    cjk
        If ``True``, prepend CJK-capable font families to ``font.family`` so
        Chinese / Japanese / Korean characters render without tofu. Falls back
        silently when none of the preferred fonts are installed; use
        :func:`register_cjk` to pick a specific one.

    Raises
    ------
    ValueError
        If ``name`` is not one of the known presets.
    """
    key = name.lower()
    if key not in _PRESETS:
        raise ValueError(
            f"unknown journal preset '{name}'. choices: {sorted(_PRESETS)}"
        )
    preset = _PRESETS[key]
    # Install SVG-savefig font-unification hook lazily on first preset.
    _install_svg_font_unify_hook()
    mpl.rcdefaults()
    _apply_scienceplots(preset["styles"])
    common_rc = dict(_COMMON_RC)
    mpl.rcParams.update(common_rc)
    # Derive tick/label/legend sizes from the preset's base font.size.
    # Hierarchy (Nature/Science): axes.labelsize = base+1, tick/legend = base.
    base = preset["rc"].get("font.size", mpl.rcParams["font.size"])
    mpl.rcParams.update(
        {
            "axes.labelsize": base + 1,
            "axes.titlesize": base + 1,
            "xtick.labelsize": base,
            "ytick.labelsize": base,
            "legend.fontsize": base,
        }
    )
    mpl.rcParams.update(preset["rc"])
    # CJK prepending must run *after* the preset's font.family has been
    # applied, otherwise the preset overwrites the CJK-merged stack.
    if cjk:
        current_family = list(mpl.rcParams.get("font.family", []))
        merged = list(_CJK_FAMILIES) + current_family
        mpl.rcParams["font.family"] = merged
        # Mirror the merge into the matching sans/serif slot so downstream
        # font resolution honours the prepended CJK families consistently.
        head = current_family[0].lower() if current_family else ""
        if "times" in head or "serif" in head or "minion" in head:
            mpl.rcParams["font.serif"] = list(_CJK_FAMILIES) + list(
                mpl.rcParams.get("font.serif", [])
            )
        else:
            mpl.rcParams["font.sans-serif"] = list(_CJK_FAMILIES) + list(
                mpl.rcParams.get("font.sans-serif", [])
            )
    # Unify tick widths with axes.linewidth so axes + ticks visually agree.
    ax_lw = float(mpl.rcParams.get("axes.linewidth", 0.7))
    mpl.rcParams.update(
        {
            "xtick.major.width": ax_lw,
            "ytick.major.width": ax_lw,
            "xtick.minor.width": ax_lw * 0.6,
            "ytick.minor.width": ax_lw * 0.6,
        }
    )
    # Apply curated palette last so it survives the preset rc merge.
    palette_name = preset.get("palette", "tol-bright")
    use_palette(palette_name)
    # Probe for Helvetica; warn once if missing so users know to install it.
    try:
        from matplotlib.font_manager import findfont, FontProperties
        stack = mpl.rcParams.get("font.family", [])
        if isinstance(stack, str):
            stack = [stack]
        if stack:
            try:
                resolved_path = findfont(
                    FontProperties(family=stack[0]), fallback_to_default=False
                )
                # findfont may succeed but return a fallback. Re-probe the name.
                resolved = FontProperties(fname=resolved_path).get_name()
                if "helvetica" not in resolved.lower() and "helvetica" in str(stack[0]).lower():
                    print(
                        f"huitu: Helvetica not found; falling back to {resolved}. "
                        f"Install Helvetica for Nature-quality typography."
                    )
            except Exception:
                try:
                    resolved_path = findfont(FontProperties(family=stack[0]))
                    resolved = FontProperties(fname=resolved_path).get_name()
                except Exception:
                    resolved = "matplotlib default"
                print(
                    f"huitu: Helvetica not found; falling back to {resolved}. "
                    f"Install Helvetica for Nature-quality typography."
                )
    except Exception:
        pass

    # Mark the active preset so ``prepare_axes`` can skip re-applying it on
    # every plot_* call (which would otherwise wipe user rc overrides).
    global _ACTIVE_PRESET
    _ACTIVE_PRESET = key


def use_font(family, *, mathtext: str | None = None,
             size: float | None = None) -> None:
    """Override ``font.family`` (and optionally ``mathtext.fontset`` / ``font.size``)
    in the current matplotlib session.

    This is the user-facing escape hatch for the per-journal font defaults set
    by :func:`use_journal`. Call it *after* :func:`use_journal` if you want a
    specific family irrespective of the preset's house style — the change
    survives subsequent ``plot_*`` calls because :func:`prepare_axes` does not
    re-apply the preset once one has been installed.

    Parameters
    ----------
    family
        Font family name (e.g. ``"Times New Roman"``) or an iterable of names
        forming a fallback chain.
    mathtext
        Optional ``mathtext.fontset`` (e.g. ``"stix"`` for serif, ``"dejavusans"``
        for sans). If ``None`` the current mathtext fontset is kept.
    size
        Optional base ``font.size`` in points.

    Examples
    --------
    >>> huitu.use_journal("nature")
    >>> huitu.use_font("Times New Roman", mathtext="stix")
    """
    if isinstance(family, str):
        fams = [family]
        head = family
    else:
        fams = list(family)
        if not fams:
            raise ValueError("use_font: family must be non-empty")
        head = str(fams[0])
    mpl.rcParams["font.family"] = fams
    head_lower = head.lower()
    if (
        "times" in head_lower
        or "serif" in head_lower
        or "minion" in head_lower
        or "liberation serif" in head_lower
    ):
        mpl.rcParams["font.serif"] = fams
    else:
        mpl.rcParams["font.sans-serif"] = fams
    if mathtext is not None:
        mpl.rcParams["mathtext.fontset"] = mathtext
    if size is not None:
        mpl.rcParams["font.size"] = float(size)


def use_palette(name_or_colors) -> list[str]:
    """Set the current axes color cycle.

    Accepts a registered palette name (see ``PALETTES``) or any iterable of
    matplotlib-recognised colors. Returns the resolved color list so callers
    can preview or reuse it.

    >>> use_palette("nord")
    >>> use_palette(["#1F4E79", "#C44536", "#4E7C5A"])
    """
    if isinstance(name_or_colors, str):
        key = name_or_colors.lower()
        if key not in PALETTES:
            raise ValueError(
                f"unknown palette '{name_or_colors}'. choices: {sorted(PALETTES)}"
            )
        colors = list(PALETTES[key])
    else:
        colors = list(name_or_colors)
        if not colors:
            raise ValueError("palette must contain at least one color")
    mpl.rcParams["axes.prop_cycle"] = cycler(color=colors)
    return colors


def list_palettes() -> list[str]:
    """Return the names of all registered palettes."""
    return sorted(PALETTES)


def role(name: str) -> str:
    """Look up a hex color by *semantic role* rather than by category index.

    Use this when the figure has a hero-vs-baseline structure, or when you
    want directional (gain/drop) cues that stay consistent across panels.

    Parameters
    ----------
    name
        Role key from :data:`SEMANTIC_PALETTE`. Common keys:

        * ``hero``, ``hero_2``, ``hero_soft`` — your method / sample
        * ``baseline``, ``baseline_2``, ``baseline_soft`` — control
        * ``positive``, ``positive_soft`` — improvement / above-mean
        * ``negative``, ``negative_soft`` — drop / below-mean
        * ``neutral``, ``neutral_light``, ``neutral_dark``, ``neutral_black``
        * ``accent_gold``, ``accent_teal``, ``accent_violet``, ``accent_magenta``

    Returns
    -------
    str
        ``#RRGGBB`` hex string.

    Raises
    ------
    KeyError
        If ``name`` is not a registered role. The error lists valid roles.

    Examples
    --------
    >>> ax.plot(x, y_mine, color=role("hero"),     label="Ours")
    >>> ax.plot(x, y_ref,  color=role("baseline"), label="Baseline")
    >>> ax.scatter(x_gain, y_gain, color=role("positive"), marker="^")
    >>> ax.scatter(x_drop, y_drop, color=role("negative"), marker="v")
    """
    key = name.lower()
    if key not in SEMANTIC_PALETTE:
        raise KeyError(
            f"unknown role '{name}'. choices: {sorted(SEMANTIC_PALETTE)}"
        )
    return SEMANTIC_PALETTE[key]


def get_cmap(name: str):
    """Return a :class:`matplotlib.colors.LinearSegmentedColormap` from a huitu palette.

    Useful for heatmaps / operando maps / density plots where an ordered
    qualitative list doubles as a gradient. Only palettes whose hex ordering is
    perceptually meaningful are supported (``crameri-batlow``, ``crameri-roma``,
    ``viridis6``, ``editorial``).

    Parameters
    ----------
    name
        Palette key registered in :data:`PALETTES`.

    Returns
    -------
    matplotlib.colors.LinearSegmentedColormap
        Colormap interpolating between the listed hex colors.

    Examples
    --------
    >>> cmap = get_cmap("crameri-batlow")
    >>> ax.imshow(Z, cmap=cmap)
    """
    from matplotlib.colors import LinearSegmentedColormap

    key = name.lower()
    if key not in PALETTES:
        raise ValueError(
            f"unknown palette '{name}'. choices: {sorted(PALETTES)}"
        )
    if key not in _GRADIENT_PALETTES:
        raise ValueError(
            f"palette '{name}' is qualitative; gradients are only supported for "
            f"{sorted(_GRADIENT_PALETTES)}"
        )
    return LinearSegmentedColormap.from_list(f"huitu-{key}", PALETTES[key])
