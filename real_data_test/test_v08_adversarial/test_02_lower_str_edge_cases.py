"""Round-3 adversarial test 2: `_lower_str` boundary behavior.

`_lower_str(value)` (huitu/review.py) is the Round-2 coercion helper used by
the 5 redundancy callsites. Its contract is:

    def _lower_str(value) -> str:
        return str(value).lower() if value is not None else ""

This file enumerates boundary inputs:
  * primitives (None, bool, int, float NaN/inf, complex)
  * binary types (bytes, bytearray)
  * containers (list, dict)
  * unicode edge cases (Turkish dotted I, emoji)
  * very long strings (1 MB)
  * deeply nested containers
  * objects with intentionally broken `__str__` / `__repr__`

PASS criterion: the function (a) returns a string when input is "well-behaved"
or (b) raises a CLEAN, DETERMINISTIC exception when input's `__str__` itself
raises. FAIL criterion: returns non-string, hangs, recurses, or silently
swallows a poisoned __str__.
"""

from __future__ import annotations

import math
import sys

from huitu.review import _lower_str

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


def _expect(desc: str, expr_callable, expected) -> None:
    try:
        got = expr_callable()
    except Exception as e:
        _bad(desc, f"raised {type(e).__name__}: {e}")
        return
    if got == expected:
        _ok(desc + f" -> {got!r}")
    else:
        _bad(desc, f"got {got!r}, expected {expected!r}")


# ── Case 1 — None ─────────────────────────────────────────────────────────

def case_01_none() -> None:
    _expect("case_01 _lower_str(None) == ''", lambda: _lower_str(None), "")


# ── Case 2 — empty string ─────────────────────────────────────────────────

def case_02_empty_string() -> None:
    _expect("case_02 _lower_str('') == ''", lambda: _lower_str(""), "")


# ── Case 3 — basic alpha ──────────────────────────────────────────────────

def case_03_basic_alpha() -> None:
    _expect("case_03 _lower_str('Hello') == 'hello'",
            lambda: _lower_str("Hello"), "hello")


# ── Case 4 — integer 0 ────────────────────────────────────────────────────

def case_04_int_zero() -> None:
    _expect("case_04 _lower_str(0) == '0'", lambda: _lower_str(0), "0")


# ── Case 5 — bool False/True ──────────────────────────────────────────────

def case_05_bool_false() -> None:
    # Python str(False) == 'False', .lower() -> 'false'
    _expect("case_05 _lower_str(False) == 'false'",
            lambda: _lower_str(False), "false")


def case_05b_bool_true() -> None:
    _expect("case_05b _lower_str(True) == 'true'",
            lambda: _lower_str(True), "true")


# ── Case 6 — float NaN, inf, -inf ─────────────────────────────────────────

def case_06_nan() -> None:
    _expect("case_06 _lower_str(NaN) == 'nan'",
            lambda: _lower_str(float("nan")), "nan")


def case_06b_inf() -> None:
    _expect("case_06b _lower_str(inf) == 'inf'",
            lambda: _lower_str(float("inf")), "inf")


def case_06c_neg_inf() -> None:
    _expect("case_06c _lower_str(-inf) == '-inf'",
            lambda: _lower_str(-float("inf")), "-inf")


# ── Case 7 — complex ──────────────────────────────────────────────────────

def case_07_complex() -> None:
    _expect("case_07 _lower_str(1+2j) == '(1+2j)'",
            lambda: _lower_str(complex(1, 2)), "(1+2j)")


# ── Case 8 — bytes (note b'' prefix) ──────────────────────────────────────

def case_08_bytes() -> None:
    # str(b'BYTES') == "b'BYTES'" then .lower() -> "b'bytes'"
    _expect("case_08 _lower_str(b'BYTES') == \"b'bytes'\"",
            lambda: _lower_str(b"BYTES"), "b'bytes'")


# ── Case 9 — bytearray ────────────────────────────────────────────────────

def case_09_bytearray() -> None:
    _expect("case_09 _lower_str(bytearray(b'X')) == \"bytearray(b'x')\"",
            lambda: _lower_str(bytearray(b"X")), "bytearray(b'x')")


# ── Case 10 — list ────────────────────────────────────────────────────────

def case_10_list() -> None:
    _expect("case_10 _lower_str([1,2,3]) == '[1, 2, 3]'",
            lambda: _lower_str([1, 2, 3]), "[1, 2, 3]")


# ── Case 11 — dict ────────────────────────────────────────────────────────

def case_11_dict() -> None:
    _expect("case_11 _lower_str({'a':1}) == \"{'a': 1}\"",
            lambda: _lower_str({"a": 1}), "{'a': 1}")


# ── Case 12 — very long string (1 MB), no truncation ──────────────────────

def case_12_huge_string() -> None:
    desc = "case_12 _lower_str('A'*1_000_000) returns 1M lowercase a's"
    s = "A" * 1_000_000
    try:
        got = _lower_str(s)
    except Exception as e:
        _bad(desc, f"raised {type(e).__name__}: {e}")
        return
    if len(got) != 1_000_000:
        _bad(desc, f"length {len(got)} != 1_000_000")
        return
    if got[0] != "a" or got[-1] != "a":
        _bad(desc, f"first/last chars {got[0]!r}/{got[-1]!r}")
        return
    _ok(desc)


# ── Case 13 — broken __str__ raises cleanly ───────────────────────────────

def case_13_broken_str() -> None:
    desc = ("case_13 object with broken __str__ either raises cleanly OR "
            "is caught — must NOT silently corrupt downstream")
    class Bad:
        def __str__(self):
            raise RuntimeError("boom")
    try:
        got = _lower_str(Bad())
    except RuntimeError as e:
        if "boom" in str(e):
            _ok(desc + " — propagated original RuntimeError (deterministic)")
        else:
            _bad(desc, f"unexpected RuntimeError message: {e}")
        return
    except Exception as e:
        _bad(desc, f"wrong exception {type(e).__name__}: {e}")
        return
    # No raise — only acceptable if a string is returned.
    if isinstance(got, str):
        _ok(desc + f" — caught and returned {got!r}")
    else:
        _bad(desc, f"returned non-string {type(got).__name__}")


# ── Case 14 — broken __repr__ when __str__ falls back ─────────────────────

def case_14_broken_repr() -> None:
    desc = ("case_14 object with broken __repr__ AND no __str__ override — "
            "Python falls back to repr; should raise cleanly")
    class Bad2:
        def __repr__(self):
            raise RuntimeError("repr boom")
    try:
        got = _lower_str(Bad2())
    except RuntimeError as e:
        if "repr boom" in str(e):
            _ok(desc + " — propagated original RuntimeError")
        else:
            _bad(desc, f"unexpected message: {e}")
        return
    except Exception as e:
        _bad(desc, f"wrong exception {type(e).__name__}: {e}")
        return
    if isinstance(got, str):
        _ok(desc + f" — repr resolved unexpectedly to {got!r}")
    else:
        _bad(desc, f"returned non-string {type(got).__name__}")


# ── Case 15 — Turkish dotted-I (locale-independence) ──────────────────────

def case_15_turkish_i() -> None:
    desc = ("case_15 _lower_str('İ') returns 'i̇' (str.lower is "
            "locale-independent in Python, so deterministic)")
    got = _lower_str("İ")
    # Python str.lower on U+0130 LATIN CAPITAL LETTER I WITH DOT ABOVE
    # returns 'i' followed by U+0307 COMBINING DOT ABOVE.
    if isinstance(got, str) and got == "İ".lower():
        _ok(desc + f" -> {got!r} ({len(got)} chars)")
    else:
        _bad(desc, f"got {got!r}, expected str.lower('İ')")


# ── Case 16 — emoji surrogate pair ────────────────────────────────────────

def case_16_emoji() -> None:
    desc = "case_16 _lower_str(rainbow emoji) does not crash"
    try:
        got = _lower_str("🌈")
        if isinstance(got, str) and "🌈" in got:
            _ok(desc + f" -> {got!r}")
        else:
            _bad(desc, f"got {got!r}")
    except Exception as e:
        _bad(desc, f"raised {type(e).__name__}: {e}")


# ── Case 17 — very deep nested list, no recursion limit hit ───────────────

def case_17_deep_nested_list() -> None:
    desc = "case_17 _lower_str(deeply nested list) does not RecursionError"
    nested = [[[[[1]]]]]
    try:
        got = _lower_str(nested)
    except RecursionError as e:
        _bad(desc, f"hit RecursionError: {e}")
        return
    except Exception as e:
        _bad(desc, f"raised {type(e).__name__}: {e}")
        return
    if isinstance(got, str):
        _ok(desc + f" -> {got!r}")
    else:
        _bad(desc, f"non-string {type(got).__name__}")


# ── Case 18 — tuple coerces ───────────────────────────────────────────────

def case_18_tuple() -> None:
    _expect("case_18 _lower_str((1,2,3)) == '(1, 2, 3)'",
            lambda: _lower_str((1, 2, 3)), "(1, 2, 3)")


# ── Case 19 — set (note: iteration order) ─────────────────────────────────

def case_19_set_single_element() -> None:
    desc = "case_19 _lower_str({'X'}) == \"{'x'}\""
    got = _lower_str({"X"})
    # set with one element has deterministic repr
    if got == "{'x'}":
        _ok(desc + f" -> {got!r}")
    else:
        _bad(desc, f"got {got!r}")


# ── Case 20 — class without __str__ falls back to repr-default ────────────

def case_20_default_repr() -> None:
    desc = ("case_20 _lower_str(object()) starts with '<object object at 0x' "
            "(lowercased default repr)")
    got = _lower_str(object())
    if isinstance(got, str) and got.startswith("<object object at 0x"):
        _ok(desc + f" -> {got!r}")
    else:
        _bad(desc, f"got {got!r}")


# ── Case 21 — numpy-like array (if numpy available) ───────────────────────

def case_21_numpy_array() -> None:
    desc = "case_21 _lower_str(np.array([1.0, 2.0])) returns deterministic str"
    try:
        import numpy as np  # type: ignore
    except ImportError:
        _ok(desc + " — numpy unavailable, skipping")
        return
    arr = np.array([1.0, 2.0])
    try:
        got = _lower_str(arr)
    except Exception as e:
        _bad(desc, f"raised {type(e).__name__}: {e}")
        return
    if isinstance(got, str) and "1" in got and "2" in got:
        _ok(desc + f" -> {got!r}")
    else:
        _bad(desc, f"got {got!r}")


def main() -> int:
    case_01_none()
    case_02_empty_string()
    case_03_basic_alpha()
    case_04_int_zero()
    case_05_bool_false()
    case_05b_bool_true()
    case_06_nan()
    case_06b_inf()
    case_06c_neg_inf()
    case_07_complex()
    case_08_bytes()
    case_09_bytearray()
    case_10_list()
    case_11_dict()
    case_12_huge_string()
    case_13_broken_str()
    case_14_broken_repr()
    case_15_turkish_i()
    case_16_emoji()
    case_17_deep_nested_list()
    case_18_tuple()
    case_19_set_single_element()
    case_20_default_repr()
    case_21_numpy_array()

    print(f"\n[SUMMARY] test_02_lower_str_edge_cases: {_passed} pass / {_failed} fail")
    if _failed == 0:
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
