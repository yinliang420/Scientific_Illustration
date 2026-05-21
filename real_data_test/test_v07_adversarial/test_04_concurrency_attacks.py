"""Adversarial test 4 (Round 2): concurrency attacks.

Thread + process attacks on the frozen palette registry. We check that:

* Many concurrent ``role("hero")`` reads always agree.
* Many concurrent ``use_palette("nord")`` calls leave a coherent
  ``axes.prop_cycle`` (no torn write).
* A multiprocessing child that tries to mutate via ``.update()`` raises
  in the child and the parent's lookup is untouched.
* A child that does ``dict(...)`` + module-level rebind cannot escape its
  address space.
* ``check_redundancy`` itself is reentrant — concurrent callers each get
  the same issue list.
"""

from __future__ import annotations

import multiprocessing as mp
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import matplotlib

matplotlib.use("Agg")

import matplotlib as mpl

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


# ── Case 1 — 100 concurrent role() reads agree ───────────────────────────

def case_01_concurrent_role_reads() -> None:
    desc = "case_01 100 threads reading role('hero') all return same hex"
    try:
        results: list[str] = []
        lock = threading.Lock()

        def worker() -> None:
            r = huitu.role("hero")
            with lock:
                results.append(r)

        with ThreadPoolExecutor(max_workers=20) as pool:
            futs = [pool.submit(worker) for _ in range(100)]
            for f in futs:
                f.result()

        unique = set(results)
        if len(unique) == 1 and HERO_ORIG in unique:
            _ok(desc)
        else:
            _bad(desc, f"got {len(unique)} distinct values: {unique!r}")
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 2 — 50 concurrent use_palette('nord') agree ─────────────────────

def case_02_concurrent_use_palette() -> None:
    desc = "case_02 50 threads calling use_palette('nord') leave a coherent cycle"
    try:
        # use_palette writes to mpl.rcParams which is a global; threads will
        # race. We don't claim atomic ordering, only that the *final* cycle
        # contains hexes from the nord palette (no torn writes mixing two
        # different palettes).
        with ThreadPoolExecutor(max_workers=10) as pool:
            futs = [pool.submit(huitu.use_palette, "nord") for _ in range(50)]
            for f in futs:
                f.result()
        final = mpl.rcParams["axes.prop_cycle"].by_key()["color"]
        nord = list(huitu.PALETTES["nord"])
        if not final:
            _bad(desc, "no cycle after concurrent use_palette calls")
            return
        # Each entry should be one of the nord hexes (case-insensitive).
        lower_nord = {c.lower() for c in nord}
        bad = [c for c in final if c.lower() not in lower_nord]
        if bad:
            _bad(desc, f"non-nord hexes leaked into cycle: {bad!r}")
        else:
            _ok(desc)
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 3 — fork child mutation via .update() ───────────────────────────

def _child_update_attempt(q: mp.Queue) -> None:
    import huitu as _hu

    try:
        _hu.SEMANTIC_PALETTE.update({"hero": "#FFFFFF"})
        q.put(("ok", _hu.role("hero")))
    except (TypeError, AttributeError) as exc:
        q.put(("frozen", type(exc).__name__))
    except Exception as exc:
        q.put(("other", f"{type(exc).__name__}: {exc}"))


def case_03_child_update_blocked() -> None:
    desc = "case_03 child process .update() blocked; parent role unchanged"
    try:
        ctx = mp.get_context("spawn")
        q = ctx.Queue()
        p = ctx.Process(target=_child_update_attempt, args=(q,))
        p.start()
        p.join(timeout=30)
        if p.is_alive():
            p.terminate()
            _bad(desc, "child hung")
            return
        if q.empty():
            _bad(desc, "child did not report back")
            return
        status, info = q.get()
        parent_after = huitu.role("hero")
        if parent_after != HERO_ORIG:
            _bad(desc, f"parent role drifted to {parent_after!r}")
            return
        if status == "frozen":
            _ok(desc)
        elif status == "ok":
            _bad(desc, f"child .update() succeeded! Child role: {info!r}")
        else:
            _bad(desc, f"unexpected child status: {status}/{info}")
    except Exception as exc:
        _bad(desc, f"outer crash: {type(exc).__name__}: {exc}")


# ── Case 4 — fork child dict-rebind escape attempt ───────────────────────

def _child_rebind_attempt(q: mp.Queue) -> None:
    import huitu as _hu

    try:
        d = dict(_hu.SEMANTIC_PALETTE)
        d["hero"] = "#FFFFFF"
        _hu.SEMANTIC_PALETTE = d  # rebind module attribute in CHILD only
        q.put(("ok", _hu.role("hero")))
    except Exception as exc:
        q.put(("err", f"{type(exc).__name__}: {exc}"))


def case_04_child_rebind_no_parent_effect() -> None:
    desc = "case_04 child rebind of SEMANTIC_PALETTE does not affect parent role"
    try:
        ctx = mp.get_context("spawn")
        q = ctx.Queue()
        p = ctx.Process(target=_child_rebind_attempt, args=(q,))
        p.start()
        p.join(timeout=30)
        if p.is_alive():
            p.terminate()
            _bad(desc, "child hung")
            return
        if q.empty():
            _bad(desc, "child did not report back")
            return
        status, info = q.get()
        parent_after = huitu.role("hero")
        if parent_after != HERO_ORIG:
            _bad(desc, f"parent role drifted to {parent_after!r}")
            return
        # In the child, role() reads style.SEMANTIC_PALETTE (not the top-level
        # rebind) so the child should still return the original — Round 1
        # made role() immune to top-level rebinds. Document the observed
        # value but don't fail if child role drifted to the rebind value;
        # the *parent* must be untouched, which we already asserted.
        _ok(desc + f" (child reported: status={status!r}, role={info!r})")
    except Exception as exc:
        _bad(desc, f"outer crash: {type(exc).__name__}: {exc}")


# ── Case 5 — concurrent check_redundancy is deterministic ────────────────

def case_05_concurrent_check_redundancy() -> None:
    desc = "case_05 50 threads calling check_redundancy on identical input produce identical results"
    try:
        panels = [
            {"id": f"p{i}", "question": "What is X?", "encoding": "bar"}
            for i in range(20)
        ]
        results: list[tuple[tuple, ...]] = []
        lock = threading.Lock()

        def worker() -> None:
            issues = huitu.check_redundancy(panels)
            sig = tuple((i.severity, tuple(i.panels), i.message) for i in issues)
            with lock:
                results.append(sig)

        with ThreadPoolExecutor(max_workers=10) as pool:
            futs = [pool.submit(worker) for _ in range(50)]
            for f in futs:
                f.result()

        unique = {r for r in results}
        if len(unique) == 1:
            _ok(desc)
        else:
            _bad(desc, f"got {len(unique)} distinct issue signatures from same input")
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 6 — concurrent reviewer_checklist on identical input ────────────

def case_06_concurrent_reviewer_checklist() -> None:
    desc = "case_06 50 threads calling reviewer_checklist agree on pass/fail and counts"
    try:
        fig = {"core_conclusion": "X", "final_size": "89 mm"}
        quant = {
            "n": "12",
            "biological_replicates": 3,
            "center": "median",
            "spread": "IQR",
            "test": "two-sided Wilcoxon",
            "source_data": "f.csv",
        }
        results: list[tuple[bool, int, int]] = []
        lock = threading.Lock()

        def worker() -> None:
            rep = huitu.reviewer_checklist(
                figure=fig, quantitative=quant, print_report=False
            )
            with lock:
                results.append(
                    (rep["pass"], rep["n_required_missing"], rep["n_recommended_missing"])
                )

        with ThreadPoolExecutor(max_workers=10) as pool:
            futs = [pool.submit(worker) for _ in range(50)]
            for f in futs:
                f.result()

        unique = set(results)
        if len(unique) == 1:
            _ok(desc)
        else:
            _bad(desc, f"got {len(unique)} distinct results from same input: {unique!r}")
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 7 — concurrent role() with rapid alternating reads ──────────────

def case_07_thrash_role() -> None:
    desc = "case_07 50k role lookups across 8 threads stay correct"
    try:
        results: list[str] = []
        lock = threading.Lock()

        def worker() -> None:
            local: list[str] = []
            for _ in range(6250):
                local.append(huitu.role("hero"))
            with lock:
                results.extend(local)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        t0 = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=60)
        elapsed = time.time() - t0
        bad = [r for r in results if r != HERO_ORIG]
        if bad:
            _bad(desc, f"{len(bad)} divergent reads across 50k lookups")
        else:
            _ok(desc + f" ({elapsed:.2f}s)")
    except Exception as exc:
        _bad(desc, f"crashed: {type(exc).__name__}: {exc}")


# ── Case 8 — child process can still read role() after parent did ────────

def _child_read_role(q: mp.Queue) -> None:
    import huitu as _hu

    q.put(_hu.role("hero"))


def case_08_child_can_read() -> None:
    desc = "case_08 fresh spawn-child reads role('hero') and matches parent"
    try:
        ctx = mp.get_context("spawn")
        q = ctx.Queue()
        p = ctx.Process(target=_child_read_role, args=(q,))
        p.start()
        p.join(timeout=30)
        if p.is_alive():
            p.terminate()
            _bad(desc, "child hung")
            return
        if q.empty():
            _bad(desc, "child silent")
            return
        v = q.get()
        if v == HERO_ORIG:
            _ok(desc)
        else:
            _bad(desc, f"child got {v!r}, parent has {HERO_ORIG!r}")
    except Exception as exc:
        _bad(desc, f"outer crash: {type(exc).__name__}: {exc}")


def main() -> int:
    case_01_concurrent_role_reads()
    case_02_concurrent_use_palette()
    case_03_child_update_blocked()
    case_04_child_rebind_no_parent_effect()
    case_05_concurrent_check_redundancy()
    case_06_concurrent_reviewer_checklist()
    case_07_thrash_role()
    case_08_child_can_read()

    print(f"\n[SUMMARY] test_04_concurrency_attacks: {_passed} pass / {_failed} fail")
    if _failed == 0:
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
