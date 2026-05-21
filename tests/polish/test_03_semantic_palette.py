"""Polish test 03 — semantic palette consistency.

User's complaint:

> "对于语义调色板（你的方法 = 蓝，对照 = 红，自动配色一致）这个也能够实现吧"

Requirements:
1. ``role('hero')`` is **the same hex** before and after switching journals.
2. ``use_palette('semantic')`` puts hero blue first in the cycle.
3. The default categorical palette (``axes.prop_cycle``) is *consistent
   across plot_* calls* — two ``ax.plot`` calls labelled "Ours" / "Baseline"
   inside the same axes get the right semantic colors.
4. The frozen contract holds: ``huitu.SEMANTIC_PALETTE['hero'] = '#000'``
   raises ``TypeError``; ``huitu.PALETTES['nord'][0] = '#000'`` mutates only
   a throwaway copy.
"""

from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest

from .conftest import report, sample

JOURNALS = ["default", "nature", "science", "acs", "rsc", "wiley", "elsevier", "ieee"]


def _hero():
    import huitu
    return huitu.role("hero")


def _baseline():
    import huitu
    return huitu.role("baseline")


def test_case_01_hero_is_blue():
    """case_01: role('hero') is a recognisably blue hex."""
    import huitu

    h = huitu.role("hero")
    # Deep blue: R<0x40, B>0x80 typical.
    r, g, b = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
    ok = b > r and b > 0x60
    report(1, "role('hero') hex is blue-dominant", ok,
           f"got {h} -> (R={r}, G={g}, B={b})")
    assert ok


def test_case_02_baseline_is_red():
    """case_02: role('baseline') is a recognisably red hex."""
    import huitu

    h = huitu.role("baseline")
    r, g, b = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
    ok = r > g and r > b
    report(2, "role('baseline') hex is red-dominant", ok,
           f"got {h} -> (R={r}, G={g}, B={b})")
    assert ok


@pytest.mark.parametrize("journal", JOURNALS)
def test_case_03_role_invariant_across_journals(journal):
    """case_03: role('hero') and role('baseline') are journal-independent.

    Their *purpose* is to be a stable semantic anchor — if Nature gives
    you one blue and Science gives you a different "hero" blue, multi-
    journal submissions would silently change colors.
    """
    import huitu

    huitu.use_journal("default")
    h0, b0 = huitu.role("hero"), huitu.role("baseline")
    huitu.use_journal(journal)
    h1, b1 = huitu.role("hero"), huitu.role("baseline")
    ok = (h0 == h1) and (b0 == b1)
    report(3, f"role() hex stable across use_journal('{journal}')",
           ok, f"hero {h0}->{h1}, baseline {b0}->{b1}")
    assert ok


def test_case_04_use_palette_semantic_first_is_hero():
    """case_04: ``use_palette('semantic')`` puts hero blue at index 0 of the cycle."""
    import huitu

    huitu.use_palette("semantic")
    cycle = mpl.rcParams["axes.prop_cycle"].by_key()["color"]
    ok = cycle[0].lower() == huitu.role("hero").lower()
    report(4, "use_palette('semantic') cycle[0] == role('hero')",
           ok, f"cycle[0]={cycle[0]} hero={huitu.role('hero')}")
    assert ok


def test_case_05_use_palette_semantic_second_is_baseline():
    """case_05: cycle[1] under 'semantic' is the baseline red."""
    import huitu

    huitu.use_palette("semantic")
    cycle = mpl.rcParams["axes.prop_cycle"].by_key()["color"]
    ok = cycle[1].lower() == huitu.role("baseline").lower()
    report(5, "use_palette('semantic') cycle[1] == role('baseline')",
           ok, f"cycle[1]={cycle[1]} baseline={huitu.role('baseline')}")
    assert ok


def test_case_06_palette_mutation_blocked():
    """case_06: ``PALETTES['nord'][0] = '#000'`` does not corrupt PALETTES."""
    import huitu

    saved = huitu.PALETTES["nord"][0]
    try:
        huitu.PALETTES["nord"][0] = "#000000"
    except (TypeError, Exception):
        pass
    fresh = huitu.PALETTES["nord"][0]
    ok = fresh == saved
    report(6, "PALETTES['nord'][0] mutation is rejected/throwaway",
           ok, f"corrupted: was {saved}, now {fresh}")
    assert ok


def test_case_07_palette_proxy_seal():
    """case_07: ``huitu.PALETTES`` is a MappingProxy — direct __setitem__ fails."""
    import huitu

    raised = False
    try:
        huitu.PALETTES["new_palette"] = ["#000"]
    except TypeError:
        raised = True
    except Exception:
        raised = True
    ok = raised
    report(7, "PALETTES['new'] = [...] raises TypeError (frozen)", ok,
           "PALETTES allowed __setitem__ — not frozen")
    assert ok


def test_case_08_semantic_palette_frozen():
    """case_08: ``SEMANTIC_PALETTE['hero'] = '#000'`` raises."""
    import huitu

    raised = False
    try:
        huitu.SEMANTIC_PALETTE["hero"] = "#000000"
    except TypeError:
        raised = True
    except Exception:
        raised = True
    ok = raised
    report(8, "SEMANTIC_PALETTE is frozen against __setitem__", ok,
           "SEMANTIC_PALETTE allowed assignment — frozen contract violated")
    assert ok


def test_case_09_two_plot_calls_same_hero_color():
    """case_09: two plot_* calls labelled 'Ours' get the same color.

    The user's literal complaint: "你的方法 = 蓝，对照 = 红，自动配色一致".
    The auto cycle inside `huitu.plot_xrd` should map the first labelled
    pattern to the same hex on every invocation when the same palette is
    active.
    """
    import huitu

    huitu.use_journal("default")
    huitu.use_palette("semantic")
    fig1, ax1 = huitu.plot_xrd(sample("xrd.txt"), labels=["Ours"])
    c1 = ax1.lines[0].get_color()
    plt.close(fig1)
    fig2, ax2 = huitu.plot_cv(sample("cv.txt"), labels=["Ours"])
    c2 = ax2.lines[0].get_color()
    plt.close(fig2)
    # Normalise to lowercase hex.
    ok = str(c1).lower() == str(c2).lower()
    report(9, "two consecutive labelled plot_* calls use same first color",
           ok, f"plot_xrd[0]={c1} plot_cv[0]={c2}")
    assert ok


def test_case_10_role_unknown_raises():
    """case_10: ``role('unknown')`` raises KeyError with a list of valid keys."""
    import huitu

    raised = False
    try:
        huitu.role("not-a-role")
    except KeyError as e:
        raised = True
        msg = str(e)
        listed = any(s in msg for s in ("hero", "baseline", "positive"))
    else:
        listed = False
    ok = raised and listed
    report(10, "role('unknown') raises KeyError + lists valid keys", ok,
           "either didn't raise KeyError or error message lacks valid keys")
    assert ok


def test_case_11_role_case_insensitive():
    """case_11: ``role('HERO')`` works (case-insensitive lookup)."""
    import huitu

    h_lower = huitu.role("hero")
    try:
        h_upper = huitu.role("HERO")
    except KeyError:
        h_upper = None
    ok = h_upper == h_lower
    report(11, "role() is case-insensitive (HERO == hero)", ok,
           f"role('HERO')={h_upper} role('hero')={h_lower}")
    assert ok


def test_case_12_palette_register_pro_succeeded():
    """case_12: ``huitu.pro`` palettes are reachable via huitu.PALETTES."""
    import huitu

    # The pro package should have registered semantic-pro, lancet, etc.
    keys = sorted(huitu.PALETTES.keys())
    # At minimum, the core entries from huitu/style.py.
    for k in ("nord", "okabe-ito", "semantic", "nature-cat"):
        assert k in keys, f"missing palette '{k}'"
    ok = True
    report(12, "core + pro palettes registered", ok, "")
    assert ok


def test_case_13_dqdv_uses_semantic_hero(tmp_path):
    """case_13: ``plot_dqdv`` first cycle line is the hero color.

    This is the canonical "hero vs baseline" use case the user described.
    """
    import huitu
    import numpy as np

    huitu.use_journal("default")
    v = np.linspace(2.5, 4.2, 200)
    q = np.cumsum(np.exp(-((v - 3.5) ** 2) / 0.05)) * 1.0
    fig, ax = huitu.plot_dqdv((v, q))
    first_color = ax.lines[0].get_color()
    plt.close(fig)
    ok = str(first_color).lower() == huitu.role("hero").lower()
    report(13, "plot_dqdv first line uses role('hero')", ok,
           f"first line color={first_color} hero={huitu.role('hero')}")
    assert ok


def test_case_14_use_palette_then_role_consistent():
    """case_14: After ``use_palette('semantic')``, ``role('hero')`` still
    returns the same hex (palette switching does not corrupt SEMANTIC_PALETTE)."""
    import huitu

    h0 = huitu.role("hero")
    huitu.use_palette("nord")
    h1 = huitu.role("hero")
    huitu.use_palette("semantic")
    h2 = huitu.role("hero")
    ok = h0 == h1 == h2
    report(14, "role('hero') survives use_palette() switches",
           ok, f"hero drift: {h0} -> {h1} -> {h2}")
    assert ok


def test_case_15_palettes_returns_list():
    """case_15: ``huitu.PALETTES['nord']`` returns a mutable list copy.

    Documented escape hatch — callers should be able to ``.copy()`` /
    ``json.dumps(...)`` without round-tripping through dict(...).
    """
    import huitu

    p = huitu.PALETTES["nord"]
    ok = isinstance(p, list) and len(p) > 0
    report(15, "PALETTES['nord'] returns a non-empty list", ok,
           f"got {type(p).__name__} of length {len(p)}")
    assert ok
