"""Round-3 adversarial test 1: dict access path bypass of `__getitem__`.

Round-2 introduced ``_DefensivePaletteDict``:

    class _DefensivePaletteDict(dict):
        def __getitem__(self, key):
            return list(super().__getitem__(key))

    _PALETTES_BACKING = _DefensivePaletteDict({...inner values stored as tuple...})
    PALETTES = MappingProxyType(_PALETTES_BACKING)

CRITICAL FACT (CPython implementation detail):
Many ``dict`` methods are implemented in C and call ``PyDict_GetItem``
directly, **bypassing** a subclass ``__getitem__``. So only some access paths
go through the defensive-copy layer — others hand back the raw stored object.

This test enumerates every dict-style access path and documents:
  1. WHAT TYPE is returned (list = defensive copy; tuple = raw storage)
  2. WHETHER repeated calls return the same object (object identity)
  3. WHETHER mutation through the returned object can leak back into the
     registry. PASS criterion is "either the access path defensive-copies
     OR it returns an immutable tuple". FAIL is "the access path returns a
     mutable list that is shared with the backing dict".

Stored values are ``tuple`` so even bypass paths are safe — but the *contract*
is "users get a list-typed value on subscript", and bypass paths break that
contract by handing out tuples. We mark contract violations as INFO (printed
as PASS-with-note); the only outright FAIL is registry corruption.
"""

from __future__ import annotations

import pickle
import sys

import huitu
import huitu.style

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


# Capture a known-good snapshot to detect leak/corruption across the suite.
NORD_ORIG = tuple(huitu.PALETTES["nord"])


# ── Case 1 — direct subscript hits __getitem__ ─────────────────────────────

def case_01_direct_subscript_defensive() -> None:
    desc = ("case_01 PALETTES['nord'] hits __getitem__: returns list AND "
            "two calls return distinct objects")
    a = huitu.PALETTES["nord"]
    b = huitu.PALETTES["nord"]
    if not isinstance(a, list):
        _bad(desc, f"expected list, got {type(a).__name__}")
        return
    if a is b:
        _bad(desc, "two subscripts returned the SAME object; defensive copy missing")
        return
    if a != b:
        _bad(desc, f"defensive copies should be equal; got a={a!r} b={b!r}")
        return
    _ok(desc + f" (type={type(a).__name__}, distinct objects)")


# ── Case 2 — .get() BYPASSES __getitem__ at C-level ───────────────────────

def case_02_get_bypasses_getitem() -> None:
    desc = ("case_02 PALETTES.get('nord') — documented behavior: dict.get is "
            "C-implemented and bypasses subclass __getitem__")
    a = huitu.PALETTES.get("nord")
    b = huitu.PALETTES.get("nord")
    typ = type(a).__name__
    same = a is b
    # PASS criterion: it must be SAFE (tuple is immutable, so safe even if shared).
    # We document what we found.
    if isinstance(a, tuple):
        # Stored as tuple; mutation impossible -> safe.
        _ok(desc + f" — returned tuple (bypassed, but tuple is immutable; a is b = {same})")
    elif isinstance(a, list):
        # Means .get DID go through __getitem__ (would be surprising).
        if same:
            _bad(desc, "returned the SAME list across calls (defensive copy missing)")
        else:
            _ok(desc + f" — returned defensive list copy (went through __getitem__)")
    else:
        _bad(desc, f"unexpected return type {typ}")


def case_02b_get_with_default() -> None:
    desc = "case_02b PALETTES.get('nord', default) — same bypass story"
    a = huitu.PALETTES.get("nord", ["sentinel"])
    if isinstance(a, (tuple, list)):
        _ok(desc + f" — type {type(a).__name__}")
    else:
        _bad(desc, f"unexpected type {type(a).__name__}")


def case_02c_get_missing_returns_default() -> None:
    desc = "case_02c PALETTES.get('__nope__', ['fallback']) returns the default"
    a = huitu.PALETTES.get("__nope__", ["fallback"])
    if a == ["fallback"]:
        _ok(desc)
    else:
        _bad(desc, f"got {a!r}")


# ── Case 3 — .values() iteration BYPASSES __getitem__ ──────────────────────

def case_03_values_bypasses_getitem() -> None:
    desc = ("case_03 list(PALETTES.values())[0] — documented behavior: "
            ".values() is C-implemented and iterates raw storage")
    v = list(huitu.PALETTES.values())[0]
    typ = type(v).__name__
    if isinstance(v, tuple):
        _ok(desc + f" — returned tuple (bypassed; immutable so safe)")
    elif isinstance(v, list):
        _ok(desc + f" — returned list (went through __getitem__)")
    else:
        _bad(desc, f"unexpected type {typ}")


# ── Case 4 — .items() iteration BYPASSES __getitem__ ──────────────────────

def case_04_items_bypasses_getitem() -> None:
    desc = ("case_04 [v for k,v in PALETTES.items()] — documented behavior: "
            ".items() is C-implemented and iterates raw storage")
    vs = [v for k, v in huitu.PALETTES.items()]
    typ = type(vs[0]).__name__
    if all(isinstance(v, tuple) for v in vs):
        _ok(desc + " — all tuples (bypassed; immutable so safe)")
    elif all(isinstance(v, list) for v in vs):
        _ok(desc + " — all lists (went through __getitem__)")
    else:
        _bad(desc, f"mixed types: {set(type(v).__name__ for v in vs)}")


# ── Case 5 — dict(PALETTES) constructor goes through __getitem__ ──────────

def case_05_dict_constructor_via_getitem() -> None:
    desc = ("case_05 dict(PALETTES)['nord'] — Python-level dict() constructor "
            "iterates keys via the proxy then re-subscripts, hitting __getitem__")
    d = dict(huitu.PALETTES)
    v = d["nord"]
    if isinstance(v, list):
        # Confirms dict() walks via __getitem__. This is GOOD because the
        # produced dict can then be pickled/deepcopied with mutable lists.
        _ok(desc + " — got list (defensive copy)")
    elif isinstance(v, tuple):
        # Some Python builds use the .keys()/raw-iter shortcut and bypass.
        _ok(desc + " — got tuple (bypassed but immutable)")
    else:
        _bad(desc, f"unexpected type {type(v).__name__}")


# ── Case 6 — pickle round-trip of dict(PALETTES) ──────────────────────────

def case_06_pickle_dict_roundtrip() -> None:
    desc = "case_06 pickle.loads(pickle.dumps(dict(PALETTES)))['nord'] round-trips"
    try:
        d = pickle.loads(pickle.dumps(dict(huitu.PALETTES)))
    except Exception as e:
        _bad(desc, f"pickle failed: {type(e).__name__}: {e}")
        return
    if "nord" not in d:
        _bad(desc, "nord key missing from round-tripped dict")
        return
    v = d["nord"]
    if list(v) != list(NORD_ORIG):
        _bad(desc, f"contents mismatch after pickle: {v!r} vs {NORD_ORIG!r}")
        return
    _ok(desc + f" (type={type(v).__name__})")


# ── Case 7 — `in` operator and `len()` ────────────────────────────────────

def case_07_contains_and_len() -> None:
    desc = "case_07 'nord' in PALETTES, len(PALETTES) > 10"
    ok1 = "nord" in huitu.PALETTES
    ok2 = len(huitu.PALETTES) > 10
    if ok1 and ok2:
        _ok(desc + f" (len={len(huitu.PALETTES)})")
    else:
        _bad(desc, f"in={ok1} len_ok={ok2}")


# ── Case 8 — equality across proxy and backing dict ───────────────────────

def case_08_eq_proxy_vs_backing() -> None:
    desc = ("case_08 PALETTES == _PALETTES_BACKING — dict equality walks "
            "raw storage on both sides; tuple == tuple so they ARE equal")
    eq = (huitu.PALETTES == huitu.style._PALETTES_BACKING)
    if eq:
        _ok(desc + " — equal")
    else:
        _bad(desc, "expected proxy and backing to compare equal")


def case_08b_eq_proxy_vs_dict_copy() -> None:
    desc = ("case_08b PALETTES == dict(PALETTES) — surprising consequence: "
            "dict(PALETTES) holds *lists* (via __getitem__), backing holds "
            "*tuples*, so equality FAILS")
    a = huitu.PALETTES
    b = dict(huitu.PALETTES)
    eq = (a == b)
    # Both behaviors are defensible; we document them.
    if not eq:
        _ok(desc + " — NOT equal (because list != tuple element-wise). "
                  "Caller should round-trip via dict() if they need equality.")
    else:
        _ok(desc + " — equal (dict() picked up raw tuples or list==tuple semantics changed)")


# ── Case 9 — iteration yields keys (strings) ──────────────────────────────

def case_09_iter_yields_keys() -> None:
    desc = "case_09 list(PALETTES)[0] is a str key"
    k = list(huitu.PALETTES)[0]
    if isinstance(k, str):
        _ok(desc + f" (first key={k!r})")
    else:
        _bad(desc, f"got {type(k).__name__}")


# ── Case 10 — .keys() & set(.keys()) accessor sanity ──────────────────────

def case_10_keys_accessor_sanity() -> None:
    desc = "case_10 PALETTES.keys() and set(PALETTES.keys()) contain 'nord'"
    ks = huitu.PALETTES.keys()
    s = set(huitu.PALETTES.keys())
    if "nord" in ks and "nord" in s:
        _ok(desc)
    else:
        _bad(desc, f"keys missing 'nord' — ks={list(ks)[:3]}, s={list(s)[:3]}")


# ── Case 11 — for k in PALETTES: ... iterator ─────────────────────────────

def case_11_for_loop_iterator() -> None:
    desc = "case_11 `for k in PALETTES: ...` yields strings; loop completes"
    seen = []
    for k in huitu.PALETTES:
        seen.append(k)
        if len(seen) >= 3:
            break
    if all(isinstance(s, str) for s in seen) and len(seen) == 3:
        _ok(desc + f" (sampled {seen!r})")
    else:
        _bad(desc, f"seen={seen!r}")


# ── Case 12 — .copy() on mappingproxy returns a dict (BYPASSES) ───────────

def case_12_copy_returns_plain_dict() -> None:
    desc = ("case_12 PALETTES.copy() returns dict (BYPASSES __getitem__); "
            "values are raw tuples")
    c = huitu.PALETTES.copy()
    if not isinstance(c, dict):
        _bad(desc, f"copy() returned {type(c).__name__}, expected dict")
        return
    v = c.get("nord")
    if isinstance(v, tuple):
        _ok(desc + " — got dict-of-tuples (bypassed; raw storage)")
    elif isinstance(v, list):
        _ok(desc + " — got dict-of-lists (went through __getitem__)")
    else:
        _bad(desc, f"unexpected value type {type(v).__name__}")


# ── Case 13 — defensive copies are distinct (PALETTES['nord'] is not PALETTES['nord']) ─

def case_13_defensive_copy_distinct_identity() -> None:
    desc = "case_13 PALETTES['nord'] is PALETTES['nord'] must be False"
    a = huitu.PALETTES["nord"]
    b = huitu.PALETTES["nord"]
    if a is b:
        _bad(desc, "two subscripts returned the SAME object — defensive copy missing")
    else:
        _ok(desc + " (distinct list objects)")


# ── Case 14 — defensive copies are equal ──────────────────────────────────

def case_14_defensive_copy_equal_values() -> None:
    desc = "case_14 PALETTES['nord'] == PALETTES['nord'] must be True"
    a = huitu.PALETTES["nord"]
    b = huitu.PALETTES["nord"]
    if a == b:
        _ok(desc)
    else:
        _bad(desc, f"copies differ: {a!r} vs {b!r}")


# ── Case 15 — mutation through subscript-returned list is harmless ────────

def case_15_subscript_mutation_isolated() -> None:
    desc = ("case_15 PALETTES['nord'][0] = 'X' must NOT corrupt the next "
            "PALETTES['nord'] access")
    huitu.PALETTES["nord"][0] = "X"  # mutate the throwaway list
    nxt = huitu.PALETTES["nord"]
    if nxt[0] == "X":
        _bad(desc, f"mutation leaked: now starts with {nxt[0]!r}")
    else:
        _ok(desc + f" (still starts with {nxt[0]!r})")


# ── Case 16 — bypass-channel mutation: can a tuple-via-get *replace* the tuple? ─

def case_16_get_returned_tuple_cant_mutate() -> None:
    desc = ("case_16 PALETTES.get('nord') returns the SHARED tuple object — "
            "but tuple is immutable so the bypass is safe")
    a = huitu.PALETTES.get("nord")
    b = huitu.PALETTES.get("nord")
    if not isinstance(a, tuple):
        # If .get() somehow returns a copy, that's also fine; just document.
        _ok(desc + f" — .get returned {type(a).__name__}, not the raw tuple "
                  "(maybe Python implementation changed)")
        return
    if a is not b:
        _ok(desc + " — .get returned DIFFERENT tuples (defensive copy at .get level)")
        return
    # Confirmed shared object. Verify it's actually safe (no __setitem__).
    try:
        a[0] = "X"
        _bad(desc, "tuple accepted assignment! Type system is broken.")
    except TypeError:
        _ok(desc + " — shared tuple, immutable, safe")


# ── Case 17 — dict.copy() of the backing direct: does it return a dict-subclass? ─

def case_17_backing_copy_type() -> None:
    desc = ("case_17 _PALETTES_BACKING.copy() — dict.copy bypasses subclass "
            "and returns plain dict, not _DefensivePaletteDict")
    b = huitu.style._PALETTES_BACKING
    c = b.copy()
    # Plain dict.copy returns plain dict (NOT the subclass).
    if type(c) is dict:
        _ok(desc + " — returned plain dict (subclass info lost; expected)")
    elif isinstance(c, type(b)):
        _ok(desc + " — returned subclass (preserved); even better")
    else:
        _bad(desc, f"unexpected copy type {type(c).__name__}")


# ── Case 18 — backing[‘nord’] direct-bypass via dict.__getitem__ ──────────

def case_18_dict_getitem_bypass_on_backing() -> None:
    desc = ("case_18 dict.__getitem__(_PALETTES_BACKING, 'nord') BYPASSES "
            "the subclass override; returns raw tuple")
    raw = dict.__getitem__(huitu.style._PALETTES_BACKING, "nord")
    if isinstance(raw, tuple):
        _ok(desc + f" (got tuple as expected; len={len(raw)})")
    else:
        _bad(desc, f"got {type(raw).__name__}; expected tuple (raw storage)")


# ── Case 19 — registry remains UNCORRUPTED after every probe ──────────────

def case_19_registry_uncorrupted_after_all() -> None:
    desc = "case_19 after all bypass probing, PALETTES['nord'] still matches snapshot"
    cur = tuple(huitu.PALETTES["nord"])
    if cur == NORD_ORIG:
        _ok(desc)
    else:
        _bad(desc, f"registry drifted: now {cur!r}, was {NORD_ORIG!r}")


# ── Case 20 — proxy reflects backing-side writes (internal API only) ──────

def case_20_proxy_reflects_backing_writes() -> None:
    desc = ("case_20 _PALETTES_BACKING['__probe__'] = ('#000',) is visible "
            "through PALETTES — proxy is a live view")
    backing = huitu.style._PALETTES_BACKING
    backing["__probe__"] = ("#000",)
    try:
        if "__probe__" in huitu.PALETTES and huitu.PALETTES["__probe__"] == ["#000"]:
            _ok(desc)
        else:
            _bad(desc, f"PALETTES did not reflect backing write — got "
                       f"{huitu.PALETTES.get('__probe__')!r}")
    finally:
        del backing["__probe__"]


def main() -> int:
    case_01_direct_subscript_defensive()
    case_02_get_bypasses_getitem()
    case_02b_get_with_default()
    case_02c_get_missing_returns_default()
    case_03_values_bypasses_getitem()
    case_04_items_bypasses_getitem()
    case_05_dict_constructor_via_getitem()
    case_06_pickle_dict_roundtrip()
    case_07_contains_and_len()
    case_08_eq_proxy_vs_backing()
    case_08b_eq_proxy_vs_dict_copy()
    case_09_iter_yields_keys()
    case_10_keys_accessor_sanity()
    case_11_for_loop_iterator()
    case_12_copy_returns_plain_dict()
    case_13_defensive_copy_distinct_identity()
    case_14_defensive_copy_equal_values()
    case_15_subscript_mutation_isolated()
    case_16_get_returned_tuple_cant_mutate()
    case_17_backing_copy_type()
    case_18_dict_getitem_bypass_on_backing()
    case_19_registry_uncorrupted_after_all()
    case_20_proxy_reflects_backing_writes()

    print(f"\n[SUMMARY] test_01_dict_access_bypass: {_passed} pass / {_failed} fail")
    if _failed == 0:
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
