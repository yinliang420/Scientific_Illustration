"""Regenerate the 9 README showcase images at journal-grade HD resolution.

Nine intentionally-different highlight figures covering the full huitu
surface, suitable for a 3 × 3 README grid:

    01  archetype.schematic_led        multi-panel Nature Fig 1 mockup
    02  Rietveld refinement             obs / calc / diff + hkl markers
    03  Operando XRD + galvanostatic    battery 2-panel (v0.4 family)
    04  BET isotherm + linear plot      v0.6 — auto V_m, S_BET, R²
    05  dQ/dV multi-cycle ageing        v0.6 — Savgol-smoothed peaks
    06  Bump chart                      rank evolution
    07  Ridgeline distributions         stacked KDE
    08  Pourbaix diagram                E-pH polygon regions
    09  Palette catalog                 55 huitu palettes visual identity

Each PNG is ~1600+ px native @ 300 dpi so they stay crisp on Retina / 4K.

Run from repo root::

    python docs/showcase/render.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

import huitu

OUT = Path(__file__).resolve().parent
SAMPLE = OUT.parent.parent / "examples" / "sample_data"
HD_DPI = 300


# ── 1. archetype.schematic_led — Nature Fig 1 mockup ───────────────────────

def _draw_hero_schematic(ax) -> None:
    """Three-stage Pristine → Activated → Cycled mechanism cartoon."""
    ax.set_xlim(0, 10); ax.set_ylim(0, 4.4); ax.set_axis_off()
    # Soft tinted backdrop to separate hero from supports visually.
    ax.add_patch(mpatches.Rectangle(
        (0.1, 0.2), 9.8, 4.0,
        facecolor="#FAFBFC", edgecolor="#E5E8EC", linewidth=0.6, zorder=0,
    ))
    stages = [
        ("Pristine",  huitu.role("baseline_soft"), 1.6, "Layered MnO$_2$"),
        ("Activated", huitu.role("hero_soft"),     5.0, "Cu-doped, opened"),
        ("Cycled",    huitu.role("hero"),          8.4, "Stable @ 500 cyc."),
    ]
    for label, color, cx, sub in stages:
        rect = mpatches.FancyBboxPatch(
            (cx - 1.05, 1.05), 2.1, 1.95,
            boxstyle="round,pad=0.05,rounding_size=0.22",
            linewidth=1.1, edgecolor=huitu.role("neutral_dark"),
            facecolor=color, alpha=0.92, zorder=2,
        )
        ax.add_patch(rect)
        text_color = "white" if color == huitu.role("hero") else huitu.role("neutral_dark")
        ax.text(cx, 2.30, label, ha="center", va="center",
                fontsize=12, fontweight="bold", color=text_color, zorder=3)
        ax.text(cx, 1.50, sub, ha="center", va="center",
                fontsize=8, color=text_color, zorder=3, alpha=0.92)
    # Stage transition arrows with verb labels above.
    for (x_from, x_to), verb in [((2.75, 3.85), "activate"),
                                  ((6.15, 7.25), "cycle")]:
        ax.annotate("", xy=(x_to, 2.0), xytext=(x_from, 2.0),
                    arrowprops=dict(arrowstyle="-|>", lw=1.6,
                                    color=huitu.role("neutral_dark"),
                                    mutation_scale=14), zorder=3)
        ax.text((x_from + x_to) / 2, 2.35, verb,
                ha="center", va="bottom", fontsize=8, style="italic",
                color=huitu.role("neutral_dark"), zorder=3)
    ax.text(5.0, 3.85,
            "Capacity gained without changing payload identity",
            ha="center", va="center", fontsize=10, fontweight="bold",
            color=huitu.role("neutral_dark"))


def render_archetype() -> None:
    # Slightly taller figure so 4 supports get more room each.
    fig, ax = huitu.archetype.schematic_led(
        journal="default", n_supports=4, figsize=(8.4, 6.6),
    )
    _draw_hero_schematic(ax["hero"])
    # No subplot titles — axis labels already tell the reader what each
    # support is. Panel letters (b/c/d/e) at the corner are sufficient.
    huitu.plot_xrd(str(SAMPLE / "xrd.txt"), ax=ax["supports"][0])
    huitu.plot_cv (str(SAMPLE / "cv.txt"),  ax=ax["supports"][1])
    huitu.plot_eis(str(SAMPLE / "eis.txt"), ax=ax["supports"][2])
    # 4th support — role-themed capacity-by-stage bar.
    sup3 = ax["supports"][3]
    sup3.bar([0, 1, 2], [85, 142, 168],
             color=[huitu.role("baseline_soft"),
                    huitu.role("hero_soft"),
                    huitu.role("hero")],
             edgecolor="white", linewidth=0.6, width=0.72)
    sup3.set_xticks([0, 1, 2])
    sup3.set_xticklabels(["Pristine", "Activ.", "Cycled"],
                         fontsize=7, rotation=0)
    sup3.set_ylabel(r"Capacity (mAh g$^{-1}$)", fontsize=8)
    sup3.set_xlabel("")
    sup3.spines["top"].set_visible(False)
    sup3.spines["right"].set_visible(False)
    sup3.tick_params(axis="y", labelsize=7)
    # Value labels above bars for quantitative readability.
    for i, v in enumerate([85, 142, 168]):
        sup3.text(i, v + 4, str(v), ha="center", va="bottom",
                  fontsize=7, color=huitu.role("neutral_dark"))
    sup3.set_ylim(0, 200)
    fig.savefig(OUT / "01_archetype_schematic_led.png",
                bbox_inches="tight", dpi=HD_DPI, facecolor="white")
    plt.close(fig)


# ── 2. Rietveld refinement ─────────────────────────────────────────────────

def render_rietveld() -> None:
    huitu.use_journal("default")
    rng = np.random.default_rng(2)
    two_theta = np.linspace(20.0, 60.0, 1200)
    # Synth 5 Bragg peaks + smooth background + noise.
    bragg_pos = [24.3, 28.6, 32.1, 38.9, 46.4]
    bragg_int = [1.0, 0.7, 0.55, 0.35, 0.22]
    bg = 0.05 + 0.03 * np.exp(-((two_theta - 35) ** 2) / 200)
    calc = bg.copy()
    for p, i in zip(bragg_pos, bragg_int):
        calc += i * 0.04 ** 2 / ((two_theta - p) ** 2 + 0.04 ** 2)
    obs = calc + rng.normal(0, 0.012, two_theta.size)
    obs[200:230] *= 1.08   # small misfit region
    obs[600:620] *= 0.93

    # 4-column input: 2θ, obs, calc, bkg
    data = np.column_stack([two_theta, obs, calc, bg])
    fig, axes = huitu.plot_rietveld(
        data, hkl_positions=bragg_pos, bragg_label="hkl",
    )
    fig.set_size_inches(7.4, 5.4)
    fig.savefig(OUT / "02_rietveld_refinement.png",
                bbox_inches="tight", dpi=HD_DPI, facecolor="white")
    plt.close(fig)


# ── 3. Operando XRD + galvanostatic ────────────────────────────────────────

def _synth_operando(seed: int = 1) -> dict:
    rng = np.random.default_rng(seed)
    two_theta = np.linspace(20.0, 35.0, 220)
    time = np.linspace(0.0, 12.0, 60)
    peak_pos = 26.0 + 1.8 * (time / time[-1])
    peak_w = 0.18 + 0.12 * (time / time[-1])
    peak_h = 1.0 - 0.18 * (time / time[-1])
    Z = np.zeros((len(time), len(two_theta)))
    for i in range(len(time)):
        bg = 0.18 * np.exp(-((two_theta - 27.5) ** 2) / 25.0)
        peak = peak_h[i] * peak_w[i] ** 2 / (
            (two_theta - peak_pos[i]) ** 2 + peak_w[i] ** 2
        )
        Z[i] = bg + peak + rng.normal(0, 0.012, two_theta.size)
    voltage = 3.0 + 1.3 * (time / time[-1]) + 0.04 * np.sin(8 * time / time[-1])
    return dict(Z=Z, two_theta=two_theta, time=time, voltage=voltage)


def render_xrd_echem() -> None:
    huitu.use_journal("default")
    d = _synth_operando(seed=3)
    fig, axes = huitu.plot_operando_xrd_echem(
        d["Z"], x=d["two_theta"], y=d["time"], echem=d["voltage"],
        xlabel=r"2$\theta$ (°)", ylabel="time (h)",
        echem_xlabel="E (V vs. Li/Li$^+$)",
    )
    fig.set_size_inches(8.0, 5.0)
    fig.savefig(OUT / "03_operando_xrd_echem.png",
                bbox_inches="tight", dpi=HD_DPI, facecolor="white")
    plt.close(fig)


# ── 4. BET isotherm + linear plot ───────────────────────────────────────────

def render_bet() -> None:
    rng = np.random.default_rng(4)
    p_rel = np.linspace(0.01, 0.99, 35)
    V_m_true, C_true = 12.0, 80.0
    v_ads = (V_m_true * C_true * p_rel) / ((1 - p_rel) * (1 + (C_true - 1) * p_rel))
    v_ads += rng.normal(0, 0.4, p_rel.size)
    v_des = v_ads + 1.5 * np.exp(-((p_rel - 0.7) ** 2) / 0.02)
    fig, axes, _ = huitu.plot_bet((p_rel, v_ads, v_des),
                                   journal="default", label="MnO₂-Cu",
                                   figsize=(7.2, 3.4))
    fig.savefig(OUT / "04_bet_isotherm.png",
                bbox_inches="tight", dpi=HD_DPI, facecolor="white")
    plt.close(fig)


# ── 5. dQ/dV multi-cycle ageing ─────────────────────────────────────────────

def render_dqdv() -> None:
    def _cycle(shift, broaden):
        v = np.linspace(2.5, 4.4, 400)
        q = 150.0 * (
            1.0 / (1.0 + np.exp(-(30.0 - broaden) * (v - (3.7 + shift))))
            + 0.4 / (1.0 + np.exp(-(25.0 - broaden) * (v - (3.5 + shift))))
        )
        return v, q
    fig, ax = huitu.plot_dqdv(
        [_cycle(0.00, 0.0), _cycle(0.04, 8.0)],
        labels=["cycle 1", "cycle 50"],
        journal="default",
    )
    fig.set_size_inches(6.4, 4.6)
    fig.savefig(OUT / "05_dqdv_multi_cycle.png",
                bbox_inches="tight", dpi=HD_DPI, facecolor="white")
    plt.close(fig)


# ── 6. Bump chart — technique rank evolution ───────────────────────────────

def render_bump() -> None:
    rng = np.random.default_rng(6)
    years = ["2020", "2021", "2022", "2023", "2024", "2025", "2026"]
    base = {
        "operando XRD":     [120, 145, 178, 220, 280, 340, 420],
        "in-situ EIS":      [ 90,  92, 100, 110, 118, 122, 128],
        "synchrotron XAS":  [110, 118, 125, 132, 140, 145, 150],
        "DFT+U":            [115, 130, 152, 172, 190, 208, 225],
        "ML potentials":    [ 20,  35,  72, 130, 220, 320, 480],
        "cryo-EM":          [ 78,  86,  95,  98, 100, 102, 105],
    }
    data = {name: [v + rng.normal(0, 3) for v in vals]
            for name, vals in base.items()}
    fig, ax = huitu.plot_bump(data, x_labels=years)
    ax.set_title("Publications by technique (rank)",
                 fontsize=11, pad=8, color=huitu.role("neutral_dark"))
    fig.set_size_inches(7.6, 5.0)
    fig.savefig(OUT / "06_bump_publications.png",
                bbox_inches="tight", dpi=HD_DPI, facecolor="white")
    plt.close(fig)


# ── 7. Ridgeline distributions ─────────────────────────────────────────────

def render_ridgeline() -> None:
    rng = np.random.default_rng(7)
    n = 6
    means = np.linspace(0.4, 0.92, n)
    spreads = np.linspace(0.06, 0.03, n)
    distributions = [rng.normal(m, s, 800) for m, s in zip(means, spreads)]
    labels = [f"sample {i+1}" for i in range(n)]
    fig, ax = huitu.plot_ridgeline(
        distributions, labels=labels,
        xlabel="Score",
        palette="met-hiroshige",
    )
    ax.set_title("Score distributions — six samples",
                 fontsize=11, pad=8, color=huitu.role("neutral_dark"))
    fig.set_size_inches(6.4, 5.0)
    fig.savefig(OUT / "07_ridgeline_distributions.png",
                bbox_inches="tight", dpi=HD_DPI, facecolor="white")
    plt.close(fig)


# ── 8. Pourbaix diagram ─────────────────────────────────────────────────────

def render_pourbaix() -> None:
    """Synthetic Fe / H2O-like Pourbaix regions.

    Five regions that perfectly tile (pH=0..14) × (E=-1..2) with no gaps
    and no overlaps:

      * Fe³⁺(aq) — top-left rectangle           (acidic + oxidizing)
      * Fe²⁺(aq) — middle-left rectangle        (acidic + mildly reducing)
      * Fe(s)    — bottom strip across full pH  (strongly reducing)
      * Fe₂O₃(s) — top-right L-shape            (basic + oxidizing)
      * Fe(OH)₂(s) — middle-right pentagon      (basic + mildly reducing)

    Shared boundaries:
      pH = 5 between Fe³⁺/Fe²⁺ (left) and Fe₂O₃/Fe(OH)₂ (right).
      E = 0.77 between Fe³⁺ ↔ Fe²⁺ and along upper Fe(OH)₂ edge.
      Diagonal (5, 0.77) → (9, 0.0) separates Fe₂O₃ (above) from
      Fe(OH)₂ (below) — the only non-axis-aligned boundary.
    """
    regions = [
        # Acidic, oxidizing: Fe³⁺
        {
            "label": "Fe³⁺(aq)",
            "vertices": [(0, 0.77), (5, 0.77), (5, 2.0), (0, 2.0)],
            "color": "#E8A89C",   # warm pink — oxidized aqueous
        },
        # Acidic, mildly reducing: Fe²⁺
        {
            "label": "Fe²⁺(aq)",
            "vertices": [(0, -0.45), (5, -0.45), (5, 0.77), (0, 0.77)],
            "color": "#C5D4E8",   # cool blue — reduced aqueous
        },
        # Strongly reducing: metallic Fe across full pH range
        {
            "label": "Fe(s)",
            "vertices": [(0, -1.0), (14, -1.0), (14, -0.45), (0, -0.45)],
            "color": "#D8D8D8",   # neutral grey — native metal
        },
        # Basic, oxidizing: hematite
        {
            "label": "Fe₂O₃(s)",
            "vertices": [(5, 0.77), (9, 0.0), (14, 0.0), (14, 2.0), (5, 2.0)],
            "color": "#B85450",   # deep rust red — hematite
        },
        # Basic, mildly reducing: ferrous hydroxide
        {
            "label": "Fe(OH)₂(s)",
            "vertices": [(5, -0.45), (14, -0.45), (14, 0.0),
                         (9, 0.0), (5, 0.77)],
            "color": "#7BA7C7",   # muted blue — hydroxide
        },
    ]
    fig, ax = huitu.plot_pourbaix(regions, journal="default",
                                   ph_range=(0, 14), e_range=(-1.0, 2.0),
                                   alpha=0.55)
    # `label_position="top"` mis-places labels for the irregular Fe(OH)₂
    # pentagon (puts it above the diagonal, inside Fe₂O₃) and pins Fe(s)
    # to the boundary with Fe²⁺. Replace the auto-placed bbox'd labels
    # with manually chosen positions guaranteed to sit inside each region.
    for txt in list(ax.texts):
        if txt.get_bbox_patch() is not None and "Fe" in txt.get_text():
            txt.remove()
    label_positions = {
        r"Fe$^{3+}$(aq)":  (2.4, 1.45),
        r"Fe$^{2+}$(aq)":  (2.4, 0.16),
        r"Fe(s)":          (7.0, -0.72),
        r"Fe$_2$O$_3$(s)": (11.0, 1.45),
        r"Fe(OH)$_2$(s)":  (10.5, -0.22),
    }
    for label, (x, y) in label_positions.items():
        ax.text(x, y, label, ha="center", va="center", fontsize=8,
                zorder=4, bbox=dict(facecolor="white", edgecolor="none",
                                     alpha=0.88, pad=2))
    # Inline-label the water-stability lines at their right endpoints
    # instead of cluttering the corner legend.
    ax.get_legend().remove()
    ph_end = 14
    ax.text(ph_end - 0.2, 1.229 - 0.05916 * ph_end - 0.05, r"O$_2$/H$_2$O",
            ha="right", va="top", fontsize=7, style="italic", color="#555",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=1))
    ax.text(ph_end - 0.2, -0.05916 * ph_end + 0.06, r"H$_2$/H$_2$O",
            ha="right", va="bottom", fontsize=7, style="italic", color="#555",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=1))
    ax.set_title("Pourbaix diagram — Fe / H₂O at 25 °C (synthetic)",
                 fontsize=11, pad=10, color=huitu.role("neutral_dark"))
    fig.set_size_inches(7.0, 5.2)
    fig.savefig(OUT / "08_pourbaix_diagram.png",
                bbox_inches="tight", dpi=HD_DPI, facecolor="white")
    plt.close(fig)


# ── 9. Palette catalog ──────────────────────────────────────────────────────

def render_palette_catalog() -> None:
    huitu.use_journal("default")
    showcase_palettes = [
        ("hero (semantic)", "semantic"),
        ("nature-cat",      "nature-cat"),
        ("science-cat",     "science-cat"),
        ("tol-vibrant",     "tol-vibrant"),
        ("okabe-ito",       "okabe-ito"),
        ("nord",            "nord"),
        ("crameri-batlow",  "crameri-batlow"),
        ("crameri-roma",    "crameri-roma"),
    ]
    fig, ax = plt.subplots(figsize=(7.6, 5.0), constrained_layout=True)
    max_n = max(len(huitu.PALETTES[n]) for _, n in showcase_palettes)
    for row, (label, name) in enumerate(showcase_palettes):
        colors = list(huitu.PALETTES[name])
        for col_idx, color in enumerate(colors):
            ax.add_patch(plt.Rectangle((col_idx, row), 1, 0.85,
                                        facecolor=color,
                                        edgecolor="white", linewidth=0.8))
        ax.text(-0.4, row + 0.425, label, ha="right", va="center",
                fontsize=10, fontfamily="monospace",
                color=huitu.role("neutral_dark"))
        ax.text(len(colors) + 0.2, row + 0.425, f"{len(colors)}",
                ha="left", va="center",
                fontsize=8.5, color=huitu.role("neutral"))
    ax.set_xlim(-5.5, max_n + 1.5)
    ax.set_ylim(-0.5, len(showcase_palettes))
    ax.invert_yaxis()
    ax.set_axis_off()
    ax.set_title("huitu — 55 curated palettes (8 shown)",
                 fontsize=12, pad=10, color=huitu.role("neutral_dark"))
    fig.savefig(OUT / "09_palette_catalog.png",
                bbox_inches="tight", dpi=HD_DPI, facecolor="white")
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("rendering 9 HD showcase images @ 300 dpi...")
    render_archetype();          print("  ✓ 01_archetype_schematic_led")
    render_rietveld();           print("  ✓ 02_rietveld_refinement")
    render_xrd_echem();          print("  ✓ 03_operando_xrd_echem")
    render_bet();                print("  ✓ 04_bet_isotherm")
    render_dqdv();               print("  ✓ 05_dqdv_multi_cycle")
    render_bump();               print("  ✓ 06_bump_publications")
    render_ridgeline();          print("  ✓ 07_ridgeline_distributions")
    render_pourbaix();           print("  ✓ 08_pourbaix_diagram")
    render_palette_catalog();    print("  ✓ 09_palette_catalog")
    print("all 9 written to docs/showcase/")


if __name__ == "__main__":
    main()
