"""Simulated activation tests — would Claude Code load `huitu` on each query?

We can't talk to a live Claude Code runtime from pytest, so we approximate
its activation logic: a query "activates" a skill when at least one
non-trivial token from the user's request appears in the skill's
``description`` field (or its synonym list).

These tests are not a perfect proxy, but they catch the most common
regression — pruning a trigger keyword from the description and then
finding that "画 XRD 图" no longer activates the skill.

Sample queries cover four registers:

1. English, technical wording ("plot an XRD pattern").
2. English, colloquial / verb-leading ("I need a CV figure").
3. Chinese, technical wording ("画一张 CV 曲线").
4. Chinese, colloquial / verb-only ("帮我出一张 Nature 风格的图").
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
SKILL_PATH = ROOT / "SKILL.md"


def _description() -> str:
    """Pull out the skill's frontmatter description (folded scalar)."""
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert text.startswith("---\n"), "SKILL.md missing frontmatter"
    closing = text.index("\n---\n", 4)
    block = text[4:closing]
    m = re.search(
        r"^description:\s*>-?\s*\n((?:[ \t]+.*\n)+)", block, flags=re.MULTILINE
    )
    assert m, "frontmatter has no `description: >-` block"
    return " ".join(ln.strip() for ln in m.group(1).splitlines()).strip()


def _tokenize(query: str) -> list[str]:
    """Split a user query into matchable tokens.

    English: lowercased words ≥ 3 chars OR uppercase acronyms (CV, XRD…).
    Chinese: each CJK run is expanded into every 2-, 3-, and 4-char
    contiguous substring, so "画态密度图" yields {"画态","态密","密度","度图",
    "画态密","态密度","密度图","画态密度","态密度图"} — and "态密度" matches
    the description without needing exact run equality.
    """
    # Latin tokens: words ≥ 3 chars OR all-caps acronyms (2+ chars).
    latin = re.findall(r"[A-Za-z][A-Za-z/\-]+", query)
    short_acronyms = re.findall(r"\b[A-Z]{2,}(?:[/\-][A-Z]+)?\b", query)

    tokens: set[str] = set()
    for t in latin:
        if len(t) >= 3 or t.isupper():
            tokens.add(t.lower() if not t.isupper() else t)
    tokens.update(short_acronyms)

    # CJK: expand each contiguous run into every 2-, 3-, 4-char substring.
    for run in re.findall(r"[一-鿿]+", query):
        for size in (2, 3, 4):
            for i in range(len(run) - size + 1):
                tokens.add(run[i : i + size])
        # Keep the full run too (some triggers are exact, e.g. "材料论文配图").
        tokens.add(run)

    return [t for t in tokens if t]


def _matches(query: str, description: str) -> tuple[bool, list[str]]:
    """Return (would_activate, list_of_matched_tokens).

    A query activates the skill if any token appears in the description.
    Matching is case-insensitive for Latin, exact for CJK.
    """
    desc_lower = description.lower()
    hits: list[str] = []
    for tok in _tokenize(query):
        if tok.lower() in desc_lower or tok in description:
            hits.append(tok)
    return (len(hits) > 0, hits)


# ── English queries that MUST activate ─────────────────────────────────────
_ENGLISH_QUERIES_POSITIVE = [
    "Plot an XRD pattern from data.txt",
    "Draw a CV curve at 5 mV/s",
    "make a multi-panel Nature-style figure",
    "BET isotherm with linear plot",
    "render an EIS Nyquist plot",
    "I need a band structure from my VASP run",
    "show me a Pourbaix diagram",
    "generate a Tafel slope plot",
    "make me a dQ/dV from this GCD",
    "build a multi-figure PDF report for my paper",
    "run the anti-redundancy checker on these panels",
    "plot a Raman spectrum",
    "TGA / DSC plot, journal-ready output",
    "I want an editable SVG for Illustrator",
]


# ── Chinese queries that MUST activate ─────────────────────────────────────
_CHINESE_QUERIES_POSITIVE = [
    "帮我画一张 XRD 图",
    "绘制 CV 曲线",
    "出一张 Nature 风格的图",
    "画 BET 等温线",
    "做一张 EIS 图",
    "渲染能带结构",
    "画态密度图",
    "Pourbaix 相图怎么画",
    "Tafel 斜率",
    "dQ/dV 曲线",
    "多图组合 PDF",
    "审稿清单帮我跑一下",
    "材料论文配图怎么出",
    "表征图 Nature 风格",
]


# ── Negative queries that should NOT activate (single trivial token only) ──
_NEGATIVE_QUERIES = [
    "what's the weather today",
    "summarise this email for me",
    "翻译一下这段话",   # translation, no plotting verb / measurement
    "explain how diffusion works",
]


@pytest.mark.parametrize("query", _ENGLISH_QUERIES_POSITIVE)
def test_english_query_activates(query):
    desc = _description()
    ok, hits = _matches(query, desc)
    assert ok, f"English query did NOT activate: {query!r}"
    # Surface what matched (helps debugging if a future edit drops a token).
    print(f"\n  query={query!r}\n  matched={hits}")


@pytest.mark.parametrize("query", _CHINESE_QUERIES_POSITIVE)
def test_chinese_query_activates(query):
    desc = _description()
    ok, hits = _matches(query, desc)
    assert ok, f"Chinese query did NOT activate: {query!r}"
    print(f"\n  query={query!r}\n  matched={hits}")


@pytest.mark.parametrize("query", _NEGATIVE_QUERIES)
def test_negative_query_does_not_falsely_activate(query):
    """Ensure the description isn't so broad that unrelated queries match.

    We accept up to 1 spurious common-noun match (e.g. "PL" appearing inside
    a longer word), but the skill shouldn't fire on every query.
    """
    desc = _description()
    ok, hits = _matches(query, desc)
    assert not ok or len(hits) <= 1, (
        f"Negative query falsely activated with too many hits: "
        f"{query!r}, matched={hits}"
    )
