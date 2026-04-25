"""Full demo gallery for huitu.pro (VIP features).

Contains ~300 unique scenarios covering:
- Premium palettes (ggsci / MetBrewer / FT)
- Comparison charts (dumbbell / slope / bump)
- Distribution charts (ridgeline)
- Advanced layered charts (parallel / waffle / streamgraph / connected scatter)
- In-situ / operando characterization charts (waterfall / diffmap / contour /
  3D surface / peak evolution / XRD+echem two-panel)

Run with an activated Pro license — either:
    export HUITU_PRO_KEY=HUITU-PRO-DEV-0000000000000
or call huitu.pro.activate("HUITU-PRO-...") at the top of the file.
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import huitu
from huitu import pro
from huitu import (
    use_journal, use_palette, plot_scatter, plot_bar, plot_line, plot_heatmap,
)

pro.activate("HUITU-PRO-DEMO-LICENSE-XYZ-0001")
assert pro.is_active(), "Pro not active"

OUT = Path(__file__).resolve().parent / "output_pro"
OUT.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(2026)
results: list[tuple[int, str, str, str]] = []
_counter = [0]


def save(fig, stem: str):
    """Save each scenario as a journal-grade high-res PNG + vector PDF."""
    import matplotlib as mpl

    png = OUT / f"{stem}.png"
    pdf = OUT / f"{stem}.pdf"
    # Honour the currently active journal preset's savefig.dpi (600 dpi by
    # default, which covers Nature/Science/RSC/ACS/Wiley minimums). Fall back
    # to 600 if the rc is still the sentinel string "figure".
    dpi = mpl.rcParams.get("savefig.dpi", 600)
    if isinstance(dpi, str):
        dpi = 600
    fig.savefig(png, dpi=dpi, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)


def scenario(name: str):
    """Use like @scenario("...") — auto-numbers."""
    _counter[0] += 1
    n = _counter[0]

    def deco(fn):
        print(f"=== [{n:03d}] {name} ===")
        try:
            fn()
            results.append((n, name, "OK", ""))
        except Exception as exc:
            tb = traceback.format_exc(limit=2)
            print(f"  [FAIL {n}] {exc}\n{tb}")
            results.append((n, name, "FAIL", str(exc)))
        return fn

    return deco


# ==================================================================
# Section A — Palette catalogs (3)
# ==================================================================
@scenario("Pro palette catalog — overview")
def _():
    use_journal("default")
    palette_names = pro.list_pro_palettes()
    n = len(palette_names)
    cols = 3
    rows = (n + cols - 1) // cols
    fig_h = rows * 0.7 + 0.8
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 3.2, fig_h),
                              constrained_layout=True)
    axes = np.atleast_2d(axes)
    for idx, name in enumerate(palette_names):
        ax = axes[idx // cols, idx % cols]
        colors = huitu.PALETTES[name]
        for i, c in enumerate(colors):
            ax.add_patch(plt.Rectangle((i, 0), 1, 1, color=c))
        ax.set_xlim(0, len(colors))
        ax.set_ylim(0, 1)
        ax.set_title(name, fontsize=7, loc="left", pad=2)
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
    for idx in range(n, rows * cols):
        axes[idx // cols, idx % cols].axis("off")
    fig.suptitle("huitu.pro — premium palettes (ggsci + MetBrewer + FT)",
                 fontsize=11)
    save(fig, f"{_counter[0]:03d}_pro_palette_catalog")


@scenario("Palette catalog — ggsci subfamily")
def _():
    use_journal("default")
    names = [n for n in pro.list_pro_palettes() if n.startswith("ggsci")]
    rows = len(names)
    fig_h = rows * 0.35 + 0.8
    fig, axes = plt.subplots(rows, 1, figsize=(6.5, fig_h),
                              constrained_layout=True)
    for ax, name in zip(axes, names):
        colors = huitu.PALETTES[name]
        for i, c in enumerate(colors):
            ax.add_patch(plt.Rectangle((i, 0), 1, 1, color=c))
        ax.set_xlim(0, len(colors))
        ax.set_ylim(0, 1)
        ax.set_ylabel(name, rotation=0, ha="right", va="center", fontsize=7)
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
    fig.suptitle("ggsci journal-branded palettes", fontsize=10)
    save(fig, f"{_counter[0]:03d}_pro_palette_ggsci")


@scenario("Palette catalog — MetBrewer subfamily")
def _():
    use_journal("default")
    names = [n for n in pro.list_pro_palettes() if n.startswith("met-")]
    rows = len(names)
    fig_h = rows * 0.35 + 0.8
    fig, axes = plt.subplots(rows, 1, figsize=(6.5, fig_h),
                              constrained_layout=True)
    for ax, name in zip(axes, names):
        colors = huitu.PALETTES[name]
        for i, c in enumerate(colors):
            ax.add_patch(plt.Rectangle((i, 0), 1, 1, color=c))
        ax.set_xlim(0, len(colors))
        ax.set_ylim(0, 1)
        ax.set_ylabel(name, rotation=0, ha="right", va="center", fontsize=7)
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
    fig.suptitle("MetBrewer art-inspired palettes", fontsize=10)
    save(fig, f"{_counter[0]:03d}_pro_palette_metbrewer")


# ==================================================================
# Section B — Ridgeline variants (40)
# Each palette × 1 scenario with varied data stories
# ==================================================================
RIDGE_PALETTES = [
    "met-hiroshige", "met-hokusai1", "met-hokusai3", "met-cassatt2",
    "met-isfahan1", "met-vangogh3", "met-johnson", "met-derain",
    "met-egypt", "met-archambault", "met-juarez", "met-renoir",
    "met-monet", "met-okeeffe2", "met-redon", "met-tam", "met-tara",
    "met-manet", "met-klimt", "met-kandinsky",
    "ggsci-npg", "ggsci-aaas", "ggsci-nejm", "ggsci-lancet", "ggsci-jama",
    "ggsci-bmj", "ggsci-jco", "ggsci-d3", "ggsci-observable10",
    "ggsci-frontiers", "ggsci-uchicago", "ggsci-simpsons", "ggsci-futurama",
    "ggsci-tron", "ggsci-startrek",
    "ft-categorical", "ft-sequential", "ft-diverging", "ft-night",
]

RIDGE_STORIES = [
    ("bandgap distribution / material class", "Bandgap (eV)",
     lambda k: [rng.normal(1.0 + 0.35 * i, 0.35 + 0.02 * i, 260) for i in range(k)],
     ["oxides", "sulfides", "nitrides", "halides", "phosphides",
      "perovskites", "2D mats", "MOFs", "spinels", "fluorides"]),
    ("particle size by batch", "Particle size (nm)",
     lambda k: [rng.gamma(2.0 + 0.3 * i, 1.2, 220) for i in range(k)],
     [f"batch {i+1}" for i in range(10)]),
    ("intensity evolution by sample", "Intensity (a.u.)",
     lambda k: [rng.normal(20 + 4 * i, 2.5 + 0.2 * i, 200) for i in range(k)],
     [f"sample {c}" for c in "ABCDEFGHIJ"]),
    ("dose response curve", "Yield (mmol)",
     lambda k: [rng.normal(5 - 0.25 * i, 0.7 + 0.05 * i, 200) for i in range(k)],
     [f"dose {d}%" for d in (0, 1, 2, 5, 10, 20, 50, 80, 100, 120)]),
    ("pore size distribution", "Pore size (nm)",
     lambda k: [np.concatenate([rng.normal(1.8, 0.3, 120),
                                 rng.normal(3.5 + 0.1 * i, 0.35, 100)])
                for i in range(k)],
     [f"sample {c}" for c in "ABCDEFGHIJ"]),
    ("temperature annealing sweep", "Lattice parameter (Å)",
     lambda k: [rng.normal(3.9 + 0.005 * i, 0.12, 240) for i in range(k)],
     [f"T={100 + 100*i} K" for i in range(10)]),
    ("depth-profiling O 1s BE", "O 1s BE (eV)",
     lambda k: [rng.normal(531 + 0.1 * i, 0.4, 200) for i in range(k)],
     [f"depth {5 * 2**i} nm" for i in range(10)]),
    ("magnetization by phase", "Magnetization (emu/g)",
     lambda k: [rng.normal(i * 1.1, 0.5 + 0.05 * i, 230) for i in range(k)],
     [f"phase {c}" for c in "αβγδεζηθικ"]),
    ("TOF by catalyst class", r"TOF (s$^{-1}$)",
     lambda k: [rng.gamma(1.5 + 0.2 * i, 20 + 5 * i, 200) for i in range(k)],
     [f"cat-{i+1}" for i in range(10)]),
    ("hardness by alloy batch", "Hardness (HV)",
     lambda k: [rng.normal(300 + 20 * i, 35, 220) for i in range(k)],
     [f"alloy {i+1}" for i in range(10)]),
]

for _i, pal in enumerate(RIDGE_PALETTES[:40]):
    _story = RIDGE_STORIES[_i % len(RIDGE_STORIES)]
    _n_rows = 5 + (_i % 6)  # 5..10 rows per scenario
    _overlap = 0.3 + 0.07 * (_i % 8)
    _title, _xlab, _gen, _lab_template = _story

    def make(pal=pal, n_rows=_n_rows, overlap=_overlap,
              title=_title, xlab=_xlab, gen=_gen, labels_tmpl=_lab_template):
        @scenario(f"Ridgeline / {pal} / {title}")
        def _():
            use_journal("default")
            labels = labels_tmpl[:n_rows]
            dists = gen(n_rows)
            fig, _ax = pro.plot_ridgeline(
                dists, labels=labels, palette=pal,
                overlap=overlap, xlabel=xlab,
            )
            save(fig, f"{_counter[0]:03d}_ridgeline_{pal.replace('-', '_')}")

    make()


# ==================================================================
# Section C — Dumbbell variants (25)
# ==================================================================
DUMBBELL_STORIES = [
    ("capacity retention", r"Capacity (mA h g$^{-1}$)",
     ["NMC622", "NMC811", "LFP", "LCO", "NCA", "LMO", "LNMO", "Li-S", "Na-ion", "SSB"],
     (140, 220), (0.55, 0.95)),
    ("bandgap shift by doping", "Bandgap (eV)",
     [r"TiO$_2$:" + el for el in
      ["Fe", "Co", "Ni", "Cu", "Cr", "V", "Mn", "N", "S", "C"]],
     (3.15, 3.25), (0.6, 0.95)),
    ("OER overpotential", r"OER $\eta$ @10 mA cm$^{-2}$ (mV)",
     [r"IrO$_2$", r"RuO$_2$", "NiFe-LDH", r"CoFe$_2$O$_4$", r"Co$_3$O$_4$",
      "CoP", "FeOOH", "NiOOH", r"Mn$_3$O$_4$", "Ni-N-C"],
     (380, 520), (0.55, 0.9)),
    ("PV module price drop", "Module price ($/W)",
     ["mono-Si", "multi-Si", "CdTe", "CIGS", "a-Si",
      "perovskite", "tandem", "DSC", "organic", "GaAs"],
     (0.5, 1.6), (0.25, 0.7)),
    ("thermal conductivity boost", r"$\kappa$ (W/m K)",
     [f"sample {i+1}" for i in range(10)],
     (2, 8), (1.3, 3.5)),
    ("stress improvement", "UTS (MPa)",
     [f"alloy-{i+1}" for i in range(10)],
     (400, 800), (1.05, 1.8)),
    ("HER activity jump", r"$\eta$ HER (mV)",
     ["Pt", "Pd", "Ru", r"MoS$_2$", "CoP", r"Ni$_2$P", "NiSe", "FeS", "CoSe", "Cu"],
     (60, 250), (0.3, 0.7)),
    ("CO2RR FE", r"CO$_2$RR FE (%)",
     ["Au", "Ag", "Cu", "Sn", "Bi", "In", "Pb", "Zn", "Pd", "Fe"],
     (20, 60), (1.1, 1.8)),
    ("ionic conductivity improvement", r"$\sigma$ (mS/cm)",
     [f"membrane-{i+1}" for i in range(10)],
     (1, 5), (1.2, 3.0)),
    ("photocurrent boost", r"J$_{ph}$ (mA cm$^{-2}$)",
     [f"device-{c}" for c in "ABCDEFGHIJ"],
     (8, 22), (1.1, 1.9)),
    ("stability retention 24h", "Stability (%)",
     [f"sample {i+1}" for i in range(10)], (75, 98), (0.8, 1.05)),
    ("surface area increase", r"BET (m$^2$/g)",
     [f"cat-{i+1}" for i in range(10)], (200, 900), (1.2, 2.6)),
    ("coercivity drop", r"H$_c$ (Oe)",
     [f"film-{c}" for c in "ABCDEFGHIJ"], (400, 1500), (0.35, 0.8)),
    ("Tc enhancement SC", "T$_c$ (K)",
     [f"SC-{i+1}" for i in range(10)], (10, 60), (1.05, 2.1)),
    ("thermopower change", r"S ($\mu$V/K)",
     [f"TE-{i+1}" for i in range(10)], (50, 250), (0.7, 1.4)),
    ("refractive index shift", "n @ 550 nm",
     [f"glass-{c}" for c in "ABCDEFGHIJ"], (1.45, 1.95), (0.95, 1.06)),
    ("sintering density gain", r"$\rho$ (g/cc)",
     [f"ceramic-{i+1}" for i in range(10)], (3.0, 5.5), (1.02, 1.18)),
    ("ZT increase", "ZT",
     [f"mat-{i+1}" for i in range(10)], (0.3, 1.1), (1.1, 2.2)),
    ("corrosion rate drop", "CR (mpy)",
     [f"coating-{i+1}" for i in range(10)], (2, 20), (0.1, 0.5)),
    ("photoluminescence QY", "PLQY (%)",
     [f"QD-{i+1}" for i in range(10)], (20, 60), (1.2, 1.8)),
    ("dielectric drop frequency", r"$\epsilon_r$",
     [f"diel-{c}" for c in "ABCDEFGHIJ"], (3, 12), (0.6, 0.95)),
    ("magnetic moment", r"$\mu$ ($\mu_B$)",
     [f"MM-{i+1}" for i in range(10)], (1, 4), (0.85, 1.15)),
    ("graphene sheet resistance", r"R$_s$ ($\Omega$/sq)",
     [f"sheet-{i+1}" for i in range(10)], (100, 500), (0.3, 0.7)),
    ("catalyst TOF by temperature", r"TOF (s$^{-1}$)",
     [f"cat-{c}" for c in "ABCDEFGHIJ"], (10, 60), (1.5, 4.0)),
    ("specific capacitance drop", "C$_s$ (F/g)",
     [f"EDLC-{i+1}" for i in range(10)], (150, 400), (0.5, 0.85)),
]

_DB_PALS = [
    ("#0072B5", "#BC3C29"), ("#374E55", "#DF8F44"), ("#7E6148", "#00A087"),
    ("#5F559B", "#FDAF91"), ("#0F7BA2", "#DD5129"), ("#2A6EBB", "#F0AB00"),
    ("#164194", "#D51317"), ("#17154F", "#E69B00"), ("#225E92", "#D29C44"),
    ("#3B4992", "#EE0000"), ("#00468B", "#ED0000"), ("#2D223C", "#DEC5DA"),
    ("#1F4287", "#CC0000"),
]

for _j, (title, xlab, cats, s_range, e_mult) in enumerate(DUMBBELL_STORIES):
    sc, ec = _DB_PALS[_j % len(_DB_PALS)]
    sort_by = ("delta", "start", "end", None)[_j % 4]

    def make(title=title, xlab=xlab, cats=cats, s_range=s_range, e_mult=e_mult,
              sc=sc, ec=ec, sort_by=sort_by):
        @scenario(f"Dumbbell / {title}")
        def _():
            use_journal("default")
            s = rng.uniform(*s_range, size=len(cats))
            e = s * rng.uniform(*e_mult, size=len(cats))
            fig, _ax = pro.plot_dumbbell(
                cats, s, e, start_label="before", end_label="after",
                start_color=sc, end_color=ec, xlabel=xlab, sort_by=sort_by,
            )
            safe = title.replace(" ", "_").replace("/", "_")[:30]
            save(fig, f"{_counter[0]:03d}_dumbbell_{safe}")

    make()


# ==================================================================
# Section D — Slope variants (20)
# ==================================================================
SLOPE_STORIES = [
    ("catalyst TOF 2 time points", ["pristine", "after 5 h"], r"TOF (s$^{-1}$)",
     ["Pt/C", "Pd/C", r"Ru/CeO$_2$", "Ni-Fe LDH", "CoP", r"MoS$_2$", "Fe-N-C"],
     (20, 250)),
    ("yield baseline→optimized", ["baseline", "optimized"], "Yield (%)",
     [f"cand {i+1}" for i in range(8)], (30, 95)),
    ("TOF 3 time points", ["0 h", "12 h", "24 h"], "Efficiency (%)",
     ["baseline", "Mg doped", "Al doped", "Sr doped", "Zr doped"], (45, 90)),
    ("hardness annealing", ["as-cast", "annealed"], "Hardness (HV)",
     [f"alloy-{i+1}" for i in range(6)], (200, 550)),
    ("EV sales by region 4Q", ["Q1", "Q2", "Q3", "Q4"], "EV sales (k)",
     ["Asia", "Europe", "NA", "SA", "Africa"], (40, 700)),
    ("membrane degradation", ["0 h", "20 h", "50 h", "100 h"],
     "Remaining conductivity (%)",
     [f"membrane-{c}" for c in "ABCDE"], (20, 100)),
    ("thermal cycling retention", ["0x", "100x", "500x", "1000x"], "Retention (%)",
     [f"cathode-{c}" for c in "ABCDEF"], (60, 100)),
    ("ionic mobility", ["100 K", "200 K", "300 K"], r"$\sigma$ (mS/cm)",
     [f"electrolyte-{i+1}" for i in range(6)], (0.1, 10)),
    ("doping level effect", ["0%", "1%", "5%", "10%"], "PLQY (%)",
     [f"QD-{c}" for c in "ABCDEF"], (20, 85)),
    ("annealing temperature", ["300 K", "500 K", "700 K", "900 K"],
     "Grain size (nm)",
     [f"film-{i+1}" for i in range(5)], (10, 300)),
    ("pressure sweep", ["0.1 MPa", "1 MPa", "10 MPa"], "Selectivity (%)",
     [f"cat-{c}" for c in "ABCDE"], (20, 90)),
    ("pH effect on activity", ["pH 1", "pH 7", "pH 13"], r"j (mA cm$^{-2}$)",
     [f"catalyst-{i+1}" for i in range(7)], (1, 50)),
    ("quarterly revenue", ["Q1", "Q2", "Q3", "Q4"], "Revenue (M$)",
     ["solar", "wind", "storage", "H2", "EV"], (50, 500)),
    ("citation lifecycle", ["y1", "y2", "y3", "y4", "y5"], "Citations",
     [f"paper-{i+1}" for i in range(6)], (5, 200)),
    ("laser intensity sweep", ["1 mW", "10 mW", "100 mW"], "PL (cps)",
     [f"sample-{c}" for c in "ABCDEF"], (100, 10000)),
    ("charge rate retention", ["0.1C", "1C", "5C", "10C"], "Capacity (%)",
     [f"LIB-{i+1}" for i in range(6)], (40, 100)),
    ("magnetic field sweep", ["0 T", "5 T", "10 T"], r"$\rho$ ($\mu\Omega$cm)",
     [f"sample-{i+1}" for i in range(5)], (1, 100)),
    ("dose irradiation", ["0 Gy", "100 Gy", "500 Gy", "1 kGy"], "Strength (%)",
     [f"polymer-{c}" for c in "ABCDEF"], (30, 100)),
    ("temperature stability", ["25°C", "80°C", "120°C"], "Retention (%)",
     [f"perovskite-{i+1}" for i in range(6)], (30, 100)),
    ("scan rate CV", ["10 mV/s", "50 mV/s", "200 mV/s"], "C$_s$ (F/g)",
     [f"material-{c}" for c in "ABCDEF"], (80, 400)),
]

for _j, (title, xs, ylab, keys, val_range) in enumerate(SLOPE_STORIES):
    pal = ["ggsci-npg", "ggsci-jama", "ggsci-nejm", "ggsci-lancet",
           "ggsci-d3", "met-archambault", "met-juarez", "met-johnson",
           "met-renoir", "met-egypt"][_j % 10]
    hl_idx = rng.choice(len(keys), size=min(2, len(keys)), replace=False)
    hl = [keys[i] for i in hl_idx]

    def make(title=title, xs=xs, ylab=ylab, keys=keys,
              val_range=val_range, pal=pal, hl=hl):
        @scenario(f"Slope / {title}")
        def _():
            use_journal("default")
            data = {}
            for k in keys:
                data[k] = np.sort(rng.uniform(*val_range, size=len(xs)))
                if rng.random() < 0.5:
                    data[k] = data[k][::-1]
            fig, _ax = pro.plot_slope(
                data, x_labels=xs, palette=pal,
                ylabel=ylab, highlight=hl,
            )
            safe = title.replace(" ", "_").replace("/", "_")[:30]
            save(fig, f"{_counter[0]:03d}_slope_{safe}")

    make()


# ==================================================================
# Section E — Bump variants (15)
# ==================================================================
BUMP_STORIES = [
    ("battery $/kWh rank", ["2018", "2020", "2022", "2024", "2026"], False,
     {"LFP": [210, 140, 98, 72, 58], "NMC811": [180, 130, 115, 98, 85],
      "NMC622": [200, 155, 128, 108, 96], "NCA": [195, 148, 122, 105, 92],
      "Na-ion": [300, 230, 170, 105, 75], "Li-S": [350, 280, 210, 160, 120],
      "SSB": [500, 420, 320, 220, 150]}),
    ("paper counts by technique", [str(y) for y in range(2018, 2027)], True,
     {"XRD": [120, 130, 145, 160, 170, 175, 180, 185, 190],
      "XPS": [90, 100, 110, 120, 130, 140, 148, 156, 162],
      "Raman": [70, 85, 100, 115, 130, 148, 165, 178, 190],
      "AFM": [60, 72, 80, 90, 98, 104, 110, 115, 118],
      "TEM": [85, 95, 102, 110, 120, 128, 133, 140, 146],
      "EIS": [40, 55, 70, 82, 95, 108, 125, 138, 150]}),
    ("emissions rankings", ["2010", "2015", "2020", "2025"], True,
     {"Power": [8.1, 9.4, 10.2, 10.5], "Transport": [6.2, 7.1, 7.8, 8.9],
      "Industry": [5.4, 6.2, 7.0, 7.6], "Building": [3.1, 3.4, 3.9, 4.2],
      "Ag": [4.8, 5.0, 5.3, 5.5], "Other": [2.0, 2.3, 2.7, 3.0]}),
    ("method adoption", [str(y) for y in range(2019, 2027)], True,
     {"DFT": [160, 170, 175, 180, 190, 195, 198, 200],
      "MLIP": [12, 28, 55, 95, 150, 210, 260, 310],
      "AIMD": [85, 92, 100, 110, 120, 128, 135, 142],
      "ML-pot": [25, 40, 58, 82, 115, 148, 178, 205],
      "DFT+U": [62, 70, 78, 85, 90, 95, 99, 102]}),
    ("solar module efficiency", ["2010", "2015", "2020", "2025"], True,
     {"mono-Si": [20, 22, 24, 26], "perovskite": [3, 12, 22, 26],
      "tandem": [18, 24, 30, 34], "CdTe": [15, 18, 21, 23],
      "CIGS": [14, 17, 20, 22], "GaAs": [24, 27, 29, 31]}),
    ("research $ allocation", ["2018", "2021", "2024"], True,
     {"ML": [50, 120, 280], "quantum": [30, 60, 100],
      "batteries": [80, 130, 180], "H2": [20, 70, 150],
      "CO2RR": [15, 40, 90], "CCUS": [10, 30, 70],
      "nuclear": [60, 55, 65]}),
    ("method citations", [str(y) for y in range(2016, 2027)], True,
     {f"method-{c}": np.cumsum(rng.uniform(2, 15, 11)) for c in "ABCDEF"}),
    ("country H2 capacity", ["2020", "2022", "2024", "2026"], True,
     {"CN": [2, 4.5, 7, 12], "US": [3, 4, 5, 6], "DE": [1.5, 2.8, 4.2, 5.8],
      "JP": [1, 1.8, 2.5, 3.2], "KR": [0.8, 1.5, 2.3, 3.0],
      "AU": [0.3, 0.9, 2.1, 4.0], "SA": [0.1, 0.7, 2.8, 5.0]}),
    ("tech readiness", [f"TRL{i}" for i in range(1, 10)], True,
     {f"tech-{c}": np.cumsum(rng.uniform(0.1, 1.0, 9)) for c in "ABCDE"}),
    ("car brand market share", ["2018", "2020", "2022", "2024", "2026"], True,
     {"Tesla": [10, 18, 25, 22, 20], "BYD": [4, 9, 17, 24, 28],
      "VW": [5, 6, 8, 10, 11], "GM": [4, 5, 6, 7, 8],
      "Ford": [3, 4, 5, 6, 7], "Hyundai": [2, 3, 5, 7, 9]}),
    ("conductivity ranking by T", [f"{t} K" for t in (100, 200, 300, 400, 500)], True,
     {f"sample-{c}": rng.uniform(1, 10, 5) for c in "ABCDEFG"}),
    ("GPU FLOPS rank", ["2020", "2022", "2024"], True,
     {"A100": [100, 100, 100], "H100": [150, 250, 300],
      "MI250X": [130, 190, 220], "TPUv4": [120, 180, 210],
      "B100": [50, 280, 500]}),
    ("pollutant reduction", ["2000", "2010", "2020"], False,
     {"NOx": [100, 70, 40], "SO2": [120, 60, 25],
      "PM2.5": [80, 65, 40], "CO": [110, 80, 45], "VOC": [90, 70, 50]}),
    ("journal IF rank", ["2018", "2020", "2022", "2024"], True,
     {"Nature": [42, 50, 65, 78], "Science": [41, 48, 56, 72],
      "Nat. Mater.": [38, 44, 47, 51], "JACS": [14, 16, 17, 17],
      "Adv. Mater.": [25, 29, 30, 32]}),
    ("software star count", [f"w{i}" for i in range(1, 13)], True,
     {f"repo-{c}": np.cumsum(rng.uniform(5, 50, 12)) for c in "ABCDEF"}),
]

_BUMP_PALS = ["met-archambault", "met-renoir", "met-manet", "ggsci-simpsons",
              "met-derain", "met-juarez", "met-redon", "met-johnson",
              "ft-categorical", "ggsci-d3", "met-tam", "met-egypt",
              "met-hokusai1", "ggsci-uchicago", "met-klimt"]

for _j, (title, years, higher, data) in enumerate(BUMP_STORIES):
    pal = _BUMP_PALS[_j]

    def make(title=title, years=years, higher=higher, data=data, pal=pal):
        @scenario(f"Bump / {title}")
        def _():
            use_journal("default")
            fig, _ax = pro.plot_bump(data, x_labels=years,
                                      higher_is_better=higher, palette=pal)
            safe = title.replace(" ", "_").replace("/", "_")[:30]
            save(fig, f"{_counter[0]:03d}_bump_{safe}")

    make()


# ==================================================================
# Section F — Parallel coordinates (15)
# ==================================================================
PARALLEL_STORIES = []

def _build_parallel(story_id):
    """Generate diverse DataFrames for parallel coord scenarios."""
    n = 60 + rng.integers(0, 60)
    if story_id == 0:
        return pd.DataFrame({
            "Eads_H (eV)": rng.normal(-0.4, 0.25, n),
            "d-band (eV)": rng.normal(-1.8, 0.4, n),
            "workfn (eV)": rng.normal(4.6, 0.3, n),
            "Ef (eV)": rng.normal(0.0, 0.15, n),
            "overpot (mV)": rng.uniform(40, 400, n),
        }), "overpot (mV)"
    elif story_id == 1:
        classes = rng.choice(["A", "B", "C", "D"], size=n)
        return pd.DataFrame({
            "feature 1": rng.normal(0, 1, n),
            "feature 2": rng.normal(1, 0.8, n) + (classes == "A") * 1.2,
            "feature 3": rng.normal(-1, 0.6, n) - (classes == "B") * 1.0,
            "feature 4": rng.normal(0.5, 1.2, n),
            "feature 5": rng.uniform(0, 1, n),
            "class": classes,
        }), "class"
    elif story_id == 2:
        return pd.DataFrame({
            "Fe (%)": rng.uniform(20, 50, n), "Cr (%)": rng.uniform(10, 30, n),
            "Ni (%)": rng.uniform(5, 25, n), "Mn (%)": rng.uniform(2, 15, n),
            "Al (%)": rng.uniform(0, 10, n),
            "UTS (MPa)": rng.uniform(500, 1200, n),
        }), "UTS (MPa)"
    elif story_id == 3:
        opt = rng.choice(["Adam", "SGD", "AdamW"], n)
        return pd.DataFrame({
            "lr": rng.uniform(1e-4, 1e-2, n),
            "bs": rng.choice([16, 32, 64, 128], n).astype(float),
            "dropout": rng.uniform(0, 0.5, n),
            "weight_decay": rng.uniform(0, 1e-2, n),
            "val_loss": rng.uniform(0.1, 0.9, n), "optimizer": opt,
        }), "optimizer"
    elif story_id == 4:
        return pd.DataFrame({f"x{i+1}": rng.uniform(0, 1, n) for i in range(5)}
                            | {"y": rng.uniform(0, 1, n)}), "y"
    elif story_id == 5:
        cat = rng.choice(["Au", "Pt", "Cu", "Ag"], n)
        return pd.DataFrame({
            "pH": rng.uniform(1, 14, n), "T (K)": rng.uniform(250, 500, n),
            "C (mM)": rng.uniform(0.1, 10, n), "E (V)": rng.uniform(-1, 1, n),
            "scan rate": rng.uniform(5, 200, n),
            "current": rng.uniform(-50, 50, n), "cat": cat,
        }), "cat"
    elif story_id == 6:
        return pd.DataFrame({
            "ΔG_H (eV)": rng.normal(-0.15, 0.3, n),
            "ΔG_O (eV)": rng.normal(1.5, 0.4, n),
            "ΔG_OH (eV)": rng.normal(0.7, 0.3, n),
            "CN": rng.integers(2, 7, n).astype(float),
            "η (V)": rng.uniform(0.2, 0.8, n),
        }), "η (V)"
    elif story_id == 7:
        mat = rng.choice(["oxide", "sulfide", "nitride", "halide"], n)
        return pd.DataFrame({
            "Eg (eV)": rng.uniform(0.5, 5, n),
            "density": rng.uniform(2, 8, n),
            "hardness": rng.uniform(1, 10, n),
            "Tc (K)": rng.uniform(100, 1500, n),
            "class": mat,
        }), "class"
    elif story_id == 8:
        return pd.DataFrame({
            "lattice a (Å)": rng.normal(5, 0.3, n),
            "lattice c (Å)": rng.normal(7, 0.4, n),
            "c/a": rng.normal(1.4, 0.08, n),
            "E coh (eV)": rng.normal(-5, 0.5, n),
            "V cell (Å$^3$)": rng.uniform(100, 400, n),
        }), "E coh (eV)"
    elif story_id == 9:
        return pd.DataFrame({
            "mp ATOM": rng.integers(1, 100, n).astype(float),
            "bonds": rng.integers(1, 8, n).astype(float),
            "n electrons": rng.integers(8, 100, n).astype(float),
            "mass": rng.uniform(50, 600, n),
            "formation energy": rng.normal(-3, 1, n),
        }), "formation energy"
    elif story_id == 10:
        g = rng.choice(["α", "β", "γ"], n)
        return pd.DataFrame({
            "δ": rng.normal(0, 0.2, n),
            "ε": rng.normal(1, 0.3, n),
            "ζ": rng.normal(-0.5, 0.4, n),
            "η": rng.normal(0.7, 0.2, n),
            "θ": rng.uniform(0, 1, n), "phase": g,
        }), "phase"
    elif story_id == 11:
        return pd.DataFrame({
            "Eg": rng.uniform(1, 3, n), "ε∞": rng.uniform(4, 10, n),
            "ε0": rng.uniform(5, 12, n), "m*": rng.uniform(0.1, 1.2, n),
            "μ": rng.uniform(10, 500, n),
        }), "μ"
    elif story_id == 12:
        return pd.DataFrame({
            "pressure": rng.uniform(0, 50, n),
            "temperature": rng.uniform(273, 1500, n),
            "conc 1": rng.uniform(0.1, 10, n),
            "conc 2": rng.uniform(0.1, 10, n),
            "conversion": rng.uniform(0, 1, n),
            "selectivity": rng.uniform(0, 1, n),
        }), "conversion"
    elif story_id == 13:
        tech = rng.choice(["slurry", "tape-cast", "spray", "ALD"], n)
        return pd.DataFrame({
            "thickness (nm)": rng.uniform(10, 1000, n),
            "density (g/cc)": rng.uniform(2, 6, n),
            "porosity": rng.uniform(0, 0.6, n),
            "roughness (nm)": rng.uniform(1, 50, n),
            "adhesion (MPa)": rng.uniform(10, 80, n), "tech": tech,
        }), "tech"
    else:
        return pd.DataFrame({
            "f1": rng.uniform(-3, 3, n), "f2": rng.uniform(-3, 3, n),
            "f3": rng.uniform(-3, 3, n), "f4": rng.uniform(-3, 3, n),
            "f5": rng.uniform(-3, 3, n), "target": rng.uniform(-3, 3, n),
        }), "target"


_PARA_PALS = ["met-hiroshige", "ggsci-nejm", "ft-sequential",
              "ggsci-observable10", "met-cassatt2", "met-klimt",
              "met-archambault", "met-johnson", "met-hokusai3",
              "ggsci-d3", "met-monet", "ggsci-lancet", "ft-diverging",
              "met-tam", "met-isfahan1"]

for _j in range(15):
    df_data, color_by = _build_parallel(_j % 15)
    pal = _PARA_PALS[_j]

    def make(df_data=df_data, color_by=color_by, pal=pal, idx=_j):
        @scenario(f"Parallel / story-{idx+1} / {pal}")
        def _():
            use_journal("default")
            fig, _ax = pro.plot_parallel(df_data, color_by=color_by,
                                          palette=pal, alpha=0.55)
            save(fig, f"{_counter[0]:03d}_parallel_s{idx+1}_{pal.replace('-','_')}")

    make()


# ==================================================================
# Section G — Waffle variants (20)
# ==================================================================
WAFFLE_STORIES = [
    ({"XRD": 28, "XPS": 18, "SEM": 16, "TEM": 14, "Raman": 11, "UV-Vis": 7,
      "FTIR": 6}, 10, 10, "techniques"),
    ({"Li-ion": 65, "Na-ion": 10, "SSB": 8, "Li-S": 6, "flow": 5, "other": 6},
     5, 20, "battery market"),
    ({"female": 38, "male": 58, "non-binary": 4}, 2, 50, "gender"),
    ({"O": 46.6, "Si": 27.7, "Al": 8.1, "Fe": 5.0, "Ca": 3.6, "Na": 2.8,
      "K": 2.6, "Mg": 2.1, "others": 1.5}, 12, 12, "crust"),
    ({"experiments": 35, "writing": 18, "meetings": 12, "reading": 10,
      "coding": 12, "teaching": 8, "admin": 5}, 8, 10, "time use"),
    ({"federal": 55, "industry": 20, "state": 10, "nonprofit": 8,
      "internal": 5, "other": 2}, 10, 10, "funding"),
    ({"Pt": 5, "Pd": 8, "Cu": 35, "Fe": 25, "Ni": 17, "Co": 10},
     10, 10, "metals"),
    ({"DFT": 30, "DFT+U": 18, "HSE": 10, "GW": 7, "AIMD": 20, "MLIP": 15},
     10, 10, "DFT methods"),
    ({"crystalline": 55, "amorphous": 30, "nanocrystalline": 15},
     5, 20, "structure"),
    ({"US": 25, "CN": 35, "EU": 20, "JP": 8, "KR": 7, "other": 5},
     5, 20, "country"),
    ({"PhD": 40, "postdoc": 25, "MSc": 20, "undergrad": 10, "staff": 5},
     10, 10, "lab demographics"),
    ({"review": 30, "primary": 60, "theory": 10}, 10, 10, "paper type"),
    ({"IrO2": 15, "RuO2": 25, "NiFe": 30, "CoFe": 15, "other": 15},
     10, 10, "OER"),
    ({"NCM": 50, "LFP": 30, "LCO": 10, "LMO": 5, "LNMO": 5},
     10, 10, "cathode"),
    ({"Si": 40, "graphite": 35, "Li-metal": 10, "SSB-anode": 8,
      "alloy": 7}, 10, 10, "anode"),
    ({"single-junction": 70, "tandem": 20, "triple-junction": 10},
     5, 20, "junction"),
    ({"fluorescence": 40, "phosphorescence": 25, "TADF": 20, "QD": 15},
     10, 10, "emitter"),
    ({"open-cell": 55, "closed-cell": 30, "mixed-cell": 15},
     5, 20, "foam"),
    ({"XRD": 20, "XRD + EXAFS": 15, "full suite": 25, "none": 40},
     10, 10, "characterization level"),
    ({"carbon": 50, "metal": 20, "oxide": 15, "polymer": 10, "composite": 5},
     10, 10, "support"),
]

_WAF_PALS = ["ggsci-observable10", "ft-categorical", "met-johnson",
             "met-hiroshige", "met-archambault", "met-manet", "ggsci-jama",
             "met-derain", "met-egypt", "ggsci-d3", "met-juarez",
             "met-tam", "ft-night", "ggsci-npg", "met-kandinsky",
             "met-renoir", "ggsci-observable10", "met-tara",
             "met-vangogh3", "ggsci-nejm"]

for _j, (parts, r, c, label) in enumerate(WAFFLE_STORIES):
    pal = _WAF_PALS[_j]

    def make(parts=parts, r=r, c=c, label=label, pal=pal):
        @scenario(f"Waffle / {label} ({r}x{c}) / {pal}")
        def _():
            use_journal("default")
            fig, _ax = pro.plot_waffle(parts, palette=pal, rows=r, cols=c)
            safe = label.replace(" ", "_")[:25]
            save(fig, f"{_counter[0]:03d}_waffle_{safe}")

    make()


# ==================================================================
# Section H — Streamgraph variants (15)
# ==================================================================
STREAM_STORIES = [
    ("publication topics 2015-26", np.arange(2015, 2027), "wiggle",
     {"perovskites": [20, 25, 32, 42, 55, 72, 95, 110, 125, 140, 160, 175],
      "MOFs": [15, 20, 28, 36, 45, 50, 58, 62, 68, 74, 80, 85],
      "2D": [40, 48, 55, 68, 75, 82, 85, 88, 92, 95, 98, 100],
      "SACs": [3, 5, 8, 12, 20, 32, 48, 65, 85, 105, 130, 160],
      "HEAs": [2, 3, 5, 8, 13, 22, 35, 52, 70, 88, 110, 135],
      "nitrides": [8, 10, 11, 12, 14, 15, 18, 20, 22, 25, 28, 30]}),
    ("energy mix", np.linspace(2018, 2026, 40), "sym", None),  # will gen below
    ("citation clusters", np.arange(2010, 2027), "zero", None),
    ("cycle degradation", np.linspace(0, 1000, 100), "wiggle", None),
    ("arXiv categories", np.arange(2015, 2027), "wiggle", None),
    ("8-segment flow", np.arange(1, 25), "sym", None),
    ("12-series stacked", np.arange(25), "wiggle", None),
    ("weekly traffic", np.arange(1, 53), "wiggle", None),
    ("monthly sales", np.arange(1, 25), "zero", None),
    ("3-tier market", np.arange(2010, 2025), "sym", None),
    ("5-topic evolution", np.arange(15), "wiggle", None),
    ("6-pollutant decline", np.arange(2000, 2025), "zero", None),
    ("4-material blend", np.linspace(0, 10, 60), "sym", None),
    ("7-sector growth", np.arange(2000, 2025), "wiggle", None),
    ("8-wavelength mix", np.linspace(400, 700, 50), "sym", None),
]

_ST_PALS = ["met-monet", "met-hiroshige", "ggsci-frontiers", "met-cassatt2",
            "ft-categorical", "met-renoir", "met-juarez", "met-archambault",
            "met-derain", "met-johnson", "ggsci-observable10",
            "met-hokusai1", "ggsci-nejm", "met-tam", "met-egypt"]

for _j, (title, t, base, data) in enumerate(STREAM_STORIES):
    if data is None:
        n_layers = 4 + (_j % 6)
        data = {f"s{i+1}": np.maximum(
            0.1, rng.uniform(3, 9, len(t)) + np.linspace(0, 2 + i / 2, len(t))
            + 0.5 * np.sin(np.linspace(0, 2 * np.pi * (1 + i/3), len(t))))
            for i in range(n_layers)}
    pal = _ST_PALS[_j]

    def make(title=title, t=t, base=base, data=data, pal=pal):
        @scenario(f"Streamgraph / {title} / {pal} / {base}")
        def _():
            use_journal("default")
            fig, ax = pro.plot_streamgraph(t, data, palette=pal, baseline=base)
            ax.set_xlabel("t")
            safe = title.replace(" ", "_")[:25]
            save(fig, f"{_counter[0]:03d}_streamgraph_{safe}")

    make()


# ==================================================================
# Section I — Connected scatter (15)
# ==================================================================
CS_PALS = ["met-hiroshige", "ggsci-npg", "met-isfahan1", "met-tam",
           "met-johnson", "ggsci-jco", "met-cassatt2", "ft-sequential",
           "met-juarez", "ggsci-lancet", "met-klimt", "met-archambault",
           "met-monet", "met-hokusai3", "met-renoir"]

for _j in range(15):
    pal = CS_PALS[_j]

    def make(idx=_j, pal=pal):
        @scenario(f"ConnectedScatter / traj-{idx+1} / {pal}")
        def _():
            use_journal("default")
            kind = idx % 5
            if kind == 0:
                rc = np.linspace(0, 5, 10 + idx % 6)
                en = np.sin(rc * 1.3) + 0.3 * np.cos(rc * 2) - 0.05 * rc
                fig, _ax = pro.plot_connected_scatter(
                    rc, en, palette=pal, xlabel="reaction coord",
                    ylabel="free energy (eV)")
            elif kind == 1:
                xs, ys = [], []
                for off in range(3):
                    v = np.linspace(-0.1, 0.5, 30) + 0.06 * off
                    j = -0.1 * np.exp(12 * (v - 0.25 - 0.04 * off))
                    xs.append(v); ys.append(j)
                fig, _ax = pro.plot_connected_scatter(
                    xs, ys, labels=["cat 1", "cat 2", "cat 3"], palette=pal,
                    xlabel="E (V)", ylabel=r"j (mA cm$^{-2}$)",
                    annotate_first_last=False)
            elif kind == 2:
                n = 15
                T = 300 + 40 * np.sin(np.linspace(0, 3 * np.pi, n)) + np.linspace(0, 150, n)
                P = 1 + 0.5 * np.cos(np.linspace(0, 2 * np.pi, n)) + np.linspace(0, 2, n)
                fig, _ax = pro.plot_connected_scatter(
                    T, P, palette=pal, xlabel="T (K)", ylabel="P (GPa)")
            elif kind == 3:
                theta = np.linspace(0, 2 * np.pi, 60)
                V = np.sin(theta)
                I = 0.7 * np.sin(theta) + 0.3 * np.sin(3 * theta + idx)
                fig, _ax = pro.plot_connected_scatter(
                    V, I, palette=pal, xlabel="E (V)", ylabel="I (mA)")
            else:
                xs, ys = [], []
                for i in range(4):
                    t = np.linspace(0, 1, 18)
                    xs.append(t * (1 + 0.2 * i))
                    ys.append(np.sin(2 * np.pi * t * (1 + 0.3 * i)) + 0.2 * i)
                fig, _ax = pro.plot_connected_scatter(
                    xs, ys, labels=[f"path {i+1}" for i in range(4)],
                    palette=pal, xlabel="t", ylabel="state",
                    annotate_first_last=False)
            save(fig, f"{_counter[0]:03d}_connected_scatter_t{idx+1}_{pal.replace('-','_')}")

    make()


# ==================================================================
# Section J — OPERANDO / IN-SITU characterization plots (50)
# Advanced premium plot types
# ==================================================================
def _synth_operando_xrd(M=60, N=400, drift=0.8, noise=0.05):
    """Synthesize operando XRD data: moving + splitting peaks over time."""
    two_theta = np.linspace(15, 55, N)
    y = np.linspace(0, 1, M)
    Z = np.zeros((M, N))
    for m in range(M):
        t = y[m]
        # Two main peaks that split and shift over time
        p1 = 25 + drift * t
        p2 = 38 - drift * t * 1.2
        w = 0.25 + 0.1 * t
        Z[m] += np.exp(-0.5 * ((two_theta - p1) / w) ** 2) * (1 - 0.3 * t)
        Z[m] += 0.75 * np.exp(-0.5 * ((two_theta - p2) / w) ** 2) * (0.5 + 0.5 * t)
        # New phase emerging
        Z[m] += 0.6 * t * np.exp(-0.5 * ((two_theta - 32) / 0.4) ** 2)
        # Weak background peaks
        Z[m] += 0.25 * np.exp(-0.5 * ((two_theta - 45) / 0.3) ** 2)
    Z += rng.normal(0, noise, Z.shape)
    Z = np.maximum(Z, 0)
    return two_theta, y, Z


def _synth_operando_raman(M=40, N=300, noise=0.04):
    wn = np.linspace(200, 1800, N)
    y = np.linspace(0, 1, M)
    Z = np.zeros((M, N))
    for m in range(M):
        t = y[m]
        for p, amp, w in [(520, 1.0 - 0.4 * t, 8),
                          (950, 0.4 + 0.5 * t, 12),
                          (1350, 0.3 * t, 15),
                          (1580, 0.4 + 0.3 * np.sin(t * np.pi), 10)]:
            Z[m] += amp * np.exp(-0.5 * ((wn - p) / w) ** 2)
    Z += rng.normal(0, noise, Z.shape)
    Z = np.maximum(Z, 0)
    return wn, y, Z


def _synth_operando_xas(M=30, N=200, noise=0.02):
    energy = np.linspace(7100, 7180, N)
    y = np.linspace(0, 1, M)
    Z = np.zeros((M, N))
    for m in range(M):
        t = y[m]
        edge = 7118 + 4 * t  # shifting edge
        Z[m] = 1 / (1 + np.exp(-(energy - edge) / 2))
        # Whiteline peak
        Z[m] += (0.4 - 0.3 * t) * np.exp(-0.5 * ((energy - (edge + 2)) / 1.5) ** 2)
        # EXAFS oscillations
        Z[m] += 0.05 * np.sin(0.5 * (energy - edge)) * np.exp(-(energy - edge) / 40)
    Z += rng.normal(0, noise, Z.shape)
    return energy, y, Z


def _galvanostatic(M=60):
    """Voltage vs time during charge/discharge cycle."""
    y = np.linspace(0, 1, M)
    v = 4.2 - 1.1 * y + 0.12 * np.exp(-((y - 0.45) / 0.15) ** 2)
    return v


def _cv_curve(M=40):
    theta = np.linspace(0, 2 * np.pi, M)
    return 0.3 * np.sin(theta) + 0.05 * np.sin(5 * theta)


# 50 operando scenarios split across 6 plot types + palettes + techniques
OP_PALS_GRAD = ["met-hiroshige", "met-hokusai3", "met-isfahan1",
                "met-vangogh3", "met-cassatt2", "met-okeeffe2", "met-tam",
                "ft-sequential"]
OP_PALS_DIV = ["ft-diverging"]

# J1 — Operando waterfall (10 scenarios)
WATERFALL_STORIES = [
    ("XRD charge", "xrd", "2$\\theta$ (°)", "time (s)"),
    ("XRD discharge", "xrd", "2$\\theta$ (°)", "time (s)"),
    ("Raman Li intercalation", "raman", r"Raman shift (cm$^{-1}$)", "time (min)"),
    ("Raman SEI formation", "raman", r"Raman shift (cm$^{-1}$)", "time (h)"),
    ("XAS Ni K-edge", "xas", "Energy (eV)", "time (min)"),
    ("XAS Fe K-edge", "xas", "Energy (eV)", "potential (V)"),
    ("XRD vs temperature", "xrd", "2$\\theta$ (°)", "Temperature (K)"),
    ("Raman vs potential", "raman", r"Raman shift (cm$^{-1}$)", "E (V vs RHE)"),
    ("XAS vs SoC", "xas", "Energy (eV)", "SoC (%)"),
    ("XRD vs cycling", "xrd", "2$\\theta$ (°)", "cycle #"),
]

for _j, (title, kind, xlab, ylab) in enumerate(WATERFALL_STORIES):
    pal = OP_PALS_GRAD[_j % len(OP_PALS_GRAD)]
    stagger = 0.08 + 0.02 * (_j % 5)

    def make(title=title, kind=kind, xlab=xlab, ylab=ylab, pal=pal,
             stagger=stagger):
        @scenario(f"Operando-waterfall / {title} / {pal}")
        def _():
            use_journal("default")
            if kind == "xrd":
                x, y, Z = _synth_operando_xrd(M=40)
            elif kind == "raman":
                x, y, Z = _synth_operando_raman(M=35)
            else:
                x, y, Z = _synth_operando_xas(M=30)
            fig, _ax = pro.plot_operando_waterfall(
                Z, x=x, y=y, cmap=pal, stagger=stagger, fill=True,
                xlabel=xlab, cbar_label=ylab, every=1,
            )
            safe = title.replace(" ", "_")[:25]
            save(fig, f"{_counter[0]:03d}_op_waterfall_{safe}")

    make()


# J2 — Operando heatmap (via plot_operando) (10 scenarios)
HEATMAP_STORIES = [
    ("XRD Li insertion", "xrd", "2$\\theta$ (°)", "time (s)", False),
    ("XRD Na intercalation", "xrd", "2$\\theta$ (°)", "time (s)", False),
    ("Raman SEI evolution", "raman", r"Raman (cm$^{-1}$)", "time (h)", False),
    ("XAS oxidation state", "xas", "E (eV)", "time (min)", False),
    ("XRD during ORR", "xrd", "2$\\theta$ (°)", "E (V)", False),
    ("Raman HER", "raman", r"Raman (cm$^{-1}$)", "E (V)", False),
    ("XAS log-colorbar", "xas", "E (eV)", "SoC (%)", True),
    ("XRD sintering", "xrd", "2$\\theta$ (°)", "T (°C)", False),
    ("Raman phase transition", "raman", r"Raman (cm$^{-1}$)", "T (K)", False),
    ("XAS vs SoC zoom", "xas", "E (eV)", "SoC (%)", False),
]
HEATMAP_CMAPS = ["crameri-batlow", "crameri-roma", "met-hiroshige",
                 "met-hokusai3", "ft-sequential", "met-tam",
                 "crameri-batlow", "met-okeeffe2", "ft-diverging",
                 "met-cassatt2"]

for _j, (title, kind, xlab, ylab, logz) in enumerate(HEATMAP_STORIES):
    cmap = HEATMAP_CMAPS[_j]

    def make(title=title, kind=kind, xlab=xlab, ylab=ylab, logz=logz, cmap=cmap):
        @scenario(f"Operando-heatmap / {title} / {cmap}")
        def _():
            use_journal("default")
            if kind == "xrd":
                x, y, Z = _synth_operando_xrd()
            elif kind == "raman":
                x, y, Z = _synth_operando_raman()
            else:
                x, y, Z = _synth_operando_xas()
            fig, _ax = huitu.plot_operando(
                Z, x=x, y=y, cmap=cmap, log_z=logz,
                xlabel=xlab, ylabel=ylab, cbar_label="Intensity",
            )
            safe = title.replace(" ", "_")[:25]
            save(fig, f"{_counter[0]:03d}_op_heatmap_{safe}")

    make()


# J3 — Operando XRD+echem two-panel (8 scenarios)
XRDEC_STORIES = [
    ("XRD+galvanostatic cycle 1", "xrd", "galv", "2$\\theta$ (°)", "time (s)", "E (V)"),
    ("XRD+cycle 5", "xrd", "galv", "2$\\theta$ (°)", "time (s)", "E (V)"),
    ("XRD+CV", "xrd", "cv", "2$\\theta$ (°)", "scan #", "I (mA)"),
    ("Raman+galv", "raman", "galv", r"Raman (cm$^{-1}$)", "time (min)", "E (V)"),
    ("Raman+CV", "raman", "cv", r"Raman (cm$^{-1}$)", "scan #", "I (mA)"),
    ("XAS+galv", "xas", "galv", "E (eV)", "time (min)", "E (V)"),
    ("XAS+CV", "xas", "cv", "E (eV)", "scan #", "I (mA)"),
    ("XRD+discharge", "xrd", "galv", "2$\\theta$ (°)", "time (s)", "E (V)"),
]
XRDEC_CMAPS = ["crameri-batlow", "met-hiroshige", "met-tam",
                "ft-sequential", "met-hokusai3", "met-isfahan1",
                "met-cassatt2", "met-okeeffe2"]

for _j, (title, kind, ec_kind, xlab, ylab, ec_lab) in enumerate(XRDEC_STORIES):
    cmap = XRDEC_CMAPS[_j]

    def make(title=title, kind=kind, ec_kind=ec_kind, xlab=xlab, ylab=ylab,
             ec_lab=ec_lab, cmap=cmap):
        @scenario(f"Operando-XRD+echem / {title} / {cmap}")
        def _():
            use_journal("default")
            if kind == "xrd":
                x, y, Z = _synth_operando_xrd(M=40)
            elif kind == "raman":
                x, y, Z = _synth_operando_raman(M=40)
            else:
                x, y, Z = _synth_operando_xas(M=40)
            M = Z.shape[0]
            ec = _galvanostatic(M) if ec_kind == "galv" else _cv_curve(M)
            fig, _axs = pro.plot_operando_xrd_echem(
                Z, x=x, y=y, echem=ec, cmap=cmap,
                xlabel=xlab, ylabel=ylab, echem_xlabel=ec_lab,
            )
            safe = title.replace(" ", "_").replace("+", "_")[:25]
            save(fig, f"{_counter[0]:03d}_op_xrdec_{safe}")

    make()


# J4 — Operando 3-D surface (6 scenarios)
SURF_STORIES = [
    ("XRD 3D early", "xrd", 30, -60),
    ("XRD 3D mid", "xrd", 40, -45),
    ("XRD 3D side", "xrd", 20, -80),
    ("Raman 3D", "raman", 35, -55),
    ("XAS 3D", "xas", 30, -65),
    ("XRD 3D high elevation", "xrd", 60, -50),
]
SURF_CMAPS = ["crameri-batlow", "met-hiroshige", "met-tam",
               "ft-sequential", "met-okeeffe2", "met-isfahan1"]

for _j, (title, kind, elev, azim) in enumerate(SURF_STORIES):
    cmap = SURF_CMAPS[_j]

    def make(title=title, kind=kind, elev=elev, azim=azim, cmap=cmap):
        @scenario(f"Operando-3D / {title} / {cmap}")
        def _():
            use_journal("default")
            if kind == "xrd":
                x, y, Z = _synth_operando_xrd(M=25, N=200)
            elif kind == "raman":
                x, y, Z = _synth_operando_raman(M=25, N=200)
            else:
                x, y, Z = _synth_operando_xas(M=25, N=150)
            fig, _ax = pro.plot_operando_3d_surface(
                Z, x=x, y=y, cmap=cmap, elev=elev, azim=azim,
                xlabel="spectral", ylabel="perturbation",
            )
            safe = title.replace(" ", "_")[:25]
            save(fig, f"{_counter[0]:03d}_op_3d_{safe}")

    make()


# J5 — Operando diffmap (8 scenarios)
DIFF_STORIES = [
    ("XRD Δ-intensity vs pristine", "xrd", "2$\\theta$ (°)", "time (s)"),
    ("XRD Δ vs mid-discharge", "xrd", "2$\\theta$ (°)", "time (s)"),
    ("Raman Δ intercalation", "raman", r"Raman (cm$^{-1}$)", "SoC (%)"),
    ("Raman Δ fully charged ref", "raman", r"Raman (cm$^{-1}$)", "SoC (%)"),
    ("XAS Δ initial state", "xas", "E (eV)", "t (min)"),
    ("XAS Δ half-cycle", "xas", "E (eV)", "t (min)"),
    ("XRD Δ thermal expansion", "xrd", "2$\\theta$ (°)", "T (K)"),
    ("Raman Δ oxidation peak", "raman", r"Raman (cm$^{-1}$)", "E (V)"),
]
DIFF_REFS = [0, "mid", 0, "last", 0, "mid", 0, 0]

for _j, (title, kind, xlab, ylab) in enumerate(DIFF_STORIES):
    ref = DIFF_REFS[_j]

    def make(title=title, kind=kind, xlab=xlab, ylab=ylab, ref=ref):
        @scenario(f"Operando-diffmap / {title}")
        def _():
            use_journal("default")
            if kind == "xrd":
                x, y, Z = _synth_operando_xrd()
            elif kind == "raman":
                x, y, Z = _synth_operando_raman()
            else:
                x, y, Z = _synth_operando_xas()
            M = Z.shape[0]
            if ref == "mid":
                use_ref = M // 2
            elif ref == "last":
                use_ref = M - 1
            else:
                use_ref = 0
            fig, _ax = pro.plot_operando_diffmap(
                Z, x=x, y=y, reference=use_ref,
                cmap="ft-diverging", xlabel=xlab, ylabel=ylab,
            )
            safe = title.replace(" ", "_").replace("Δ", "d")[:25]
            save(fig, f"{_counter[0]:03d}_op_diff_{safe}")

    make()


# J6 — Operando peak evolution (8 scenarios)
PEAK_STORIES = [
    ("peak positions XRD", "y (time, s)",
     ["(200) 2θ", "(220) 2θ", "(311) 2θ"]),
    ("FWHM evolution XRD", "y (time, s)",
     ["(200) FWHM", "(220) FWHM", "(311) FWHM"]),
    ("peak area Raman", "potential (V)",
     ["E2g area", "A1g area", "D-band area", "G-band area"]),
    ("Ni K-edge position", "SoC (%)", ["edge E (eV)", "whiteline E (eV)"]),
    ("bandgap shift", "T (K)", ["Eg direct", "Eg indirect"]),
    ("lattice param a", "pressure (GPa)", ["a (Å)", "c (Å)"]),
    ("integrated intensity", "time (h)",
     ["(001) area", "(002) area", "(003) area", "(004) area"]),
    ("phase fraction", "cycle #", ["α-phase", "β-phase", "γ-phase"]),
]
PEAK_PALS = ["ggsci-npg", "ggsci-nejm", "ggsci-jama", "ggsci-lancet",
              "met-archambault", "met-johnson", "ft-categorical", "met-juarez"]

for _j, (title, xlab, names) in enumerate(PEAK_STORIES):
    pal = PEAK_PALS[_j]

    def make(title=title, xlab=xlab, names=names, pal=pal):
        @scenario(f"Operando-peak-evolution / {title} / {pal}")
        def _():
            use_journal("default")
            y = np.linspace(0, 100, 40)
            series = {}
            for i, name in enumerate(names):
                base = rng.uniform(10, 30)
                drift = rng.uniform(-0.05, 0.05)
                series[name] = (base + drift * y
                                + 2 * np.sin(y / 15 + i)
                                + rng.normal(0, 0.3, 40))
            fig, _ax = pro.plot_operando_peak_evolution(
                y, series, palette=pal, xlabel=xlab, ylabel="value",
            )
            safe = title.replace(" ", "_")[:25]
            save(fig, f"{_counter[0]:03d}_op_peakevo_{safe}")

    make()


# J7 — Operando contour (8 scenarios)
CONTOUR_STORIES = [
    ("XRD contour filled", "xrd", True, [25.0, 37.5, 44.8]),
    ("XRD contour lines", "xrd", False, [25.0, 37.5, 44.8]),
    ("Raman contour filled", "raman", True, [520, 950, 1350, 1580]),
    ("Raman contour lines", "raman", False, [520, 1350]),
    ("XAS contour filled", "xas", True, None),
    ("XAS contour lines", "xas", False, None),
    ("XRD zoom lines", "xrd", False, [25.0, 37.5]),
    ("Raman zoom filled", "raman", True, [520]),
]
CONTOUR_CMAPS = ["met-hiroshige", "met-tam", "met-hokusai3",
                  "met-cassatt2", "ft-sequential", "met-okeeffe2",
                  "met-isfahan1", "met-vangogh3"]

for _j, (title, kind, filled, refs) in enumerate(CONTOUR_STORIES):
    cmap = CONTOUR_CMAPS[_j]

    def make(title=title, kind=kind, filled=filled, refs=refs, cmap=cmap):
        @scenario(f"Operando-contour / {title} / {cmap}")
        def _():
            use_journal("default")
            if kind == "xrd":
                x, y, Z = _synth_operando_xrd()
                xlab = r"2$\theta$ (°)"
            elif kind == "raman":
                x, y, Z = _synth_operando_raman()
                xlab = r"Raman shift (cm$^{-1}$)"
            else:
                x, y, Z = _synth_operando_xas()
                xlab = "E (eV)"
            fig, _ax = pro.plot_operando_contour(
                Z, x=x, y=y, cmap=cmap, filled=filled,
                reference_peaks=refs, xlabel=xlab, ylabel="time",
            )
            safe = title.replace(" ", "_")[:25]
            save(fig, f"{_counter[0]:03d}_op_contour_{safe}")

    make()


# ==================================================================
# Section K — Pro palette sweeps on classic huitu plots (39 × 2 = 78)
# ==================================================================
ALL_PAL = pro.list_pro_palettes()

# K1 — Scatter per palette
for pal in ALL_PAL:
    def make(pal=pal):
        @scenario(f"Scatter / {pal}")
        def _():
            use_journal("default")
            colors = huitu.PALETTES[pal]
            n = min(len(colors), 8)
            fig, ax = plt.subplots(figsize=(4.2, 3.2))
            for i in range(n):
                x = rng.normal(i * 0.8, 0.25, 30)
                y = rng.normal(i * 0.5, 0.3, 30)
                ax.scatter(x, y, label=f"g{i+1}", s=22, color=colors[i],
                            alpha=0.85, edgecolor="white", linewidth=0.4)
            ax.set_xlabel("x"); ax.set_ylabel("y")
            ax.legend(frameon=False, fontsize=6, ncol=2, loc="upper left")
            ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
            ax.tick_params(which="both", top=False, right=False)
            save(fig, f"{_counter[0]:03d}_scatter_{pal.replace('-','_')}")

    make()

# K2 — Bar per palette
for pal in ALL_PAL:
    def make(pal=pal):
        @scenario(f"Bar / {pal}")
        def _():
            use_journal("default")
            colors = huitu.PALETTES[pal]
            n = min(len(colors), 7)
            fig, ax = plt.subplots(figsize=(4.6, 3.1))
            x = np.arange(n)
            h = rng.uniform(30, 95, n)
            ax.bar(x, h, color=colors[:n], edgecolor="white", linewidth=0.6)
            ax.set_xticks(x)
            ax.set_xticklabels([f"cat {i+1}" for i in range(n)],
                                fontsize=7, rotation=0)
            ax.set_ylabel("value")
            ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
            ax.tick_params(which="both", top=False, right=False)
            save(fig, f"{_counter[0]:03d}_bar_{pal.replace('-','_')}")

    make()


# ==================================================================
# Section L — Gradient-palette heatmaps (9)
# ==================================================================
GRADIENT_PALS = ["met-hiroshige", "met-hokusai3", "met-isfahan1",
                 "met-vangogh3", "met-cassatt2", "met-okeeffe2",
                 "met-tam", "ft-sequential", "ft-diverging"]

for pal in GRADIENT_PALS:
    def make(pal=pal):
        @scenario(f"Gradient heatmap / {pal}")
        def _():
            use_journal("default")
            x = np.linspace(-3, 3, 80)
            y = np.linspace(-3, 3, 80)
            X, Y = np.meshgrid(x, y)
            Z = np.exp(-(X**2 + Y**2) / 4) * np.cos(2 * X) * np.sin(2 * Y)
            fig, ax = plt.subplots(figsize=(4.5, 3.8))
            cmap = huitu.get_cmap(pal)
            im = ax.imshow(Z, cmap=cmap, origin="lower",
                            extent=[-3, 3, -3, 3])
            fig.colorbar(im, ax=ax, label="Z")
            ax.set_xlabel("x"); ax.set_ylabel("y")
            save(fig, f"{_counter[0]:03d}_heatmap_grad_{pal.replace('-','_')}")

    make()


# ==================================================================
# Section M — Multi-panel compositions (10)
# ==================================================================
@scenario("Multi-panel: dumbbell+slope+bump")
def _():
    use_journal("default")
    fig = plt.figure(figsize=(10, 3.4))
    ax1, ax2, ax3 = (fig.add_subplot(1, 3, i) for i in (1, 2, 3))
    cats = [f"M{i+1}" for i in range(6)]
    pro.plot_dumbbell(cats, rng.uniform(30, 70, 6), rng.uniform(40, 90, 6),
                       ax=ax1, start_color="#374E55", end_color="#DF8F44",
                       xlabel="yield (%)")
    pro.plot_slope({"A":[20,70],"B":[30,25],"C":[50,62],"D":[45,30]},
                    x_labels=["old","new"], ax=ax2, palette="ggsci-nejm",
                    highlight=["A","B"])
    pro.plot_bump({f"s{i+1}": rng.uniform(10, 50, 4) for i in range(5)},
                   x_labels=["Q1","Q2","Q3","Q4"], ax=ax3,
                   palette="met-archambault")
    ax1.set_title("dumbbell", fontsize=8)
    ax2.set_title("slope", fontsize=8)
    ax3.set_title("bump", fontsize=8)
    fig.subplots_adjust(wspace=0.45)
    save(fig, f"{_counter[0]:03d}_multipanel_comparison")


@scenario("Multi-panel: 4 ridgelines")
def _():
    use_journal("default")
    fig, axes = plt.subplots(2, 2, figsize=(7.5, 6.0))
    palettes = ["met-hiroshige", "ggsci-npg", "met-cassatt2", "ft-sequential"]
    for ax, pal in zip(axes.flat, palettes):
        dists = [rng.normal(i * 0.7, 0.4, 200) for i in range(6)]
        pro.plot_ridgeline(dists, labels=[f"r{i+1}" for i in range(6)],
                            palette=pal, overlap=0.6, ax=ax)
        ax.set_title(pal, fontsize=8)
    fig.subplots_adjust(hspace=0.5, wspace=0.35)
    save(fig, f"{_counter[0]:03d}_multipanel_ridgelines")


@scenario("Multi-panel: 4 waffles")
def _():
    use_journal("default")
    fig, axes = plt.subplots(2, 2, figsize=(8, 5.5))
    datasets = [
        ({"LFP": 65, "NMC": 25, "NCA": 10}, "ggsci-jama"),
        ({"O": 46, "Si": 28, "Al": 8, "Fe": 5, "Ca": 4, "etc": 9}, "met-hiroshige"),
        ({"coding": 35, "writing": 25, "reading": 20, "meetings": 20}, "met-johnson"),
        ({"exp": 40, "theory": 25, "review": 15, "teaching": 10, "service": 10},
         "ft-categorical"),
    ]
    for ax, (parts, pal) in zip(axes.flat, datasets):
        pro.plot_waffle(parts, palette=pal, rows=8, cols=12, ax=ax)
        ax.set_title(pal, fontsize=8)
    fig.subplots_adjust(hspace=0.4, wspace=0.55)
    save(fig, f"{_counter[0]:03d}_multipanel_waffles")


@scenario("Multi-panel: 3 streamgraph baselines")
def _():
    use_journal("default")
    t = np.arange(20)
    s = {f"c{i+1}": rng.uniform(2, 10, 20) + np.linspace(0, i, 20) for i in range(5)}
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.0))
    for ax, base in zip(axes, ["zero", "sym", "wiggle"]):
        pro.plot_streamgraph(t, s, palette="met-monet", baseline=base, ax=ax)
        ax.set_title(f"baseline={base}", fontsize=8)
        ax.set_xlabel("t")
        leg = ax.get_legend()
        if leg is not None:
            leg.remove()
    handles, labels = axes[-1].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, fontsize=7,
               loc="center right", bbox_to_anchor=(1.0, 0.5))
    fig.subplots_adjust(wspace=0.4, right=0.90)
    save(fig, f"{_counter[0]:03d}_multipanel_streamgraph_baselines")


@scenario("Multi-panel: 4 connected-scatter spirals")
def _():
    use_journal("default")
    fig, axes = plt.subplots(2, 2, figsize=(7.5, 6.0))
    palettes = ["met-hiroshige", "met-juarez", "ggsci-observable10", "met-tam"]
    for ax, pal in zip(axes.flat, palettes):
        theta = np.linspace(0, 2 * np.pi, 30)
        x = np.cos(theta) * (1 + 0.2 * theta)
        y = np.sin(theta) * (1 + 0.2 * theta)
        pro.plot_connected_scatter(x, y, palette=pal, ax=ax,
                                    annotate_first_last=False)
        ax.set_title(pal, fontsize=8)
    fig.subplots_adjust(hspace=0.4, wspace=0.35)
    save(fig, f"{_counter[0]:03d}_multipanel_connected_spirals")


@scenario("Multi-panel: 2x2 operando heatmap")
def _():
    use_journal("default")
    fig, axes = plt.subplots(2, 2, figsize=(8.5, 6.5))
    specs = [
        ("xrd", "met-hiroshige", r"2$\theta$", "t (s)"),
        ("raman", "met-tam", r"Raman (cm$^{-1}$)", "E (V)"),
        ("xas", "ft-sequential", "E (eV)", "SoC (%)"),
        ("xrd", "met-hokusai3", r"2$\theta$", "T (K)"),
    ]
    for ax, (kind, cmap, xlab, ylab) in zip(axes.flat, specs):
        if kind == "xrd":
            x, y, Z = _synth_operando_xrd(M=30, N=200)
        elif kind == "raman":
            x, y, Z = _synth_operando_raman(M=30, N=200)
        else:
            x, y, Z = _synth_operando_xas(M=25, N=150)
        im = ax.imshow(Z, aspect="auto", origin="lower",
                       extent=[x.min(), x.max(), y.min(), y.max()],
                       cmap=huitu.get_cmap(cmap))
        fig.colorbar(im, ax=ax, shrink=0.85)
        ax.set_xlabel(xlab); ax.set_ylabel(ylab)
        ax.set_title(cmap, fontsize=8)
    fig.subplots_adjust(hspace=0.45, wspace=0.45)
    save(fig, f"{_counter[0]:03d}_multipanel_operando_heatmaps")


@scenario("Multi-panel: 3 operando waterfall kinds")
def _():
    use_journal("default")
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
    kinds = [
        ("xrd", "met-hiroshige", "2θ"),
        ("raman", "met-tam", r"Raman (cm$^{-1}$)"),
        ("xas", "ft-sequential", "E (eV)"),
    ]
    for ax, (kind, cmap, xlab) in zip(axes, kinds):
        if kind == "xrd":
            x, y, Z = _synth_operando_xrd(M=20, N=200)
        elif kind == "raman":
            x, y, Z = _synth_operando_raman(M=20, N=200)
        else:
            x, y, Z = _synth_operando_xas(M=20, N=150)
        pro.plot_operando_waterfall(Z, x=x, y=y, cmap=cmap, stagger=0.12,
                                     fill=True, xlabel=xlab, ax=ax)
        ax.set_title(kind.upper(), fontsize=8)
    fig.subplots_adjust(wspace=0.4)
    save(fig, f"{_counter[0]:03d}_multipanel_operando_waterfall")


@scenario("Multi-panel: 6 palette showcase")
def _():
    use_journal("default")
    fig, axes = plt.subplots(2, 3, figsize=(9, 5.5))
    pals = ["met-hiroshige", "met-archambault", "ggsci-npg",
            "met-cassatt2", "ft-categorical", "met-juarez"]
    for ax, pal in zip(axes.flat, pals):
        colors = huitu.PALETTES[pal]
        n = min(len(colors), 6)
        for i in range(n):
            ax.plot(np.linspace(0, 10, 80),
                    np.sin(np.linspace(0, 10, 80) + i * 0.4) + 0.15 * i,
                    color=colors[i], linewidth=1.2)
        ax.set_title(pal, fontsize=8)
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        ax.tick_params(which="both", top=False, right=False)
    fig.subplots_adjust(hspace=0.4, wspace=0.3)
    save(fig, f"{_counter[0]:03d}_multipanel_palette_lines")


@scenario("Multi-panel: bump+slope+dumbbell variations")
def _():
    use_journal("default")
    fig = plt.figure(figsize=(12, 3.8))
    ax1 = fig.add_subplot(1, 3, 1)
    ax2 = fig.add_subplot(1, 3, 2)
    ax3 = fig.add_subplot(1, 3, 3)
    pro.plot_bump({f"m{i}": rng.uniform(10, 80, 5) for i in range(7)},
                   x_labels=["y1", "y2", "y3", "y4", "y5"], ax=ax1,
                   palette="met-renoir")
    pro.plot_slope({f"c{i}": [rng.uniform(20, 60), rng.uniform(30, 80)]
                    for i in range(8)}, x_labels=["A", "B"], ax=ax2,
                   palette="ggsci-lancet", highlight=["c0", "c3"])
    pro.plot_dumbbell([f"X{i+1}" for i in range(10)],
                       rng.uniform(10, 60, 10), rng.uniform(30, 90, 10),
                       ax=ax3, xlabel="score")
    ax1.set_title("bump", fontsize=8)
    ax2.set_title("slope", fontsize=8)
    ax3.set_title("dumbbell", fontsize=8)
    fig.subplots_adjust(wspace=0.5)
    save(fig, f"{_counter[0]:03d}_multipanel_rank_variations")


@scenario("Multi-panel: 4 parallel coords")
def _():
    use_journal("default")
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    pals = ["met-hiroshige", "ggsci-nejm", "ft-sequential", "met-cassatt2"]
    for ax, pal in zip(axes.flat, pals):
        n = 60
        df = pd.DataFrame({f"x{i+1}": rng.normal(0, 1, n) for i in range(5)}
                          | {"y": rng.uniform(0, 1, n)})
        pro.plot_parallel(df, color_by="y", palette=pal, alpha=0.6, ax=ax)
        ax.set_title(pal, fontsize=8)
    fig.subplots_adjust(hspace=0.5, wspace=0.4)
    save(fig, f"{_counter[0]:03d}_multipanel_parallel")


# ==================================================================
# Run + summarize
# ==================================================================
if __name__ == "__main__":
    ok = sum(1 for _, _, s, _ in results if s == "OK")
    fail = sum(1 for _, _, s, _ in results if s == "FAIL")
    print()
    print(f"===== huitu.pro gallery — {ok} OK / {fail} FAIL =====")
    for n, name, status, detail in results:
        mark = "+" if status == "OK" else "x"
        print(f"  {mark} {n:03d}  {name}")
        if status == "FAIL":
            print(f"       {detail}")
    print(f"\nOutput: {OUT}")
