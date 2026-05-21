"""Adversarial test 3: archetype layouts.

Edge cases for the four archetypes:
* degenerate counts (n_supports=0, rows=0, n_cols=1, n_cols=8, 10×10)
* panel-letter overflow (n_supports=12 ⇒ wrap to aa/ab)
* repeated invocation (state leakage across journals)
* multi-format save (svg/png/pdf all editable)
* panel_labels=False suppresses all letters
* dark_image_plate(facecolor='white') still strips ticks/spines
* post-render mutation: panel label color readability vs dark facecolor
* asymmetric_hero hero panel with real imshow + colorbar
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


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def _label_letters_in_svg(svg_path: Path) -> set[str]:
    """Best-effort scrape of one-letter / two-letter panel labels in an SVG."""
    body = _read(svg_path)
    # Extract bare text content; matplotlib emits letters as <text ...>X</text>.
    return set(re.findall(r">([a-z]{1,2})<", body))


# ── Case 1 — happy path for all 4 archetypes ──────────────────────────────

def case_01_happy_each_archetype() -> None:
    desc = "case_01 each archetype renders with default args"
    try:
        huitu.use_journal("nature")
        fig, ax = huitu.archetype.schematic_led()
        plt.close(fig)
        fig, _ = huitu.archetype.dark_image_plate()
        plt.close(fig)
        fig, _ = huitu.archetype.clinical_triptych()
        plt.close(fig)
        fig, _ = huitu.archetype.asymmetric_hero()
        plt.close(fig)
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 2 — schematic_led n_supports=1 ───────────────────────────────────

def case_02_schematic_led_single_support() -> None:
    desc = "case_02 schematic_led(n_supports=1) has 1 support + correct labels"
    try:
        fig, ax = huitu.archetype.schematic_led(n_supports=1)
        n = len(ax["supports"])
        svg = OUT / "case_02_schematic_led_1.svg"
        fig.savefig(svg)
        plt.close(fig)
        letters = _label_letters_in_svg(svg)
        if n != 1:
            _bad(desc, f"got {n} supports")
            return
        # Should contain hero label 'a' and first support 'b'.
        if not ({"a", "b"}.issubset(letters)):
            _bad(desc, f"labels missing — got {sorted(letters)}")
            return
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 3 — schematic_led n_supports=0 (degenerate) ──────────────────────

def case_03_schematic_led_zero_supports() -> None:
    desc = "case_03 schematic_led(n_supports=0) either raises ValueError or gives 0 supports"
    try:
        fig, ax = huitu.archetype.schematic_led(n_supports=0)
        n = len(ax["supports"])
        plt.close(fig)
        if n == 0:
            _ok(desc)
        else:
            _bad(desc, f"silent fail: returned {n} supports for n_supports=0")
    except (ValueError, RuntimeError) as exc:
        # Acceptable: raised cleanly.
        _ok(desc + f" (raised {type(exc).__name__})")
    except Exception as exc:
        _bad(
            desc,
            f"crashed with {type(exc).__name__}: {exc}. Should raise ValueError or render 0 supports gracefully.",
        )


# ── Case 4 — n_supports=12 (label overflow to aa/ab) ──────────────────────

def case_04_schematic_led_12_supports() -> None:
    desc = "case_04 schematic_led(n_supports=12) produces 12 supports + a..m labels"
    # 12 supports + 1 hero = 13 labels. Letter 'a' for hero, then 'b'..'m' for
    # supports — no overflow yet. 26 is the magic number; we hit it next.
    try:
        fig, ax = huitu.archetype.schematic_led(n_supports=12)
        svg = OUT / "case_04_schematic_led_12.svg"
        fig.savefig(svg)
        plt.close(fig)
        n = len(ax["supports"])
        if n != 12:
            _bad(desc, f"got {n} supports")
            return
        letters = _label_letters_in_svg(svg)
        expected_single = set("abcdefghijklm")  # a (hero) + 12 supports
        if not expected_single.issubset(letters):
            missing = expected_single - letters
            _bad(desc, f"missing labels: {sorted(missing)}")
            return
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 5 — schematic_led n_supports=30 hits two-letter wrap ─────────────

def case_05_schematic_led_two_letter_wrap() -> None:
    desc = "case_05 schematic_led(n_supports=30) wraps to two-letter labels"
    try:
        fig, ax = huitu.archetype.schematic_led(n_supports=30)
        svg = OUT / "case_05_schematic_led_30.svg"
        fig.savefig(svg)
        plt.close(fig)
        n = len(ax["supports"])
        if n != 30:
            _bad(desc, f"got {n} supports")
            return
        letters = _label_letters_in_svg(svg)
        # Expect at least one two-letter label (e.g. 'aa', 'ab', ...) past z.
        two_letter = [s for s in letters if len(s) == 2]
        if not two_letter:
            _bad(
                desc,
                "no two-letter panel labels found — _flat_letters wrap may be broken",
            )
            return
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 6 — dark_image_plate rows=0 cols=5 (degenerate row count) ────────

def case_06_dip_zero_rows() -> None:
    desc = "case_06 dark_image_plate(rows=0, cols=5) raises ValueError gracefully"
    try:
        fig, grid = huitu.archetype.dark_image_plate(rows=0, cols=5)
        plt.close(fig)
        # If it returns, the grid should be empty.
        if grid == []:
            _ok(desc + " (returned empty grid)")
        else:
            _bad(desc, f"silent return with grid={grid!r}")
    except (ValueError, RuntimeError):
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"crashed with {type(exc).__name__}: {exc}")


# ── Case 7 — dark_image_plate 1×1 still strips ticks/spines ───────────────

def case_07_dip_1x1_clean() -> None:
    desc = "case_07 dark_image_plate(1,1) tile has no spines / no ticks"
    try:
        fig, grid = huitu.archetype.dark_image_plate(rows=1, cols=1)
        ax = grid[0][0]
        spines_visible = [name for name, sp in ax.spines.items() if sp.get_visible()]
        ticks_x = ax.get_xticks()
        ticks_y = ax.get_yticks()
        plt.close(fig)
        if spines_visible:
            _bad(desc, f"spines still visible: {spines_visible}")
            return
        if len(ticks_x) or len(ticks_y):
            _bad(desc, f"ticks not cleared: x={len(ticks_x)}, y={len(ticks_y)}")
            return
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 8 — dark_image_plate 10×10 (100 tiles), figure still finite ──────

def case_08_dip_10x10() -> None:
    desc = "case_08 dark_image_plate(10,10) returns 100 tiles, fig saves"
    try:
        fig, grid = huitu.archetype.dark_image_plate(rows=10, cols=10)
        total = sum(len(r) for r in grid)
        png = OUT / "case_08_dip_10x10.png"
        fig.savefig(png)
        plt.close(fig)
        if total != 100:
            _bad(desc, f"total tiles {total} != 100")
            return
        if not png.exists() or png.stat().st_size < 100:
            _bad(desc, "png save failed or too small")
            return
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 9 — clinical_triptych n_cols=1 ───────────────────────────────────

def case_09_triptych_single_col() -> None:
    desc = "case_09 clinical_triptych(n_cols=1) has 1+1+1 axes"
    try:
        fig, ax = huitu.archetype.clinical_triptych(n_cols=1)
        n_top = len(ax["top"])
        n_mid = len(ax["mid"])
        n_bot = len(ax["bot"])
        plt.close(fig)
        if (n_top, n_mid, n_bot) != (1, 1, 1):
            _bad(desc, f"got ({n_top}, {n_mid}, {n_bot})")
        else:
            _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 10 — clinical_triptych n_cols=8 (wide) ───────────────────────────

def case_10_triptych_eight_cols() -> None:
    desc = "case_10 clinical_triptych(n_cols=8) has 8+8+8 axes"
    try:
        fig, ax = huitu.archetype.clinical_triptych(n_cols=8)
        n_top = len(ax["top"])
        n_mid = len(ax["mid"])
        n_bot = len(ax["bot"])
        plt.close(fig)
        if (n_top, n_mid, n_bot) != (8, 8, 8):
            _bad(desc, f"got ({n_top}, {n_mid}, {n_bot})")
        else:
            _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 11 — asymmetric_hero with real imshow + colorbar inside hero ─────

def case_11_asymmetric_hero_imshow_colorbar() -> None:
    desc = "case_11 asymmetric_hero hero panel renders imshow + colorbar without crash"
    try:
        huitu.use_journal("nature")
        fig, ax = huitu.archetype.asymmetric_hero()
        # 'e' is the documented hero key.
        rng = np.random.default_rng(0)
        Z = rng.normal(0, 1, (32, 32))
        im = ax["e"].imshow(Z, cmap="viridis", aspect="auto")
        fig.colorbar(im, ax=ax["e"], shrink=0.8)
        png = OUT / "case_11_asym_hero.png"
        fig.savefig(png)
        plt.close(fig)
        if not png.exists() or png.stat().st_size < 100:
            _bad(desc, "png save failed")
        else:
            _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 12 — repeated archetype call with different journals ─────────────

def case_12_repeat_archetype_journal_switch() -> None:
    desc = "case_12 schematic_led() then schematic_led(journal='acs') applies ACS rcParams"
    try:
        huitu.use_journal("default")
        fig, _ = huitu.archetype.schematic_led(journal="nature")
        plt.close(fig)
        # After nature, font.size should be 7 (Nature preset).
        size_after_nature = mpl.rcParams["font.size"]
        fig, _ = huitu.archetype.schematic_led(journal="acs")
        plt.close(fig)
        size_after_acs = mpl.rcParams["font.size"]
        if size_after_nature == 7 and size_after_acs == 8:
            _ok(desc)
        else:
            _bad(
                desc,
                f"font.size unexpected: after_nature={size_after_nature}, after_acs={size_after_acs}",
            )
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 13 — same archetype saved as .svg/.png/.pdf with editable text ──

def case_13_multi_format_save() -> None:
    desc = "case_13 schematic_led saved as svg/png/pdf — vector formats keep <text>"
    try:
        huitu.use_journal("nature")
        fig, ax = huitu.archetype.schematic_led(n_supports=3)
        # Put a unique marker in one support.
        ax["supports"][0].set_xlabel("MULTIFMT_MARKER")
        svg = OUT / "case_13.svg"
        png = OUT / "case_13.png"
        pdf = OUT / "case_13.pdf"
        fig.savefig(svg)
        fig.savefig(png)
        fig.savefig(pdf)
        plt.close(fig)
        if not (svg.exists() and png.exists() and pdf.exists()):
            _bad(desc, "one of svg/png/pdf missing")
            return
        body = _read(svg)
        if "MULTIFMT_MARKER" not in body or "<text" not in body:
            _bad(desc, "SVG missing marker literal or <text>")
            return
        # PDF check: TrueType-family embed (plain /TrueType OR /Type0 +
        # /CIDFontType2) and at least one Tj/TJ show op in the streams.
        import re
        import zlib

        pdf_blob = pdf.read_bytes()
        has_truetype = b"/TrueType" in pdf_blob
        has_type0_cid2 = (b"/Type0" in pdf_blob) and (b"/CIDFontType2" in pdf_blob)
        has_type3 = b"/Subtype /Type3" in pdf_blob
        if has_type3 and not (has_truetype or has_type0_cid2):
            _bad(desc, "PDF uses /Type3 (outlined glyphs) — pdf.fonttype=42 not honored")
            return
        if not (has_truetype or has_type0_cid2):
            _bad(desc, "PDF lacks TrueType / Type0+CIDFontType2 font — fonttype=42 broken")
            return
        streams = re.findall(rb"stream\r?\n(.*?)\r?\nendstream", pdf_blob, re.DOTALL)
        found_text_show = False
        for s in streams:
            try:
                dec = zlib.decompress(s)
            except Exception:
                continue
            if b"Tj" in dec or b"TJ" in dec:
                found_text_show = True
                break
        if not found_text_show:
            _bad(desc, "no Tj/TJ text-show ops in PDF streams")
            return
        _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 14 — panel_labels=False suppresses ALL letters ───────────────────

def case_14_panel_labels_off() -> None:
    desc = "case_14 schematic_led(panel_labels=False) emits no panel-letter annotations"
    try:
        huitu.use_journal("default")
        fig, ax = huitu.archetype.schematic_led(n_supports=3, panel_labels=False)
        svg = OUT / "case_14_no_labels.svg"
        fig.savefig(svg)
        plt.close(fig)
        letters = _label_letters_in_svg(svg)
        # The page may still contain incidental one-letter text in tick labels.
        # We require that the canonical Nature labels 'a','b','c','d' do NOT
        # appear as standalone <text>...</text> nodes near axes corners.
        # As a proxy: matching annotation nodes with fontweight=bold and a
        # transform=offset are the panel labels; if panel_labels=False there
        # shouldn't be a single-char text element styled with font-weight:bold.
        body = _read(svg)
        # Look for the explicit bold annotation form produced by _label().
        # matplotlib emits annotation with style attribute "font-weight: bold".
        bold_single_letters = re.findall(
            r"font-weight:\s*bold[^<]*>([a-z])<",
            body,
        )
        if bold_single_letters:
            _bad(
                desc,
                f"bold single-letter labels still emitted: {bold_single_letters}",
            )
        else:
            _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 15 — dark_image_plate facecolor='white' still strips chrome ──────

def case_15_dip_white_facecolor() -> None:
    desc = "case_15 dark_image_plate(facecolor='white') still strips ticks + spines"
    try:
        fig, grid = huitu.archetype.dark_image_plate(rows=2, cols=2, facecolor="white")
        bad: list[str] = []
        for r, row in enumerate(grid):
            for c, ax in enumerate(row):
                if any(sp.get_visible() for sp in ax.spines.values()):
                    bad.append(f"[{r},{c}] spines visible")
                if len(ax.get_xticks()) or len(ax.get_yticks()):
                    bad.append(f"[{r},{c}] ticks visible")
        plt.close(fig)
        if bad:
            _bad(desc, "; ".join(bad))
        else:
            _ok(desc)
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


# ── Case 16 — post-render mutation: caller flips hero facecolor to black ──

def case_16_post_render_facecolor_mutation() -> None:
    desc = "case_16 mutating axes['hero'].set_facecolor('black') post-render still saves OK"
    try:
        huitu.use_journal("nature")
        fig, ax = huitu.archetype.schematic_led(n_supports=2)
        ax["hero"].set_facecolor("black")
        # The panel label was placed as a black-on-default annotation. After
        # facecolor=black it'll be black-on-black (unreadable). This case is
        # primarily a *survival* check: the save shouldn't crash and the
        # rasterised file shouldn't be empty.
        png = OUT / "case_16_mutated.png"
        fig.savefig(png)
        plt.close(fig)
        if not png.exists() or png.stat().st_size < 100:
            _bad(desc, "png save failed / empty after mutation")
        else:
            _ok(
                desc
                + " (note: label color may now be black-on-black — readability is a UX bug if so)"
            )
    except Exception as exc:
        _bad(desc, f"exception {type(exc).__name__}: {exc}")


def main() -> int:
    case_01_happy_each_archetype()
    case_02_schematic_led_single_support()
    case_03_schematic_led_zero_supports()
    case_04_schematic_led_12_supports()
    case_05_schematic_led_two_letter_wrap()
    case_06_dip_zero_rows()
    case_07_dip_1x1_clean()
    case_08_dip_10x10()
    case_09_triptych_single_col()
    case_10_triptych_eight_cols()
    case_11_asymmetric_hero_imshow_colorbar()
    case_12_repeat_archetype_journal_switch()
    case_13_multi_format_save()
    case_14_panel_labels_off()
    case_15_dip_white_facecolor()
    case_16_post_render_facecolor_mutation()

    print(f"\n[SUMMARY] test_03_archetypes: {_passed} pass / {_failed} fail")
    if _failed == 0:
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
