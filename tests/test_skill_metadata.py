"""Verify SKILL.md is a well-formed Claude Code skill, not just docs.

Three guarantees this file enforces (so it can be checked in CI):

1. ``SKILL.md`` starts with valid YAML frontmatter (``---`` block).
2. Frontmatter has ``name`` and ``description`` fields, both non-empty.
3. The ``description`` field actually mentions a broad set of trigger
   keywords in **both English and Chinese**, so Claude Code's
   description-matcher reliably activates the skill regardless of which
   language the user types in.

These tests would have caught the v0.5-era SKILL.md, which had no
frontmatter at all and would never have auto-activated.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
SKILL_PATH = ROOT / "SKILL.md"


def _frontmatter() -> dict:
    """Parse the YAML frontmatter block at the top of SKILL.md."""
    text = SKILL_PATH.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise AssertionError("SKILL.md must start with a `---` frontmatter block")
    # Locate the closing `---` on its own line.
    closing = text.index("\n---\n", 4)
    block = text[4:closing]

    # Minimal YAML parser — we only need name + description (folded scalar).
    try:
        import yaml  # type: ignore
        return yaml.safe_load(block) or {}
    except ImportError:
        # Fallback: hand-parse the two fields we care about.
        out: dict[str, str] = {}
        # name: <value>
        m = re.search(r"^name:\s*(.+?)\s*$", block, flags=re.MULTILINE)
        if m:
            out["name"] = m.group(1).strip()
        # description: >- followed by indented continuation lines.
        d = re.search(
            r"^description:\s*>-?\s*\n((?:[ \t]+.*\n)+)", block, flags=re.MULTILINE
        )
        if d:
            # Strip leading whitespace from each line, join into one blob.
            lines = [ln.strip() for ln in d.group(1).splitlines()]
            out["description"] = " ".join(lines).strip()
        return out


# ── 1. Structural checks ────────────────────────────────────────────────────

def test_skill_has_frontmatter_block():
    """SKILL.md must open with `---` so Claude Code recognises it as a skill."""
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert text.startswith("---\n"), (
        "SKILL.md is missing the opening `---` frontmatter delimiter — "
        "without it Claude Code will not auto-activate this skill."
    )


def test_frontmatter_has_name_and_description():
    fm = _frontmatter()
    assert "name" in fm and fm["name"], "frontmatter must include a non-empty `name`"
    assert "description" in fm and fm["description"], (
        "frontmatter must include a non-empty `description` "
        "— this is what Claude Code matches user queries against"
    )


def test_name_matches_package():
    fm = _frontmatter()
    assert fm["name"] == "huitu", (
        f"skill name should match the package name; got {fm['name']!r}"
    )


def test_description_length_reasonable():
    """A skill description that's too short can't carry enough trigger
    keywords; one that's too long bloats every Claude Code prompt that
    sees the skill catalogue. 400–2500 chars is the productive band."""
    fm = _frontmatter()
    desc = fm["description"]
    assert 400 <= len(desc) <= 2500, (
        f"description length {len(desc)} chars is outside the 400–2500 band"
    )


# ── 2. Trigger coverage — English + Chinese must both work ──────────────────

# Core English triggers — verb + plot family. Skipping any of these means
# the skill won't activate on common English queries.
_REQUIRED_ENGLISH = [
    # measurement families
    "XRD", "XPS", "Raman", "FTIR", "UV-Vis", "PL", "TGA",
    "Rietveld", "BET", "CV", "GCD", "EIS", "Tafel", "dQ/dV",
    "band structure", "DOS", "Pourbaix", "phase diagram",
    "crystal structure",
    # general families
    "bar", "scatter", "heatmap",
    # workflow surface
    "Nature-style", "multi-panel", "PDF report", "checklist",
    # outputs
    "journal-ready", "SVG", "PDF",
    # verbs
    "plot", "draw",
]

# Core Chinese triggers — required for activation on CN queries. If any of
# these are missing, Chinese users get no auto-activation.
_REQUIRED_CHINESE = [
    "画", "绘制", "出图",
    "XRD", "CV", "EIS",
    "BET",
    "dQ/dV",
    "能带", "态密度", "相图",
    "期刊", "Nature",
    "材料论文配图", "表征图",
]


@pytest.mark.parametrize("trigger", _REQUIRED_ENGLISH)
def test_description_covers_english_triggers(trigger):
    """Every required English trigger must appear in the description."""
    fm = _frontmatter()
    desc = fm["description"]
    assert trigger.lower() in desc.lower(), (
        f"English trigger {trigger!r} missing from SKILL.md description — "
        f"queries containing it may not auto-activate the skill"
    )


@pytest.mark.parametrize("trigger", _REQUIRED_CHINESE)
def test_description_covers_chinese_triggers(trigger):
    """Every required Chinese trigger must appear in the description."""
    fm = _frontmatter()
    desc = fm["description"]
    assert trigger in desc, (
        f"Chinese trigger {trigger!r} missing from SKILL.md description — "
        f"Chinese users may not get auto-activation"
    )


# ── 3. Negative-list — explicit non-activation cases ────────────────────────

# The description should also call out things NOT covered, so Claude Code's
# matcher knows when to decline. These should also appear in the doc body.
_NEGATIVE_KEYWORDS = ["dashboard", "plotly", "GIS"]


@pytest.mark.parametrize("term", _NEGATIVE_KEYWORDS)
def test_negative_keywords_mentioned_somewhere(term):
    """The SKILL.md body (not necessarily frontmatter) should mention what
    NOT to use the skill for, so the matcher can distinguish."""
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert term.lower() in text.lower(), (
        f"negative-list keyword {term!r} missing from SKILL.md — "
        f"the 'When NOT to load' section should mention it"
    )


# ── 4. "When to use" / "When NOT" structural sections ──────────────────────

def test_when_to_use_section_present():
    """The body must have a `## When to use this skill` heading so
    Claude Code can surface it in the activation reasoning."""
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert "## When to use this skill" in text, (
        "SKILL.md must have a `## When to use this skill` section"
    )


def test_when_not_to_load_section_present():
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert "## When NOT to load" in text, (
        "SKILL.md must have a `## When NOT to load` section to bound activation"
    )
