"""Round-3 adversarial test 6: ``gc.get_referents`` bypass of SEMANTIC_PALETTE.

Round-2 wrapped ``huitu.SEMANTIC_PALETTE`` in ``types.MappingProxyType``,
which appeared to be a complete freeze. Round-3 surfaced one more channel:

    import gc
    inner = [o for o in gc.get_referents(huitu.SEMANTIC_PALETTE)
             if isinstance(o, dict)][0]
    inner['hero'] = '#FF00FF'
    huitu.role('hero')   # returns '#FF00FF' — silent corruption!

``MappingProxyType`` keeps a reference to the wrapped dict so ``gc.get_referents``
returns it, and that inner dict is fully mutable. The fix (Round-3 D) replaces
the proxy with a tuple-backed ``_FrozenStrMap`` whose only stored attribute is
an immutable tuple — ``gc.get_referents`` surfaces only the tuple and the
class object, never a writable dict.

PASS criterion: no mutable dict is reachable via ``gc.get_referents`` on
``huitu.SEMANTIC_PALETTE``, AND even if an attacker holds a reference to
whatever ``gc.get_referents`` returns, ``huitu.role()`` lookups stay
reproducible across the session.

FAIL: an inner dict is reachable, OR mutation through any reachable object
leaks into ``role()`` output.
"""

from __future__ import annotations

import gc
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
BASELINE_ORIG = huitu.role("baseline")


# ── Case 1 — gc.get_referents surfaces no mutable dict ───────────────────

def case_01_no_inner_dict_via_gc() -> None:
    desc = ("case_01 gc.get_referents(huitu.SEMANTIC_PALETTE) must NOT yield "
            "any dict instance")
    refs = gc.get_referents(huitu.SEMANTIC_PALETTE)
    inner_dicts = [o for o in refs if isinstance(o, dict)]
    if inner_dicts:
        _bad(
            desc,
            f"found {len(inner_dicts)} reachable dict(s) via gc: "
            f"{[list(d.keys())[:3] for d in inner_dicts]!r}. "
            "Round-3 fix is incomplete — backing dict is still leaking.",
        )
        return
    # Show what IS reachable so the test is self-documenting.
    types_seen = sorted({type(o).__name__ for o in refs})
    _ok(desc + f" (reachable types: {types_seen})")


# ── Case 2 — gc.get_referents via huitu.style.SEMANTIC_PALETTE ────────────

def case_02_no_inner_dict_via_style_module() -> None:
    desc = ("case_02 gc.get_referents(huitu.style.SEMANTIC_PALETTE) must "
            "NOT yield any dict instance either")
    refs = gc.get_referents(huitu.style.SEMANTIC_PALETTE)
    inner_dicts = [o for o in refs if isinstance(o, dict)]
    if inner_dicts:
        _bad(
            desc,
            f"found {len(inner_dicts)} dict(s) via gc on style.SEMANTIC_PALETTE",
        )
    else:
        _ok(desc)


# ── Case 3 — mutating the reachable tuple does not affect role() ─────────

def case_03_tuple_mutation_blocked() -> None:
    desc = ("case_03 reachable tuple via gc is immutable; even attempts to "
            "rebind its elements raise TypeError and role() stays stable")
    refs = gc.get_referents(huitu.SEMANTIC_PALETTE)
    tuples = [o for o in refs if isinstance(o, tuple)]
    if not tuples:
        # Permissible: maybe future fix uses some other backing. Just check
        # role() is still stable.
        if huitu.role("hero") == HERO_ORIG:
            _ok(desc + " (no tuple reachable, but role still stable)")
        else:
            _bad(desc, "role drifted unexpectedly")
        return
    # Try to mutate the tuple — should fail.
    backing = tuples[0]
    mutated = False
    try:
        backing[0] = ("hero", "#FF00FF")  # type: ignore[index]
        mutated = True
    except TypeError:
        pass
    except Exception as exc:
        _bad(desc, f"wrong exception {type(exc).__name__}: {exc}")
        return
    if mutated:
        _bad(desc, "tuple element assignment succeeded — backing is not a real tuple")
        return
    if huitu.role("hero") != HERO_ORIG:
        _bad(desc, f"role drifted after attempted tuple mutation: {huitu.role('hero')!r}")
        return
    _ok(desc)


# ── Case 4 — full historical exploit no longer corrupts role() ───────────

def case_04_historical_exploit_neutralized() -> None:
    desc = ("case_04 the Round-3 historical exploit "
            "(inner = [o for o in gc.get_referents(SEMANTIC_PALETTE) if "
            "isinstance(o, dict)][0]; inner['hero']='#FF00FF') no longer "
            "corrupts role('hero')")
    try:
        inner_candidates = [
            o for o in gc.get_referents(huitu.SEMANTIC_PALETTE)
            if isinstance(o, dict)
        ]
    except Exception as exc:
        _bad(desc, f"gc.get_referents itself crashed: {type(exc).__name__}: {exc}")
        return
    if inner_candidates:
        # Attempt the actual exploit and report the result.
        try:
            inner_candidates[0]["hero"] = "#FF00FF"
        except TypeError:
            # Inner dict happens to be read-only — partial credit, but the
            # exploit precondition (dict reachable) still leaks.
            _bad(
                desc,
                "inner dict reachable but happens to be read-only; "
                "Round-3 fix should hide the inner dict entirely",
            )
            return
        if huitu.role("hero") == "#FF00FF":
            _bad(desc, "exploit succeeded — role('hero') is now '#FF00FF'")
            return
        # role didn't update — but the dict was still mutable. Still leaky.
        _bad(
            desc,
            "exploit mutation succeeded on the reachable dict; even if "
            "role() didn't pick it up, the dict reachability is the bug.",
        )
        return
    # No inner dict reachable → exploit precondition fails. role stays sane.
    if huitu.role("hero") == HERO_ORIG:
        _ok(desc)
    else:
        _bad(desc, f"role drifted without exploit: {huitu.role('hero')!r}")


# ── Case 5 — every reachable object is either immutable or doesn't carry role data ─

def case_05_all_reachable_safe() -> None:
    desc = ("case_05 every object returned by gc.get_referents on "
            "SEMANTIC_PALETTE is safe (immutable, or doesn't hold role mappings)")
    refs = gc.get_referents(huitu.SEMANTIC_PALETTE)
    unsafe = []
    for obj in refs:
        if isinstance(obj, dict):
            # Any reachable dict is dangerous because role() reads via name lookup.
            unsafe.append(f"dict({list(obj.keys())[:3]!r})")
        elif isinstance(obj, list):
            # Reachable lists can be appended/mutated.
            unsafe.append(f"list(len={len(obj)})")
        elif isinstance(obj, set):
            unsafe.append(f"set(len={len(obj)})")
        # tuple, type, str, frozenset → immutable / not a role mapping → safe
    if unsafe:
        _bad(desc, f"reachable mutable container(s): {unsafe!r}")
    else:
        _ok(desc + f" ({len(refs)} reachable object(s), all safe)")


# ── Case 6 — gc.get_referrers does not magically reach the backing dict ──

def case_06_get_referrers_does_not_expose_dict() -> None:
    desc = ("case_06 the reverse query — gc.get_referrers — also does not "
            "yield a mutable dict that mirrors SEMANTIC_PALETTE contents")
    # get_referrers can be noisy; we only check that we don't land in a dict
    # that holds the same role keys.
    target_keys = set(huitu.SEMANTIC_PALETTE)
    suspicious = []
    try:
        for owner in gc.get_referrers(huitu.SEMANTIC_PALETTE):
            if isinstance(owner, dict) and target_keys.issubset(set(owner)):
                # A dict that has ALL our role keys is suspicious.
                # (Module dicts won't match — they have 'role', '__name__' etc.)
                suspicious.append(owner)
    except Exception as exc:
        _bad(desc, f"gc.get_referrers crashed: {type(exc).__name__}: {exc}")
        return
    if suspicious:
        _bad(desc, f"found {len(suspicious)} dict(s) mirroring role keys")
    else:
        _ok(desc)


# ── Case 7 — role() still returns identical hex after every probe ────────

def case_07_role_stable_after_all_probes() -> None:
    desc = "case_07 after every gc probe, role('hero') and role('baseline') are unchanged"
    h = huitu.role("hero")
    b = huitu.role("baseline")
    if h != HERO_ORIG:
        _bad(desc, f"hero drifted: got {h!r}, expected {HERO_ORIG!r}")
        return
    if b != BASELINE_ORIG:
        _bad(desc, f"baseline drifted: got {b!r}, expected {BASELINE_ORIG!r}")
        return
    _ok(desc)


# ── Case 8 — vars() / __dict__ does not expose a mutable backing ─────────

def case_08_no_writable_dict_attr() -> None:
    desc = ("case_08 huitu.SEMANTIC_PALETTE has no __dict__ attribute that "
            "would expose a writable backing")
    sp = huitu.SEMANTIC_PALETTE
    # MappingProxyType has no __dict__; _FrozenStrMap uses __slots__ so also
    # no __dict__. Either way, we should not be able to grab a dict via __dict__.
    inst_dict = getattr(sp, "__dict__", None)
    if inst_dict is None:
        _ok(desc + " (no __dict__ — slots or proxy)")
        return
    if isinstance(inst_dict, dict) and "hero" in inst_dict:
        _bad(desc, f"__dict__ exposes role mapping directly: {list(inst_dict)[:3]!r}")
        return
    _ok(desc + f" (__dict__ exists but does not mirror roles: keys={list(inst_dict)[:3]!r})")


def main() -> int:
    case_01_no_inner_dict_via_gc()
    case_02_no_inner_dict_via_style_module()
    case_03_tuple_mutation_blocked()
    case_04_historical_exploit_neutralized()
    case_05_all_reachable_safe()
    case_06_get_referrers_does_not_expose_dict()
    case_07_role_stable_after_all_probes()
    case_08_no_writable_dict_attr()

    print(f"\n[SUMMARY] test_06_semantic_gc_bypass: {_passed} pass / {_failed} fail")
    if _failed == 0:
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
