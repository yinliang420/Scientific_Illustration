"""Comprehensive stress test of the huitu plotting skill on real materials-science data.

Exercises >=17 scenarios covering characterization (XRD / Raman / XAFS),
palette / journal comparisons, legend-mode showcase, general plots (bar /
scatter / box-violin / heatmap / radar), and edge cases (single-point,
reversed-x, large data). Each scenario is self-contained in a try/except so
one failure does not abort the run. All figures save both PNG (>=200 dpi)
and PDF to ``output_comprehensive/``.
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Make the package importable even if not pip-installed.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from huitu import (  # noqa: E402
    use_journal, use_palette, list_palettes, PALETTES, register_cjk,
    plot_xrd, plot_raman,
    plot_bar, plot_scatter, plot_line, plot_heatmap, plot_box_violin, plot_radar,
    make_subplots, add_inset,
)

# -------- paths --------
HERE = Path(__file__).resolve().parent
OUT = HERE / "output_comprehensive"
OUT.mkdir(parents=True, exist_ok=True)

XRD_DIR = Path("/Users/ylll/phd/coding/huitu_skills/xrd_real_patterns_2026-04-23/opxrd/CNRS")
RAMAN_ROOT = Path("/Users/ylll/phd/coding/raman/data")
XAFS_ROOT = Path("/Users/ylll/phd/coding/xafs/data")


# -------- helpers --------
def load_xrd(pattern_path: Path):
    d = json.loads(pattern_path.read_text())
    x = np.asarray(d["two_theta_values"], dtype=float)
    y = np.asarray(d["intensities"], dtype=float)
    return x, y


def load_xlsx(path: Path):
    df = pd.read_excel(path)
    return df["X"].to_numpy(dtype=float), df["Y"].to_numpy(dtype=float)


def first_xlsx(d: Path) -> Path | None:
    for p in sorted(d.glob("images/*.xlsx")):
        if not p.name.startswith("."):
            return p
    return None


def chem(d: Path, kind: str) -> str:
    p = d / f"chemical_formulas_{kind}.json"
    if not p.exists():
        return d.name[:8]
    try:
        data = json.loads(p.read_text())
        first = next(iter(data.values()))
        formulas = first.get("chemical_formulas") or ["?"]
        return formulas[0] if formulas else d.name[:8]
    except Exception:
        return d.name[:8]


def save_both(fig, stem: str, dpi: int | None = None):
    """Save journal-grade PNG + vector PDF (honours active journal DPI)."""
    import matplotlib as mpl

    png = OUT / f"{stem}.png"
    pdf = OUT / f"{stem}.pdf"
    if dpi is None:
        dpi = mpl.rcParams.get("savefig.dpi", 600)
        if isinstance(dpi, str):
            dpi = 600
    fig.savefig(png, dpi=dpi, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)
    return png, pdf


def latex_formula(formula: str) -> str:
    """Turn ``Fe2O3`` into mathtext ``$Fe_{2}O_{3}$``.

    mathtext is used (not Unicode subscripts U+2080…) because Helvetica /
    Arial / DejaVu Sans — our default font stack — do not ship the unicode
    subscript glyphs, and matplotlib renders them as blanks. mathtext is
    font-independent. Labels are safe from label_trim because
    ``plot_raman(..., label_trim=...)`` skips any label containing ``$``.
    """
    import re
    if not formula or any(ch in formula for ch in "$\\^{"):
        return formula
    s = re.sub(r"([A-Za-z\)\]])(\d+(?:\.\d+)?)", r"\1_{\2}", formula)
    return f"${s}$"


# -------- index data sources once --------
xrd_patterns = sorted(XRD_DIR.glob("pattern_*.json"),
                      key=lambda p: int(p.stem.split("_")[1]))
raman_dirs = sorted(d for d in RAMAN_ROOT.iterdir() if d.is_dir())
xafs_dirs = sorted(d for d in XAFS_ROOT.iterdir() if d.is_dir())

print(f"Found {len(xrd_patterns)} XRD patterns, {len(raman_dirs)} Raman dirs, "
      f"{len(xafs_dirs)} XAFS dirs")


def load_raman_chain(max_n: int):
    """Yield (chem_label_latex, x, y) up to max_n usable Raman dirs."""
    out = []
    for d in raman_dirs:
        if len(out) >= max_n:
            break
        xlsx = first_xlsx(d)
        if xlsx is None:
            continue
        try:
            x, y = load_xlsx(xlsx)
        except Exception:
            continue
        if x.size < 4:
            continue
        label = latex_formula(chem(d, "raman"))
        out.append((label, x, y))
    return out


def load_xafs_chain(max_n: int):
    out = []
    for d in xafs_dirs:
        if len(out) >= max_n:
            break
        xlsx = first_xlsx(d)
        if xlsx is None:
            continue
        try:
            x, y = load_xlsx(xlsx)
        except Exception:
            continue
        if x.size < 4:
            continue
        # try both exafs / xafs
        label = chem(d, "exafs")
        if label == d.name[:8]:
            label = chem(d, "xafs")
        out.append((label, x, y))
    return out


def group_xafs_same_edge(chain, tol_ev: float = 5000.0):
    """Return the largest subset of ``chain`` whose edge energies cluster within ``tol_ev``.

    Uses each spectrum's median energy as a proxy for the absorption edge
    (for E-space XAFS files this is near the edge itself). Falls back to the
    2 closest-in-energy spectra if no group of 2+ sits within ``tol_ev``.
    """
    if len(chain) <= 1:
        return chain
    edges = [float(np.median(x)) for _, x, _ in chain]
    # Greedy: for each spectrum, grow a cluster of others within tol_ev.
    best_idx: list[int] = []
    for i, ei in enumerate(edges):
        idx = [j for j, ej in enumerate(edges) if abs(ej - ei) <= tol_ev]
        if len(idx) > len(best_idx):
            best_idx = idx
    if len(best_idx) >= 2:
        return [chain[i] for i in best_idx]
    # Fallback: pick the two closest in energy.
    order = sorted(range(len(edges)), key=lambda j: edges[j])
    best_pair = (order[0], order[1])
    best_gap = abs(edges[order[1]] - edges[order[0]])
    for a, b in zip(order, order[1:]):
        g = abs(edges[b] - edges[a])
        if g < best_gap:
            best_gap, best_pair = g, (a, b)
    return [chain[best_pair[0]], chain[best_pair[1]]]


# -------- bookkeeping --------
results: list[tuple[int, str, str, str]] = []  # (n, name, status, detail)


def scenario(n: int, name: str):
    """Decorator-style wrapper: run a function inside try/except."""
    def deco(fn):
        print(f"\n=== Scenario {n}: {name} ===")
        try:
            produced = fn()
            detail = produced if isinstance(produced, str) else ""
            print(f"  -> OK {detail}")
            results.append((n, name, "OK", detail))
        except Exception as exc:
            tb = traceback.format_exc(limit=2)
            print(f"[FAIL Scenario {n}]: {exc}")
            print(tb)
            results.append((n, name, "FAIL", str(exc)))
        return fn
    return deco


# ============================================================
# Scenario 1 — XRD stacked 6 patterns, Nature preset, inline legend
# ============================================================
@scenario(1, "XRD stacked 6 patterns (Nature, inline legend)")
def _s1():
    use_journal("nature")
    idxs = [0, 3, 6, 9, 12, 15]
    data, labels = [], []
    for i in idxs:
        if i >= len(xrd_patterns):
            continue
        x, y = load_xrd(xrd_patterns[i])
        data.append((x, y))
        labels.append(f"sample {i}")
    fig, _ = plot_xrd(data, labels=labels, offset=1.1, legend="inline")
    fig.suptitle("XRD stack (Nature preset)", y=1.02, fontsize=9)
    save_both(fig, "01_xrd_stack_nature")
    return f"6 patterns -> 01_xrd_stack_nature.png/pdf"


# ============================================================
# Scenario 2 — XRD with hkl markers
# ============================================================
@scenario(2, "XRD single pattern with hkl markers")
def _s2():
    use_journal("default")
    x, y = load_xrd(xrd_patterns[0])
    # Pick five tallest peaks as synthetic hkl annotations.
    order = np.argsort(y)[::-1]
    picked: list[float] = []
    for idx in order:
        two_theta = float(x[idx])
        if all(abs(two_theta - p) > 1.5 for p in picked):
            picked.append(two_theta)
        if len(picked) >= 5:
            break
    hkl_labels = ["(110)", "(200)", "(211)", "(220)", "(310)"]
    hkl = {round(p, 2): lab for p, lab in zip(picked, hkl_labels)}
    fig, _ = plot_xrd((x, y), hkl=hkl)
    save_both(fig, "02_xrd_hkl_markers")
    return f"hkl={hkl}"


# ============================================================
# Scenario 3 — XRD zoomed inset around strongest peak
# ============================================================
@scenario(3, "XRD with zoomed inset around strongest peak")
def _s3():
    use_journal("default")
    x, y = load_xrd(xrd_patterns[0])
    fig, ax = plot_xrd((x, y))
    # Normalized plot y is 0..1 via plot_xrd; line already drawn.
    # Use the actual plotted line data (already normalized) for the inset region.
    yn = (y - y.min()) / (y.max() - y.min() + 1e-12)
    peak_idx = int(np.argmax(yn))
    peak_x = float(x[peak_idx])
    x_span = float(x.max() - x.min())
    half = x_span / 10.0  # ~5x zoom (2*half vs full span/2)
    add_inset(
        ax,
        bounds=(0.55, 0.45, 0.42, 0.45),
        xlim=(peak_x - half, peak_x + half),
        ylim=(0.0, 1.05),
    )
    save_both(fig, "03_xrd_zoom_inset")
    return f"peak at 2theta={peak_x:.2f}"


# ============================================================
# Scenario 4 — Raman stacked 5 spectra (ACS, chemical formula labels)
# ============================================================
@scenario(4, "Raman stacked 5 spectra (ACS, chemical formulas)")
def _s4():
    use_journal("acs")
    chain = load_raman_chain(5)
    if len(chain) < 2:
        raise RuntimeError("not enough Raman spectra found")
    data = [(x, y) for _, x, y in chain]
    labels = [lab for lab, _, _ in chain]
    fig, _ = plot_raman(data, labels=labels, offset=1.1, legend="inline")
    save_both(fig, "04_raman_stack_acs")
    return f"labels={labels}"


# ============================================================
# Scenario 5 — Raman with Chinese title (CJK rendering)
# ============================================================
@scenario(5, "Raman with Chinese title (CJK, no mathtext)")
def _s5():
    chain = load_raman_chain(3)
    if not chain:
        raise RuntimeError("no Raman spectra")

    # Probe for a CJK font before rendering so we don't silently emit tofu.
    cjk_font = register_cjk()
    if cjk_font is None:
        print("  [SKIP] no CJK-capable font installed on this system; "
              "scenario 5 cannot render Chinese characters legibly.")
        return "SKIPPED (no CJK font)"

    use_journal("nature", cjk=True)
    data = [(x, y) for _, x, y in chain]
    # Plain-unicode labels only (no $...$) to avoid mathtext + CJK collisions.
    plain_labels = [chem(raman_dirs[i], "raman") for i in range(len(chain))]
    fig, ax = plot_raman(data, labels=plain_labels, offset=1.1, legend="best")
    ax.set_title("氧化铁拉曼光谱对比")
    # Use a real Unicode superscript so the label reads as cm⁻¹.
    ax.set_xlabel("拉曼位移 (cm\u207b\u00b9)")
    ax.set_ylabel("强度 (任意单位)")
    save_both(fig, "05_raman_cjk_title")
    # Restore non-CJK default so later scenarios aren't affected.
    use_journal("default")
    return f"Chinese title ok (font={cjk_font})"


# ============================================================
# Scenario 6 — XAFS compare 4 samples (overlay via plot_line)
# ============================================================
@scenario(6, "XAFS compare 4 samples (plot_line overlay)")
def _s6():
    use_journal("wiley")
    raw_chain = load_xafs_chain(4)
    if len(raw_chain) < 2:
        raise RuntimeError("not enough XAFS spectra")
    # Samples may span very different absorption edges (e.g. Zr K ~18 keV vs
    # V K ~5.5 keV); overlaying across edges gives flat lines. Cluster by
    # edge energy within 5 keV.
    chain = group_xafs_same_edge(raw_chain, tol_ev=5000.0)
    dropped = [c[0] for c in raw_chain if c not in chain]
    if dropped:
        print(f"  [note] dropped {dropped} — different absorption edge")
    # Interpolate all onto a shared x-grid so plot_line (wide-format DF) works.
    x_min = max(c[1].min() for c in chain)
    x_max = min(c[1].max() for c in chain)
    xs = np.linspace(x_min, x_max, 600)
    df = pd.DataFrame({"energy_eV": xs})
    for label, x, y in chain:
        # XAFS energy axis may be non-monotonic for some files — sort first.
        order = np.argsort(x)
        xi, yi = x[order], y[order]
        df[label] = np.interp(xs, xi, yi)
    fig, _ = plot_line(
        df,
        xlabel="Photon energy (eV)",
        ylabel="Absorption (a.u.)",
    )
    save_both(fig, "06_xafs_overlay_4")
    return f"kept={[c[0] for c in chain]} dropped={dropped}"


# ============================================================
# Scenario 7 — XAFS normalized & stacked with offset
# ============================================================
@scenario(7, "XAFS normalized & stacked (edge-step normalized)")
def _s7():
    use_journal("default")
    raw_chain = load_xafs_chain(4)
    if len(raw_chain) < 2:
        raise RuntimeError("not enough XAFS spectra")
    # Same-edge filtering as scenario 6 so the shared x-grid isn't degenerate.
    chain = group_xafs_same_edge(raw_chain, tol_ev=5000.0)
    dropped = [c[0] for c in raw_chain if c not in chain]
    if dropped:
        print(f"  [note] dropped {dropped} — different absorption edge")
    # Normalize each to its full min-max edge step, then stack with offset.
    x_min = max(c[1].min() for c in chain)
    x_max = min(c[1].max() for c in chain)
    xs = np.linspace(x_min, x_max, 600)
    df = pd.DataFrame({"energy_eV": xs})
    kept_any = False
    for i, (label, x, y) in enumerate(chain):
        order = np.argsort(x)
        xi, yi = x[order], y[order]
        yint = np.interp(xs, xi, yi)
        span = yint.max() - yint.min()
        if span <= 0:
            print(f"  [note] skipping {label!r}: zero edge step on shared grid")
            continue
        yn = (yint - yint.min()) / span
        df[f"{label} (+{i:.0f})"] = yn + i * 1.1
        kept_any = True
    if not kept_any:
        raise RuntimeError("all XAFS samples had zero edge step on shared grid")
    fig, _ = plot_line(
        df,
        xlabel="Photon energy (eV)",
        ylabel="Normalized absorption + offset",
    )
    save_both(fig, "07_xafs_normalized_stack")
    return f"kept={len(df.columns)-1} dropped={dropped}"


# ============================================================
# Scenario 8 — Same XRD data in 4 journal presets (2x2 subplot)
# ============================================================
@scenario(8, "Same XRD data in 4 journal presets")
def _s8():
    # Subplots share one journal preset from make_subplots, so we instead
    # rebuild each axes under its own journal rcParams.
    x, y = load_xrd(xrd_patterns[0])
    presets = ["nature", "acs", "wiley", "ieee"]
    fig, axes = plt.subplots(2, 2, figsize=(8, 6), constrained_layout=True)
    for ax, journal in zip(axes.flatten(), presets):
        use_journal(journal)
        plot_xrd((x, y), ax=ax, journal=journal)
        ax.set_title(journal, fontsize=9)
    fig.suptitle("Same XRD pattern across 4 journal presets", fontsize=10)
    save_both(fig, "08_xrd_4_journals")
    # Restore default after loop.
    use_journal("default")
    return f"presets={presets}"


# ============================================================
# Scenario 9 — Palette test on scatter with 6 groups (carto-bold, then nord)
# ============================================================
@scenario(9, "Scatter with 6 groups x 2 palettes (carto-bold vs nord)")
def _s9():
    rng = np.random.default_rng(7)
    groups = []
    for i in range(6):
        cx = rng.uniform(-2, 2)
        cy = rng.uniform(-2, 2)
        x = rng.normal(cx, 0.3, size=25)
        y = rng.normal(cy, 0.3, size=25)
        groups.append((f"grp{i+1}", x, y))

    produced = []
    for pal in ("carto-bold", "nord"):
        use_journal("default")
        use_palette(pal)
        fig, ax = plt.subplots(figsize=(5, 4), constrained_layout=True)
        for label, gx, gy in groups:
            ax.scatter(gx, gy, label=label, s=18, alpha=0.85)
        ax.set_xlabel("PC1")
        ax.set_ylabel("PC2")
        ax.set_title(f"6 groups — palette={pal}")
        ax.legend(loc="best", fontsize=7, frameon=False, ncols=2)
        name = f"09_scatter_palette_{pal.replace('-', '_')}"
        save_both(fig, name)
        produced.append(name)
    return ", ".join(produced)


# ============================================================
# Scenario 10 — Four legend modes on the same Raman data (1x4 subplot)
# ============================================================
@scenario(10, "Four legend modes showcase (Raman 1x4)")
def _s10():
    chain = load_raman_chain(4)
    if len(chain) < 2:
        raise RuntimeError("not enough Raman data")
    data = [(x, y) for _, x, y in chain]
    labels = [lab for lab, _, _ in chain]
    modes = ["inline", "best", "outside", "upper right"]
    use_journal("default")
    # 2x2 layout at a smaller figsize keeps tick labels readable instead of
    # squeezing each panel into a narrow 1x4 strip.
    fig, axes = plt.subplots(2, 2, figsize=(7.5, 6.5), constrained_layout=True)
    for ax, mode in zip(axes.flatten(), modes):
        plot_raman(data, ax=ax, labels=labels, offset=1.1, legend=mode)
        ax.set_title(f'legend="{mode}"', fontsize=9)
    save_both(fig, "10_raman_legend_modes")
    return f"modes={modes}"


# ============================================================
# Scenario 11 — Bar chart: specific capacity of 5 cathodes with error bars
# ============================================================
@scenario(11, "Bar chart: cathode specific capacity w/ error bars")
def _s11():
    use_journal("default")
    cats = ["LFP", "NMC111", "NMC622", "NMC811", "LNMO"]
    vals = [130.0, 150.0, 170.0, 180.0, 200.0]
    errs = [4.0, 6.0, 7.0, 8.0, 9.0]
    df = pd.DataFrame({"material": cats, "capacity": vals})
    fig, ax = plot_bar(
        df,
        xlabel="Cathode",
        ylabel="Specific capacity (mAh/g)",
    )
    # Overlay error bars on the existing bars.
    xs = np.arange(len(cats))
    ax.errorbar(xs, vals, yerr=errs, fmt="none", ecolor="black", capsize=3, lw=1.0)
    ax.set_ylim(0, max(v + e for v, e in zip(vals, errs)) * 1.1)
    # Drop the stray "capacity" legend — the x-axis already labels each bar.
    leg = ax.get_legend()
    if leg is not None:
        leg.remove()
    save_both(fig, "11_bar_cathode_capacity")
    return "5 cathodes"


# ============================================================
# Scenario 12 — Scatter w/ linear fit: conductivity vs doping
# ============================================================
@scenario(12, "Scatter: conductivity vs doping (fit=True)")
def _s12():
    use_journal("default")
    rng = np.random.default_rng(42)
    doping = np.linspace(0.5, 10.0, 14)  # at.%
    # Plausible linear trend + noise: sigma ~ 2 + 1.3 * doping
    sigma = 2.0 + 1.3 * doping + rng.normal(0, 1.2, size=doping.size)
    df = pd.DataFrame({"doping_at_pct": doping, "sigma_S_cm": sigma})
    fig, _ = plot_scatter(
        df,
        fit=True,
        xlabel="Doping concentration (at.%)",
        ylabel="Conductivity (S/cm)",
    )
    save_both(fig, "12_scatter_conductivity_doping")
    return f"{doping.size} points, linear fit"


# ============================================================
# Scenario 13 — Box/violin: grain size across 3 processing routes
# ============================================================
@scenario(13, "Box/violin: grain size 3 processing routes")
def _s13():
    use_journal("default")
    rng = np.random.default_rng(0)
    r1 = rng.normal(50, 10, 80)   # ball-milled
    r2 = rng.normal(80, 15, 80)   # spark-plasma-sintered
    r3 = rng.normal(120, 25, 80)  # furnace-sintered
    df = pd.DataFrame({
        "Ball-milled": r1,
        "SPS": r2,
        "Furnace": r3,
    })
    fig, _ = plot_box_violin(
        df,
        kind="violin",
        xlabel="Processing route",
        ylabel="Grain size (nm)",
    )
    save_both(fig, "13_violin_grain_size")
    return "3 distributions"


# ============================================================
# Scenario 14 — Heatmap: 10x10 DFT-like correlation matrix
# ============================================================
@scenario(14, "Heatmap: 10x10 composition correlation")
def _s14():
    use_journal("default")
    rng = np.random.default_rng(123)
    elements = ["Li", "Na", "Mg", "Al", "Ti", "Mn", "Fe", "Co", "Ni", "Cu"]
    # Build a symmetric positive-semidefinite-ish "correlation" matrix.
    base = rng.normal(size=(10, 10))
    corr = (base + base.T) / 2
    np.fill_diagonal(corr, 1.0)
    corr = np.clip(corr / max(abs(corr.min()), abs(corr.max()), 1.0), -1.0, 1.0)
    np.fill_diagonal(corr, 1.0)
    df = pd.DataFrame(corr, index=elements, columns=elements)
    fig, _ = plot_heatmap(df, annot=True, cbar_label="Pearson r", cmap="RdBu_r",
                          center=0.0)
    save_both(fig, "14_heatmap_10x10")
    return "10x10 correlation matrix"


# ============================================================
# Scenario 15 — Radar: 3 materials, 5 performance axes
# ============================================================
@scenario(15, "Radar: 3 materials x 5 metrics")
def _s15():
    use_journal("default")
    axes_ = ["Capacity", "Rate", "Cycle life", "Cost", "Safety"]
    data = {
        "LFP":    [140, 80, 95, 90, 98],
        "NMC622": [175, 90, 75, 60, 70],
        "NMC811": [195, 92, 65, 55, 60],
    }
    fig = plt.figure(figsize=(5.5, 5.0), constrained_layout=True)
    ax = fig.add_subplot(111, projection="polar")
    plot_radar(data, ax=ax, categories=axes_, normalize="per_axis")
    ax.set_title("Cathode performance comparison", y=1.1, fontsize=9)
    save_both(fig, "15_radar_cathodes")
    return "3 materials, 5 metrics"


# ============================================================
# Scenario 16 — Edge-case robustness (tiny data, reversed-x XRD)
# ============================================================
@scenario(16, "Edge case: tiny Raman + reversed-x XRD")
def _s16():
    use_journal("default")
    # tiny Raman with 10 points
    tiny_x = np.linspace(100, 1600, 10)
    tiny_y = np.sin(tiny_x / 300.0) + 1.0
    # reversed-x XRD: take a real pattern and reverse it
    x, y = load_xrd(xrd_patterns[0])
    rev_x, rev_y = x[::-1].copy(), y[::-1].copy()

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5), constrained_layout=True)
    plot_raman((tiny_x, tiny_y), ax=axes[0])
    axes[0].set_title("Tiny Raman (10 pts)", fontsize=9)
    plot_xrd((rev_x, rev_y), ax=axes[1])
    axes[1].set_title("Reversed-x XRD", fontsize=9)
    save_both(fig, "16_edge_cases")
    return "tiny + reversed"


# ============================================================
# Scenario 17 — Large-data mega figure (biggest Raman xlsx + biggest XRD pattern)
# ============================================================
@scenario(17, "Large data: biggest Raman xlsx + biggest XRD pattern")
def _s17():
    use_journal("default")

    # biggest XRD — limit the search a bit for speed
    candidates_xrd = xrd_patterns[: min(200, len(xrd_patterns))]
    best_xrd, best_n = None, -1
    for p in candidates_xrd:
        try:
            d = json.loads(p.read_text())
            n = len(d.get("two_theta_values") or [])
        except Exception:
            continue
        if n > best_n:
            best_n, best_xrd = n, p
    if best_xrd is None:
        raise RuntimeError("no XRD pattern found")
    x_xrd, y_xrd = load_xrd(best_xrd)

    # biggest Raman — scan up to ~40 dirs
    best_raman, best_rn = None, -1
    for d in raman_dirs[:40]:
        xlsx = first_xlsx(d)
        if xlsx is None:
            continue
        try:
            xr, yr = load_xlsx(xlsx)
        except Exception:
            continue
        if xr.size > best_rn:
            best_rn, best_raman = xr.size, (xr, yr, d.name[:8])
    if best_raman is None:
        raise RuntimeError("no Raman xlsx found")
    xr, yr, rname = best_raman

    fig, axes = plt.subplots(2, 1, figsize=(9, 7), constrained_layout=True)
    plot_xrd((x_xrd, y_xrd), ax=axes[0])
    axes[0].set_title(f"Largest XRD pattern: {best_xrd.name} ({len(x_xrd)} pts)", fontsize=9)
    plot_raman((xr, yr), ax=axes[1])
    axes[1].set_title(f"Largest Raman: {rname} ({xr.size} pts)", fontsize=9)
    # Open up the gap between the two rows (constrained_layout still applies).
    try:
        fig.set_constrained_layout_pads(hspace=0.35)
    except Exception:
        fig.subplots_adjust(hspace=0.35)
    save_both(fig, "17_large_data")
    return f"XRD={len(x_xrd)}, Raman={xr.size}"


# ============================================================
# Summary
# ============================================================
ok = sum(1 for _, _, s, _ in results if s == "OK")
total = len(results)
print("\n" + "=" * 60)
print(f"SUMMARY: {ok} / {total} scenarios succeeded")
print("=" * 60)
for n, name, status, detail in results:
    marker = " " if status == "OK" else "!"
    print(f"  {marker}{n:>2}. [{status}] {name}")
    if status == "FAIL":
        print(f"        reason: {detail}")

print("\nOutput files in", OUT)
files = sorted(OUT.iterdir())
for f in files:
    if f.is_file():
        kb = f.stat().st_size / 1024.0
        print(f"  {f.name:50s}  {kb:8.1f} KB")
print(f"\nTotal files: {len(files)}")
