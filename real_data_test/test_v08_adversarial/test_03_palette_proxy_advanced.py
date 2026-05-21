"""Round-3 adversarial test 3: advanced MappingProxyType semantics.

Round-2 made ``huitu.PALETTES`` a ``MappingProxyType`` over a
``_DefensivePaletteDict`` (a dict subclass storing tuples and overriding
``__getitem__`` to defensive-copy into a list).

This file probes the *semantic* corners that are too weird for test_01:
  * pickling the proxy itself (must TypeError; round-trip via dict() works)
  * subclassing the proxy type (must TypeError — mappingproxy is final from
    Python)
  * inner-list defensive-copy boundary (every probe returns a distinct list)
  * union operators ``|`` / ``|=`` semantics
  * reload of ``huitu.style`` — does the proxy still wrap the right thing?
  * absence of ChainMap-style ``maps`` attribute on the proxy

PASS criterion: all behaviors match the documented Round-2 contract.
FAIL criterion: the proxy leaks mutability through a corner not yet plugged.
"""

from __future__ import annotations

import copy
import importlib
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


# ── Case 1 — pickle of the proxy must TypeError ───────────────────────────

def case_01_pickle_proxy_blocked() -> None:
    desc = "case_01 pickle.dumps(PALETTES) raises TypeError"
    try:
        pickle.dumps(huitu.PALETTES)
        _bad(desc, "pickle succeeded; freeze contract broken")
    except TypeError as e:
        _ok(desc + f" -> {type(e).__name__}: {str(e)[:60]}")
    except Exception as e:
        _bad(desc, f"wrong exception {type(e).__name__}: {e}")


# ── Case 2 — pickle of dict(proxy) round-trips ────────────────────────────

def case_02_pickle_dict_proxy_works() -> None:
    desc = "case_02 pickle.loads(pickle.dumps(dict(PALETTES))) works"
    try:
        b = pickle.dumps(dict(huitu.PALETTES))
        d = pickle.loads(b)
    except Exception as e:
        _bad(desc, f"raised {type(e).__name__}: {e}")
        return
    if "nord" in d and list(d["nord"]) == list(huitu.PALETTES["nord"]):
        _ok(desc)
    else:
        _bad(desc, f"round-trip mismatch; d.nord={d.get('nord')!r}")


# ── Case 3 — subclassing mappingproxy is blocked ──────────────────────────

def case_03_cannot_subclass_proxy() -> None:
    desc = "case_03 cannot subclass type(PALETTES); raises TypeError"
    try:
        class Sneaky(type(huitu.PALETTES)):  # type: ignore[misc]
            pass
        _bad(desc, f"subclass succeeded: {Sneaky}")
    except TypeError as e:
        _ok(desc + f" -> {str(e)[:80]}")
    except Exception as e:
        _bad(desc, f"wrong exception {type(e).__name__}: {e}")


# ── Case 4 — defensive-copy isolates inner-list mutation ──────────────────

def case_04_inner_list_mutation_isolated() -> None:
    desc = ("case_04 PALETTES['nord'][0] = 'X'; PALETTES['nord'][0] must "
            "NOT be 'X' on the next access")
    huitu.PALETTES["nord"][0] = "X"
    after = huitu.PALETTES["nord"][0]
    if after != "X":
        _ok(desc + f" (next access starts with {after!r})")
    else:
        _bad(desc, "mutation leaked")


# ── Case 5 — aliased copies are distinct objects ──────────────────────────

def case_05_aliased_copies_distinct() -> None:
    desc = "case_05 a = PALETTES['nord']; b = PALETTES['nord']; a is b is False"
    a = huitu.PALETTES["nord"]
    b = huitu.PALETTES["nord"]
    if a is b:
        _bad(desc, "got the SAME list object across two subscripts")
    else:
        _ok(desc)


# ── Case 6 — alias mutation does not leak to subsequent access ────────────

def case_06_alias_mutation_isolated() -> None:
    desc = ("case_06 a = PALETTES['nord']; a[0]='X'; PALETTES['nord'][0] "
            "must NOT be 'X'")
    a = huitu.PALETTES["nord"]
    a[0] = "X"
    if huitu.PALETTES["nord"][0] != "X":
        _ok(desc)
    else:
        _bad(desc, "alias mutation leaked")


# ── Case 7 — |= on mappingproxy raises ────────────────────────────────────

def case_07_ior_blocked() -> None:
    desc = "case_07 PALETTES |= {'new': ('#000',)} raises TypeError"
    try:
        huitu.PALETTES |= {"new": ("#000",)}  # type: ignore[operator]
        _bad(desc, "|= succeeded; freeze leaked")
    except TypeError as e:
        _ok(desc + f" -> {str(e)[:70]}")
    except Exception as e:
        _bad(desc, f"wrong exception {type(e).__name__}: {e}")


# ── Case 8 — | (non-mutating) returns a fresh dict, leaves proxy alone ────

def case_08_or_returns_fresh_dict() -> None:
    desc = ("case_08 PALETTES | {'new': ('#000',)} returns a fresh dict; "
            "registry is unaffected")
    try:
        out = huitu.PALETTES | {"__or_test__": ("#000",)}  # type: ignore[operator]
    except TypeError:
        # If huitu disables | as well, that's also fine — note it.
        _ok(desc + " — | also blocked (stricter freeze)")
        return
    except Exception as e:
        _bad(desc, f"wrong exception {type(e).__name__}: {e}")
        return
    if not isinstance(out, dict):
        _bad(desc, f"got {type(out).__name__}, expected dict")
        return
    if "__or_test__" not in out:
        _bad(desc, "fresh dict missing union key")
        return
    if "__or_test__" in huitu.PALETTES:
        _bad(desc, "union LEAKED into the live registry!")
        return
    _ok(desc + " — got dict, registry untouched")


# ── Case 9 — reload huitu.style still produces a _DefensivePaletteDict ────

def case_09_reload_preserves_defensive_subclass() -> None:
    desc = ("case_09 importlib.reload(huitu.style) — new PALETTES is still a "
            "mappingproxy over a _DefensivePaletteDict")
    importlib.reload(huitu.style)
    proxy = huitu.style.PALETTES
    if type(proxy).__name__ != "mappingproxy":
        _bad(desc, f"after reload, type is {type(proxy).__name__}")
        return
    backing = huitu.style._PALETTES_BACKING
    if type(backing).__name__ != "_DefensivePaletteDict":
        _bad(desc, f"backing type is {type(backing).__name__}")
        return
    # And __getitem__ still defensive-copies?
    v = proxy["nord"]
    if not isinstance(v, list):
        _bad(desc, f"subscript returned {type(v).__name__}, expected list")
        return
    _ok(desc + " — defensive layer intact post-reload")


# ── Case 10 — reload rebinds _PALETTES_BACKING (fresh module-state) ───────

def case_10_reload_creates_new_backing_object() -> None:
    desc = ("case_10 after importlib.reload(huitu.style), "
            "_PALETTES_BACKING is a NEW object (id differs from snapshot)")
    snapshot = id(huitu.style._PALETTES_BACKING)
    importlib.reload(huitu.style)
    after = id(huitu.style._PALETTES_BACKING)
    if after != snapshot:
        _ok(desc + f" (snapshot id={snapshot}, post-reload id={after})")
    else:
        _bad(desc, "reload returned the SAME object — module-state not refreshed")


# ── Case 11 — proxy has NO ``maps`` attribute (it's not ChainMap) ─────────

def case_11_proxy_has_no_maps_attr() -> None:
    desc = "case_11 PALETTES has no ``maps`` attribute (proxy is not ChainMap)"
    if hasattr(huitu.PALETTES, "maps"):
        _bad(desc, "proxy exposed `maps` — investigate")
    else:
        _ok(desc)


# ── Case 12 — deepcopy of the proxy itself is blocked ─────────────────────

def case_12_deepcopy_proxy_blocked() -> None:
    desc = ("case_12 copy.deepcopy(PALETTES) — fails because mappingproxy "
            "uses pickle protocol under the hood")
    try:
        copy.deepcopy(huitu.PALETTES)
        _bad(desc, "deepcopy succeeded; proxy isn't actually frozen against deepcopy")
    except TypeError as e:
        _ok(desc + f" -> {str(e)[:60]}")
    except Exception as e:
        _bad(desc, f"wrong exception {type(e).__name__}: {e}")


# ── Case 13 — deepcopy of dict(proxy) works and is independent ────────────

def case_13_deepcopy_dict_proxy_independent() -> None:
    desc = ("case_13 deep_d = copy.deepcopy(dict(PALETTES)); mutating "
            "deep_d['nord'][0] leaves PALETTES['nord'][0] untouched")
    d = copy.deepcopy(dict(huitu.PALETTES))
    if "nord" not in d:
        _bad(desc, "nord missing from deepcopy")
        return
    original_first = huitu.PALETTES["nord"][0]
    if not isinstance(d["nord"], list):
        # Promote to list so we can mutate (immutable tuples can't be poked).
        d["nord"] = list(d["nord"])
    d["nord"][0] = "<<deepcopy_poison>>"
    after = huitu.PALETTES["nord"][0]
    if after == original_first:
        _ok(desc)
    else:
        _bad(desc, f"PALETTES['nord'][0] became {after!r}")


# ── Case 14 — empty defensive dict accepts __getitem__ on missing → KeyError ─

def case_14_missing_key_raises_keyerror() -> None:
    desc = ("case_14 PALETTES['__definitely_missing__'] raises KeyError "
            "(defensive layer must not swallow it)")
    try:
        huitu.PALETTES["__definitely_missing__"]
    except KeyError:
        _ok(desc)
        return
    except Exception as e:
        _bad(desc, f"wrong exception {type(e).__name__}: {e}")
        return
    _bad(desc, "no exception raised — defensive layer swallowed the miss")


# ── Case 15 — repr/str of proxy doesn't crash ────────────────────────────

def case_15_proxy_repr_str_safe() -> None:
    desc = "case_15 repr(PALETTES) and str(PALETTES) return strings (no crash)"
    try:
        r = repr(huitu.PALETTES)
        s = str(huitu.PALETTES)
    except Exception as e:
        _bad(desc, f"raised {type(e).__name__}: {e}")
        return
    if isinstance(r, str) and isinstance(s, str):
        _ok(desc + f" (repr starts with {r[:30]!r})")
    else:
        _bad(desc, f"non-str: repr={type(r).__name__} str={type(s).__name__}")


# ── Case 16 — proxy iteration preserves all keys ─────────────────────────

def case_16_iteration_covers_all_keys() -> None:
    desc = ("case_16 iterating PALETTES yields the same keys as "
            "list(_PALETTES_BACKING)")
    via_proxy = set(huitu.PALETTES)
    via_backing = set(huitu.style._PALETTES_BACKING)
    if via_proxy == via_backing:
        _ok(desc + f" ({len(via_proxy)} keys)")
    else:
        diff = via_backing ^ via_proxy
        _bad(desc, f"key sets differ by {diff!r}")


# ── Case 17 — concurrent subscripts return independent objects ───────────

def case_17_concurrent_subscripts_independent() -> None:
    desc = ("case_17 5 sequential PALETTES['nord'] calls return 5 distinct "
            "list objects (no caching)")
    snapshots = [huitu.PALETTES["nord"] for _ in range(5)]
    ids = {id(s) for s in snapshots}
    if len(ids) == 5:
        _ok(desc)
    else:
        _bad(desc, f"only {len(ids)} distinct ids among 5 subscripts — "
                   "defensive copy is being cached/aliased")


def main() -> int:
    case_01_pickle_proxy_blocked()
    case_02_pickle_dict_proxy_works()
    case_03_cannot_subclass_proxy()
    case_04_inner_list_mutation_isolated()
    case_05_aliased_copies_distinct()
    case_06_alias_mutation_isolated()
    case_07_ior_blocked()
    case_08_or_returns_fresh_dict()
    # Reload cases must come last so they don't perturb earlier state.
    case_11_proxy_has_no_maps_attr()
    case_12_deepcopy_proxy_blocked()
    case_13_deepcopy_dict_proxy_independent()
    case_14_missing_key_raises_keyerror()
    case_15_proxy_repr_str_safe()
    case_16_iteration_covers_all_keys()
    case_17_concurrent_subscripts_independent()
    case_09_reload_preserves_defensive_subclass()
    case_10_reload_creates_new_backing_object()

    print(f"\n[SUMMARY] test_03_palette_proxy_advanced: {_passed} pass / {_failed} fail")
    if _failed == 0:
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
