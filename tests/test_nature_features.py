"""Tests for the Nature-style features added in v0.5.0:

* editable-text rcParams (SVG/PDF/PS) survive every preset
* semantic role-based palette + ``role()`` lookup
* four archetype layout helpers
* anti-redundancy panel checker
* reviewer-risk checklist
"""

from __future__ import annotations

import io

import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest

import huitu


# ── 1. Editable text ────────────────────────────────────────────────────────

@pytest.mark.parametrize("preset", [
    "default", "nature", "science", "acs",
    "rsc",     "wiley",  "elsevier", "ieee",
])
def test_editable_text_in_every_preset(preset):
    """Every journal preset must leave SVG text as <text> nodes and embed
    TrueType in PDF/PS so reviewers can re-align labels."""
    huitu.use_journal(preset)
    assert mpl.rcParams["svg.fonttype"] == "none", preset
    assert mpl.rcParams["pdf.fonttype"] == 42, preset
    assert mpl.rcParams["ps.fonttype"]  == 42, preset


def test_saved_svg_contains_text_nodes(tmp_path):
    """A saved SVG should still carry <text ...> elements (not <path>)."""
    huitu.use_journal("nature")
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    ax.set_xlabel("x label")
    ax.set_ylabel("y label")
    out = tmp_path / "fig.svg"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    body = out.read_text()
    # If svg.fonttype were 'path', '<text' would not appear at all.
    assert "<text" in body, "SVG body has no <text> nodes — text is outlined"


# ── 2. Semantic palette + role() ────────────────────────────────────────────

def test_role_lookup_basic():
    assert huitu.role("hero")     == "#0F4D92"
    assert huitu.role("baseline") == "#B64342"
    assert huitu.role("positive") == "#2E9E44"
    assert huitu.role("negative") == "#E53935"
    assert huitu.role("neutral")  == "#767676"


def test_role_case_insensitive():
    assert huitu.role("HERO") == huitu.role("hero")


def test_role_unknown_raises():
    with pytest.raises(KeyError):
        huitu.role("not-a-role")


def test_semantic_palette_registered():
    assert "semantic" in huitu.list_palettes()
    huitu.use_palette("semantic")
    cycle = mpl.rcParams["axes.prop_cycle"].by_key()["color"]
    # Hero must lead the cycle.
    assert cycle[0].lower() == huitu.role("hero").lower()


# ── 3. Archetypes ───────────────────────────────────────────────────────────

def test_schematic_led_returns_named_dict():
    fig, axes = huitu.archetype.schematic_led(n_supports=3)
    assert set(axes) == {"hero", "supports"}
    assert len(axes["supports"]) == 3
    plt.close(fig)


def test_schematic_led_n_supports_variants():
    for n in (2, 4, 5):
        fig, axes = huitu.archetype.schematic_led(n_supports=n)
        assert len(axes["supports"]) == n
        plt.close(fig)


def test_dark_image_plate_strips_ticks_and_spines():
    fig, grid = huitu.archetype.dark_image_plate(rows=2, cols=3)
    for row in grid:
        for ax in row:
            assert ax.get_xticks().size == 0
            assert ax.get_yticks().size == 0
            assert all(not s.get_visible() for s in ax.spines.values())
    plt.close(fig)


def test_clinical_triptych_columns_parallel():
    fig, axes = huitu.archetype.clinical_triptych(n_cols=3)
    assert set(axes) == {"top", "mid", "bot"}
    assert len(axes["top"]) == len(axes["mid"]) == len(axes["bot"]) == 3
    plt.close(fig)


def test_asymmetric_hero_has_six_named_panels():
    fig, axes = huitu.archetype.asymmetric_hero()
    assert set(axes) == {"a", "b", "c", "d", "e", "f"}
    # Hero panel `e` must be the tallest (spans all 3 rows).
    fig.canvas.draw()
    heights = {k: ax.get_window_extent().height for k, ax in axes.items()}
    assert heights["e"] == max(heights.values()), heights
    plt.close(fig)


# ── 4. Anti-redundancy ──────────────────────────────────────────────────────

def test_redundancy_clean_figure():
    """Three panels with proper Overview→Deviation→Relationship climb."""
    issues = huitu.check_redundancy([
        {"id": "a", "question": "What is the composition?",
         "encoding": "stacked_bar",     "level": "overview"},
        {"id": "b", "question": "What is atypical per group?",
         "encoding": "z_score_heatmap", "level": "deviation"},
        {"id": "c", "question": "How do x and y co-vary?",
         "encoding": "bubble_scatter",  "level": "relationship"},
    ])
    assert issues == [], issues


def test_redundancy_same_question_warns():
    issues = huitu.check_redundancy([
        {"id": "a", "question": "What is the composition?", "encoding": "stacked_bar"},
        {"id": "b", "question": "What is the composition?", "encoding": "pie"},
    ])
    assert any(i.severity == "warn" and "same scientific question" in i.message
               for i in issues)


def test_redundancy_same_data_slice_warns():
    issues = huitu.check_redundancy([
        {"id": "a", "question": "Q1?", "encoding": "stacked_bar", "data": "composition"},
        {"id": "b", "question": "Q2?", "encoding": "heatmap",     "data": "composition"},
    ])
    assert any(i.severity == "warn" and "same data slice" in i.message
               for i in issues)


def test_redundancy_pie_plus_stacked_warns():
    issues = huitu.check_redundancy([
        {"id": "a", "question": "Q1?", "encoding": "pie"},
        {"id": "b", "question": "Q2?", "encoding": "stacked_bar"},
    ])
    assert any("pie + stacked bar" in i.message for i in issues)


def test_redundancy_two_ranked_bars_warns():
    issues = huitu.check_redundancy([
        {"id": "a", "question": "Q1?", "encoding": "ranked_bar"},
        {"id": "b", "question": "Q2?", "encoding": "ranked_bar"},
    ])
    assert any("ranked-bar" in i.message for i in issues)


def test_redundancy_print_report_does_not_raise(capsys):
    huitu.print_redundancy_report([
        {"id": "a", "question": "Q1?", "encoding": "stacked_bar", "level": "overview"},
        {"id": "b", "question": "Q2?", "encoding": "scatter",     "level": "relationship"},
    ])
    out = capsys.readouterr().out
    assert "panels" in out.lower() or "ok" in out.lower()


# ── 5. Reviewer-risk checklist ──────────────────────────────────────────────

def test_checklist_pass_when_required_present():
    rep = huitu.reviewer_checklist(
        figure={
            "core_conclusion": "X reduces Y by Z %",
            "final_size": "183 mm × 130 mm",
        },
        quantitative={
            "n": "n=12 cells / group",
            "biological_replicates": 3,
            "center": "median",
            "spread": "IQR",
            "test": "two-sided Wilcoxon",
            "source_data": "fig3.csv",
        },
        print_report=False,
    )
    assert rep["pass"] is True
    assert rep["n_required_missing"] == 0


def test_checklist_fails_when_required_missing():
    rep = huitu.reviewer_checklist(
        figure={"core_conclusion": "X reduces Y"},   # missing final_size
        quantitative={"n": "12"},                    # missing 4 required fields
        print_report=False,
    )
    assert rep["pass"] is False
    assert rep["n_required_missing"] >= 1


def test_checklist_image_section_only_when_passed():
    rep = huitu.reviewer_checklist(
        figure={"core_conclusion": "X", "final_size": "89 mm"},
        quantitative={"n": "1", "biological_replicates": 1, "center": "mean",
                      "spread": "SD", "test": "t-test", "source_data": "f.csv"},
        print_report=False,
    )
    section_names = [s["name"] for s in rep["sections"]]
    assert "Image" not in section_names
    assert "ML / model" not in section_names


def test_checklist_machine_learning_section():
    rep = huitu.reviewer_checklist(
        figure={"core_conclusion": "Model M outperforms B by 5 %",
                "final_size": "183 mm"},
        quantitative={"n": "5 seeds", "biological_replicates": "n/a",
                      "center": "mean", "spread": "±SD", "test": "permutation",
                      "source_data": "results.csv"},
        machine_learning={
            "split": "70/15/15 by patient",
            "seeds": 5,
            "metric": "AUROC at fixed threshold 0.5",
            "baseline": "ResNet-50 published v1.2",
        },
        print_report=False,
    )
    ml_section = next(s for s in rep["sections"] if s["name"] == "ML / model")
    statuses = {row[0]: row[2] for row in ml_section["rows"]}
    assert statuses["split"]    == "ok"
    assert statuses["metric"]   == "ok"
    assert statuses["baseline"] == "ok"


def test_checklist_print_does_not_raise(capsys):
    huitu.reviewer_checklist(
        figure={"core_conclusion": "ok"},
        quantitative={"n": "5"},
    )
    out = capsys.readouterr().out
    assert "checklist" in out.lower()
