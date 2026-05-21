"""Adversarial test 2: huitu.role and use_palette('semantic').

Round-2 attacks on the 18-key semantic palette: bad input types, dict
mutability, cross-preset interaction, full key sweep, and verification that
the chosen hexes survive into the saved SVG.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

import huitu

OUT = Path(__file__).resolve().parent / "output"
OUT.mkdir(parents=True, exist_ok=True)

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


REQUIRED_ROLES = [
    "hero", "hero_2", "hero_soft",
    "baseline", "baseline_2", "baseline_soft",
    "positive", "positive_soft",
    "negative", "negative_soft",
    "neutral", "neutral_light", "neutral_dark", "neutral_black",
    "accent_gold", "accent_teal", "accent_violet", "accent_magenta",
]

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


# ── Case 1 — happy path ────────────────────────────────────────────────────

def case_01_happy() -> None:
    desc = "case_01 role('hero') == '#0F4D92'"
    try:
        got = huitu.role("hero")
        if got == "#0F4D92":
            _ok(desc)
        else:
            _bad(desc, f"got {got!r}")
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 2 — case + whitespace insensitivity ──────────────────────────────

def case_02_case_insensitive() -> None:
    desc = "case_02 role('HERO') and role('Hero') == role('hero')"
    try:
        base = huitu.role("hero")
        if huitu.role("HERO") == base and huitu.role("Hero") == base:
            _ok(desc)
        else:
            _bad(desc, "case folding broke")
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


def case_03_whitespace_strict() -> None:
    desc = "case_03 role(' hero ') is NOT silently accepted (whitespace strict)"
    # Documented behaviour is .lower() only, not .strip(). A leading space
    # SHOULD raise KeyError; if it returns a color, that's a silent corruption.
    try:
        got = huitu.role(" hero ")
        _bad(desc, f"whitespace key returned {got!r} instead of KeyError")
    except KeyError:
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"wrong exception {type(exc).__name__}: {exc}")


# ── Case 4 — non-string input must not silently succeed ───────────────────

def case_04_none_input() -> None:
    desc = "case_04 role(None) raises TypeError/AttributeError, not silent #..."
    try:
        got = huitu.role(None)
        _bad(desc, f"role(None) returned {got!r}")
    except (TypeError, AttributeError, KeyError):
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"unexpected exception {type(exc).__name__}: {exc}")


def case_05_int_input() -> None:
    desc = "case_05 role(42) raises (no silent fallback)"
    try:
        got = huitu.role(42)
        _bad(desc, f"role(42) returned {got!r}")
    except (TypeError, AttributeError, KeyError):
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"unexpected exception {type(exc).__name__}: {exc}")


def case_06_list_input() -> None:
    desc = "case_06 role(['hero']) raises (no list/silent fallback)"
    try:
        got = huitu.role(["hero"])
        _bad(desc, f"role(['hero']) returned {got!r}")
    except (TypeError, AttributeError, KeyError):
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"unexpected exception {type(exc).__name__}: {exc}")


# ── Case 7 — unicode confusable key ───────────────────────────────────────

def case_07_unicode_confusable() -> None:
    desc = "case_07 role('héro') raises KeyError (not silent fall-through)"
    try:
        got = huitu.role("héro")
        _bad(desc, f"unicode confusable returned {got!r}")
    except KeyError:
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"wrong exception {type(exc).__name__}: {exc}")


# ── Case 8 — semantic palette hexes survive into saved SVG ────────────────

def case_08_semantic_in_svg() -> None:
    desc = "case_08 use_palette('semantic') produces SVG with hero/baseline hex strokes"
    try:
        huitu.use_journal("default")
        colors = huitu.use_palette("semantic")
        fig, ax = plt.subplots()
        x = np.linspace(0, 1, 25)
        ax.plot(x, x, label="L1")
        ax.plot(x, x ** 2, label="L2")
        ax.plot(x, x ** 0.5, label="L3")
        svg = OUT / "case_08_semantic.svg"
        fig.savefig(svg)
        plt.close(fig)
        body = svg.read_text(encoding="utf-8", errors="replace").lower()
        wanted = [colors[0].lower(), colors[1].lower(), colors[2].lower()]
        missing = [c for c in wanted if c not in body]
        if missing:
            _bad(desc, f"hexes missing from SVG: {missing}")
        else:
            _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 9 — use_journal then use_palette: cycle isn't reverted ───────────

def case_09_journal_then_palette() -> None:
    desc = "case_09 use_journal('nature') then use_palette('semantic') keeps semantic cycle"
    try:
        huitu.use_journal("nature")
        huitu.use_palette("semantic")
        cyc = mpl.rcParams["axes.prop_cycle"].by_key()["color"]
        if cyc[0].lower() == huitu.role("hero").lower():
            _ok(desc)
        else:
            _bad(desc, f"cycle[0]={cyc[0]!r} != hero={huitu.role('hero')!r}")
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 10 — empty palette name must raise ValueError ────────────────────

def case_10_empty_palette_name() -> None:
    desc = "case_10 use_palette('') raises ValueError"
    try:
        huitu.use_palette("")
        _bad(desc, "no exception")
    except ValueError:
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"wrong exception {type(exc).__name__}: {exc}")


# ── Case 11 — SEMANTIC_PALETTE mutation must NOT poison role() ────────────

def case_11_mutation_immutability() -> None:
    desc = "case_11 mutating SEMANTIC_PALETTE['hero'] does not corrupt role('hero')"
    # P1 spec: SEMANTIC_PALETTE should ideally be frozen / role() should
    # snapshot. If a user can mutate the dict and corrupt subsequent lookups,
    # that's a real bug we want surfaced.
    original = huitu.role("hero")
    try:
        huitu.SEMANTIC_PALETTE["hero"] = "#FFFFFF"
        got = huitu.role("hero")
        if got != "#FFFFFF" and got == original:
            _ok(desc)
        else:
            _bad(
                desc,
                f"mutation leaked: role('hero')={got!r}; expected stable {original!r}. "
                "SEMANTIC_PALETTE should be frozen or role() should snapshot.",
            )
    except TypeError:
        # If the dict raises TypeError on assignment that's the *desired* fix.
        _ok(desc)
    finally:
        # Best-effort restore so subsequent cases aren't poisoned.
        try:
            huitu.SEMANTIC_PALETTE["hero"] = original
        except Exception:
            pass


# ── Case 12 — full sweep: every documented role returns hex ───────────────

def case_12_all_18_keys() -> None:
    desc = "case_12 all 18 documented roles return 7-char #RRGGBB"
    huitu.use_journal("default")
    bad: list[str] = []
    for r in REQUIRED_ROLES:
        try:
            c = huitu.role(r)
        except Exception as exc:
            bad.append(f"{r}:{type(exc).__name__}")
            continue
        if not isinstance(c, str) or not HEX_RE.match(c) or len(c) != 7:
            bad.append(f"{r}:{c!r}")
    if bad:
        _bad(desc, "; ".join(bad))
    else:
        _ok(desc)


# ── Case 13 — KeyError message lists choices ──────────────────────────────

def case_13_keyerror_message() -> None:
    desc = "case_13 role('not-a-role') KeyError lists valid roles"
    try:
        huitu.role("not-a-role")
        _bad(desc, "did not raise")
    except KeyError as exc:
        msg = str(exc)
        if "hero" in msg and "baseline" in msg:
            _ok(desc)
        else:
            _bad(desc, f"message lacks role hints: {msg!r}")
    except Exception as exc:
        _bad(desc, f"wrong exception {type(exc).__name__}: {exc}")


def main() -> int:
    case_01_happy()
    case_02_case_insensitive()
    case_03_whitespace_strict()
    case_04_none_input()
    case_05_int_input()
    case_06_list_input()
    case_07_unicode_confusable()
    case_08_semantic_in_svg()
    case_09_journal_then_palette()
    case_10_empty_palette_name()
    case_11_mutation_immutability()
    case_12_all_18_keys()
    case_13_keyerror_message()

    print(f"\n[SUMMARY] test_02_role_palette: {_passed} pass / {_failed} fail")
    if _failed == 0:
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
