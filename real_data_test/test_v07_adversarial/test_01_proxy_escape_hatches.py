"""Adversarial test 1 (Round 2): MappingProxy freeze escape hatches.

Round-1 wrapped ``huitu.SEMANTIC_PALETTE`` and ``huitu.PALETTES`` in
``types.MappingProxyType``. The proxy blocks ``__setitem__``, ``__delitem__``,
``clear``, ``pop``, ``popitem``, ``setdefault``, and ``update`` on the
outer mapping. This file hunts for **escape hatches** in that freeze —
places where a hostile/sloppy caller can still corrupt the registry.

Confirmed real bugs surfaced here (FAIL = real Round-1 miss):
  * inner palette lists are *not* frozen — ``huitu.PALETTES["nord"][0] = X``
    succeeds and pollutes subsequent ``use_palette("nord")`` returns.

Pass means the freeze held. Fail means D has more sealing to do.
"""

from __future__ import annotations

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


HERO_ORIG = huitu.role("hero")
NORD_ORIG = list(huitu.PALETTES["nord"])


# ── Case 1 — __setitem__ on SEMANTIC_PALETTE ──────────────────────────────

def case_01_setitem_semantic() -> None:
    desc = "case_01 SEMANTIC_PALETTE['hero'] = 'x' raises TypeError"
    try:
        huitu.SEMANTIC_PALETTE["hero"] = "x"
        _bad(desc, "assignment succeeded; freeze leaked")
    except TypeError:
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"wrong exception {type(exc).__name__}: {exc}")


# ── Case 2 — __delitem__ on SEMANTIC_PALETTE ──────────────────────────────

def case_02_delitem_semantic() -> None:
    desc = "case_02 del SEMANTIC_PALETTE['hero'] raises TypeError"
    try:
        del huitu.SEMANTIC_PALETTE["hero"]
        _bad(desc, "del succeeded; freeze leaked")
    except TypeError:
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"wrong exception {type(exc).__name__}: {exc}")


# ── Case 3 — .update() ────────────────────────────────────────────────────

def case_03_update_semantic() -> None:
    desc = "case_03 SEMANTIC_PALETTE.update({'hero':'x'}) raises"
    try:
        huitu.SEMANTIC_PALETTE.update({"hero": "x"})
        _bad(desc, ".update() succeeded; freeze leaked")
    except (TypeError, AttributeError):
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"wrong exception {type(exc).__name__}: {exc}")


# ── Case 4 — .pop() ───────────────────────────────────────────────────────

def case_04_pop_semantic() -> None:
    desc = "case_04 SEMANTIC_PALETTE.pop('hero') raises"
    try:
        huitu.SEMANTIC_PALETTE.pop("hero")
        _bad(desc, ".pop() succeeded; freeze leaked")
    except (TypeError, AttributeError):
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"wrong exception {type(exc).__name__}: {exc}")


# ── Case 5 — .clear() ─────────────────────────────────────────────────────

def case_05_clear_semantic() -> None:
    desc = "case_05 SEMANTIC_PALETTE.clear() raises"
    try:
        huitu.SEMANTIC_PALETTE.clear()
        _bad(desc, ".clear() succeeded; freeze leaked")
    except (TypeError, AttributeError):
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"wrong exception {type(exc).__name__}: {exc}")


# ── Case 6 — .popitem() ───────────────────────────────────────────────────

def case_06_popitem_semantic() -> None:
    desc = "case_06 SEMANTIC_PALETTE.popitem() raises"
    try:
        huitu.SEMANTIC_PALETTE.popitem()
        _bad(desc, ".popitem() succeeded; freeze leaked")
    except (TypeError, AttributeError):
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"wrong exception {type(exc).__name__}: {exc}")


# ── Case 7 — .setdefault() ────────────────────────────────────────────────

def case_07_setdefault_semantic() -> None:
    desc = "case_07 SEMANTIC_PALETTE.setdefault('hero','x') raises"
    try:
        huitu.SEMANTIC_PALETTE.setdefault("hero", "x")
        _bad(desc, ".setdefault() succeeded; freeze leaked")
    except (TypeError, AttributeError):
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"wrong exception {type(exc).__name__}: {exc}")


# ── Case 8 — inner palette list mutation (KNOWN ROUND-1 MISS) ─────────────

def case_08_inner_list_mutation() -> None:
    desc = "case_08 huitu.PALETTES['nord'][0] = '#FFFFFF' must NOT corrupt the registry"
    # Round-1 freeze wraps PALETTES but each value is still a plain list.
    # Mutating an item via index leaks the change globally because
    # `huitu.PALETTES["nord"]` returns the *same* list object every time.
    orig = list(huitu.PALETTES["nord"])
    try:
        try:
            huitu.PALETTES["nord"][0] = "#FFFFFF"
        except TypeError:
            # If D ships frozen inner lists / tuples this is the right answer.
            _ok(desc + " (inner list is frozen — Round-2 sealed)")
            return
        after = huitu.PALETTES["nord"][0]
        if after == "#FFFFFF":
            _bad(
                desc,
                f"inner list mutation leaked. PALETTES['nord'][0] = {after!r}; "
                f"original was {orig[0]!r}. Wrap inner values in tuple() or "
                "return defensive copies from PALETTES.__getitem__.",
            )
        else:
            _ok(desc)
    finally:
        # Best-effort restore (only works if list is still mutable, which is
        # the buggy state). If the freeze landed, restore is a no-op.
        try:
            list_obj = huitu.style.PALETTES["nord"] if hasattr(huitu.style, "PALETTES") else None
            # MappingProxy doesn't expose the wrapped dict; access via style
            # which may also be a proxy. Skip restore — case_09 doesn't depend
            # on a clean nord, and downstream cases re-fetch from the registry.
        except Exception:
            pass


# ── Case 9 — aliased inner list ───────────────────────────────────────────

def case_09_aliased_inner_list() -> None:
    desc = "case_09 nord = PALETTES['nord']; nord[0] = 'x' must NOT pollute PALETTES['nord']"
    # Same root cause as case_08 — aliasing exposes the inner list. Test it
    # separately because callers commonly write
    #   palette = huitu.PALETTES["nord"]
    # then index/iterate, accidentally mutating downstream.
    nord_before = list(huitu.PALETTES["nord"])
    nord = huitu.PALETTES["nord"]
    try:
        nord[0] = "<<HACKED>>"
    except TypeError:
        _ok(desc + " (inner sequence is frozen — Round-2 sealed)")
        return
    after = huitu.PALETTES["nord"][0]
    if after == "<<HACKED>>":
        _bad(
            desc,
            f"aliased mutation leaked: PALETTES['nord'][0] = {after!r}, "
            f"originally {nord_before[0]!r}. Indicates inner list is not copied "
            "or frozen on access.",
        )
    else:
        _ok(desc)


# ── Case 10 — direct alias of the proxy itself ────────────────────────────

def case_10_alias_of_proxy() -> None:
    desc = "case_10 d = SEMANTIC_PALETTE; d['hero']='x' still TypeError (d is the proxy)"
    d = huitu.SEMANTIC_PALETTE
    try:
        d["hero"] = "x"
        _bad(desc, "alias mutation succeeded; proxy did not propagate")
    except TypeError:
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"wrong exception {type(exc).__name__}: {exc}")


# ── Case 11 — module-level rebind escape ──────────────────────────────────

def case_11_module_rebind() -> None:
    desc = "case_11 huitu.SEMANTIC_PALETTE = {...} only shadows top-level; role() unaffected"
    # Rebinding the attribute on the package doesn't reach inside
    # ``style.py`` where ``role()`` reads from. We assert that:
    #   1. After rebind, huitu.SEMANTIC_PALETTE is the user dict.
    #   2. huitu.style.SEMANTIC_PALETTE is still the original frozen proxy.
    #   3. huitu.role("hero") still returns the original color.
    original_top = huitu.SEMANTIC_PALETTE
    original_style_id = id(huitu.style.SEMANTIC_PALETTE)
    try:
        huitu.SEMANTIC_PALETTE = {"hero": "#FFFFFF"}
        if huitu.SEMANTIC_PALETTE.get("hero") != "#FFFFFF":
            _bad(desc, "rebind didn't take effect on huitu.SEMANTIC_PALETTE")
            return
        if id(huitu.style.SEMANTIC_PALETTE) != original_style_id:
            _bad(desc, "huitu.style.SEMANTIC_PALETTE was mutated by top-level rebind")
            return
        got = huitu.role("hero")
        if got == HERO_ORIG:
            _ok(desc)
        else:
            _bad(
                desc,
                f"role('hero') = {got!r}, expected {HERO_ORIG!r}. role() must "
                "read style.SEMANTIC_PALETTE, not the top-level alias.",
            )
    finally:
        huitu.SEMANTIC_PALETTE = original_top


# ── Case 12 — vars(huitu.style)["SEMANTIC_PALETTE"] still the proxy ───────

def case_12_vars_style() -> None:
    desc = "case_12 vars(huitu.style)['SEMANTIC_PALETTE'] is the same proxy (no writable backdoor)"
    sp = vars(huitu.style)["SEMANTIC_PALETTE"]
    if type(sp).__name__ != "mappingproxy":
        _bad(desc, f"vars()-access type is {type(sp).__name__}, not mappingproxy")
        return
    try:
        sp["hero"] = "x"
        _bad(desc, "vars()-access dict was writable; backdoor exists")
    except TypeError:
        _ok(desc)


# ── Case 13 — huitu.style.SEMANTIC_PALETTE direct write ───────────────────

def case_13_style_direct_setitem() -> None:
    desc = "case_13 huitu.style.SEMANTIC_PALETTE['hero']='x' raises TypeError"
    try:
        huitu.style.SEMANTIC_PALETTE["hero"] = "x"
        _bad(desc, "style.SEMANTIC_PALETTE was writable")
    except TypeError:
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"wrong exception {type(exc).__name__}: {exc}")


# ── Case 14 — PALETTES __setitem__ ────────────────────────────────────────

def case_14_palettes_setitem() -> None:
    desc = "case_14 huitu.PALETTES['x'] = [...] raises TypeError"
    try:
        huitu.PALETTES["new"] = ["#000000"]
        _bad(desc, "PALETTES.__setitem__ leaked")
    except TypeError:
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"wrong exception {type(exc).__name__}: {exc}")


# ── Case 15 — role() still reproducibly returns original after attacks ────

def case_15_role_stable_after_all() -> None:
    desc = "case_15 after all attacks role('hero') still equals original hex"
    got = huitu.role("hero")
    if got == HERO_ORIG:
        _ok(desc)
    else:
        _bad(desc, f"role('hero')={got!r}, expected {HERO_ORIG!r}")


def main() -> int:
    case_01_setitem_semantic()
    case_02_delitem_semantic()
    case_03_update_semantic()
    case_04_pop_semantic()
    case_05_clear_semantic()
    case_06_popitem_semantic()
    case_07_setdefault_semantic()
    case_08_inner_list_mutation()
    case_09_aliased_inner_list()
    case_10_alias_of_proxy()
    case_11_module_rebind()
    case_12_vars_style()
    case_13_style_direct_setitem()
    case_14_palettes_setitem()
    case_15_role_stable_after_all()

    print(f"\n[SUMMARY] test_01_proxy_escape_hatches: {_passed} pass / {_failed} fail")
    if _failed == 0:
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
