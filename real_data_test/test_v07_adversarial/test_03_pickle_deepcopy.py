"""Adversarial test 3 (Round 2): serialization escape hatches.

``MappingProxyType`` is intentionally not picklable in stdlib (Python issue
#33373). That's *protective* — it means a user cannot accidentally pickle
the proxy and ship a corrupted copy. We just check that the failure mode
is clear (TypeError with a useful message, not a silent partial dump).

Conversely, ``dict(huitu.SEMANTIC_PALETTE)`` MUST work and round-trip
through pickle / json / deepcopy — that's the documented escape hatch.
And mutating the dict copy MUST NOT poison the original registry.
"""

from __future__ import annotations

import copy
import json
import pickle
import sys

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


HERO_ORIG = huitu.role("hero")
NORD_ORIG = list(huitu.PALETTES["nord"])


# ── Case 1 — pickle of mappingproxy raises (documented) ──────────────────

def case_01_pickle_proxy_raises() -> None:
    desc = "case_01 pickle.dumps(SEMANTIC_PALETTE) raises with clear TypeError"
    try:
        try:
            pickle.dumps(huitu.SEMANTIC_PALETTE)
            _bad(
                desc,
                "pickle succeeded — protect-via-non-picklable lost. "
                "User can now ship a 'frozen' copy that's actually a free dict.",
            )
            return
        except TypeError as exc:
            msg = str(exc)
            if "mappingproxy" in msg.lower() or "cannot pickle" in msg.lower():
                _ok(desc)
            else:
                _bad(desc, f"TypeError msg unhelpful: {msg!r}")
        except Exception as exc:
            _bad(desc, f"wrong exception {type(exc).__name__}: {exc}")
    except Exception as exc:
        _bad(desc, f"outer crash: {type(exc).__name__}: {exc}")


# ── Case 2 — pickle of dict copy round-trips equal ───────────────────────

def case_02_pickle_dict_copy() -> None:
    desc = "case_02 pickle round-trip of dict(SEMANTIC_PALETTE) preserves all keys"
    try:
        d = dict(huitu.SEMANTIC_PALETTE)
        blob = pickle.dumps(d)
        loaded = pickle.loads(blob)
        if loaded == d and set(loaded) == set(huitu.SEMANTIC_PALETTE):
            _ok(desc)
        else:
            _bad(desc, f"keys drifted: orig={sorted(d)[:3]}…, loaded={sorted(loaded)[:3]}…")
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 3 — copy.copy on the proxy ──────────────────────────────────────

def case_03_copy_copy_proxy() -> None:
    desc = "case_03 copy.copy(SEMANTIC_PALETTE) either returns proxy or raises clearly"
    # Behavior on Python 3.13: copy.copy uses pickle internally so it
    # raises TypeError("cannot pickle 'mappingproxy' object"). Either
    # outcome is acceptable as long as it isn't silently giving back a
    # writable dict.
    try:
        c = copy.copy(huitu.SEMANTIC_PALETTE)
    except TypeError:
        _ok(desc + " (raised TypeError — same as pickle)")
        return
    except Exception as exc:
        _bad(desc, f"wrong exception {type(exc).__name__}: {exc}")
        return
    # If it returned something, it must not be a writable dict aliasing the
    # original storage.
    if isinstance(c, dict) and not isinstance(type(c), type(type({}))):
        # Likely a mappingproxy clone — still safe.
        _ok(desc)
        return
    if isinstance(c, dict):
        # Writable dict copy is acceptable as long as it doesn't alias.
        try:
            c["hero"] = "#FFFFFF"
        except TypeError:
            _ok(desc + " (returned proxy)")
            return
        if huitu.role("hero") == HERO_ORIG:
            _ok(desc + " (returned writable but detached dict)")
        else:
            _bad(desc, "copy.copy returned an aliasing dict — mutation leaked into role()")
        return
    _bad(desc, f"returned unexpected type {type(c).__name__}")


# ── Case 4 — copy.deepcopy on the proxy ──────────────────────────────────

def case_04_deepcopy_proxy() -> None:
    desc = "case_04 copy.deepcopy(SEMANTIC_PALETTE) is safe (raises or returns detached)"
    try:
        c = copy.deepcopy(huitu.SEMANTIC_PALETTE)
    except TypeError:
        _ok(desc + " (raised TypeError — proxy not deep-copyable on this Python)")
        return
    except Exception as exc:
        _bad(desc, f"wrong exception {type(exc).__name__}: {exc}")
        return
    if isinstance(c, dict):
        try:
            c["hero"] = "#FFFFFF"
        except TypeError:
            pass  # frozen → safe
        if huitu.role("hero") == HERO_ORIG:
            _ok(desc + " (deepcopy returned detached object)")
        else:
            _bad(desc, "deepcopy aliased the underlying dict — mutation leaked")
    else:
        _bad(desc, f"unexpected return type {type(c).__name__}")


# ── Case 5 — escape-hatch dict mutation must NOT poison globals ──────────

def case_05_dict_copy_mutation_isolated() -> None:
    desc = "case_05 d = dict(SEMANTIC_PALETTE); d['hero']='x' does not touch role('hero')"
    try:
        d = dict(huitu.SEMANTIC_PALETTE)
        d["hero"] = "#FFFFFF"
        got = huitu.role("hero")
        if got == HERO_ORIG:
            _ok(desc)
        else:
            _bad(desc, f"mutation leaked into role(): {got!r}")
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 6 — deepcopy of dict(PALETTES) then mutate inner list ───────────

def case_06_deepcopy_palettes_inner() -> None:
    desc = "case_06 deepcopy(dict(PALETTES))['nord'][0]='x' does not pollute PALETTES['nord']"
    try:
        snap = copy.deepcopy(dict(huitu.PALETTES))
        snap["nord"][0] = "<<HACKED>>"
        live = huitu.PALETTES["nord"]
        if "<<HACKED>>" in live:
            _bad(
                desc,
                "deepcopy aliased inner list — PALETTES['nord'] now contains "
                "the mutation. Indicates inner lists are shared, not copied.",
            )
        else:
            _ok(desc)
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 7 — json round-trip works for SEMANTIC_PALETTE values ───────────

def case_07_json_round_trip() -> None:
    desc = "case_07 json.dumps(dict(SEMANTIC_PALETTE)) round-trips"
    try:
        d = dict(huitu.SEMANTIC_PALETTE)
        text = json.dumps(d)
        back = json.loads(text)
        if back == d:
            _ok(desc)
        else:
            _bad(desc, "round-trip changed dict contents")
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 8 — pickle of dict(PALETTES) round-trips ────────────────────────

def case_08_pickle_dict_palettes() -> None:
    desc = "case_08 pickle round-trip of dict(PALETTES) preserves all keys + values"
    try:
        d = dict(huitu.PALETTES)
        blob = pickle.dumps(d)
        back = pickle.loads(blob)
        if set(back) != set(d):
            _bad(desc, "key set drifted")
            return
        if back["nord"] != list(d["nord"]):
            _bad(desc, "nord palette drifted on round-trip")
            return
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 9 — pickling the PALETTES proxy itself raises ───────────────────

def case_09_pickle_palettes_proxy_raises() -> None:
    desc = "case_09 pickle.dumps(huitu.PALETTES) raises (frozen ≠ shippable backdoor)"
    try:
        try:
            pickle.dumps(huitu.PALETTES)
            _bad(desc, "pickle succeeded — PALETTES proxy got serialised")
            return
        except TypeError:
            _ok(desc)
        except Exception as exc:
            _bad(desc, f"wrong exception {type(exc).__name__}: {exc}")
    except Exception as exc:
        _bad(desc, f"outer crash: {type(exc).__name__}: {exc}")


# ── Case 10 — after every attack, hero+nord are still original ───────────

def case_10_post_attack_invariant() -> None:
    desc = "case_10 after every serialization attack, role+PALETTES are unchanged"
    if huitu.role("hero") != HERO_ORIG:
        _bad(desc, f"hero drifted: {huitu.role('hero')!r}")
        return
    live = list(huitu.PALETTES["nord"])
    if live != NORD_ORIG:
        _bad(desc, f"PALETTES['nord'] drifted: live={live!r}, orig={NORD_ORIG!r}")
        return
    _ok(desc)


def main() -> int:
    case_01_pickle_proxy_raises()
    case_02_pickle_dict_copy()
    case_03_copy_copy_proxy()
    case_04_deepcopy_proxy()
    case_05_dict_copy_mutation_isolated()
    case_06_deepcopy_palettes_inner()
    case_07_json_round_trip()
    case_08_pickle_dict_palettes()
    case_09_pickle_palettes_proxy_raises()
    case_10_post_attack_invariant()

    print(f"\n[SUMMARY] test_03_pickle_deepcopy: {_passed} pass / {_failed} fail")
    if _failed == 0:
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
