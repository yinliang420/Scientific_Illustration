"""Polish test 01 — font consistency across journal presets.

User's complaint (verbatim):

> "字体的问题能够解决吧，能自己选字体这种吧，这个看着好奇怪整个字体形式，
>  默认都是各个期刊的字体默认"

Things to check:
1. Every journal preset survives ``use_journal()`` without crashing.
2. ``font.family`` for ``science/rsc/wiley/elsevier/ieee`` is **not identical**
   to ``nature`` — Science/Cell traditionally use Times/Minion, IEEE has its
   own family, etc. The expectation set by the user is "each journal preset
   gets its own font default", not "every preset shares Helvetica Neue".
3. ``mathtext.fontset`` agrees with ``font.family`` so a ``r"$\theta$"`` does
   not render in DejaVuSerif while surrounding text renders in Helvetica
   (which is the "mixed/weird" visual the user described).
4. A user-facing font-override API exists (``font_family=`` kwarg to plot
   functions, or a top-level helper). Both are reasonable; we test for at
   least one of them.

Cases 1–8 are parametrized over journals. Cases 9–12 are mathtext / API.
"""

from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest

from .conftest import report, sample

JOURNALS = ["default", "nature", "science", "acs", "rsc", "wiley", "elsevier", "ieee"]

# Journal-house preferred font *family* (loose match, lowercase).
# Sources:
#   Nature  — Helvetica / Arial sans-serif since 2002
#   Science — Times / serif for body, may pair with sans for figures
#   ACS     — Arial / Helvetica
#   RSC     — sans-serif (Calibri/Arial)
#   Wiley   — sans-serif (Univers / Helvetica)
#   Elsevier — sans-serif preferred, but historically Times for some titles
#   IEEE    — Times for body, sans for figures
EXPECTED_FAMILY_HINT = {
    "default": "sans",
    "nature":  "helvetica",
    "science": "times",        # Science prefers serif body in production
    "acs":     "helvetica",
    "rsc":     "sans",
    "wiley":   "sans",
    "elsevier": "sans",
    "ieee":    "times",
}


def _resolve_first_family() -> str:
    """First member of the active ``font.family`` rc as lowercase string."""
    fam = mpl.rcParams.get("font.family", "")
    if isinstance(fam, (list, tuple)):
        return str(fam[0]).lower() if fam else ""
    return str(fam).lower()


@pytest.mark.parametrize("journal", JOURNALS)
def test_case_01_journal_applies(journal):
    """case_01: use_journal(<j>) does not crash and sets a non-empty font.family."""
    import huitu

    huitu.use_journal(journal)
    fam = _resolve_first_family()
    ok = bool(fam)
    report(1, f"use_journal('{journal}') sets font.family", ok,
           f"font.family resolved to empty: {mpl.rcParams.get('font.family')}")
    assert ok, f"font.family empty after use_journal('{journal}')"


@pytest.mark.parametrize("journal", JOURNALS)
def test_case_02_per_journal_font(journal):
    """case_02: each journal's font.family hints at its house style.

    Hard-fails on Nature/ACS expecting Helvetica/Arial. We treat
    Science/IEEE/Elsevier looser — "serif vs sans" is the minimum
    differentiator. The point of this case is to *expose* the v0.5/v0.6
    behaviour where every preset hard-codes ``Helvetica Neue``.
    """
    import huitu

    huitu.use_journal(journal)
    fam = _resolve_first_family()
    hint = EXPECTED_FAMILY_HINT[journal]

    if hint in ("sans", "helvetica"):
        # sans-serif is acceptable
        ok = ("helv" in fam or "arial" in fam or "sans" in fam
              or "dejavu" in fam)
        why = f"journal '{journal}' wants {hint}-ish, got {fam!r}"
    elif hint == "times":
        ok = "times" in fam or "serif" in fam or "minion" in fam
        why = (f"journal '{journal}' traditionally uses serif/Times, "
               f"got sans-serif {fam!r}")
    else:
        ok = True
        why = ""
    report(2, f"font.family hint for journal='{journal}'", ok, why)
    assert ok, why


def test_case_03_presets_differ():
    """case_03: at least *some* journal presets produce *distinct* fonts.

    If `huitu.use_journal('nature')` and `huitu.use_journal('science')`
    both leave ``font.family[0]`` == "Helvetica Neue", the user's complaint
    "默认都是各个期刊的字体默认" is fully justified — there is no per-journal
    typography differentiation.
    """
    import huitu

    seen = []
    for j in JOURNALS:
        huitu.use_journal(j)
        seen.append(_resolve_first_family())
    unique = set(seen)
    ok = len(unique) >= 2
    report(3, "journal presets produce >=2 distinct font.family[0]",
           ok, f"all presets resolved to single family: {unique}")
    assert ok, f"expected >=2 fonts across presets, got {unique}"


def test_case_04_helvetica_resolves_on_macos():
    """case_04: on macOS dev box, font.family[0] resolves to a real ttf.

    Important: this is the "your dev box has the font; CI might not"
    smoke test. Skipped on Linux/CI where Helvetica isn't installed.
    """
    import platform
    import huitu

    if platform.system() != "Darwin":
        pytest.skip("Helvetica resolution check is macOS-only")
    from matplotlib.font_manager import findfont, FontProperties

    huitu.use_journal("nature")
    fam = mpl.rcParams["font.family"][0]
    path = findfont(FontProperties(family=fam), fallback_to_default=True)
    resolved = FontProperties(fname=path).get_name().lower()
    ok = "helvetica" in resolved or "arial" in resolved
    report(4, "Nature preset resolves to Helvetica on macOS",
           ok, f"resolved font: {resolved}")
    assert ok, f"resolved font: {resolved}"


def test_case_05_font_family_kwarg_exists():
    """case_05: API exposes a way to override font per-call.

    User said "能自己选字体这种吧" (can pick my own font). We expect either:
      * ``plot_xrd(..., font_family="Times New Roman")`` accepted, or
      * a top-level helper like ``huitu.use_font(...)``.
    """
    import huitu

    has_use_font = hasattr(huitu, "use_font") and callable(getattr(huitu, "use_font", None))
    has_set_font = hasattr(huitu, "set_font") and callable(getattr(huitu, "set_font", None))
    accepts_kwarg = False
    try:
        huitu.use_journal("default")
        fig, _ = huitu.plot_xrd(sample("xrd.txt"), font_family="Times New Roman")
        plt.close(fig)
        accepts_kwarg = True
    except TypeError:
        accepts_kwarg = False
    except Exception:
        accepts_kwarg = False
    ok = has_use_font or has_set_font or accepts_kwarg
    report(5, "huitu exposes a font-override API", ok,
           "no use_font/set_font/font_family= path found — user's 自己选字体 not met")
    assert ok, "user-facing font-override API is missing"


def test_case_06_use_journal_with_font_override():
    """case_06: user can override font.family via direct rcParams **after**
    ``use_journal`` without huitu clobbering the change.

    This is a softer version of case 05 — even if there's no kwarg, the
    documented escape hatch ``mpl.rcParams['font.family']='Times New Roman'``
    should survive the next plot call.
    """
    import huitu

    huitu.use_journal("nature")
    mpl.rcParams["font.family"] = ["Times New Roman"]
    # Should NOT trigger a fresh use_journal that wipes rcdefaults.
    fig, ax = huitu.plot_xrd(sample("xrd.txt"))
    fam = mpl.rcParams["font.family"]
    ok = "Times New Roman" in (list(fam) if isinstance(fam, (list, tuple)) else [fam])
    plt.close(fig)
    report(6, "post-use_journal rcParams override survives plot_xrd call",
           ok, f"font.family clobbered: now {fam}")
    assert ok, f"font.family clobbered after plot call: {fam}"


@pytest.mark.parametrize("journal", JOURNALS)
def test_case_07_mathtext_matches_text_font(journal):
    """case_07: ``mathtext.fontset`` agrees with sans/serif choice.

    If the body font is Helvetica (sans-serif) but mathtext.fontset is
    "dejavuserif", a label like ``r"2$\\theta$"`` will render with a
    Helvetica '2' next to a DejaVuSerif 'θ' — the exact "好奇怪整个字体形式"
    the user described.
    """
    import huitu

    huitu.use_journal(journal)
    fam = _resolve_first_family()
    fontset = mpl.rcParams.get("mathtext.fontset", "")
    body_is_serif = "times" in fam or "serif" in fam or "minion" in fam
    body_is_sans = "helv" in fam or "arial" in fam or "sans" in fam or "dejavu" in fam
    # Allow "cm" / "stix" as neutral.
    set_is_serif = "serif" in fontset or "stix" in fontset or "cm" in fontset
    set_is_sans = "sans" in fontset

    if body_is_serif and set_is_sans:
        ok, why = False, f"body is serif ({fam}) but mathtext is sans ({fontset})"
    elif body_is_sans and set_is_serif:
        ok, why = False, f"body is sans ({fam}) but mathtext is serif ({fontset})"
    else:
        ok, why = True, ""
    report(7, f"mathtext.fontset matches body font ({journal})", ok, why)
    assert ok, why


def test_case_08_mathtext_default_regular():
    """case_08: ``mathtext.default`` is ``"regular"`` so math inherits body font."""
    import huitu

    huitu.use_journal("nature")
    val = mpl.rcParams.get("mathtext.default", "")
    ok = val == "regular"
    report(8, "mathtext.default == 'regular'", ok,
           f"got {val!r} — mathtext won't inherit body font")
    assert ok


def test_case_09_mathtext_renders_in_body_font(tmp_path):
    """case_09: after savefig, a mathtext label uses *one* font-family, not two.

    Concretely: ``r"2$\\theta$ ($^\\circ$) "`` should not be split between
    Helvetica (for '2θ') and STIXGeneral (for '∘'). The user's "weird font"
    is exactly this mixed rendering. We grep the SVG for >1 font-family.
    """
    import huitu

    from .conftest import parse_svg, svg_font_families

    huitu.use_journal("nature")
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    ax.set_xlabel(r"2$\theta$ ($^\circ$)")
    ax.set_ylabel(r"Intensity (a.u.)")
    out = tmp_path / "mathtext.svg"
    fig.savefig(out)
    plt.close(fig)

    root = parse_svg(out)
    fams = svg_font_families(root)
    # Filter generic stack heads — what matters is the *resolved* font.
    fam_heads = {f.split(",")[0].strip().strip("'\"").lower() for f in fams}
    ok = len(fam_heads) <= 1
    report(9, "mathtext label survives savefig with a single font-family",
           ok, f"multiple font families in SVG: {fam_heads}")
    # Soft assertion: this catches the user's complaint.
    assert ok, f"mathtext fell back to a second font: {fam_heads}"


def test_case_10_font_family_string_vs_list():
    """case_10: ``font.family`` is consistently a list (not a string).

    Mixed list/string types break downstream code that calls ``fam[0]``. The
    user-facing escape hatch ``mpl.rcParams['font.family'] = 'Times'`` (a
    *string*) should still work *after* use_journal — i.e. huitu should not
    re-normalise the rc value into something fragile.
    """
    import huitu

    huitu.use_journal("nature")
    val = mpl.rcParams["font.family"]
    ok = isinstance(val, (list, tuple)) and len(val) > 0
    report(10, "font.family is a non-empty list after use_journal",
           ok, f"got {type(val).__name__} value {val!r}")
    assert ok


def test_case_11_cjk_flag_changes_font(tmp_path):
    """case_11: ``use_journal(cjk=True)`` prepends a CJK font family.

    If no CJK font is installed, this case is a soft-skip — we only assert
    that the font.family list LOOKS LONGER (CJK fonts inserted at front).
    """
    import huitu

    huitu.use_journal("nature", cjk=False)
    base = list(mpl.rcParams["font.family"])
    huitu.use_journal("nature", cjk=True)
    expanded = list(mpl.rcParams["font.family"])
    ok = len(expanded) > len(base)
    report(11, "cjk=True prepends fonts to family stack",
           ok, f"base={base} cjk={expanded}")
    assert ok


def test_case_12_two_plots_same_font():
    """case_12: two back-to-back ``plot_*`` calls don't drift fonts.

    If the second plot inherits a different font.family for any reason
    (e.g. side effect of mathtext rendering, scienceplots leak), labels in
    a multi-panel figure look inconsistent.
    """
    import huitu

    huitu.use_journal("nature")
    fig1, _ = huitu.plot_xrd(sample("xrd.txt"))
    fam1 = list(mpl.rcParams["font.family"])
    fig2, _ = huitu.plot_cv(sample("cv.txt"))
    fam2 = list(mpl.rcParams["font.family"])
    plt.close(fig1); plt.close(fig2)
    ok = fam1 == fam2
    report(12, "two consecutive plot_* calls preserve font.family",
           ok, f"drift detected: before={fam1} after={fam2}")
    assert ok


def test_case_13_use_journal_resets_then_applies():
    """case_13: ``use_journal()`` resets rcParams before applying its preset.

    Pollution from a previous session (e.g. ``rcParams['axes.labelcolor']='red'``)
    must not leak into the next preset. This is documented behaviour
    (`huitu.style:use_journal` docstring) — we lock it in.
    """
    import huitu

    huitu.use_journal("default")
    mpl.rcParams["axes.labelcolor"] = "fuchsia"
    huitu.use_journal("nature")
    val = mpl.rcParams["axes.labelcolor"]
    ok = val != "fuchsia"
    report(13, "use_journal() resets stray rcParams",
           ok, f"rc leak: axes.labelcolor still {val}")
    assert ok
