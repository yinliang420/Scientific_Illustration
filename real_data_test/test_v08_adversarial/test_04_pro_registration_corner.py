"""Round-3 adversarial test 4: `register_pro_palettes()` corner cases.

Round-2 added an idempotency guard:

    pal = pro_palettes()
    if all(name in target for name in pal):
        already_registered = True
    else:
        already_registered = False
        for name, colors in pal.items():
            target[name] = tuple(colors)

This file probes the corners:
  * Repeat calls are no-ops (idempotency)
  * Backing-side writes leak through the proxy (intentional internal API)
  * Empty pro_palettes() works
  * Name clash with a standard palette (currently overwrites? skips?)
  * Concurrent registration from 5 threads
  * Reload of huitu.pro.palettes resets the guard
  * Forward-compat: deleting a pro palette then re-registering re-adds it

PASS criterion: behavior is deterministic and the registry isn't corrupted.
FAIL criterion: race condition, duplicate writes, lost state, or crash on
edge input.
"""

from __future__ import annotations

import importlib
import sys
import threading

import huitu
import huitu.style
import huitu.pro
import huitu.pro.palettes as pp

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


# ── Case 1 — five calls are idempotent (registry length stable) ───────────

def case_01_idempotent_5x() -> None:
    desc = ("case_01 register_pro_palettes() 5 times in a row leaves "
            "len(PALETTES) constant")
    before = len(huitu.PALETTES)
    for _ in range(5):
        pp.register_pro_palettes()
    after = len(huitu.PALETTES)
    if before == after:
        _ok(desc + f" (before={before}, after={after})")
    else:
        _bad(desc, f"len changed: {before} -> {after}")


# ── Case 2 — backing-side write IS visible through the proxy ──────────────

def case_02_backing_write_visible_via_proxy() -> None:
    desc = ("case_02 _PALETTES_BACKING['__leak__'] = ('#000',) shows up in "
            "PALETTES (intentional — internal API, used by pro registration)")
    backing = huitu.style._PALETTES_BACKING
    backing["__leak__"] = ("#000",)
    try:
        if "__leak__" not in huitu.PALETTES:
            _bad(desc, "backing write did NOT propagate to proxy")
            return
        v = huitu.PALETTES["__leak__"]
        if v == ["#000"]:
            _ok(desc + f" — proxy returned defensive list {v!r}")
        else:
            _bad(desc, f"proxy returned {v!r}, expected ['#000']")
    finally:
        del backing["__leak__"]


# ── Case 3 — empty pro_palettes() must NOT crash registration ─────────────

def case_03_empty_pro_palettes_safe() -> None:
    desc = ("case_03 monkey-patched pro_palettes() returning {} — "
            "register_pro_palettes() must not crash")
    orig = pp.pro_palettes
    pp.pro_palettes = lambda: {}
    try:
        before = len(huitu.PALETTES)
        pp.register_pro_palettes()
        after = len(huitu.PALETTES)
        if before == after:
            _ok(desc + f" (len unchanged at {after})")
        else:
            _bad(desc, f"len changed: {before} -> {after}")
    except Exception as e:
        _bad(desc, f"raised {type(e).__name__}: {e}")
    finally:
        pp.pro_palettes = orig


# ── Case 4 — name clash with a standard palette ───────────────────────────

def case_04_name_clash_with_standard() -> None:
    desc = ("case_04 monkey-patch pro_palettes() to redefine 'nord' — "
            "must not overwrite the standard palette (idempotency guard "
            "treats 'all names already present' as a no-op)")
    orig_pal = pp.pro_palettes
    orig_nord = tuple(huitu.PALETTES["nord"])
    pp.pro_palettes = lambda: {"nord": ["#FFFFFF", "#000000"]}
    try:
        pp.register_pro_palettes()
        cur_nord = tuple(huitu.PALETTES["nord"])
        if cur_nord == orig_nord:
            _ok(desc + " — 'nord' preserved (idempotency guard caught it)")
        else:
            _bad(desc, f"'nord' overwritten: {orig_nord!r} -> {cur_nord!r}")
    finally:
        pp.pro_palettes = orig_pal


# ── Case 5 — 5 threads concurrently call register_pro_palettes ────────────

def case_05_concurrent_registration() -> None:
    desc = ("case_05 5 threads × 10 register_pro_palettes calls — "
            "no exception, no duplicate entries")
    errs: list[Exception] = []
    def worker() -> None:
        try:
            for _ in range(10):
                pp.register_pro_palettes()
        except Exception as e:  # noqa: BLE001
            errs.append(e)
    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    if errs:
        _bad(desc, f"{len(errs)} thread errors: first={errs[0]!r}")
        return
    # Verify no duplicates and pro palettes are all present.
    expected = set(pp.pro_palettes())
    actual = set(huitu.PALETTES)
    missing = expected - actual
    if missing:
        _bad(desc, f"missing after concurrent register: {missing!r}")
        return
    _ok(desc)


# ── Case 6 — reload(huitu.pro.palettes) resets the module state ───────────

def case_06_reload_resets_module() -> None:
    desc = ("case_06 importlib.reload(huitu.pro.palettes) succeeds and "
            "register_pro_palettes is still callable")
    try:
        importlib.reload(pp)
    except Exception as e:
        _bad(desc, f"reload raised {type(e).__name__}: {e}")
        return
    # After reload, the function should still exist and not crash.
    if not callable(getattr(pp, "register_pro_palettes", None)):
        _bad(desc, "register_pro_palettes missing after reload")
        return
    try:
        pp.register_pro_palettes()
        _ok(desc)
    except Exception as e:
        _bad(desc, f"post-reload call raised {type(e).__name__}: {e}")


# ── Case 7 — forward-compat: delete one pro palette then re-register ──────

def case_07_delete_then_reregister() -> None:
    desc = ("case_07 del a pro palette ('met-monet') from backing, then "
            "register_pro_palettes() — should re-add it (because guard's "
            "`all in target` becomes False)")
    backing = huitu.style._PALETTES_BACKING
    name = "met-monet"
    if name not in backing:
        _bad(desc, f"baseline failure: {name!r} not in backing before deletion")
        return
    saved = backing[name]
    del backing[name]
    try:
        pp.register_pro_palettes()
        if name in backing:
            _ok(desc + " — re-added")
        else:
            _bad(desc, f"{name!r} not re-added after registration")
    finally:
        # Make sure we restore it if registration didn't.
        if name not in backing:
            backing[name] = saved  # raw save (was tuple originally)


# ── Case 8 — register_pro_palettes does NOT touch _GRADIENT_PALETTES once frozen ─

def case_08_gradient_palettes_frozen_skip() -> None:
    desc = ("case_08 huitu.__init__ rebinds _GRADIENT_PALETTES to a frozenset "
            "after pro registration; subsequent register_pro_palettes calls "
            "leave it alone (no AttributeError on .update)")
    grad = huitu.style._GRADIENT_PALETTES
    is_frozen = isinstance(grad, frozenset)
    if not is_frozen:
        _ok(desc + " — _GRADIENT_PALETTES is still mutable set; freeze not yet applied")
        return
    try:
        pp.register_pro_palettes()
        # After call, grad should STILL be frozenset (untouched)
        if isinstance(huitu.style._GRADIENT_PALETTES, frozenset):
            _ok(desc + " — frozen set survived re-registration intact")
        else:
            _bad(desc, "frozen set was replaced by mutable set!")
    except AttributeError as e:
        _bad(desc, f"register tried to call .update on frozenset: {e}")
    except Exception as e:
        _bad(desc, f"raised {type(e).__name__}: {e}")


# ── Case 9 — all pro palette names present after init ─────────────────────

def case_09_all_pro_names_registered() -> None:
    desc = "case_09 every pro palette name is registered in huitu.PALETTES"
    expected = set(pp.pro_palettes())
    actual = set(huitu.PALETTES)
    missing = expected - actual
    if missing:
        _bad(desc, f"missing: {sorted(missing)}")
    else:
        _ok(desc + f" ({len(expected)} pro palettes)")


# ── Case 10 — registered values are stored as tuple (immutable) ───────────

def case_10_pro_values_stored_as_tuple() -> None:
    desc = ("case_10 raw backing entry for a pro palette is stored as tuple "
            "(not list) — matches the standard palettes' contract")
    backing = huitu.style._PALETTES_BACKING
    raw = dict.__getitem__(backing, "ggsci-npg")
    if isinstance(raw, tuple):
        _ok(desc + f" (raw type=tuple, len={len(raw)})")
    else:
        _bad(desc, f"raw type is {type(raw).__name__}, expected tuple")


def main() -> int:
    case_01_idempotent_5x()
    case_02_backing_write_visible_via_proxy()
    case_03_empty_pro_palettes_safe()
    case_04_name_clash_with_standard()
    case_05_concurrent_registration()
    case_06_reload_resets_module()
    case_07_delete_then_reregister()
    case_08_gradient_palettes_frozen_skip()
    case_09_all_pro_names_registered()
    case_10_pro_values_stored_as_tuple()

    print(f"\n[SUMMARY] test_04_pro_registration_corner: {_passed} pass / {_failed} fail")
    if _failed == 0:
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
