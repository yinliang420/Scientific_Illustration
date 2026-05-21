"""Shared helpers for the v0.6 polish test suite.

Each polish test calls ``case(NN, desc, predicate)`` from this module so
``pytest -v`` and ``bash tests/polish/run_all.sh`` both produce the same
human-readable ``[PASS] case_NN <desc>`` / ``[FAIL] ...`` lines that AGENT B
(Reviewer) and AGENT C (Fixer) can grep for.

Pure pytest fixtures live here; no module-level imports of huitu so individual
test files keep their own ``use_journal()`` state pristine.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Callable, Iterable

import matplotlib

os.environ.setdefault("MPLBACKEND", "Agg")
matplotlib.use("Agg", force=True)


# ── Sample data fixture ────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLE = ROOT / "examples" / "sample_data"


def sample(name: str) -> str:
    """Return absolute path to a file under examples/sample_data/."""
    p = SAMPLE / name
    if not p.exists():
        raise FileNotFoundError(f"missing sample data file: {p}")
    return str(p)


# ── Reporter shim ───────────────────────────────────────────────────────────
#
# Many test cases follow the pattern::
#
#     ok, why = check_something(...)
#     report(NN, "description", ok, why)
#
# Inside pytest, a failure is signalled via ``assert ok, why`` immediately
# after; the print line is for the bash driver.
def report(num: int, desc: str, ok: bool, why: str = "") -> None:
    tag = "[PASS]" if ok else "[FAIL]"
    line = f"{tag} case_{num:02d} {desc}"
    if not ok and why:
        line += f" — {why}"
    print(line)


# ── SVG parsing helpers ────────────────────────────────────────────────────
SVG_NS = "{http://www.w3.org/2000/svg}"


def parse_svg(path: str | Path):
    """Return ``ElementTree`` for an SVG file.

    Uses stdlib ``xml.etree.ElementTree`` so the test suite has no lxml
    dependency. Returns the root element.
    """
    import xml.etree.ElementTree as ET

    tree = ET.parse(str(path))
    return tree.getroot()


def svg_text_nodes(root) -> list:
    """All ``<text>`` elements (including nested ``<tspan>`` parents)."""
    return root.findall(f".//{SVG_NS}text")


def svg_path_count(root) -> int:
    """Count ``<path>`` elements — proxy for "how outline-heavy the file is"."""
    return len(root.findall(f".//{SVG_NS}path"))


def svg_text_to_string(root) -> str:
    """Concatenate the visible text of every ``<text>``/``<tspan>``."""
    out = []
    for t in svg_text_nodes(root):
        out.append("".join(t.itertext()))
    return "\n".join(out)


def svg_font_families(root) -> set[str]:
    """Distinct ``font-family`` values appearing inside ``<text>``/``<tspan>``."""
    fams: set[str] = set()
    pat = re.compile(r"font-family:\s*([^;\"]+)")
    for t in svg_text_nodes(root):
        sty = t.get("style", "") or ""
        m = pat.search(sty)
        if m:
            fams.add(m.group(1).strip())
        for span in t.findall(f".//{SVG_NS}tspan"):
            sty = span.get("style", "") or ""
            m = pat.search(sty)
            if m:
                fams.add(m.group(1).strip())
    return fams


# ── Geometry helpers (pixel-level overlap) ─────────────────────────────────
def bbox_overlaps(a, b) -> bool:
    """Return True if two matplotlib Bbox-like objects overlap.

    Works on any object with ``x0/x1/y0/y1`` attributes (Text, Annotation,
    Line2D after ``get_window_extent``, etc.).
    """
    return not (a.x1 < b.x0 or b.x1 < a.x0 or a.y1 < b.y0 or b.y1 < a.y0)


def bbox_inside(inner, outer, pad_px: float = 0.0) -> bool:
    """Is ``inner`` fully inside ``outer`` (with optional padding)?"""
    return (
        inner.x0 >= outer.x0 - pad_px
        and inner.x1 <= outer.x1 + pad_px
        and inner.y0 >= outer.y0 - pad_px
        and inner.y1 <= outer.y1 + pad_px
    )


def fig_extent_after_draw(fig):
    """Force a draw and return the figure's bbox in display coords."""
    fig.canvas.draw()
    return fig.get_window_extent()


def all_text_extents(ax) -> list:
    """All ``ax.texts`` + tick labels + xlabel/ylabel/title bboxes."""
    ax.figure.canvas.draw()
    bbs = [t.get_window_extent() for t in ax.texts]
    for lbl in (
        ax.xaxis.label,
        ax.yaxis.label,
        ax.title,
        *ax.get_xticklabels(),
        *ax.get_yticklabels(),
    ):
        try:
            bbs.append(lbl.get_window_extent())
        except Exception:
            continue
    return bbs


def line_text_overlap(ax, line, text) -> bool:
    """Return True if a Line2D's window-extent bbox overlaps a Text bbox.

    Caveat: ``Line2D.get_window_extent`` reports the axis-aligned bbox of the
    entire polyline, not the actual stroke. We still use it as a coarse "this
    line cuts through the label region" detector — which is exactly what the
    user complained about for Pourbaix.
    """
    ax.figure.canvas.draw()
    return bbox_overlaps(line.get_window_extent(), text.get_window_extent())


__all__ = [
    "ROOT",
    "SAMPLE",
    "sample",
    "report",
    "parse_svg",
    "svg_text_nodes",
    "svg_path_count",
    "svg_text_to_string",
    "svg_font_families",
    "bbox_overlaps",
    "bbox_inside",
    "fig_extent_after_draw",
    "all_text_extents",
    "line_text_overlap",
]
