"""Adversarial test 2 (Round 2): importlib.reload attacks.

A user who reloads ``huitu`` or ``huitu.style`` during a notebook session
must not end up with a broken registry, a stale proxy reference that has
desync'd from ``role()``, or a re-mutable palette.

These tests deliberately exercise reload corner cases that are easy to
overlook when wrapping module-level state in ``MappingProxyType``.
"""

from __future__ import annotations

import importlib
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


# ── Case 1 — reload huitu.style: role() still works ──────────────────────

def case_01_reload_style_role_works() -> None:
    desc = "case_01 importlib.reload(huitu.style) then huitu.role('hero') == original"
    try:
        importlib.reload(huitu.style)
        got = huitu.style.role("hero")
        if got == HERO_ORIG:
            _ok(desc)
        else:
            _bad(desc, f"role('hero')={got!r}, expected {HERO_ORIG!r}")
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 2 — reload huitu.style: new proxy is still a proxy ──────────────

def case_02_reload_style_proxy_type() -> None:
    desc = "case_02 after reload(huitu.style) SEMANTIC_PALETTE is still mappingproxy"
    try:
        importlib.reload(huitu.style)
        t = type(huitu.style.SEMANTIC_PALETTE).__name__
        if t == "mappingproxy":
            _ok(desc)
        else:
            _bad(
                desc,
                f"after reload type is {t!r} — freeze didn't re-apply on reload",
            )
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 3 — reload huitu.style: stale top-level alias detection ─────────

def case_03_reload_stale_reference() -> None:
    desc = "case_03 reload(huitu.style) replaces style.SEMANTIC_PALETTE id"
    # Top-level ``huitu.SEMANTIC_PALETTE`` may legitimately still point at the
    # *old* proxy (Python import semantics — re-exported attributes don't auto-
    # refresh). We just check that the inner module's proxy is a NEW object,
    # i.e. reload actually re-ran the freeze.
    old_id = id(huitu.style.SEMANTIC_PALETTE)
    try:
        importlib.reload(huitu.style)
        new_id = id(huitu.style.SEMANTIC_PALETTE)
        if new_id != old_id:
            _ok(desc)
        else:
            _bad(desc, "reload returned the same proxy id; module-level cache hit?")
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 4 — multi-step reload: style then huitu, then role() ────────────

def case_04_multi_step_reload() -> None:
    desc = "case_04 reload(style), reload(huitu), role('hero') still works"
    try:
        importlib.reload(huitu.style)
        importlib.reload(huitu)
        got = huitu.role("hero")
        if got == HERO_ORIG:
            _ok(desc)
        else:
            _bad(desc, f"role broke after both reloads: got {got!r}")
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 5 — reload then use_palette('semantic') ─────────────────────────

def case_05_reload_then_use_palette() -> None:
    desc = "case_05 reload then use_palette('semantic') applies the cycle without error"
    try:
        importlib.reload(huitu.style)
        importlib.reload(huitu)
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib as mpl

        colors = huitu.use_palette("semantic")
        applied = mpl.rcParams["axes.prop_cycle"].by_key()["color"]
        if not colors or applied[0].lower() != colors[0].lower():
            _bad(desc, f"cycle did not apply: applied={applied!r}, colors={colors!r}")
            return
        if applied[0].lower() != huitu.role("hero").lower():
            _bad(desc, f"cycle[0]={applied[0]!r} != hero={huitu.role('hero')!r}")
            return
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 6 — after reload PALETTES still a mappingproxy ──────────────────

def case_06_reload_palettes_still_frozen() -> None:
    desc = "case_06 reload(huitu) → huitu.PALETTES is still mappingproxy"
    try:
        importlib.reload(huitu)
        t = type(huitu.PALETTES).__name__
        if t == "mappingproxy":
            _ok(desc)
        else:
            _bad(
                desc,
                f"after reload(huitu), PALETTES is {t!r} — freeze in __init__.py "
                "didn't re-run (or wrapped the wrong reference)",
            )
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 7 — after reload PALETTES write still fails ─────────────────────

def case_07_reload_palettes_still_immutable() -> None:
    desc = "case_07 after reload, PALETTES['k']='v' still raises TypeError"
    try:
        importlib.reload(huitu)
        try:
            huitu.PALETTES["pwn"] = ["#000000"]
            _bad(desc, "PALETTES became writable after reload")
            return
        except TypeError:
            _ok(desc)
        except Exception as exc:
            _bad(desc, f"wrong exception {type(exc).__name__}: {exc}")
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 8 — old held proxy reference stays usable but read-only ─────────

def case_08_old_proxy_still_readable() -> None:
    desc = "case_08 old proxy ref captured before reload remains readable"
    # Holding the old proxy is fine — what matters is that it still acts
    # like the original frozen mapping, not that it's been GC'd into a
    # weird state.
    old = huitu.style.SEMANTIC_PALETTE
    try:
        importlib.reload(huitu.style)
        try:
            val = old["hero"]
        except Exception as exc:
            _bad(desc, f"old proxy unreadable after reload: {type(exc).__name__}: {exc}")
            return
        if val == HERO_ORIG:
            _ok(desc)
        else:
            _bad(desc, f"old proxy value drifted: {val!r}")
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 9 — reload doesn't expose underlying dict via proxy `__init__` ──

def case_09_reload_no_writable_inner() -> None:
    desc = "case_09 after reload, dict(huitu.SEMANTIC_PALETTE)['hero']='x' doesn't poison role"
    try:
        importlib.reload(huitu)
        d = dict(huitu.SEMANTIC_PALETTE)
        d["hero"] = "#FFFFFF"
        got = huitu.role("hero")
        if got == HERO_ORIG:
            _ok(desc)
        else:
            _bad(desc, f"dict() copy mutation leaked into role(): {got!r}")
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 10 — reload preserves all 18 documented roles ───────────────────

def case_10_reload_keys_preserved() -> None:
    desc = "case_10 after reload, all 18 documented roles still resolvable"
    REQUIRED = [
        "hero", "hero_2", "hero_soft",
        "baseline", "baseline_2", "baseline_soft",
        "positive", "positive_soft",
        "negative", "negative_soft",
        "neutral", "neutral_light", "neutral_dark", "neutral_black",
        "accent_gold", "accent_teal", "accent_violet", "accent_magenta",
    ]
    try:
        importlib.reload(huitu.style)
        importlib.reload(huitu)
        missing = []
        for r in REQUIRED:
            try:
                huitu.role(r)
            except Exception as exc:
                missing.append(f"{r}:{type(exc).__name__}")
        if missing:
            _bad(desc, f"after reload, missing/erroring: {missing}")
        else:
            _ok(desc)
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


def main() -> int:
    case_01_reload_style_role_works()
    case_02_reload_style_proxy_type()
    case_03_reload_stale_reference()
    case_04_multi_step_reload()
    case_05_reload_then_use_palette()
    case_06_reload_palettes_still_frozen()
    case_07_reload_palettes_still_immutable()
    case_08_old_proxy_still_readable()
    case_09_reload_no_writable_inner()
    case_10_reload_keys_preserved()

    print(f"\n[SUMMARY] test_02_reload_attacks: {_passed} pass / {_failed} fail")
    if _failed == 0:
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
