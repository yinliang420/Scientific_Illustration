"""Test 5: Reviewer-risk checklist — ``huitu.reviewer_checklist``.

Scenarios:

  * **PASS** — every required field across Figure + Quantitative is filled.
  * **FAIL** — at least one required field is empty / missing.
  * **ML-only** — pass machine_learning data; ML required fields gate the
    ``pass`` bool.
  * **Image-only** — pass image data; image required fields gate ``pass``.
  * **All four sections together** — Figure + Quantitative + Image + ML
    metadata, all complete; expect PASS.
  * **Edge cases** — None for a section, empty dict, ``print_report=False``,
    long values truncated cleanly, value=0 (falsy but valid).
  * Capture printed output and confirm it actually formats sections.
"""

from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

import huitu

OUT = Path(__file__).resolve().parent / "output"
OUT.mkdir(exist_ok=True)


COMPLETE_FIGURE = {
    "core_conclusion": "Treatment X reduces tumor volume by 60% over 12 weeks.",
    "archetype": "schematic-led",
    "final_size": "183 mm",
    "editable_text": True,
    "color_grayscale_safe": True,
}

COMPLETE_QUANT = {
    "n": "n=12 mice / group, 3 biological replicates",
    "biological_replicates": 3,
    "technical_replicates": 3,
    "center": "median",
    "spread": "IQR",
    "test": "two-sided Wilcoxon rank-sum",
    "correction": "BH-FDR",
    "p_value_format": "exact",
    "source_data": "fig3_source_data.csv",
}

COMPLETE_IMAGE = {
    "scale_bar": "10 µm white bar, bottom-right",
    "raw_file": "raw_data/sample_001.czi (DOI: 10.1234/foo)",
    "crop": "1024×1024 ROI, no local crops",
    "brightness_contrast": "Linear stretch only, no gamma adjust",
    "pseudo_color": "GFP -> cyan, mCherry -> magenta",
    "stitching": "Fiji Grid/Collection plugin, linear blend seams",
    "reuse": "Sample shown also in Fig 2c (different ROI)",
}

COMPLETE_ML = {
    "split": "70/15/15 patient-disjoint",
    "seeds": "5 random restarts",
    "metric": "AUROC of recurrence-vs-no-recurrence",
    "ci": "Bootstrap 95% CI, 1000 samples",
    "baseline": "logreg (scikit-learn 1.4.0, default L2, C=1.0)",
}


def _capture(fn, *args, **kwargs):
    buf = io.StringIO()
    with redirect_stdout(buf):
        result = fn(*args, **kwargs)
    return result, buf.getvalue()


def main() -> int:
    failures: list[str] = []
    log = OUT / "reviewer_log.txt"
    log_lines: list[str] = []

    def _log(s: str) -> None:
        print(s)
        log_lines.append(s)

    # 1. PASS — Figure + Quantitative complete.
    rep, out = _capture(
        huitu.reviewer_checklist,
        figure=COMPLETE_FIGURE,
        quantitative=COMPLETE_QUANT,
    )
    if not rep["pass"]:
        failures.append(
            f"complete figure+quant did NOT pass; "
            f"required missing={rep['n_required_missing']}"
        )
    if "PASS" not in out:
        failures.append(
            f"complete figure+quant report header missing PASS: {out[:200]!r}"
        )
    log_lines.append("=== complete figure+quant ===")
    log_lines.append(out)

    # 2. FAIL — drop one required field from Quantitative ('source_data').
    quant_no_source = dict(COMPLETE_QUANT)
    quant_no_source.pop("source_data")
    rep, out = _capture(
        huitu.reviewer_checklist,
        figure=COMPLETE_FIGURE,
        quantitative=quant_no_source,
    )
    if rep["pass"]:
        failures.append("missing source_data did NOT trigger FAIL")
    if "FAIL" not in out:
        failures.append("missing source_data report header missing FAIL")
    if rep["n_required_missing"] != 1:
        failures.append(
            f"expected exactly 1 required missing; got {rep['n_required_missing']}"
        )
    log_lines.append("=== missing source_data ===")
    log_lines.append(out)

    # 3. ML-only — only ML section provided. The function ALWAYS includes
    #    Figure + Quantitative as default sections (they default to {}), so
    #    even with ML metadata the checklist will FAIL if those defaults
    #    require fields. This is a useful test: confirm the documented
    #    behaviour matches what's coded.
    rep, out = _capture(
        huitu.reviewer_checklist,
        machine_learning=COMPLETE_ML,
    )
    if rep["pass"]:
        failures.append(
            "ML-only call passed even though Figure + Quantitative defaults "
            "have unmet required fields — silent free pass"
        )
    if "ML / model" not in out:
        failures.append("ML section header not in printed output")
    log_lines.append("=== ML-only ===")
    log_lines.append(out)

    # 4. Image-only.
    rep, out = _capture(
        huitu.reviewer_checklist,
        image=COMPLETE_IMAGE,
    )
    if "Image" not in out:
        failures.append("Image section header not in printed output")
    log_lines.append("=== image-only ===")
    log_lines.append(out)

    # 5. All four sections complete — should PASS.
    rep, out = _capture(
        huitu.reviewer_checklist,
        figure=COMPLETE_FIGURE,
        quantitative=COMPLETE_QUANT,
        image=COMPLETE_IMAGE,
        machine_learning=COMPLETE_ML,
    )
    if not rep["pass"]:
        failures.append(
            "all four sections complete did NOT pass; "
            f"required missing={rep['n_required_missing']}, "
            f"recommended missing={rep['n_recommended_missing']}"
        )
    for sec in ("Figure", "Quantitative", "Image", "ML / model"):
        if sec not in out:
            failures.append(f"section {sec!r} not in printed all-four output")
    log_lines.append("=== all four complete ===")
    log_lines.append(out)

    # 6. Edge: print_report=False suppresses output.
    rep, out = _capture(
        huitu.reviewer_checklist,
        figure=COMPLETE_FIGURE,
        quantitative=COMPLETE_QUANT,
        print_report=False,
    )
    if out.strip():
        failures.append(
            f"print_report=False still printed: {out!r}"
        )

    # 7. Edge: pass None for everything — Figure + Quantitative defaults
    # apply ⇒ many missing required ⇒ FAIL.
    rep, out = _capture(huitu.reviewer_checklist)
    if rep["pass"]:
        failures.append(
            "all-None call passed — empty defaults should fail required fields"
        )

    # 8. Edge: required field present but value=0 (falsy).
    quant_zero = dict(COMPLETE_QUANT, n=0, biological_replicates=0)
    rep, _ = _capture(
        huitu.reviewer_checklist,
        figure=COMPLETE_FIGURE,
        quantitative=quant_zero,
        print_report=False,
    )
    # The implementation treats value in (None, "", []) as missing, so 0 is
    # accepted. Verify this matches our expectation.
    if not rep["pass"]:
        failures.append(
            "value=0 (an explicit zero) was rejected as missing — "
            "should be accepted as a valid 'provided' marker"
        )

    # 9. Edge: very long source_data string — should be truncated to <= 60 ch
    #    in the printed table per _print_checklist (line 410).
    long_path = "/very/" + ("long/" * 50) + "data.csv"
    quant_long = dict(COMPLETE_QUANT, source_data=long_path)
    _, out = _capture(
        huitu.reviewer_checklist,
        figure=COMPLETE_FIGURE,
        quantitative=quant_long,
    )
    # Expect the printed line to be truncated with "..." somewhere.
    if long_path in out:
        failures.append(
            "long source_data not truncated in printed report — line will wrap"
        )

    # 10. machine_learning={} is an explicit opt-in: the ML section must render
    #     even when empty so required-field gaps are flagged.
    rep, out = _capture(
        huitu.reviewer_checklist,
        figure=COMPLETE_FIGURE,
        quantitative=COMPLETE_QUANT,
        machine_learning={},
    )
    if "ML / model" not in out:
        failures.append(
            "passing machine_learning={} did NOT render ML section — "
            "explicit opt-in must run the ML checklist (review.py)"
        )

    # 11. Bug-hunt: editable_text=True is documented as 'recommended' but
    # huitu.use_journal already enforces svg.fonttype='none'. The checklist
    # should not be flagged as missing-recommended just because the user
    # didn't pass it. Confirm: when editable_text is omitted, the report
    # marks it 'missing_recommended', which is a tiny ergonomics issue:
    # the lib already enforces it, so the user shouldn't have to assert it.
    fig_no_edit = dict(COMPLETE_FIGURE)
    fig_no_edit.pop("editable_text")
    rep, _ = _capture(
        huitu.reviewer_checklist,
        figure=fig_no_edit,
        quantitative=COMPLETE_QUANT,
        print_report=False,
    )
    found_missing_edit = False
    for sec in rep["sections"]:
        if sec["name"] != "Figure":
            continue
        for key, label, status, *_ in sec["rows"]:
            if key == "editable_text" and status == "missing_recommended":
                found_missing_edit = True
    if not found_missing_edit:
        # If huitu later auto-fills this, fine — but right now we expect it
        # to be missing.
        _log(
            "editable_text NOT auto-filled — user must assert it manually "
            "even though use_journal already sets svg.fonttype='none'."
        )

    log.write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    if failures:
        print("\nFAILED:")
        for f in failures:
            print(" -", f)
        return 1
    print("\nALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
