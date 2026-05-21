"""Adversarial test 4: huitu.check_redundancy.

Edge / hostile inputs:
* empty list / single panel (must not warn spuriously)
* 50 panels with the same question (linear scale, correct grouping)
* id collisions ('a' twice) — currently dedups within the question bucket;
  arguably should ALSO flag the dup
* non-string id (1, ("a", 0))
* data="" treated as "missing" not as a duplicate slice
* whitespace + case normalisation per documented behaviour
* unknown panel keys ignored gracefully
* print_redundancy_report on malformed panels must not crash
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


# ── Case 1 — happy path: correctly tiered 3-panel figure ──────────────────

def case_01_happy() -> None:
    desc = "case_01 clean 3-tier plan returns 0 issues"
    try:
        panels = [
            {"id": "a", "question": "What is the composition?",
             "encoding": "stacked_bar", "data": "composition", "level": "overview"},
            {"id": "b", "question": "Which features deviate?",
             "encoding": "z_score_heatmap", "data": "z_score", "level": "deviation"},
            {"id": "c", "question": "How does X co-vary with Y?",
             "encoding": "bubble_scatter", "data": "correlation", "level": "relationship"},
        ]
        issues = huitu.check_redundancy(panels)
        if issues:
            _bad(desc, f"got {len(issues)} false-positive issues: {[str(i) for i in issues]}")
        else:
            _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 2 — single panel with all fields → 0 issues ──────────────────────

def case_02_single_panel() -> None:
    desc = "case_02 single complete panel returns 0 issues"
    try:
        issues = huitu.check_redundancy([
            {"id": "a", "question": "Composition?", "encoding": "stacked_bar"},
        ])
        if issues:
            _bad(desc, f"single panel produced {len(issues)} issues")
        else:
            _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 3 — empty list → 0 issues, no crash ──────────────────────────────

def case_03_empty_list() -> None:
    desc = "case_03 empty panel list returns []"
    try:
        issues = huitu.check_redundancy([])
        if issues == []:
            _ok(desc)
        else:
            _bad(desc, f"got {issues!r}")
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 4 — 50-panel scale (linear, no crash) ────────────────────────────

def case_04_scale_50_panels() -> None:
    desc = "case_04 50 panels all same question scales linearly + warns once"
    try:
        panels = [
            {"id": f"p{i}", "question": "What is X?", "encoding": "bar"}
            for i in range(50)
        ]
        issues = huitu.check_redundancy(panels)
        warns = [i for i in issues if i.severity == "warn"
                 and "same scientific question" in i.message]
        if not warns:
            _bad(desc, "no 'same scientific question' warn emitted")
            return
        # All 50 ids should be in the single bucket.
        ids = set(warns[0].panels)
        if len(ids) != 50:
            _bad(desc, f"warn bucket has {len(ids)} ids, expected 50")
            return
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 5 — id collision: 'a' used twice ─────────────────────────────────

def case_05_id_collision() -> None:
    desc = "case_05 two panels with same id 'a' surfaces some signal (warn/info)"
    # Spec: ideally the heuristic flags 'duplicate id'. Currently it doesn't —
    # the same-question / same-data buckets just include 'a' twice. The minimum
    # acceptable behaviour is *not silently dedup*: at least one warn must
    # mention 'a' twice.
    try:
        panels = [
            {"id": "a", "question": "Q1?", "encoding": "bar", "data": "d1"},
            {"id": "a", "question": "Q2?", "encoding": "line", "data": "d2"},
        ]
        issues = huitu.check_redundancy(panels)
        # Without same q/d/encoding overlap, 'a' duplication won't fire any
        # rule. The library currently lacks a unique-id check entirely;
        # surface that as a missing signal.
        has_dup_signal = any("duplicate" in i.message.lower() or
                             i.panels.count("a") >= 2 for i in issues)
        if has_dup_signal:
            _ok(desc)
        else:
            _bad(
                desc,
                "no duplicate-id signal. check_redundancy silently accepts two panels "
                "with id='a'; library should at least emit an info that ids must be unique.",
            )
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 6 — non-string id ────────────────────────────────────────────────

def case_06_non_string_id() -> None:
    desc = "case_06 non-string ids (int, tuple) don't crash + don't corrupt panels tuple"
    try:
        panels = [
            {"id": 1, "question": "Q?", "encoding": "bar"},
            {"id": ("a", 0), "question": "Q?", "encoding": "bar"},
        ]
        issues = huitu.check_redundancy(panels)
        # Should produce at least one warn (same question), with non-string ids
        # preserved in the panels tuple.
        if not issues:
            _bad(desc, "no issue at all for same-question with non-string ids")
            return
        # Spec: PanelIssue.panels is documented as tuple[str, ...]; allowing
        # non-strings is a typing bug. Capture this for the reviewer.
        warn = next((i for i in issues if i.severity == "warn"), None)
        if warn is None:
            _bad(desc, "no warn-level issue")
            return
        non_strings = [p for p in warn.panels if not isinstance(p, str)]
        if non_strings:
            _bad(
                desc,
                f"PanelIssue.panels carries non-string ids {non_strings!r}; "
                "violates tuple[str, ...] type hint. Should str()-coerce.",
            )
            return
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"crashed on non-string id with {type(exc).__name__}: {exc}")


# ── Case 7 — empty-string data must NOT be treated as duplicate slice ─────

def case_07_empty_data_string() -> None:
    desc = "case_07 panels with data='' are NOT flagged as 'same data slice'"
    try:
        panels = [
            {"id": "a", "question": "Q1?", "encoding": "bar", "data": ""},
            {"id": "b", "question": "Q2?", "encoding": "line", "data": ""},
        ]
        issues = huitu.check_redundancy(panels)
        data_slice = [i for i in issues if "data slice" in i.message]
        if data_slice:
            _bad(desc, f"empty data='' was flagged as same data slice: {data_slice[0]}")
        else:
            _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 8 — case + whitespace normalisation per documented behaviour ─────

def case_08_case_whitespace_normalisation() -> None:
    desc = "case_08 'What is X?' vs 'what  is x?' normalise to same bucket"
    try:
        panels = [
            {"id": "a", "question": "What is X?", "encoding": "bar"},
            {"id": "b", "question": "what  is x?", "encoding": "line"},
        ]
        issues = huitu.check_redundancy(panels)
        warns = [i for i in issues if i.severity == "warn"
                 and set(i.panels) == {"a", "b"}
                 and "same scientific question" in i.message]
        if warns:
            _ok(desc)
        else:
            _bad(desc, f"no normalised match for a/b; issues: {[str(i) for i in issues]}")
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 9 — unknown extra keys must be ignored ───────────────────────────

def case_09_unknown_keys_ignored() -> None:
    desc = "case_09 panels with unknown 'future_field' key still parse without crash"
    try:
        panels = [
            {"id": "a", "question": "Q?", "encoding": "bar", "future_field": 42},
            {"id": "b", "question": "Q?", "encoding": "line", "totally_new": object()},
        ]
        issues = huitu.check_redundancy(panels)
        # Same-question warn should still fire.
        if not any(i.severity == "warn" and set(i.panels) == {"a", "b"} for i in issues):
            _bad(desc, "same-question warn missing; unknown keys may have broken parsing")
            return
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 10 — print_redundancy_report on malformed input ──────────────────

def case_10_print_malformed() -> None:
    desc = "case_10 print_redundancy_report on malformed panels does not crash"
    try:
        # Mix of valid and invalid dicts.
        malformed = [
            {"id": "a", "question": "Q?", "encoding": "bar"},
            {"question": "Q?", "encoding": "bar"},  # no id at all
            {"id": "c"},  # no question, no encoding
        ]
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                huitu.print_redundancy_report(malformed)
        except Exception as exc:
            _bad(desc, f"crashed: {type(exc).__name__}: {exc}")
            return
        if not buf.getvalue().strip():
            _bad(desc, "no output produced")
        else:
            _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 11 — same data slice with stacked_bar + pie ──────────────────────

def case_11_pie_stacked_trap() -> None:
    desc = "case_11 pie + stacked-bar of same data triggers BOTH same-data and trap warns"
    try:
        panels = [
            {"id": "a", "question": "Composition by class?",
             "encoding": "stacked_bar", "data": "comp"},
            {"id": "b", "question": "Class fractions?",
             "encoding": "pie", "data": "comp"},
        ]
        issues = huitu.check_redundancy(panels)
        has_data_slice = any("data slice" in i.message for i in issues)
        has_pie_trap = any("pie + stacked bar" in i.message for i in issues)
        if has_data_slice and has_pie_trap:
            _ok(desc)
        else:
            _bad(
                desc,
                f"data_slice={has_data_slice}, pie_trap={has_pie_trap}",
            )
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 12 — overview-only plan triggers missing-levels info ─────────────

def case_12_missing_levels() -> None:
    desc = "case_12 3 overview panels emit INFO listing deviation+relationship missing"
    try:
        panels = [
            {"id": "a", "question": "C1?", "encoding": "stacked_bar"},
            {"id": "b", "question": "C2?", "encoding": "stacked_bar"},
            {"id": "c", "question": "C3?", "encoding": "single_bar"},
        ]
        issues = huitu.check_redundancy(panels)
        info = [i for i in issues if i.severity == "info"
                and "missing the information level" in i.message]
        if not info:
            _bad(desc, "no info-level missing-levels issue")
            return
        msg = info[0].message
        if "deviation" not in msg or "relationship" not in msg:
            _bad(desc, f"message doesn't mention both missing levels: {msg!r}")
        else:
            _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 13 — panel missing 'id' but with question (round-1 known edge) ──

def case_13_missing_id_with_question() -> None:
    desc = "case_13 panel without 'id' but with question does not crash"
    try:
        issues = huitu.check_redundancy([
            {"question": "Q?", "encoding": "bar"},
        ])
        # No crash is the bar. The function should treat the panel as id='?'.
        _ok(desc)
    except KeyError as exc:
        _bad(desc, f"KeyError on missing id: {exc}. review.py uses p['id'] in some paths.")
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


def main() -> int:
    case_01_happy()
    case_02_single_panel()
    case_03_empty_list()
    case_04_scale_50_panels()
    case_05_id_collision()
    case_06_non_string_id()
    case_07_empty_data_string()
    case_08_case_whitespace_normalisation()
    case_09_unknown_keys_ignored()
    case_10_print_malformed()
    case_11_pie_stacked_trap()
    case_12_missing_levels()
    case_13_missing_id_with_question()

    print(f"\n[SUMMARY] test_04_check_redundancy: {_passed} pass / {_failed} fail")
    if _failed == 0:
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
