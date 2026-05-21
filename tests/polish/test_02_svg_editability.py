"""Polish test 02 — SVG editability.

User's complaint:

> "能够实现 svg 的图绘制吧"

v0.5 / v0.6 already sets ``svg.fonttype='none'`` so ``<text>`` should be
retained. We test the *consequence*: open the SVG, count text nodes, count
path nodes, and verify the font-family attribute the user would need to
re-skin a figure in Illustrator/Inkscape.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pytest

from .conftest import (
    parse_svg,
    report,
    sample,
    svg_font_families,
    svg_path_count,
    svg_text_nodes,
    svg_text_to_string,
)


def _save_xrd(tmp_path, journal="nature"):
    import huitu
    huitu.use_journal(journal)
    fig, ax = huitu.plot_xrd(sample("xrd.txt"))
    out = tmp_path / "xrd.svg"
    fig.savefig(out)
    plt.close(fig)
    return out


def test_case_01_svg_writes(tmp_path):
    """case_01: savefig(*.svg) writes a non-empty file."""
    out = _save_xrd(tmp_path)
    ok = out.exists() and out.stat().st_size > 0
    report(1, "savefig writes a non-empty .svg", ok,
           f"file size {out.stat().st_size if out.exists() else 0}")
    assert ok


def test_case_02_has_text_nodes(tmp_path):
    """case_02: the .svg contains at least 5 <text> nodes (not all rasterised)."""
    out = _save_xrd(tmp_path)
    root = parse_svg(out)
    texts = svg_text_nodes(root)
    ok = len(texts) >= 5
    report(2, "SVG has >=5 <text> nodes", ok, f"only {len(texts)} text nodes")
    assert ok


def test_case_03_text_contains_label(tmp_path):
    """case_03: the actual xlabel text ('2θ' substring) shows up in <text> body.

    If the text were converted to paths, the literal '2' / 'θ' character would
    be gone from the SVG XML.
    """
    out = _save_xrd(tmp_path)
    root = parse_svg(out)
    body = svg_text_to_string(root)
    ok = "2" in body and ("θ" in body or "theta" in body.lower())
    report(3, "SVG body contains literal label characters", ok,
           f"label chars not found in {body[:200]!r}")
    assert ok


def test_case_04_font_family_attribute(tmp_path):
    """case_04: <text> nodes carry a font-family style attribute.

    Required for Illustrator/Inkscape to render the text faithfully.
    """
    out = _save_xrd(tmp_path)
    root = parse_svg(out)
    fams = svg_font_families(root)
    ok = len(fams) >= 1
    report(4, "SVG <text> nodes carry font-family style", ok,
           "no font-family found in any <text>/<tspan>")
    assert ok


def test_case_05_no_excessive_paths(tmp_path):
    """case_05: <path> count is not absurdly high (proxy: text not outlined).

    An XRD plot with ~15 tick labels and 2 axis labels rendered as outlined
    paths would balloon path count. Cutoff is generous to avoid flakes.
    """
    out = _save_xrd(tmp_path)
    root = parse_svg(out)
    n_path = svg_path_count(root)
    # Even a complex plot has <80 paths under svg.fonttype='none'.
    ok = n_path < 200
    report(5, "SVG <path> count under 200", ok,
           f"too many paths: {n_path} — text may be outlined")
    assert ok


def test_case_06_mathtext_in_text_nodes(tmp_path):
    """case_06: mathtext labels generate <text>/<tspan> not standalone <path>.

    With ``svg.fonttype='none'``, matplotlib emits one <text> per math node and
    breaks individual chars into <tspan>. We assert that the SVG contains a
    'θ' or 'theta' character somewhere inside a text-context (not in a path).
    """
    import huitu

    huitu.use_journal("nature")
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    ax.set_xlabel(r"2$\theta$ (deg)")
    out = tmp_path / "mathtext.svg"
    fig.savefig(out)
    plt.close(fig)

    root = parse_svg(out)
    body = svg_text_to_string(root)
    ok = "θ" in body or "theta" in body.lower()
    report(6, "mathtext θ ends up in <text>/<tspan>, not glyph paths",
           ok, f"θ missing from SVG body — got {body[:200]!r}")
    assert ok


@pytest.mark.parametrize("journal", ["default", "nature", "science", "acs", "ieee"])
def test_case_07_multi_journal_text_nodes(journal, tmp_path):
    """case_07: every journal preset still produces editable SVGs."""
    out = _save_xrd(tmp_path, journal=journal)
    root = parse_svg(out)
    texts = svg_text_nodes(root)
    ok = len(texts) >= 5
    report(7, f"journal='{journal}': SVG has >=5 <text> nodes", ok,
           f"only {len(texts)} <text> nodes for journal={journal}")
    assert ok


def test_case_08_pdf_text_fonttype_42(tmp_path):
    """case_08: PDF backend uses ``pdf.fonttype=42`` (TrueType, searchable).

    The user only mentioned SVG, but the same editability promise belongs to
    PDF. Type-42 (TrueType) is the editorial standard.
    """
    import huitu
    import matplotlib as mpl

    huitu.use_journal("nature")
    ok = mpl.rcParams.get("pdf.fonttype") == 42
    report(8, "pdf.fonttype=42 after use_journal", ok,
           f"got {mpl.rcParams.get('pdf.fonttype')}")
    assert ok


def test_case_09_eps_fonttype_42():
    """case_09: ``ps.fonttype=42`` (Type 42 TrueType in EPS)."""
    import huitu
    import matplotlib as mpl

    huitu.use_journal("nature")
    ok = mpl.rcParams.get("ps.fonttype") == 42
    report(9, "ps.fonttype=42 after use_journal", ok,
           f"got {mpl.rcParams.get('ps.fonttype')}")
    assert ok


def test_case_10_svg_fonttype_none():
    """case_10: ``svg.fonttype='none'`` after use_journal."""
    import huitu
    import matplotlib as mpl

    huitu.use_journal("nature")
    ok = mpl.rcParams.get("svg.fonttype") == "none"
    report(10, "svg.fonttype='none' after use_journal", ok,
           f"got {mpl.rcParams.get('svg.fonttype')}")
    assert ok


def test_case_11_pourbaix_svg_editable(tmp_path):
    """case_11: even Pourbaix region labels (used in showcase) are editable text.

    The user specifically called out Pourbaix; if its region labels rasterise,
    Illustrator/Inkscape can't fix them.
    """
    import huitu

    regions = [
        {"label": "Fe", "color": "tab:blue",
         "vertices": [(0, -1), (5, -1), (5, 0), (0, 0)]},
        {"label": "Fe2+", "color": "tab:red",
         "vertices": [(0, 0), (5, 0), (5, 1), (0, 1)]},
    ]
    huitu.use_journal("nature")
    fig, _ = huitu.plot_pourbaix(regions)
    out = tmp_path / "pourbaix.svg"
    fig.savefig(out)
    plt.close(fig)
    root = parse_svg(out)
    body = svg_text_to_string(root)
    ok = "Fe" in body and ("Fe2+" in body or "Fe" in body)
    report(11, "Pourbaix region labels are editable <text>", ok,
           f"region labels missing in SVG body: {body[:300]!r}")
    assert ok


def test_case_12_dqdv_svg_editable(tmp_path):
    """case_12: dQ/dV figure preserves its mathtext y-axis label ('dQ/dV (mAh/g/V)')."""
    import huitu
    import numpy as np
    import pandas as pd

    huitu.use_journal("nature")
    df = pd.read_csv(sample("gcd.txt"), sep=None, engine="python", comment="#",
                     header=None)
    df = df.apply(pd.to_numeric, errors="coerce").dropna(how="all")
    # gcd.txt is (capacity, voltage) — flip for dq/dv.
    fig, ax = huitu.plot_dqdv((df.iloc[:, 1].to_numpy(), df.iloc[:, 0].to_numpy()))
    out = tmp_path / "dqdv.svg"
    fig.savefig(out)
    plt.close(fig)
    root = parse_svg(out)
    body = svg_text_to_string(root)
    # mathtext is split into per-glyph <tspan> elements so 'dQ' becomes
    # 'd\nQ' in the joined body. Normalise whitespace before matching.
    body_flat = "".join(body.split())
    # Tightened predicate: previously the OR/AND mix made "any 'd' + any 'Q'
    # + any 'V'" pass, which silently accepted runs where the y-label was
    # missing. Require the literal "dQ" pair plus either "dV" or "mAh" so the
    # mathtext label has to be present.
    ok = "dQ" in body_flat and ("dV" in body_flat or "mAh" in body_flat)
    report(12, "plot_dqdv preserves mathtext y-label in SVG",
           ok, f"dQ/mAh chars not found in {body_flat[:300]!r}")
    assert ok
