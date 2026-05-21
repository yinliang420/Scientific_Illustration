"""Round-3 adversarial test 5: review.py callsites under attack.

Round-2 added `_lower_str` and threaded it through 5 callsites in
``huitu/review.py``:
  * `question` grouping in :func:`check_redundancy`
  * `data` grouping in :func:`check_redundancy`
  * `level` / `encoding` resolution in :func:`check_redundancy` and
    :func:`_infer_level`
  * `encoding` heuristic match (ranked / pie / stacked)

This file feeds each callsite a weird type and asserts the function still:
  (a) returns deterministic output
  (b) does NOT crash on the input
  (c) groups inputs sensibly under str-coercion semantics
  (d) handles huge / nested values without hanging

The companion `reviewer_checklist` callsite is also probed (it does
``str(value)`` for display) — must not crash on bytes/tuples/etc.

PASS: deterministic, no crash. FAIL: crash, infinite loop, or non-grouping
where _lower_str would normally collapse two inputs.
"""

from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout

import huitu
from huitu.review import check_redundancy, reviewer_checklist

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


def _silent_review(panels):
    """Run check_redundancy without printing to stdout (avoid noise)."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        return check_redundancy(panels)


# ── Case 1 — single NaN question doesn't crash ────────────────────────────

def case_01_nan_question_single() -> None:
    desc = "case_01 single panel with question=NaN → no crash"
    try:
        issues = _silent_review([
            {"id": "a", "question": float("nan"), "encoding": "line"},
        ])
    except Exception as e:
        _bad(desc, f"raised {type(e).__name__}: {e}")
        return
    if isinstance(issues, list):
        _ok(desc + f" — got {len(issues)} issue(s)")
    else:
        _bad(desc, f"non-list result {type(issues).__name__}")


# ── Case 2 — two NaN questions GROUP into a 'same-question' warning ───────

def case_02_two_nan_questions_grouped() -> None:
    desc = ("case_02 two panels with question=NaN — both coerce via "
            "_lower_str to 'nan', so check_redundancy groups them")
    issues = _silent_review([
        {"id": "a", "question": float("nan"), "encoding": "line"},
        {"id": "b", "question": float("nan"), "encoding": "bar"},
    ])
    same_q = [i for i in issues if "same scientific question" in i.message]
    if any("a" in i.panels and "b" in i.panels for i in same_q):
        _ok(desc + f" — grouped: {same_q[0].panels!r}")
    else:
        _bad(desc, f"NaN questions not grouped; issues={[str(i) for i in issues]!r}")


# ── Case 3 — gigantic data tag (1 MB string) doesn't hang ─────────────────

def case_03_huge_data_tag() -> None:
    desc = "case_03 panel with data = 'X' * 1_000_000 — no hang, terminates"
    big = "X" * 1_000_000
    try:
        issues = _silent_review([
            {"id": "a", "question": "Q", "data": big, "encoding": "line"},
            {"id": "b", "question": "Q2", "data": big, "encoding": "scatter"},
        ])
    except Exception as e:
        _bad(desc, f"raised {type(e).__name__}: {e}")
        return
    # 1MB strings, both same: should group as same-data.
    if isinstance(issues, list):
        same_data = [i for i in issues if "same data slice" in i.message]
        _ok(desc + f" — {len(same_data)} same-data warning(s) raised on 1MB tags")
    else:
        _bad(desc, "non-list result")


# ── Case 4 — Mock-like object with deterministic __str__ ──────────────────

def case_04_mock_like_object() -> None:
    desc = ("case_04 panel with data = Mock-ish object having deterministic "
            "__str__ — group by repr-string")
    class Det:
        def __init__(self, name: str) -> None:
            self.name = name
        def __str__(self) -> str:
            return f"<Det name={self.name}>"
    a = Det("X")
    b = Det("X")
    issues = _silent_review([
        {"id": "a", "question": "Q1", "data": a, "encoding": "line"},
        {"id": "b", "question": "Q2", "data": b, "encoding": "scatter"},
    ])
    same_data = [i for i in issues if "same data slice" in i.message]
    if same_data:
        _ok(desc + f" — same-data grouped on str(): {same_data[0].panels!r}")
    else:
        _bad(desc, f"not grouped; issues={[str(i) for i in issues]!r}")


# ── Case 5 — uppercase level "OVERVIEW" still detected ────────────────────

def case_05_uppercase_level_inferred() -> None:
    desc = ("case_05 panel with level='OVERVIEW' — _lower_str makes the "
            "info-hierarchy check case-insensitive")
    # 3+ panels triggers the level-hierarchy check.
    issues = _silent_review([
        {"id": "a", "question": "Q1", "encoding": "line", "level": "OVERVIEW"},
        {"id": "b", "question": "Q2", "encoding": "scatter", "level": "RELATIONSHIP"},
        {"id": "c", "question": "Q3", "encoding": "z_score_heatmap", "level": "DEVIATION"},
    ])
    missing = [i for i in issues if "missing the information level" in i.message]
    if not missing:
        _ok(desc + " — all 3 levels detected via case-insensitive match")
    else:
        _bad(desc, f"unexpected hierarchy gap: {missing[0].message}")


# ── Case 6 — mixed-case 'Pie' + 'Stacked' triggers pie+stacked warning ────

def case_06_mixed_case_encoding_pie_stacked() -> None:
    desc = ("case_06 encoding='Pie' + 'Stacked' — case-insensitive match "
            "triggers the pie+stacked composition warning")
    issues = _silent_review([
        {"id": "a", "question": "Q1", "encoding": "Pie"},
        {"id": "b", "question": "Q2", "encoding": "Stacked_Bar"},
    ])
    pie_stack = [i for i in issues
                 if "pie + stacked" in i.message.lower()]
    if pie_stack:
        _ok(desc + f" — warning raised: {pie_stack[0].panels!r}")
    else:
        _bad(desc, f"warning not raised; issues={[str(i) for i in issues]!r}")


# ── Case 7 — 1000-panel figure with list-typed questions ──────────────────

def case_07_1000_panels_list_questions() -> None:
    desc = ("case_07 1000-panel figure where every question = list(range(N)) "
            "— _lower_str returns the list's repr string; check_redundancy "
            "must terminate")
    panels = [
        {"id": f"p{n:04d}",
         "question": list(range(n % 10)),
         "encoding": "line"}
        for n in range(1000)
    ]
    try:
        issues = _silent_review(panels)
    except Exception as e:
        _bad(desc, f"raised {type(e).__name__}: {e}")
        return
    if not isinstance(issues, list):
        _bad(desc, f"non-list result {type(issues).__name__}")
        return
    _ok(desc + f" — terminated, {len(issues)} issues")


# ── Case 8 — reviewer_checklist with bytes core_conclusion ────────────────

def case_08_checklist_bytes_value() -> None:
    desc = ("case_08 reviewer_checklist(figure={'core_conclusion': b'bytes'}) "
            "— runs through str(value) for display, must not crash")
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            rep = reviewer_checklist(
                figure={"core_conclusion": b"bytes"},
                print_report=True,
            )
    except Exception as e:
        _bad(desc, f"raised {type(e).__name__}: {e}")
        return
    if isinstance(rep, dict) and "sections" in rep:
        _ok(desc + " — returned dict report")
    else:
        _bad(desc, f"weird return {type(rep).__name__}")


# ── Case 9 — reviewer_checklist with tuple final_size ─────────────────────

def case_09_checklist_tuple_value() -> None:
    desc = ("case_09 reviewer_checklist(figure={'final_size': (89, 70, 'mm')}) "
            "— tuple coerces via str(); no crash")
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            rep = reviewer_checklist(
                figure={"final_size": (89, 70, "mm")},
                print_report=True,
            )
    except Exception as e:
        _bad(desc, f"raised {type(e).__name__}: {e}")
        return
    if isinstance(rep, dict):
        _ok(desc + " — clean")
    else:
        _bad(desc, "non-dict result")


# ── Case 10 — None panel ids handled by str() ─────────────────────────────

def case_10_panel_id_none() -> None:
    desc = ("case_10 panel with id=None — str(None) -> 'None' becomes the "
            "panel id in the report, no crash")
    try:
        issues = _silent_review([
            {"id": None, "question": "Q", "encoding": "line"},
            {"id": None, "question": "Q", "encoding": "bar"},
        ])
    except Exception as e:
        _bad(desc, f"raised {type(e).__name__}: {e}")
        return
    # Two id=None panels should be grouped as same-question and also flag
    # duplicate id "None".
    dup = [i for i in issues if "is duplicated" in i.message]
    if dup:
        _ok(desc + f" — flagged dup id 'None'; panels={dup[0].panels!r}")
    else:
        _bad(desc, f"duplicate-id detection did not fire; issues={[str(i) for i in issues]!r}")


# ── Case 11 — generator panels (Sequence-ish but not list) ────────────────

def case_11_generator_panels() -> None:
    desc = ("case_11 check_redundancy accepts a generator (the docstring "
            "says 'accept generators / non-sized iterables')")
    def gen():
        yield {"id": "a", "question": "Q1", "encoding": "line"}
        yield {"id": "b", "question": "Q1", "encoding": "bar"}
    try:
        issues = _silent_review(gen())
    except Exception as e:
        _bad(desc, f"raised {type(e).__name__}: {e}")
        return
    if any("same scientific question" in i.message for i in issues):
        _ok(desc)
    else:
        _bad(desc, f"generator panels not grouped; issues={[str(i) for i in issues]!r}")


# ── Case 12 — empty panel list ────────────────────────────────────────────

def case_12_empty_panel_list() -> None:
    desc = "case_12 check_redundancy([]) returns empty list (no crash)"
    try:
        issues = _silent_review([])
    except Exception as e:
        _bad(desc, f"raised {type(e).__name__}: {e}")
        return
    if issues == []:
        _ok(desc)
    else:
        _bad(desc, f"non-empty result: {issues!r}")


# ── Case 13 — missing 'question' field (None default) triggers info ───────

def case_13_missing_question_field() -> None:
    desc = ("case_13 panel missing 'question' (-> None -> '') triggers "
            "an 'info' issue, not a crash")
    issues = _silent_review([
        {"id": "a", "encoding": "line"},
    ])
    miss = [i for i in issues if "missing a 'question'" in i.message]
    if miss:
        _ok(desc)
    else:
        _bad(desc, f"no info issue raised; issues={[str(i) for i in issues]!r}")


# ── Case 14 — boolean encoding doesn't crash inference ────────────────────

def case_14_bool_encoding() -> None:
    desc = ("case_14 panel with encoding=True — _lower_str(True) == 'true', "
            "_infer_level returns '' (no keyword match); no crash")
    try:
        issues = _silent_review([
            {"id": "a", "question": "Q", "encoding": True},
        ])
    except Exception as e:
        _bad(desc, f"raised {type(e).__name__}: {e}")
        return
    if isinstance(issues, list):
        _ok(desc + f" — terminated, {len(issues)} issues")
    else:
        _bad(desc, "non-list result")


def main() -> int:
    case_01_nan_question_single()
    case_02_two_nan_questions_grouped()
    case_03_huge_data_tag()
    case_04_mock_like_object()
    case_05_uppercase_level_inferred()
    case_06_mixed_case_encoding_pie_stacked()
    case_07_1000_panels_list_questions()
    case_08_checklist_bytes_value()
    case_09_checklist_tuple_value()
    case_10_panel_id_none()
    case_11_generator_panels()
    case_12_empty_panel_list()
    case_13_missing_question_field()
    case_14_bool_encoding()

    print(f"\n[SUMMARY] test_05_review_lower_str_uses: {_passed} pass / {_failed} fail")
    if _failed == 0:
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
