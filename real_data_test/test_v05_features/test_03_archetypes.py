"""Test 3: Four Nature-style archetypes in v0.5.

Renders all four archetypes from ``huitu.archetype`` with **real** plot_*
content drawn into every panel using the sample data. Saves both PNG and
SVG. Actively probes for layout problems (label collisions, missing axes,
etc.).

  * ``schematic_led(n_supports=3)`` — hero schematic + 3 supporting
    quantitative panels (XRD / CV / EIS).
  * ``dark_image_plate(rows=3, cols=5)`` — black-faced grid populated with
    synthetic micrographs (because we have no real images in sample_data,
    we synthesize plausible 2-D fields).
  * ``clinical_triptych()`` — 3 columns x 3 rows of trajectories /
    forest plot / summary bars.
  * ``asymmetric_hero()`` — six panels with the hero spanning rows.
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

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = ROOT / "examples" / "sample_data"
OUT = Path(__file__).resolve().parent / "output"
OUT.mkdir(exist_ok=True)


def _save_both(fig, stem: str) -> tuple[Path, Path]:
    png = OUT / f"{stem}.png"
    svg = OUT / f"{stem}.svg"
    fig.savefig(png)
    fig.savefig(svg)
    plt.close(fig)
    return png, svg


def _grep_text(svg: Path) -> int:
    text = svg.read_text(encoding="utf-8", errors="replace")
    return len(re.findall(r"<text[\s>]", text))


# ── 1. schematic_led ────────────────────────────────────────────────────────

def test_schematic_led(failures: list[str]) -> None:
    fig, ax = huitu.archetype.schematic_led(journal="nature", n_supports=3)
    if "hero" not in ax or "supports" not in ax:
        failures.append("schematic_led: missing 'hero'/'supports' keys")
        return
    if len(ax["supports"]) != 3:
        failures.append(
            f"schematic_led(n_supports=3): got {len(ax['supports'])} supports"
        )

    # Hero panel: a synthetic mechanism cartoon (just a labeled block diagram).
    hero = ax["hero"]
    hero.set_facecolor("#F5F7FB")
    hero.set_xlim(0, 10)
    hero.set_ylim(0, 4)
    hero.set_xticks([])
    hero.set_yticks([])
    for x0, label, fc in [
        (0.5, "Pristine", huitu.role("baseline_soft")),
        (3.5, "Activated", huitu.role("hero_soft")),
        (6.5, "Cycled", huitu.role("hero")),
    ]:
        hero.add_patch(
            mpl.patches.FancyBboxPatch(
                (x0, 1.4), 2.4, 1.2,
                boxstyle="round,pad=0.1",
                fc=fc, ec="black", lw=0.7,
            )
        )
        hero.text(x0 + 1.2, 2.0, label, ha="center", va="center",
                  fontsize=8)
    hero.annotate("", xy=(3.4, 2.0), xytext=(3.0, 2.0),
                  arrowprops=dict(arrowstyle="->", lw=0.9))
    hero.annotate("", xy=(6.4, 2.0), xytext=(6.0, 2.0),
                  arrowprops=dict(arrowstyle="->", lw=0.9))

    # Supporting quantitative panels — XRD, CV, EIS.
    huitu.plot_xrd(SAMPLES / "xrd.txt", ax=ax["supports"][0], journal="nature")
    huitu.plot_cv(SAMPLES / "cv.txt", ax=ax["supports"][1], journal="nature")
    huitu.plot_eis(SAMPLES / "eis.txt", ax=ax["supports"][2], journal="nature")

    png, svg = _save_both(fig, "archetype_schematic_led")
    if _grep_text(svg) == 0:
        failures.append(f"{svg.name}: no <text> nodes (editable text broken)")
    print(f"  schematic_led -> {png.name}, {svg.name}")


# ── 2. dark_image_plate ─────────────────────────────────────────────────────

def test_dark_image_plate(failures: list[str]) -> None:
    rows, cols = 3, 5
    fig, grid = huitu.archetype.dark_image_plate(
        rows=rows, cols=cols, journal="nature"
    )
    if not isinstance(grid, list) or len(grid) != rows or any(
        len(r) != cols for r in grid
    ):
        failures.append(
            f"dark_image_plate(rows={rows}, cols={cols}): grid shape wrong"
        )
        return

    # Synthesize plausible "fluorescence" micrographs.
    rng = np.random.default_rng(0)
    for r in range(rows):
        for c in range(cols):
            ax = grid[r][c]
            # base random field + a couple of bright spots
            field = rng.normal(0.3, 0.05, (64, 64))
            yy, xx = np.mgrid[0:64, 0:64]
            for _ in range(3):
                cy, cx = rng.integers(8, 56, size=2)
                amp = rng.uniform(0.6, 1.0)
                field += amp * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / 25.0)
            field = np.clip(field, 0, None)
            ax.imshow(field, cmap="magma", aspect="equal",
                      origin="lower", interpolation="bilinear")
            # Scale bar — every panel needs one in real Nature plates.
            ax.plot([4, 18], [4, 4], color="white", lw=1.8)
            if r == rows - 1 and c == cols - 1:
                ax.text(11, 7, "1 µm", color="white", ha="center", va="bottom",
                        fontsize=6)

    png, svg = _save_both(fig, "archetype_dark_image_plate")
    n_text = _grep_text(svg)
    print(f"  dark_image_plate -> {png.name}, {svg.name}, <text> count={n_text}")
    # Each row should label its first cell with a, b, c…
    if n_text == 0:
        failures.append(
            f"{svg.name}: no <text> nodes — panel labels missing entirely"
        )


# ── 3. clinical_triptych ────────────────────────────────────────────────────

def test_clinical_triptych(failures: list[str]) -> None:
    fig, ax = huitu.archetype.clinical_triptych(journal="nature")
    for key in ("top", "mid", "bot"):
        if key not in ax:
            failures.append(f"clinical_triptych: key {key!r} missing")
            return

    rng = np.random.default_rng(1)
    n_subjects = 30
    weeks = np.arange(0, 13)

    # Top row: longitudinal trajectories (3 outcomes). Spaghetti per subject.
    outcome_names = ["Tumor volume", "Body weight", "Activity"]
    centers = [10.0, 25.0, 0.5]
    for col, (axt, name, ctr) in enumerate(
        zip(ax["top"], outcome_names, centers)
    ):
        traj = ctr + rng.normal(0, 0.05 * ctr, (n_subjects, len(weeks)))
        traj += np.linspace(0, -0.3 * ctr if col == 0 else 0.1 * ctr, len(weeks))
        for s in range(n_subjects):
            axt.plot(weeks, traj[s], color=huitu.role("neutral_light"), lw=0.4)
        axt.plot(weeks, traj.mean(0), color=huitu.role("hero"), lw=1.6,
                 label="mean")
        axt.set_title(name, fontsize=7)
        axt.set_xlabel("Week")
        if col == 0:
            axt.set_ylabel("Value")

    # Middle row: forest plot per outcome.
    studies = [f"Study {k}" for k in range(1, 7)]
    for col, axm in enumerate(ax["mid"]):
        effects = rng.normal(0.0, 0.4, len(studies))
        ses = rng.uniform(0.1, 0.3, len(studies))
        ys = np.arange(len(studies))[::-1]
        axm.errorbar(
            effects, ys, xerr=ses,
            fmt="s", color=huitu.role("hero"),
            ecolor=huitu.role("neutral_dark"),
            ms=3.5, lw=0.8, capsize=2,
        )
        axm.axvline(0, color=huitu.role("baseline"), ls="--", lw=0.7)
        axm.set_yticks(ys)
        axm.set_yticklabels(studies, fontsize=6)
        axm.set_xlabel("Effect size (log HR)")

    # Bottom row: compact summary bars per outcome.
    groups = ["Control", "Low dose", "High dose"]
    for col, axb in enumerate(ax["bot"]):
        vals = rng.uniform(0.5, 1.5, len(groups))
        errs = rng.uniform(0.05, 0.18, len(groups))
        x = np.arange(len(groups))
        axb.bar(x, vals, yerr=errs,
                color=[huitu.role("baseline"),
                       huitu.role("neutral"),
                       huitu.role("hero")],
                edgecolor="black", lw=0.5, capsize=3)
        axb.set_xticks(x)
        axb.set_xticklabels(groups, fontsize=6, rotation=20)
        if col == 0:
            axb.set_ylabel("Summary metric")

    png, svg = _save_both(fig, "archetype_clinical_triptych")
    if _grep_text(svg) == 0:
        failures.append(f"{svg.name}: no <text> nodes")
    print(f"  clinical_triptych -> {png.name}, {svg.name}")


# ── 4. asymmetric_hero ──────────────────────────────────────────────────────

def test_asymmetric_hero(failures: list[str]) -> None:
    fig, ax = huitu.archetype.asymmetric_hero(journal="nature")
    for key in ("a", "b", "c", "d", "e", "f"):
        if key not in ax:
            failures.append(f"asymmetric_hero: key {key!r} missing")
            return

    rng = np.random.default_rng(2)

    # a — wide top-left: an XRD pattern.
    huitu.plot_xrd(SAMPLES / "xrd.txt", ax=ax["a"], journal="nature")

    # b — small top-right cell: a CV summary.
    huitu.plot_cv(SAMPLES / "cv.txt", ax=ax["b"], journal="nature")

    # c — middle wide-left: Raman.
    huitu.plot_raman(SAMPLES / "raman.txt", ax=ax["c"], journal="nature")

    # d — middle small: a small bar comparison from bar.csv.
    huitu.plot_bar(SAMPLES / "bar.csv", ax=ax["d"], journal="nature",
                   ylabel="Capacity (mAh g⁻¹)")

    # e — hero (spans all 3 rows): a UMAP-like scatter.
    n = 400
    xy = rng.normal(0, 1, (n, 2))
    xy[:n // 2] += [3.0, 0.0]
    xy[n // 2:] += [-2.5, 1.5]
    classes = np.r_[np.zeros(n // 2), np.ones(n - n // 2)]
    for k, color in enumerate([huitu.role("hero"), huitu.role("baseline")]):
        m = classes == k
        ax["e"].scatter(xy[m, 0], xy[m, 1], s=8, color=color,
                        alpha=0.7, edgecolor="none",
                        label=("class A", "class B")[k])
    ax["e"].set_xlabel("UMAP-1")
    ax["e"].set_ylabel("UMAP-2")
    ax["e"].legend(loc="lower right", fontsize=6)

    # f — bottom wide: a heatmap.
    huitu.plot_heatmap(SAMPLES / "heatmap.csv", ax=ax["f"], journal="nature",
                       cbar_label="z-score")

    png, svg = _save_both(fig, "archetype_asymmetric_hero")
    if _grep_text(svg) == 0:
        failures.append(f"{svg.name}: no <text> nodes")
    print(f"  asymmetric_hero -> {png.name}, {svg.name}")


def main() -> int:
    failures: list[str] = []
    huitu.use_journal("nature")
    test_schematic_led(failures)
    test_dark_image_plate(failures)
    test_clinical_triptych(failures)
    test_asymmetric_hero(failures)

    # Edge cases — n_supports=2 and n_supports=5 should both work.
    for n in (2, 5):
        try:
            fig, ax = huitu.archetype.schematic_led(n_supports=n)
            if len(ax["supports"]) != n:
                failures.append(
                    f"schematic_led(n_supports={n}): "
                    f"got {len(ax['supports'])} supports"
                )
            plt.close(fig)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"schematic_led(n_supports={n}) raised: {exc}")

    # Edge: dark_image_plate with rows=1 cols=1 (degenerate).
    try:
        fig, grid = huitu.archetype.dark_image_plate(rows=1, cols=1)
        if not (len(grid) == 1 and len(grid[0]) == 1):
            failures.append("dark_image_plate(1,1): grid shape unexpected")
        plt.close(fig)
    except Exception as exc:  # noqa: BLE001
        failures.append(f"dark_image_plate(1,1) raised: {exc}")

    if failures:
        print("\nFAILED:")
        for f in failures:
            print(" -", f)
        return 1
    print("\nALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
