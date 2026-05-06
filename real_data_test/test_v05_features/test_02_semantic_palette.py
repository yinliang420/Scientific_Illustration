"""Test 2: Semantic role palette in v0.5.

Exercises every documented branch of ``huitu.role(...)``:

  * Each canonical role key returns a hex string of the documented form.
  * ``role()`` is case-insensitive (per the implementation).
  * Unknown roles raise ``KeyError`` with a useful message.
  * ``huitu.use_palette('semantic')`` swaps the categorical color cycle
    to the semantic ordering hero -> baseline -> accent_teal ...
  * Real plot: a "hero vs baseline" line panel using the semantic colors,
    saved as PNG + SVG. The SVG must still contain editable text.
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
OUT.mkdir(exist_ok=True)

REQUIRED_ROLES = [
    "hero", "hero_2", "hero_soft",
    "baseline", "baseline_2", "baseline_soft",
    "positive", "positive_soft",
    "negative", "negative_soft",
    "neutral", "neutral_light", "neutral_dark", "neutral_black",
    "accent_gold", "accent_teal", "accent_violet", "accent_magenta",
]

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def main() -> int:
    failures: list[str] = []
    huitu.use_journal("default")

    # 1. Each documented role returns a #RRGGBB string.
    for r in REQUIRED_ROLES:
        try:
            c = huitu.role(r)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"role({r!r}) raised {type(exc).__name__}: {exc}")
            continue
        if not isinstance(c, str) or not HEX_RE.match(c):
            failures.append(f"role({r!r}) returned non-hex: {c!r}")
        else:
            print(f"  role({r!r:20s}) -> {c}")

    # 2. SEMANTIC_PALETTE dict matches role().
    for r in REQUIRED_ROLES:
        if huitu.role(r) != huitu.SEMANTIC_PALETTE[r]:
            failures.append(f"role({r}) != SEMANTIC_PALETTE[{r}]")

    # 3. Case-insensitive lookup (per docstring).
    if huitu.role("HERO") != huitu.role("hero"):
        failures.append("role('HERO') is not equal to role('hero') — case-sensitive bug")

    # 4. Unknown role raises KeyError.
    try:
        huitu.role("not-a-role")
        failures.append("role('not-a-role') did NOT raise — silent miss")
    except KeyError as exc:
        msg = str(exc)
        # The error message should suggest valid roles.
        if "hero" not in msg or "baseline" not in msg:
            failures.append(
                f"role error msg does not hint valid roles: {msg!r}"
            )
        else:
            print("  role('not-a-role') correctly raised KeyError with hint")
    except Exception as exc:  # noqa: BLE001
        failures.append(
            f"role('not-a-role') raised wrong exception: {type(exc).__name__}: {exc}"
        )

    # 5. huitu.use_palette('semantic') swaps the prop_cycle.
    colors = huitu.use_palette("semantic")
    if colors[0] != huitu.role("hero"):
        failures.append(
            f"use_palette('semantic')[0]={colors[0]} != role('hero')={huitu.role('hero')}"
        )
    cyc = mpl.rcParams["axes.prop_cycle"].by_key()["color"]
    if cyc[0] != huitu.role("hero"):
        failures.append(
            f"prop_cycle[0]={cyc[0]} != role('hero')={huitu.role('hero')} "
            "after use_palette('semantic')"
        )

    # 6. Real hero-vs-baseline line panel using sample line.csv.
    line_csv = Path(__file__).resolve().parents[2] / "examples" / "sample_data" / "line.csv"
    if not line_csv.exists():
        failures.append(f"sample data missing: {line_csv}")
    else:
        import csv

        t = []
        v = []
        i = []
        T = []
        with line_csv.open() as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                t.append(float(row["t"]))
                v.append(float(row["voltage"]))
                i.append(float(row["current"]))
                T.append(float(row["temperature"]))
        t = np.array(t)
        v = np.array(v)
        i = np.array(i)
        T = np.array(T)

        # Show a hero method + baseline + improvement positive shading.
        huitu.use_journal("nature")
        fig, ax = plt.subplots(figsize=(3.5, 2.5))
        ax.plot(t, v, color=huitu.role("hero"), lw=1.4, label="Ours (V)")
        ax.plot(t, i + 2.0, color=huitu.role("baseline"), lw=1.2,
                label="Baseline (I+2)")
        # Positive / negative directional cues — fill where ours > baseline.
        ax.fill_between(
            t, v, i + 2.0,
            where=(v > i + 2.0),
            color=huitu.role("positive_soft"),
            alpha=0.6, label="ours > baseline",
        )
        ax.fill_between(
            t, v, i + 2.0,
            where=(v < i + 2.0),
            color=huitu.role("negative_soft"),
            alpha=0.6, label="ours < baseline",
        )
        ax.set_xlabel("t (s)")
        ax.set_ylabel("Signal")
        ax.legend(loc="best", fontsize=6)
        for ext in ("png", "svg"):
            fig.savefig(OUT / f"semantic_hero_vs_baseline.{ext}")
        plt.close(fig)

        # Verify the SVG retained editable text.
        svg = OUT / "semantic_hero_vs_baseline.svg"
        text = svg.read_text(encoding="utf-8", errors="replace")
        n_text = len(re.findall(r"<text[\s>]", text))
        if n_text == 0:
            failures.append(f"{svg} has no <text> nodes — editable text broken")
        # Verify the hero hex color appears in the SVG (sanity).
        if huitu.role("hero").lower() not in text.lower():
            failures.append(
                f"hero color {huitu.role('hero')} not found in {svg.name} — "
                "color was overridden somewhere"
            )

    if failures:
        print("\nFAILED:")
        for f in failures:
            print(" -", f)
        return 1
    print("\nALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
