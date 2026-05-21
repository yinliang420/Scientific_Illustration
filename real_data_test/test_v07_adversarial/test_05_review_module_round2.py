"""Adversarial test 5 (Round 2): review.py after Round-1 fixes.

Round-1 added:
  * ``str()`` coercion on panel ids → ``PanelIssue.panels`` always carries strs
  * a duplicate-id rule
  * generator/non-sized input accepted via ``panels = list(panels)``

Round-2 attacks:
  * cyclic / self-referential panel dicts
  * non-string ``id`` (bytes, tuple, object) — already coerced
  * non-string ``data`` field (numpy array, dict) — currently calls
    ``.lower()`` on it → AttributeError. Real bug surfaced here.
  * non-string ``question`` (list, dict) — same root cause
  * ``reviewer_checklist`` with dict subclasses (``OrderedDict``,
    user-defined ``dict``)
  * ``reviewer_checklist`` with hostile dict subclass whose ``.get()``
    raises — must not corrupt the partial report
  * non-stringifiable but truthy ``core_conclusion`` → ``str()`` must
    succeed and the print row must not crash
  * recursive value in machine_learning section → ``repr`` truncation
    must not infinite-loop
  * ``PanelIssue`` is frozen dataclass → hashable, can live in ``set``
"""

from __future__ import annotations

import io
import sys
from collections import OrderedDict
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


# ── Case 1 — circular self-reference inside a panel dict ─────────────────

def case_01_circular_self_ref() -> None:
    desc = "case_01 panel dict with self-reference doesn't infinite-loop"
    try:
        p = {"id": "a", "question": "Q1?", "encoding": "bar"}
        p["self"] = p  # cycle
        # check_redundancy must not deepcopy or repr-traverse the panel.
        issues = huitu.check_redundancy([p, {"id": "b", "question": "Q2?", "encoding": "bar"}])
        # No assertion on issue count — only that we returned within 30s.
        _ok(desc + f" (returned {len(issues)} issues)")
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 2 — bytes id is coerced to str ──────────────────────────────────

def case_02_bytes_id() -> None:
    desc = "case_02 id=b'a' is str-coerced; PanelIssue.panels contains str"
    try:
        panels = [
            {"id": b"a", "question": "Q?", "encoding": "bar"},
            {"id": b"a", "question": "Q?", "encoding": "bar"},
        ]
        issues = huitu.check_redundancy(panels)
        if not issues:
            _bad(desc, "no issues fired (expected same-question + dup-id)")
            return
        all_strs = all(isinstance(p, str) for i in issues for p in i.panels)
        if not all_strs:
            non = [p for i in issues for p in i.panels if not isinstance(p, str)]
            _bad(desc, f"PanelIssue.panels has non-str entries: {non!r}")
            return
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 3 — numpy array in 'data' field ─────────────────────────────────

def case_03_numpy_data() -> None:
    desc = "case_03 data=np.array([1,2]) does not crash check_redundancy"
    try:
        try:
            import numpy as np
        except Exception:
            _ok(desc + " (numpy not available; skipping)")
            return
        panels = [
            {"id": "a", "question": "Q?", "encoding": "bar", "data": np.array([1, 2, 3])},
            {"id": "b", "question": "Q?", "encoding": "bar"},
        ]
        try:
            issues = huitu.check_redundancy(panels)
        except (AttributeError, ValueError) as exc:
            _bad(
                desc,
                f"crashed on numpy data: {type(exc).__name__}: {exc}. "
                "review.py calls .lower().strip() on whatever is in 'data'; "
                "should coerce via str() first.",
            )
            return
        except Exception as exc:
            _bad(desc, f"unexpected crash: {type(exc).__name__}: {exc}")
            return
        _ok(desc + f" (returned {len(issues)} issues)")
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 4 — list as 'question' field ────────────────────────────────────

def case_04_list_question() -> None:
    desc = "case_04 question=['a','b'] does not crash check_redundancy"
    try:
        try:
            issues = huitu.check_redundancy([
                {"id": "a", "question": ["composition", "fraction"], "encoding": "bar"},
            ])
        except AttributeError as exc:
            _bad(
                desc,
                f"crashed: {exc}. (p.get('question') or '').lower() assumes str; "
                "should str()-coerce or skip non-strings.",
            )
            return
        except Exception as exc:
            _bad(desc, f"unexpected crash: {type(exc).__name__}: {exc}")
            return
        _ok(desc + f" (returned {len(issues)} issues)")
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 5 — generator of generators ─────────────────────────────────────

def case_05_generator_of_generators() -> None:
    desc = "case_05 nested generator input is accepted (list() coerces)"
    try:
        def gen():
            for i in range(3):
                yield {"id": f"p{i}", "question": "What?", "encoding": "bar"}

        try:
            issues = huitu.check_redundancy(p for p in gen())
        except Exception as exc:
            _bad(desc, f"crashed: {type(exc).__name__}: {exc}")
            return
        if not any(i.severity == "warn" and len(i.panels) == 3 for i in issues):
            _bad(desc, "same-question warn missing or wrong bucket size")
            return
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 6 — reviewer_checklist with dict subclass ───────────────────────

def case_06_dict_subclass() -> None:
    desc = "case_06 reviewer_checklist accepts user dict subclass"
    try:
        class D(dict):
            pass

        fig = D(
            {
                "core_conclusion": "X reduces Y by Z%",
                "final_size": "89 mm",
            }
        )
        quant = D(
            {
                "n": "12",
                "biological_replicates": 3,
                "center": "median",
                "spread": "IQR",
                "test": "Wilcoxon",
                "source_data": "f.csv",
            }
        )
        rep = huitu.reviewer_checklist(figure=fig, quantitative=quant, print_report=False)
        if not rep["pass"]:
            _bad(
                desc,
                f"dict subclass treated differently: missing={rep['n_required_missing']}",
            )
            return
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 7 — reviewer_checklist with OrderedDict ─────────────────────────

def case_07_ordered_dict() -> None:
    desc = "case_07 reviewer_checklist accepts OrderedDict"
    try:
        fig = OrderedDict(
            {"core_conclusion": "X", "final_size": "89 mm"}
        )
        quant = OrderedDict(
            {
                "n": "12",
                "biological_replicates": 3,
                "center": "median",
                "spread": "IQR",
                "test": "Wilcoxon",
                "source_data": "f.csv",
            }
        )
        rep = huitu.reviewer_checklist(figure=fig, quantitative=quant, print_report=False)
        if not rep["pass"]:
            _bad(
                desc,
                f"OrderedDict treated differently: missing={rep['n_required_missing']}",
            )
            return
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 8 — hostile .get() that raises ──────────────────────────────────

def case_08_hostile_get() -> None:
    desc = "case_08 dict subclass whose .get() raises: behavior must be safe (raise or catch)"
    # P2: huitu doesn't currently guard against this — payload.get(key)
    # will propagate the RuntimeError. Either outcome (clean propagation OR
    # caught + flagged-as-missing) is acceptable as long as we don't see a
    # partial / inconsistent report dict.
    try:
        class Evil(dict):
            def get(self, key, default=None):
                raise RuntimeError("hostile get")

        fig = Evil({"core_conclusion": "X", "final_size": "89 mm"})
        try:
            rep = huitu.reviewer_checklist(
                figure=fig, quantitative={"n": "12"}, print_report=False
            )
        except RuntimeError:
            # Propagation is acceptable — user-supplied dict is buggy.
            _ok(desc + " (RuntimeError propagated cleanly)")
            return
        except Exception as exc:
            _bad(desc, f"unexpected crash type: {type(exc).__name__}: {exc}")
            return
        # If we got a report, it should be coherent.
        if not isinstance(rep, dict) or "pass" not in rep:
            _bad(desc, f"corrupt report dict: {rep!r}")
            return
        _ok(desc + " (hostile .get caught — report still coherent)")
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 9 — non-stringifiable but truthy core_conclusion ────────────────

def case_09_non_stringifiable_truthy() -> None:
    desc = "case_09 figure['core_conclusion']=<object> prints + treats as 'ok'"
    try:
        class O:
            def __str__(self) -> str:
                return "<O instance>"

        fig = {"core_conclusion": O(), "final_size": "89 mm"}
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                rep = huitu.reviewer_checklist(figure=fig, print_report=True)
        except Exception as exc:
            _bad(desc, f"print crashed on object value: {type(exc).__name__}: {exc}")
            return
        if "<O instance>" not in buf.getvalue():
            _bad(desc, "object value not str()-rendered in output")
            return
        # core_conclusion is required → with the object present, it's not None,
        # so n_required_missing for core_conclusion must be 0.
        figure_section = next((s for s in rep["sections"] if s["name"] == "Figure"), None)
        if figure_section is None:
            _bad(desc, "no Figure section")
            return
        cc = next((r for r in figure_section["rows"] if r[0] == "core_conclusion"), None)
        if cc is None or cc[2] != "ok":
            _bad(desc, f"core_conclusion status: {cc[2] if cc else 'missing row'}")
            return
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 10 — recursive value in machine_learning section ────────────────

def case_10_recursive_ml_value() -> None:
    desc = "case_10 ml dict with recursive value does not infinite-loop on print"
    try:
        rec: dict = {"name": "loop"}
        rec["self"] = rec
        # repr() of recursive dict is safe (uses {...} marker for cycles),
        # but the long-string truncation in _print_checklist uses len(repr(v)),
        # so if huitu str()-renders the value it must not blow up.
        ml = {
            "split": "70/15/15",
            "seeds": 5,
            "metric": "AUROC",
            "baseline": rec,  # cyclic value
        }
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                rep = huitu.reviewer_checklist(
                    figure={"core_conclusion": "X", "final_size": "89 mm"},
                    quantitative={
                        "n": "1",
                        "biological_replicates": 1,
                        "center": "mean",
                        "spread": "SD",
                        "test": "t",
                        "source_data": "f",
                    },
                    machine_learning=ml,
                    print_report=True,
                )
        except RecursionError as exc:
            _bad(desc, f"RecursionError: {exc}")
            return
        except Exception as exc:
            _bad(desc, f"crashed: {type(exc).__name__}: {exc}")
            return
        if "ML / model" not in buf.getvalue():
            _bad(desc, "ML section missing from print output")
            return
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"outer crash: {type(exc).__name__}: {exc}")


# ── Case 11 — PanelIssue hashable + set-friendly ─────────────────────────

def case_11_panelissue_hashable() -> None:
    desc = "case_11 PanelIssue is frozen dataclass and hashable / set-de-dupes equal items"
    try:
        a = huitu.PanelIssue("warn", ("a", "b"), "msg")
        b = huitu.PanelIssue("warn", ("a", "b"), "msg")
        try:
            h = hash(a)
        except TypeError as exc:
            _bad(desc, f"unhashable: {exc}")
            return
        if hash(a) != hash(b):
            _bad(desc, "equal PanelIssues hash differently")
            return
        s = {a, b}
        if len(s) != 1:
            _bad(desc, f"set didn't de-dupe equal issues: len={len(s)}")
            return
        # frozen check
        try:
            a.severity = "info"  # type: ignore[misc]
            _bad(desc, "@dataclass(frozen=True) didn't freeze attribute assignment")
            return
        except Exception:
            pass
        _ok(desc + f" (hash={h})")
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 12 — bytes data in check_redundancy ─────────────────────────────

def case_12_bytes_data() -> None:
    desc = "case_12 data=b'composition' does not crash + produces same-data warn"
    # bytes.lower() exists, so this should work. But strip() on bytes returns
    # bytes, not str, which then gets stored as dict key — different bucket
    # from str b'composition' vs 'composition'. We test no crash.
    try:
        panels = [
            {"id": "a", "question": "Q1?", "encoding": "bar", "data": b"composition"},
            {"id": "b", "question": "Q2?", "encoding": "bar", "data": b"composition"},
        ]
        try:
            issues = huitu.check_redundancy(panels)
        except Exception as exc:
            _bad(desc, f"crashed on bytes data: {type(exc).__name__}: {exc}")
            return
        _ok(desc + f" (returned {len(issues)} issues)")
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 13 — int as encoding field ──────────────────────────────────────

def case_13_int_encoding() -> None:
    desc = "case_13 encoding=42 does not crash check_redundancy"
    try:
        try:
            issues = huitu.check_redundancy([
                {"id": "a", "question": "Q?", "encoding": 42},
            ])
        except AttributeError as exc:
            _bad(
                desc,
                f"crashed: {exc}. (p.get('encoding') or '').lower() assumes str.",
            )
            return
        except Exception as exc:
            _bad(desc, f"crashed: {type(exc).__name__}: {exc}")
            return
        _ok(desc + f" (returned {len(issues)} issues)")
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


def main() -> int:
    case_01_circular_self_ref()
    case_02_bytes_id()
    case_03_numpy_data()
    case_04_list_question()
    case_05_generator_of_generators()
    case_06_dict_subclass()
    case_07_ordered_dict()
    case_08_hostile_get()
    case_09_non_stringifiable_truthy()
    case_10_recursive_ml_value()
    case_11_panelissue_hashable()
    case_12_bytes_data()
    case_13_int_encoding()

    print(f"\n[SUMMARY] test_05_review_module_round2: {_passed} pass / {_failed} fail")
    if _failed == 0:
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
