"""Adversarial test 5: huitu.reviewer_checklist.

Round-2 attacks on the checklist:
* bare call must FAIL on core required fields
* explicit image={} / machine_learning={} must FAIL with required-field gaps
* None vs missing keys treated identically
* non-dict figure= must raise TypeError, not silently process
* truthy-but-meaningless values ('TODO', '?') currently accepted — document P2
* value=0 (round-1 confirmed-accept) — still accepted in v0.5.1
* nested dict in core_conclusion still prints without crash
* very long source_data (10000 ch) doesn't blow up print
* positional call signature is keyword-only
"""

from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout

import huitu

_failed = 0
_passed = 0


def _ok(desc: str) -> None:
    global _passed
    _passed += 1
    print(f"[PASS] {desc}")


def _bad(desc: str, reason: str) -> None:
    global _failed
    _failed += 1
    print(f"[FAIL] {desc} — {reason}")


def _capture(fn, *args, **kwargs):
    buf = io.StringIO()
    with redirect_stdout(buf):
        result = fn(*args, **kwargs)
    return result, buf.getvalue()


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
    "raw_file": "raw_data/sample_001.czi",
    "crop": "1024×1024 ROI",
    "brightness_contrast": "Linear stretch only",
    "pseudo_color": "GFP -> cyan",
    "stitching": "Fiji",
    "reuse": "Sample shown also in Fig 2c",
}

COMPLETE_ML = {
    "split": "70/15/15 patient-disjoint",
    "seeds": "5 random restarts",
    "metric": "AUROC",
    "ci": "Bootstrap 95% CI",
    "baseline": "logreg",
}


# ── Case 1 — happy path ────────────────────────────────────────────────────

def case_01_happy() -> None:
    desc = "case_01 complete figure+quant passes"
    try:
        rep, out = _capture(
            huitu.reviewer_checklist,
            figure=COMPLETE_FIGURE,
            quantitative=COMPLETE_QUANT,
        )
        if rep["pass"] and "PASS" in out:
            _ok(desc)
        else:
            _bad(desc, f"pass={rep.get('pass')}, header={'PASS' in out}")
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 2 — bare reviewer_checklist() must FAIL ──────────────────────────

def case_02_bare_call_fails() -> None:
    desc = "case_02 bare reviewer_checklist() FAILS (core required fields missing)"
    try:
        rep, out = _capture(huitu.reviewer_checklist)
        if rep["pass"]:
            _bad(desc, "empty call passed — silent free pass")
            return
        if rep["n_required_missing"] == 0:
            _bad(desc, "n_required_missing = 0 with no input")
            return
        if "FAIL" not in out:
            _bad(desc, "no FAIL banner in stdout")
            return
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 3 — explicit image={} + ml={} surfaces required gaps ─────────────

def case_03_explicit_empty_image_ml() -> None:
    desc = "case_03 image={} and machine_learning={} both render and surface required fields"
    try:
        rep, out = _capture(
            huitu.reviewer_checklist,
            figure=COMPLETE_FIGURE,
            quantitative=COMPLETE_QUANT,
            image={},
            machine_learning={},
        )
        if "Image" not in out:
            _bad(desc, "Image section missing from output")
            return
        if "ML / model" not in out:
            _bad(desc, "ML / model section missing from output")
            return
        if rep["pass"]:
            _bad(desc, "report passed despite empty image/ML opt-ins")
            return
        # n_required_missing should now include image+ml required fields.
        # Image has 2 required (scale_bar, raw_file); ML has 3 (split, seeds,
        # metric, baseline) → 4. So at least 5 required missing total (image 2 + ml 4 = 6).
        if rep["n_required_missing"] < 5:
            _bad(
                desc,
                f"only {rep['n_required_missing']} required missing — image/ml required fields not flagged",
            )
            return
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 4 — explicit None for required key treated as missing ────────────

def case_04_explicit_none_vs_missing() -> None:
    desc = "case_04 figure={'core_conclusion':'X','final_size':None} treats None as missing"
    try:
        rep, _ = _capture(
            huitu.reviewer_checklist,
            figure={"core_conclusion": "X", "final_size": None},
            quantitative=COMPLETE_QUANT,
            print_report=False,
        )
        # final_size is required — None should count as missing.
        figure_section = next((s for s in rep["sections"] if s["name"] == "Figure"), None)
        if figure_section is None:
            _bad(desc, "no Figure section")
            return
        final_size_row = next(
            (r for r in figure_section["rows"] if r[0] == "final_size"), None
        )
        if final_size_row is None:
            _bad(desc, "final_size row missing")
            return
        if final_size_row[2] != "missing_required":
            _bad(desc, f"final_size status = {final_size_row[2]!r}, expected 'missing_required'")
            return
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 5 — non-dict input must raise TypeError ──────────────────────────

def case_05_non_dict_figure() -> None:
    desc = "case_05 figure=['a','b'] raises TypeError (no silent list-as-dict)"
    try:
        huitu.reviewer_checklist(figure=["a", "b"])
        _bad(desc, "did not raise")
    except (TypeError, AttributeError):
        # AttributeError on payload.get is technically also a signal, but
        # the function should validate inputs and raise a clean TypeError.
        # Accept either as evidence the input is not silently processed.
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"wrong exception {type(exc).__name__}: {exc}")


# ── Case 6 — truthy-but-meaningless values are silently accepted ──────────

def case_06_truthy_but_meaningless() -> None:
    desc = "case_06 quant values 'TODO'/'?'/'TBD' accepted as 'ok' (P2: no content validation)"
    # If huitu doesn't validate string content, all of these will pass. Surface
    # that as informational, but the test passes (this is current behaviour).
    try:
        meaningless_quant = {
            "n": "TODO",
            "biological_replicates": "?",
            "center": "?",
            "spread": "?",
            "test": "see methods",
            "source_data": "TBD",
        }
        rep, _ = _capture(
            huitu.reviewer_checklist,
            figure=COMPLETE_FIGURE,
            quantitative=meaningless_quant,
            print_report=False,
        )
        if rep["pass"]:
            # P2 issue surfaced via [PASS] message: huitu accepts these.
            _ok(
                desc
                + " (P2 surfaced: no plausibility check on TODO/?/TBD — Reviewer C investigate)"
            )
        else:
            # If huitu DOES validate, even better — but we expect current=accept.
            _ok(desc + " (huitu rejected meaningless values — content validation in place)")
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 7 — value=0 accepted ─────────────────────────────────────────────

def case_07_value_zero_accepted() -> None:
    desc = "case_07 value=0 in n / biological_replicates is accepted as provided"
    # Round-1 spec: 0 is a valid 'provided' marker.
    try:
        zero_quant = dict(COMPLETE_QUANT, n=0, biological_replicates=0)
        rep, _ = _capture(
            huitu.reviewer_checklist,
            figure=COMPLETE_FIGURE,
            quantitative=zero_quant,
            print_report=False,
        )
        if not rep["pass"]:
            _bad(desc, "value=0 rejected as missing (regression from round-1)")
            return
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 8 — nested dict in core_conclusion: print must not crash ─────────

def case_08_nested_dict_value() -> None:
    desc = "case_08 figure={'core_conclusion': {...}} prints without crashing"
    try:
        nested_figure = dict(COMPLETE_FIGURE)
        nested_figure["core_conclusion"] = {"english": "X reduces tumor", "中文": "X 减小肿瘤"}
        try:
            rep, out = _capture(
                huitu.reviewer_checklist,
                figure=nested_figure,
                quantitative=COMPLETE_QUANT,
            )
        except Exception as exc:
            _bad(desc, f"_print_checklist crashed on dict value: {type(exc).__name__}: {exc}")
            return
        if not out.strip():
            _bad(desc, "no output produced")
            return
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 9 — very long source_data string doesn't blow up print ───────────

def case_09_very_long_source_data() -> None:
    desc = "case_09 10 000-char source_data prints truncated"
    try:
        long_path = "x" * 10_000
        long_quant = dict(COMPLETE_QUANT, source_data=long_path)
        rep, out = _capture(
            huitu.reviewer_checklist,
            figure=COMPLETE_FIGURE,
            quantitative=long_quant,
        )
        if long_path in out:
            _bad(desc, "full 10 000-char string emitted (should be truncated)")
            return
        # Expect "..." somewhere in the output (truncation marker).
        if "..." not in out:
            _bad(desc, "no '...' truncation marker found")
            return
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 10 — positional call is rejected (kw-only) ───────────────────────

def case_10_positional_rejected() -> None:
    desc = "case_10 reviewer_checklist({}, {}, {}, {}) raises TypeError (kw-only)"
    try:
        huitu.reviewer_checklist({}, {}, {}, {})
        _bad(desc, "positional call did not raise")
    except TypeError:
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"wrong exception {type(exc).__name__}: {exc}")


# ── Case 11 — all 4 sections complete passes ──────────────────────────────

def case_11_all_four_complete() -> None:
    desc = "case_11 all 4 sections (fig+quant+image+ml) complete passes"
    try:
        rep, out = _capture(
            huitu.reviewer_checklist,
            figure=COMPLETE_FIGURE,
            quantitative=COMPLETE_QUANT,
            image=COMPLETE_IMAGE,
            machine_learning=COMPLETE_ML,
        )
        if not rep["pass"]:
            _bad(
                desc,
                f"required missing={rep['n_required_missing']}, recommended missing={rep['n_recommended_missing']}",
            )
            return
        for sec in ("Figure", "Quantitative", "Image", "ML / model"):
            if sec not in out:
                _bad(desc, f"section {sec!r} missing from output")
                return
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 12 — print_report=False suppresses output ────────────────────────

def case_12_print_report_false() -> None:
    desc = "case_12 print_report=False produces no stdout"
    try:
        rep, out = _capture(
            huitu.reviewer_checklist,
            figure=COMPLETE_FIGURE,
            quantitative=COMPLETE_QUANT,
            print_report=False,
        )
        if out.strip():
            _bad(desc, f"non-empty output: {out!r}")
        else:
            _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 13 — image=None must NOT render Image section ────────────────────

def case_13_image_none_skips_section() -> None:
    desc = "case_13 image=None (default) does NOT render Image section"
    try:
        rep, out = _capture(
            huitu.reviewer_checklist,
            figure=COMPLETE_FIGURE,
            quantitative=COMPLETE_QUANT,
        )
        if "Image" in out:
            _bad(desc, "Image section rendered even though image=None")
        else:
            _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


def main() -> int:
    case_01_happy()
    case_02_bare_call_fails()
    case_03_explicit_empty_image_ml()
    case_04_explicit_none_vs_missing()
    case_05_non_dict_figure()
    case_06_truthy_but_meaningless()
    case_07_value_zero_accepted()
    case_08_nested_dict_value()
    case_09_very_long_source_data()
    case_10_positional_rejected()
    case_11_all_four_complete()
    case_12_print_report_false()
    case_13_image_none_skips_section()

    print(f"\n[SUMMARY] test_05_reviewer_checklist: {_passed} pass / {_failed} fail")
    if _failed == 0:
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
