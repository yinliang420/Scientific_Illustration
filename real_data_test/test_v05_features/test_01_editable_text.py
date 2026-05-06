"""Test 1: Editable SVG / PDF text in v0.5.

Verifies the documented behaviour from huitu/style.py and review.py:

  * After ``huitu.use_journal(...)``, ``mpl.rcParams['svg.fonttype'] == 'none'``
    so SVG text is preserved as ``<text>`` nodes.
  * ``mpl.rcParams['pdf.fonttype'] == 42`` so PDFs ship TrueType outlines
    (selectable / searchable text in Illustrator).
  * Real saves: actually write a SVG and a PDF and confirm the SVG file
    contains ``<text`` nodes (i.e. text is NOT outlined to paths).
  * Repeats the test across the four canonical journal presets so we know
    the rcParams are not silently overridden by a preset.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

import huitu

OUT = Path(__file__).resolve().parent / "output"
OUT.mkdir(exist_ok=True)


def _check_rcparams(label: str) -> list[str]:
    failures: list[str] = []
    sf = mpl.rcParams.get("svg.fonttype")
    pf = mpl.rcParams.get("pdf.fonttype")
    psf = mpl.rcParams.get("ps.fonttype")
    if sf != "none":
        failures.append(f"[{label}] svg.fonttype={sf!r}, expected 'none'")
    if pf != 42:
        failures.append(f"[{label}] pdf.fonttype={pf!r}, expected 42")
    if psf != 42:
        failures.append(f"[{label}] ps.fonttype={psf!r}, expected 42")
    return failures


def _render_demo(out_stem: str) -> tuple[Path, Path]:
    fig, ax = plt.subplots(figsize=(3.5, 2.2))
    x = np.linspace(0, 2 * np.pi, 200)
    ax.plot(x, np.sin(x), color=huitu.role("hero"), label="hero sin")
    ax.plot(x, np.cos(x), color=huitu.role("baseline"), label="baseline cos")
    ax.set_xlabel("Angle (rad)")
    ax.set_ylabel("Amplitude (a.u.)")
    ax.set_title("Editable text demo")
    ax.legend(frameon=False)
    svg = OUT / f"{out_stem}.svg"
    pdf = OUT / f"{out_stem}.pdf"
    fig.savefig(svg)
    fig.savefig(pdf)
    plt.close(fig)
    return svg, pdf


def _grep_text_nodes(svg_path: Path) -> int:
    text = svg_path.read_text(encoding="utf-8", errors="replace")
    # Count <text ...> opening tags. Use a tolerant regex to allow attrs.
    return len(re.findall(r"<text[\s>]", text))


def _grep_path_glyphs(svg_path: Path) -> int:
    """Count <path id="..."> entries that look like outlined glyphs.

    matplotlib outlines glyphs as <path> with ids starting with the font
    family. If editable-text is on, the text appears as <text>...</text>
    nodes referencing reusable <path id="...font..."> definitions. The
    presence of <path id="DejaVuSans-..."/> without surrounding <use>/<text>
    references would indicate outlined fallback.
    """
    text = svg_path.read_text(encoding="utf-8", errors="replace")
    return len(re.findall(r"<text[^>]*>[^<]*<\/text>", text))


def _has_use_glyph_refs(svg_path: Path) -> bool:
    """matplotlib uses <use xlink:href='#GLYPH-...'/> pattern for editable text."""
    text = svg_path.read_text(encoding="utf-8", errors="replace")
    return bool(re.search(r"<use\s+[^>]*href=", text))


def main() -> int:
    failures: list[str] = []
    for journal in ("default", "nature", "acs", "rsc"):
        huitu.use_journal(journal)
        failures.extend(_check_rcparams(journal))
        svg, pdf = _render_demo(f"editable_text_{journal}")
        n_text = _grep_text_nodes(svg)
        if n_text == 0:
            failures.append(
                f"[{journal}] {svg} contains no <text> nodes — "
                "editable-text claim is FALSE"
            )
        # Editable text must also retain non-trivial text (at least the
        # axes labels, tick labels, title and legend ⇒ many nodes).
        if n_text < 5:
            failures.append(
                f"[{journal}] only {n_text} <text> nodes in {svg.name} "
                "(axes/tick/legend labels missing or partially outlined?)"
            )
        # PDF: just verify it was written and is non-empty.
        if not pdf.exists() or pdf.stat().st_size < 100:
            failures.append(f"[{journal}] {pdf} missing or too small")
        print(
            f"[{journal}] svg.fonttype={mpl.rcParams['svg.fonttype']!r} "
            f"pdf.fonttype={mpl.rcParams['pdf.fonttype']!r} "
            f"ps.fonttype={mpl.rcParams['ps.fonttype']!r} "
            f"<text> nodes in {svg.name}={n_text}"
        )

    # Now actively try to break things: user writes their own rcParams
    # after use_journal — does anything in huitu silently outline them?
    huitu.use_journal("nature")
    mpl.rcParams["svg.fonttype"] = "none"  # explicit
    fig, ax = plt.subplots(figsize=(3.0, 2.0))
    ax.set_title(r"Mixed math: $\alpha$ + ASCII")
    ax.set_xlabel("ASCII xlabel — with em–dash")
    svg = OUT / "editable_text_mixed_math.svg"
    fig.savefig(svg)
    plt.close(fig)
    n_text = _grep_text_nodes(svg)
    if n_text == 0:
        failures.append(f"mixed-math SVG {svg} has no <text> nodes")
    print(f"[mixed-math] <text> nodes in {svg.name}={n_text}")

    if failures:
        print("\nFAILED:")
        for f in failures:
            print(" -", f)
        return 1
    print("\nALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
