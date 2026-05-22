"""Visual-audit harness — render one figure per public huitu plot helper.

8 categories × N functions each. Each PNG goes to a category subdirectory so
a reviewer can scan one folder at a time without distraction.

Output: ``tests/visual_audit/output/<category>/<function>.png``  (gitignored).
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import huitu

ROOT = Path(__file__).resolve().parent
SAMPLE = ROOT.parent.parent / "examples" / "sample_data"
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)


def _save(fig, category: str, name: str, dpi: int = 200) -> None:
    """Save figure into its category subdir."""
    sub = OUT / category
    sub.mkdir(exist_ok=True)
    fig.savefig(sub / f"{name}.png", bbox_inches="tight", dpi=dpi, facecolor="white")
    plt.close(fig)


# ── 1. characterization ─────────────────────────────────────────────────────

def gen_characterization() -> None:
    cat = "01_characterization"
    huitu.use_journal("nature")

    fig, ax = huitu.plot_xrd(str(SAMPLE / "xrd.txt"),
                              hkl={28.4: "(111)", 32.9: "(200)"})
    _save(fig, cat, "plot_xrd")

    fig, ax = huitu.plot_xps(str(SAMPLE / "xps.txt"))
    _save(fig, cat, "plot_xps")

    fig, ax = huitu.plot_raman(str(SAMPLE / "raman.txt"))
    _save(fig, cat, "plot_raman")

    fig, ax = huitu.plot_ftir(str(SAMPLE / "ftir.txt"))
    _save(fig, cat, "plot_ftir")

    fig, ax = huitu.plot_uvvis(str(SAMPLE / "uvvis.txt"))
    _save(fig, cat, "plot_uvvis")

    fig, ax = huitu.plot_pl(str(SAMPLE / "pl.txt"))
    _save(fig, cat, "plot_pl")

    fig, ax = huitu.plot_thermal(str(SAMPLE / "tga.txt"))
    _save(fig, cat, "plot_thermal")

    fig, axes = huitu.plot_rietveld(str(SAMPLE / "rietveld.txt"))
    _save(fig, cat, "plot_rietveld")

    # BET (returns 3-tuple) — synthesise a clean Type-IV-ish isotherm.
    rng = np.random.default_rng(4)
    p_rel = np.linspace(0.01, 0.99, 35)
    V_m_true, C_true = 12.0, 80.0
    v_ads = (V_m_true * C_true * p_rel) / ((1 - p_rel) * (1 + (C_true - 1) * p_rel))
    v_ads += rng.normal(0, 0.4, p_rel.size)
    fig, axes, _ = huitu.plot_bet((p_rel, v_ads))
    _save(fig, cat, "plot_bet")


# ── 2. electrochem ──────────────────────────────────────────────────────────

def gen_electrochem() -> None:
    cat = "02_electrochem"
    huitu.use_journal("nature")

    fig, ax = huitu.plot_cv(str(SAMPLE / "cv.txt"))
    _save(fig, cat, "plot_cv")

    fig, ax = huitu.plot_gcd(str(SAMPLE / "gcd.txt"))
    _save(fig, cat, "plot_gcd")

    fig, ax = huitu.plot_cycle(str(SAMPLE / "cycle.txt"))
    _save(fig, cat, "plot_cycle")

    fig, ax = huitu.plot_eis(str(SAMPLE / "eis.txt"))
    _save(fig, cat, "plot_eis")

    fig, ax = huitu.plot_bode(str(SAMPLE / "bode.txt"))
    _save(fig, cat, "plot_bode")

    fig, ax = huitu.plot_tafel(str(SAMPLE / "tafel.txt"))
    _save(fig, cat, "plot_tafel")

    # dQ/dV synthetic 2-cycle ageing
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
    )
    _save(fig, cat, "plot_dqdv")


# ── 3. computational ────────────────────────────────────────────────────────

def gen_computational() -> None:
    cat = "03_computational"
    huitu.use_journal("nature")

    fig, ax = huitu.plot_band(
        str(SAMPLE / "band.txt"),
        k_labels=["Γ", "X", "M", "Γ", "R"],
        k_ticks=[0.0, 0.25, 0.5, 0.75, 1.0],
    )
    _save(fig, cat, "plot_band")

    fig, ax = huitu.plot_dos(str(SAMPLE / "dos.txt"))
    _save(fig, cat, "plot_dos")

    fig, ax = huitu.plot_cohp(str(SAMPLE / "cohp.txt"))
    _save(fig, cat, "plot_cohp")

    # Pourbaix: 5 cleanly-tiled Fe/H₂O regions
    regions = [
        {"label": "Fe³⁺(aq)", "color": "#F6CFCB",
         "vertices": [(0, 2.0), (4.5, 2.0), (4.5, 0.77), (0, 0.77)]},
        {"label": "Fe²⁺(aq)", "color": "#B4C0E4",
         "vertices": [(0, 0.77), (4.5, 0.77), (4.5, -0.45), (0, -0.45)]},
        {"label": "Fe(s)",    "color": "#CFCECE",
         "vertices": [(0, -0.45), (14, -0.45), (14, -1.0), (0, -1.0)]},
        {"label": "Fe₂O₃(s)", "color": "#0F4D92",
         "vertices": [(4.5, 2.0), (14, 2.0), (14, 0.0), (8.5, 0.0), (4.5, 0.77)]},
        {"label": "Fe(OH)₂(s)", "color": "#E9A6A1",
         "vertices": [(8.5, 0.0), (14, 0.0), (14, -0.45), (4.5, -0.45), (4.5, 0.77)]},
    ]
    fig, ax = huitu.plot_pourbaix(regions, ph_range=(0, 14), e_range=(-1.0, 2.0))
    _save(fig, cat, "plot_pourbaix")

    # Phase diagram — 4 binary regions + 1 eutectic
    pd_regions = [
        {"label": "L (liquid)", "color": "#B4C0E4",
         "vertices": [(0, 700), (1, 700), (1, 500), (0, 500)]},
        {"label": "L + α", "color": "#F6CFCB",
         "vertices": [(0, 500), (0.4, 500), (0.4, 400), (0, 400)]},
        {"label": "L + β", "color": "#E9A6A1",
         "vertices": [(0.6, 500), (1, 500), (1, 400), (0.6, 400)]},
        {"label": "α + β", "color": "#CFCECE",
         "vertices": [(0, 400), (1, 400), (1, 300), (0, 300)]},
    ]
    fig, ax = huitu.plot_phase_diagram(pd_regions, invariants=[(0.5, 400, "eutectic")])
    _save(fig, cat, "plot_phase_diagram")

    # Crystal — skip if ASE not installed; fall through silently
    try:
        fig, ax = huitu.plot_crystal_ase(str(SAMPLE / "crystal.cif"))
        _save(fig, cat, "plot_crystal_ase")
    except Exception as e:
        print(f"  skipped plot_crystal_ase: {e}")
    try:
        fig, ax = huitu.plot_crystal_vesta(str(SAMPLE / "crystal.cif"))
        _save(fig, cat, "plot_crystal_vesta")
    except Exception as e:
        print(f"  skipped plot_crystal_vesta: {e}")


# ── 4. general ──────────────────────────────────────────────────────────────

def gen_general() -> None:
    cat = "04_general"
    huitu.use_journal("nature")

    fig, ax = huitu.plot_bar(
        str(SAMPLE / "bar.csv"),
        xlabel="Sample", ylabel=r"Capacity (mAh g$^{-1}$)",
    )
    _save(fig, cat, "plot_bar")

    fig, ax = huitu.plot_scatter(
        str(SAMPLE / "scatter.csv"), fit=True,
        xlabel="Predicted (eV)", ylabel="Measured (eV)",
    )
    _save(fig, cat, "plot_scatter")

    fig, ax = huitu.plot_line(
        str(SAMPLE / "line.csv"),
        xlabel="Time (s)", ylabel="Signal (a.u.)",
    )
    _save(fig, cat, "plot_line")

    rng = np.random.default_rng(40)
    Z = rng.normal(0, 1, size=(15, 20))
    fig, ax = huitu.plot_heatmap(
        Z, xlabel="column index", ylabel="row index", cbar_label="value (a.u.)"
    )
    _save(fig, cat, "plot_heatmap")

    fig, ax = huitu.plot_box_violin(
        str(SAMPLE / "boxviolin.csv"), kind="box",
        xlabel="Group", ylabel="Score",
    )
    _save(fig, cat, "plot_box_violin")

    fig, ax = huitu.plot_radar(str(SAMPLE / "radar.csv"))
    _save(fig, cat, "plot_radar")

    x = rng.normal(0, 1, 600)
    y = x * 0.5 + rng.normal(0, 0.8, 600)
    fig, ax = huitu.plot_density(
        x, y, xlabel="Feature 1", ylabel="Feature 2"
    )
    _save(fig, cat, "plot_density")

    shap_vals = rng.normal(0, 1, size=(40, 7))
    feature_names = ["feat_A", "feat_B", "feat_C", "feat_D", "feat_E", "feat_F", "feat_G"]
    fig, ax = huitu.plot_shap(shap_vals, feature_names)
    _save(fig, cat, "plot_shap")


# ── 5. advanced (statistical / comparison) ──────────────────────────────────

def gen_advanced() -> None:
    cat = "05_advanced"
    huitu.use_journal("nature")
    rng = np.random.default_rng(5)

    fig, ax = huitu.plot_ridgeline(
        [rng.normal(m, s, 600) for m, s in zip(np.linspace(0.4, 0.9, 5),
                                                 np.linspace(0.06, 0.03, 5))],
        labels=[f"sample {i+1}" for i in range(5)],
        xlabel="Score",
    )
    _save(fig, cat, "plot_ridgeline")

    fig, ax = huitu.plot_dumbbell(
        categories=["A", "B", "C", "D", "E"],
        start=[0.62, 0.71, 0.80, 0.74, 0.68],
        end=[0.78, 0.82, 0.88, 0.83, 0.77],
        xlabel="Accuracy",
    )
    _save(fig, cat, "plot_dumbbell")

    fig, ax = huitu.plot_slope(
        {"A": [0.62, 0.78], "B": [0.71, 0.82], "C": [0.80, 0.88],
         "D": [0.74, 0.83], "E": [0.68, 0.77]},
        x_labels=["before", "after"],
        ylabel="Accuracy",
    )
    _save(fig, cat, "plot_slope")

    bump_data = {
        "operando XRD":   [120, 145, 178, 220, 280],
        "in-situ EIS":    [ 90,  92, 100, 110, 118],
        "ML potentials":  [ 20,  35,  72, 130, 220],
        "DFT+U":          [115, 130, 152, 172, 190],
    }
    fig, ax = huitu.plot_bump(bump_data, x_labels=["2021","2022","2023","2024","2025"])
    _save(fig, cat, "plot_bump")

    parallel_df = pd.DataFrame(
        rng.uniform(0, 1, size=(20, 5)),
        columns=["acc", "f1", "prec", "recall", "auc"],
    )
    fig, ax = huitu.plot_parallel(parallel_df)
    _save(fig, cat, "plot_parallel")

    fig, ax = huitu.plot_waffle({"A": 40, "B": 30, "C": 20, "D": 10})
    _save(fig, cat, "plot_waffle")

    x_stream = np.arange(12)
    stream_data = {ch: list(rng.uniform(0.5, 1.5, 12)) for ch in ["w","x","y","z"]}
    fig, ax = huitu.plot_streamgraph(
        x_stream, stream_data,
        xlabel="Month", ylabel="Composition (a.u.)",
    )
    _save(fig, cat, "plot_streamgraph")

    t = np.linspace(0, 2 * np.pi, 30)
    fig, ax = huitu.plot_connected_scatter(
        x=np.cos(t) + rng.normal(0, 0.05, 30),
        y=np.sin(t) + rng.normal(0, 0.05, 30),
        xlabel="PC1", ylabel="PC2",
    )
    _save(fig, cat, "plot_connected_scatter")


# ── 6. operando ─────────────────────────────────────────────────────────────

def _synth_operando(seed: int = 0) -> dict:
    rng = np.random.default_rng(seed)
    two_theta = np.linspace(20.0, 35.0, 200)
    time = np.linspace(0.0, 12.0, 50)
    peak_pos = 26.0 + 1.8 * (time / time[-1])
    peak_w = 0.18 + 0.12 * (time / time[-1])
    Z = np.zeros((len(time), len(two_theta)))
    for i in range(len(time)):
        bg = 0.18 * np.exp(-((two_theta - 27.5) ** 2) / 25.0)
        peak = peak_w[i] ** 2 / ((two_theta - peak_pos[i]) ** 2 + peak_w[i] ** 2)
        Z[i] = bg + peak + rng.normal(0, 0.012, two_theta.size)
    voltage = 3.0 + 1.3 * (time / time[-1])
    return dict(Z=Z, x=two_theta, y=time, echem=voltage)


def gen_operando() -> None:
    cat = "06_operando"
    huitu.use_journal("nature")
    d = _synth_operando(seed=6)

    fig, ax = huitu.plot_operando_waterfall(d["Z"], x=d["x"], y=d["y"],
                                              stagger=0.4, auto_stagger=True,
                                              xlabel=r"2$\theta$ (°)",
                                              ylabel="time (h)")
    _save(fig, cat, "plot_operando_waterfall")

    fig, axes = huitu.plot_operando_xrd_echem(
        d["Z"], x=d["x"], y=d["y"], echem=d["echem"],
        xlabel=r"2$\theta$ (°)", ylabel="time (h)",
        echem_xlabel="E (V)",
    )
    _save(fig, cat, "plot_operando_xrd_echem")

    fig, ax = huitu.plot_operando_3d_surface(
        d["Z"], x=d["x"], y=d["y"],
        xlabel=r"2$\theta$ (°)", ylabel="time (h)", zlabel="Intensity (a.u.)",
    )
    _save(fig, cat, "plot_operando_3d_surface")

    fig, ax = huitu.plot_operando_diffmap(d["Z"], x=d["x"], y=d["y"], reference=0,
                                             xlabel=r"2$\theta$ (°)", ylabel="time (h)")
    _save(fig, cat, "plot_operando_diffmap")

    # plot_operando_peak_evolution: (y, series, ...) where series is dict of peak tracks.
    fig, ax = huitu.plot_operando_peak_evolution(
        d["y"],
        {"peak A": 26.0 + 1.8 * (d["y"] / d["y"][-1]),
         "peak B": 27.5 + 0.6 * (d["y"] / d["y"][-1])},
        xlabel="time (h)", ylabel=r"2$\theta$ (°)",
    )
    _save(fig, cat, "plot_operando_peak_evolution")

    fig, ax = huitu.plot_operando_contour(d["Z"], x=d["x"], y=d["y"],
                                            xlabel=r"2$\theta$ (°)", ylabel="time (h)")
    _save(fig, cat, "plot_operando_contour")


# ── 7. archetype ────────────────────────────────────────────────────────────

def gen_archetype() -> None:
    cat = "07_archetype"

    fig, ax = huitu.archetype.schematic_led(journal="nature", n_supports=3)
    ax["hero"].text(0.5, 0.5, "hero schematic",
                    transform=ax["hero"].transAxes,
                    ha="center", va="center", fontsize=14)
    ax["hero"].set_xticks([]); ax["hero"].set_yticks([])
    x = np.linspace(0, 10, 50)
    for i, s in enumerate(ax["supports"]):
        s.plot(x, np.sin(x + i * np.pi / 3))
    _save(fig, cat, "archetype_schematic_led")

    fig, grid = huitu.archetype.dark_image_plate(rows=3, cols=4, journal="nature")
    rng = np.random.default_rng(70)
    for row in grid:
        for sub in row:
            sub.imshow(rng.random((20, 20)), cmap="magma")
    _save(fig, cat, "archetype_dark_image_plate")

    fig, ax = huitu.archetype.clinical_triptych(journal="nature")
    rng = np.random.default_rng(71)
    x = np.linspace(0, 10, 30)
    # top row: longitudinal trajectories
    for sub in ax["top"]:
        traj = np.cumsum(rng.normal(0, 0.3, 30))
        sub.plot(x, traj)
    # middle row: forest plot of effects (errorbars + reference line)
    for sub in ax["mid"]:
        y = rng.normal(0, 0.5, 5)
        err = rng.uniform(0.1, 0.3, 5)
        sub.errorbar(np.arange(5), y, yerr=err, fmt="o")
        sub.axvline(0, ls="--", color="gray", lw=0.8)
    # bottom row: compact summary bars
    for sub in ax["bot"]:
        sub.bar(np.arange(4), rng.uniform(0.3, 1.0, 4))
    _save(fig, cat, "archetype_clinical_triptych")

    fig, ax = huitu.archetype.asymmetric_hero(journal="nature")
    for k, sub in ax.items():
        sub.plot(np.linspace(0, 10, 30), np.random.rand(30))
    _save(fig, cat, "archetype_asymmetric_hero")


# ── 8. layout helpers ───────────────────────────────────────────────────────

def gen_layout() -> None:
    cat = "08_layout"
    huitu.use_journal("nature")

    fig, axes = huitu.make_subplots(2, 3)
    for ax_ in axes.flatten():
        ax_.plot(np.linspace(0, 10, 30), np.random.rand(30))
    _save(fig, cat, "make_subplots")

    # add_inset on a single line plot
    fig, ax = plt.subplots(figsize=(5, 4))
    x = np.linspace(0, 20, 200)
    ax.plot(x, np.sin(x) + 0.1 * np.sin(40 * x))
    # Inset bounds intentionally non-abutting (right edge of zoom region in
    # axes-frac ≈ 0.6) so the dashed connectors have visible length.
    ax_inset = huitu.add_inset(ax, xlim=(8, 12), ylim=(-0.5, 0.5),
                                bounds=(0.66, 0.55, 0.32, 0.4))
    _save(fig, cat, "add_inset")

    fig, axes = plt.subplots(1, 3, figsize=(7.5, 2.5))
    for i, ax_ in enumerate(axes):
        ax_.plot(np.linspace(0, 10, 30), np.random.rand(30) * (i + 1))
    huitu.share_axes(list(axes), which="both")
    _save(fig, cat, "share_axes")

    # pdf_report — capture cover + 2 figs by saving the first PDF page as PNG snapshot
    f1, _ = huitu.plot_xrd(str(SAMPLE / "xrd.txt"))
    f2, _ = huitu.plot_cv(str(SAMPLE / "cv.txt"))
    out_pdf = OUT / cat / "pdf_report.pdf"
    out_pdf.parent.mkdir(exist_ok=True)
    huitu.make_pdf_report([f1, f2], save=out_pdf,
                          title="audit report", captions=["Fig 1", "Fig 2"])


def main() -> None:
    cats = [
        ("01_characterization", gen_characterization),
        ("02_electrochem",      gen_electrochem),
        ("03_computational",    gen_computational),
        ("04_general",          gen_general),
        ("05_advanced",         gen_advanced),
        ("06_operando",         gen_operando),
        ("07_archetype",        gen_archetype),
        ("08_layout",           gen_layout),
    ]
    for cat_name, fn in cats:
        print(f"=== {cat_name} ===")
        try:
            fn()
            n = len(list((OUT / cat_name).glob("*.png"))) if (OUT / cat_name).exists() else 0
            print(f"  ✓ {n} figures written")
        except Exception as e:
            print(f"  ✗ {cat_name} failed: {type(e).__name__}: {e}")
    print()
    total = sum(len(list((OUT / c).glob("*.png"))) for c, _ in cats if (OUT / c).exists())
    print(f"total: {total} figures across {len(cats)} categories")


if __name__ == "__main__":
    main()
