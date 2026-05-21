"""Pre-submission QA workflow: anti-redundancy check + reviewer checklist.

Walks through the two QA helpers huitu ships for the "before you submit"
moment — `check_redundancy` audits a multi-panel plan against the
Overview → Deviation → Relationship hierarchy; `reviewer_checklist` flags
missing statistics / source-data / image-integrity fields a Nature-tier
reviewer is going to ask about.

Run from repo root::

    python examples/reviewer_checklist.py
"""

import huitu


# ── 1. Anti-redundancy on a 3-panel plan ────────────────────────────────────
print("=" * 60)
print("1. check_redundancy — 3-panel multi-figure audit")
print("=" * 60)

panels = [
    {"id": "a", "question": "What is the composition?",
     "encoding": "stacked_bar", "level": "overview"},
    {"id": "b", "question": "What is atypical per group?",
     "encoding": "z_score_heatmap", "level": "deviation"},
    {"id": "c", "question": "How do tumour and immune % co-vary?",
     "encoding": "bubble_scatter", "level": "relationship"},
]
huitu.print_redundancy_report(panels)

print()
print("Same plan but with two panels asking the same question — should warn:")
panels_dup = panels + [
    {"id": "d", "question": "What is the composition?",
     "encoding": "pie", "level": "overview"},
]
huitu.print_redundancy_report(panels_dup)


# ── 2. Pre-submission reviewer checklist ───────────────────────────────────
print()
print("=" * 60)
print("2. reviewer_checklist — complete and intentionally-incomplete examples")
print("=" * 60)

print("\n--- A complete figure that should PASS:")
huitu.reviewer_checklist(
    figure={
        "core_conclusion": "Cu-doping raises MnO₂ capacity by 32 % at 1 C",
        "archetype": "schematic-led",
        "final_size": "183 mm × 130 mm",
    },
    quantitative={
        "n": "n=12 cells / group",
        "biological_replicates": 3,
        "center": "median",
        "spread": "IQR",
        "test": "two-sided Wilcoxon",
        "source_data": "fig3_source.csv",
    },
    image={
        "scale_bar": "50 µm",
        "raw_file": "raw/fig3a.tif",
    },
)

print("\n--- An ML-results figure with all four sections:")
huitu.reviewer_checklist(
    figure={
        "core_conclusion": "Model M outperforms baseline B by 5 % AUROC",
        "final_size": "183 mm",
    },
    quantitative={
        "n": "5 seeds",
        "biological_replicates": "n/a",
        "center": "mean",
        "spread": "±SD",
        "test": "permutation",
        "source_data": "results.csv",
    },
    machine_learning={
        "split": "70/15/15 by patient",
        "seeds": 5,
        "metric": "AUROC at fixed threshold 0.5",
        "baseline": "ResNet-50 v1.2",
    },
)
