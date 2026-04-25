"""Aesthetic gallery test for the huitu plotting library.

Produces >=220 figures (PNG + PDF pairs) exercising every plot function,
every journal preset, and every palette, with emphasis on advanced figure
types (operando, density, SHAP) and Nature/Science-quality aesthetics.

Each scenario is wrapped in try/except so a single failure does not abort
the gallery. Run from repo root::

    python real_data_test/test_gallery.py
"""
from __future__ import annotations

import json
import re
import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from huitu import (  # noqa: E402
    use_journal, use_palette, list_palettes, PALETTES,
    plot_xrd, plot_raman, plot_xps, plot_ftir, plot_uvvis, plot_pl,
    plot_thermal, plot_rietveld, plot_operando,
    plot_cv, plot_gcd, plot_cycle, plot_eis, plot_bode, plot_tafel,
    plot_band, plot_dos, plot_cohp, plot_pourbaix, plot_phase_diagram,
    plot_bar, plot_scatter, plot_line, plot_heatmap, plot_box_violin,
    plot_radar, plot_density, plot_shap,
    make_subplots, add_inset, panel_tag, supertitle,
)


def _tag_panels(axes, letters=None, loc: str = "outside-left"):
    """Apply ``panel_tag`` to a flat or nd-array of axes in row-major order."""
    try:
        flat = list(axes.flatten())
    except AttributeError:
        flat = list(axes)
    if letters is None:
        letters = [chr(ord("a") + i) for i in range(len(flat))]
    for ax, lt in zip(flat, letters):
        try:
            panel_tag(ax, lt, loc=loc)
        except Exception:
            pass

# ------------------------------------------------------------------
# Paths & data loading helpers
# ------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
OUT = HERE / "output_gallery"
OUT.mkdir(parents=True, exist_ok=True)

XRD_DIR = Path("/Users/ylll/phd/coding/huitu_skills/xrd_real_patterns_2026-04-23/opxrd/CNRS")
RAMAN_ROOT = Path("/Users/ylll/phd/coding/raman/data")
XAFS_ROOT = Path("/Users/ylll/phd/coding/xafs/data")

ALL_JOURNALS = ["default", "nature", "science", "acs", "rsc", "wiley", "elsevier", "ieee"]
# Huitu palettes for which we want qualitative colour cycling on lines/bars.
QUALITATIVE_PALETTES = [
    "tol-bright", "tol-muted", "tol-vibrant", "okabe-ito",
    "carto-safe", "carto-bold", "nord", "nature-cat", "science-cat",
    "bold-qualitative",
]
# Gradient-capable palettes (usable as cmap).
GRADIENT_PALETTES = ["crameri-batlow", "crameri-roma", "viridis6", "editorial"]
ALL_PALETTES = QUALITATIVE_PALETTES + GRADIENT_PALETTES


def load_xrd(path: Path):
    d = json.loads(path.read_text())
    return np.asarray(d["two_theta_values"], dtype=float), np.asarray(d["intensities"], dtype=float)


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


def latex_formula(formula: str) -> str:
    if not formula or any(ch in formula for ch in "$\\^{"):
        return formula
    s = re.sub(r"([A-Za-z\)\]])(\d+(?:\.\d+)?)", r"\1_{\2}", formula)
    return f"${s}$"


def save_both(fig, stem: str, dpi: int | None = None):
    """Save journal-grade PNG + vector PDF.

    ``dpi=None`` (default) picks up the active journal preset's
    ``savefig.dpi`` (600 by default), falling back to 600 when matplotlib
    still holds the sentinel ``"figure"`` string.
    """
    import matplotlib as mpl

    png = OUT / f"{stem}.png"
    pdf = OUT / f"{stem}.pdf"
    if dpi is None:
        dpi = mpl.rcParams.get("savefig.dpi", 600)
        if isinstance(dpi, str):
            dpi = 600
    fig.savefig(png, dpi=dpi, bbox_inches="tight")
    try:
        fig.savefig(pdf, bbox_inches="tight")
    except Exception:
        # Some polar/complex figures can fail PDF save; PNG still counts.
        pass
    plt.close(fig)
    return png


# ------------------------------------------------------------------
# Index real-data sources once
# ------------------------------------------------------------------
xrd_patterns = sorted(XRD_DIR.glob("pattern_*.json"),
                     key=lambda p: int(p.stem.split("_")[1]))
raman_dirs = sorted(d for d in RAMAN_ROOT.iterdir() if d.is_dir())
xafs_dirs = sorted(d for d in XAFS_ROOT.iterdir() if d.is_dir())

print(f"Found {len(xrd_patterns)} XRD patterns, {len(raman_dirs)} Raman dirs, "
      f"{len(xafs_dirs)} XAFS dirs")


def load_raman_chain(max_n: int, skip: int = 0):
    out = []
    for d in raman_dirs[skip:]:
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
        out.append((latex_formula(chem(d, "raman")), x, y))
    return out


# ------------------------------------------------------------------
# Bookkeeping
# ------------------------------------------------------------------
results: list[tuple[int, str, str, str]] = []


def scenario(n: int, name: str, section: str = "misc"):
    def deco(fn):
        print(f"[{n:03d}] {section:9s} {name}")
        try:
            fn()
            results.append((n, name, "OK", section))
        except Exception as exc:
            tb = traceback.format_exc(limit=2)
            print(f"   FAIL: {exc}")
            print(tb.splitlines()[-3] if tb else "")
            results.append((n, name, f"FAIL: {exc}", section))
        return fn
    return deco


# ------------------------------------------------------------------
# Synthetic-data generators
# ------------------------------------------------------------------
def synth_xps(rng, center_list=(285.0, 286.5, 288.3), widths=(0.8, 0.9, 1.1), heights=(1.0, 0.55, 0.3)):
    x = np.linspace(282, 292, 600)
    y = np.zeros_like(x)
    for c, w, h in zip(center_list, widths, heights):
        y += h * np.exp(-0.5 * ((x - c) / w) ** 2)
    y += 0.02 * rng.normal(size=x.size)
    y += 0.05 + 0.005 * (x - x.min())  # linear baseline
    return x, y


def synth_ftir(rng):
    wn = np.linspace(4000, 400, 1000)
    # Several absorption dips -> transmittance %
    t = 98.0 * np.ones_like(wn)
    for c, w, depth in [(3400, 200, 35), (2900, 80, 20), (1630, 60, 15),
                        (1050, 50, 40), (600, 70, 25)]:
        t -= depth * np.exp(-0.5 * ((wn - c) / w) ** 2)
    t += 0.3 * rng.normal(size=wn.size)
    return wn, t


def synth_uvvis(rng, edge_nm=450.0, sharpness=15.0):
    wl = np.linspace(300, 800, 600)
    a = 2.0 / (1.0 + np.exp((wl - edge_nm) / sharpness)) + 0.1
    a += 0.01 * rng.normal(size=wl.size)
    return wl, a


def synth_pl(rng, center_nm=620.0, width=25.0, height=1.0):
    wl = np.linspace(400, 800, 500)
    y = height * np.exp(-0.5 * ((wl - center_nm) / width) ** 2)
    y += 0.02 * rng.normal(size=wl.size)
    y = np.clip(y, 0, None)
    return wl, y


def synth_tga(rng):
    T = np.linspace(25, 900, 500)
    # 5% moisture loss around 100 C, 10% decomposition at 450 C
    w = 100.0 - 5.0 / (1 + np.exp(-(T - 110) / 15)) - 10.0 / (1 + np.exp(-(T - 450) / 30))
    w += 0.15 * rng.normal(size=T.size)
    return T, w


def synth_dsc(rng):
    T = np.linspace(25, 900, 500)
    y = -0.3 * np.exp(-0.5 * ((T - 110) / 25) ** 2)
    y += 0.5 * np.exp(-0.5 * ((T - 450) / 45) ** 2)
    y += 0.02 * rng.normal(size=T.size)
    return T, y


def synth_cv(rng, scan_rate: float = 50.0, peaks=((0.4, 1.0), (-0.3, -0.8))):
    # Reference scan rate for peak-current scaling (Randles-Sevcik: ip ~ sqrt(nu)).
    ref_rate = 50.0
    V = np.concatenate([np.linspace(-0.6, 0.8, 400), np.linspace(0.8, -0.6, 400)])
    # Capacitive baseline scales linearly with scan rate.
    j = 0.02 * (V + 0.6) * scan_rate / ref_rate
    peak_scale = np.sqrt(scan_rate / ref_rate)
    for c, h in peaks:
        sign = np.where(np.r_[np.ones(400), -np.ones(400)] > 0, 1, -1)
        j += h * peak_scale * sign * np.exp(-0.5 * ((V - c) / 0.08) ** 2)
    j += 0.01 * rng.normal(size=V.size)
    return V, j


def synth_gcd(rng, capacity: float = 150.0):
    # Charge branch: capacity 0 -> cap, V rises
    cap_c = np.linspace(0, capacity, 200)
    V_c = 3.2 + 0.9 / (1 + np.exp(-(cap_c - capacity * 0.4) / 20)) + 0.01 * rng.normal(size=cap_c.size)
    # Discharge
    cap_d = np.linspace(capacity, 0, 200)
    V_d = 4.0 - 0.9 / (1 + np.exp(-(cap_d - capacity * 0.6) / 20)) + 0.01 * rng.normal(size=cap_d.size)
    x = np.concatenate([cap_c, cap_d])
    y = np.concatenate([V_c, V_d])
    return x, y


def synth_eis(rng, Rs: float = 5.0, Rct: float = 50.0, C: float = 1e-4):
    omega = np.logspace(-1, 5, 60)
    z = Rs + Rct / (1 + 1j * omega * Rct * C)
    return np.real(z), -np.imag(z)


def synth_bode(rng):
    omega = np.logspace(-1, 5, 60)
    Rs, Rct, C = 5.0, 50.0, 1e-4
    z = Rs + Rct / (1 + 1j * omega * Rct * C)
    mag = np.abs(z)
    phase = np.degrees(np.angle(z))
    return np.column_stack([omega, mag, phase])


def synth_tafel(rng, slope_mV: float = 60.0):
    eta = np.linspace(0.05, 0.4, 40)
    log_j = (eta - 0.2) / (slope_mV / 1000.0)
    log_j += 0.05 * rng.normal(size=eta.size)
    return log_j, eta


def synth_band(rng, n_bands: int = 6):
    k = np.linspace(0, 1, 120)
    rows = [k]
    for b in range(n_bands):
        cos = np.cos(np.pi * k + rng.uniform(-0.5, 0.5))
        base = -2.5 + b * 1.1 + rng.uniform(-0.3, 0.3)
        rows.append(base + 0.9 * cos + 0.3 * rng.normal(size=k.size) * 0.2)
    return np.column_stack(rows)


def synth_dos(rng):
    E = np.linspace(-8, 6, 600)
    total = 1.2 * np.exp(-0.5 * ((E + 3) / 0.8) ** 2) \
          + 0.9 * np.exp(-0.5 * ((E + 1) / 0.6) ** 2) \
          + 0.4 * np.exp(-0.5 * ((E - 2.2) / 0.7) ** 2)
    total += 0.03 * rng.normal(size=E.size)
    s = 0.4 * np.exp(-0.5 * ((E + 3) / 0.8) ** 2)
    p = 0.8 * np.exp(-0.5 * ((E + 1) / 0.6) ** 2)
    d = 0.4 * np.exp(-0.5 * ((E - 2.2) / 0.7) ** 2)
    return pd.DataFrame({"E": E, "total": total, "s": s, "p": p, "d": d})


def synth_cohp(rng):
    E = np.linspace(-8, 5, 500)
    c = 0.8 * np.exp(-0.5 * ((E + 3) / 0.8) ** 2) \
       - 0.5 * np.exp(-0.5 * ((E - 1.5) / 0.7) ** 2)
    # integrated COHP (running sum as proxy)
    icohp = np.cumsum(c) * (E[1] - E[0])
    return pd.DataFrame({"E": E, "COHP": c, "ICOHP": icohp})


def synth_operando(rng, n_frames: int = 60, n_bins: int = 300,
                  evolve: str = "peak_shift"):
    x = np.linspace(20, 60, n_bins)
    y = np.linspace(0, 3600, n_frames)
    Z = np.zeros((n_frames, n_bins))
    for i, t in enumerate(y):
        if evolve == "peak_shift":
            c1 = 32 + 2.0 * (i / n_frames)
            c2 = 45 - 1.0 * (i / n_frames)
        elif evolve == "intensity":
            c1, c2 = 32, 45
        else:
            c1 = 32 + rng.normal(0, 0.1)
            c2 = 45 + rng.normal(0, 0.1)
        amp1 = 1.0 * (1 - i / (n_frames * 1.5))
        amp2 = 0.6 + 0.5 * (i / n_frames)
        Z[i] = amp1 * np.exp(-0.5 * ((x - c1) / 0.5) ** 2) \
             + amp2 * np.exp(-0.5 * ((x - c2) / 0.6) ** 2)
    Z += 0.03 * rng.normal(size=Z.shape)
    return Z, x, y


def synth_shap_dataset(rng, n: int = 400, n_feat: int = 10):
    feature_names = ["bandgap", "Ef", "workfn", "radius", "electroneg",
                    "coord_num", "n_atoms", "cell_vol", "density", "stability"][:n_feat]
    fv = rng.normal(0, 1, size=(n, n_feat))
    # Synthetic SHAP values correlated with feature value (to give nice beeswarm).
    sv = fv * rng.normal(0, 1, size=(n_feat,)) + 0.3 * rng.normal(size=(n, n_feat))
    # Boost importance of first few features.
    sv[:, 0] *= 3.0
    sv[:, 1] *= 2.2
    sv[:, 2] *= 1.6
    return sv, fv, feature_names


def pourbaix_data():
    # Simplified Fe-Pourbaix in the 0..14 pH / -1..2 V region.
    # Domains drawn so soluble Fe^2+/Fe^3+ stretch across acid pH, and
    # Fe2O3 fills the alkaline oxide region with enough room for labels.
    return [
        {"label": "Fe", "vertices": [(0, -1.0), (9, -1.0), (9, -0.62), (0, -0.45)], "color": "#8DA4BF"},
        {"label": r"Fe$^{2+}$", "vertices": [(0, -0.45), (9, -0.62), (8, 0.6), (0, 0.77)], "color": "#F6B26B"},
        {"label": r"Fe$^{3+}$", "vertices": [(0, 0.77), (8, 0.6), (6, 2.0), (0, 2.0)], "color": "#E06666"},
        {"label": r"Fe$_2$O$_3$", "vertices": [(9, -1.0), (14, -1.0), (14, 2.0), (6, 2.0), (8, 0.6), (9, -0.62)], "color": "#93C47D"},
    ]


def phase_diagram_data():
    return [
        {"label": "L (liquid)", "vertices": [(0, 900), (1, 900), (1, 650), (0.5, 520), (0, 650)], "color": "#E8B86A"},
        {"label": r"$\alpha$", "vertices": [(0, 650), (0.0, 25), (0.2, 25), (0.35, 520)], "color": "#7DA7BD"},
        {"label": r"$\beta$", "vertices": [(1, 650), (1, 25), (0.8, 25), (0.65, 520)], "color": "#B85E5E"},
        {"label": r"$\alpha + \beta$", "vertices": [(0.2, 25), (0.8, 25), (0.65, 520), (0.5, 520), (0.35, 520)], "color": "#C8B897"},
    ]


# ------------------------------------------------------------------
# Gallery scenarios — each numbered scenario saves 1+ figures
# ------------------------------------------------------------------

# ==================== XRD (30+) ====================
# XRD 001–008: each journal preset, 4 stacked patterns
for i, journal in enumerate(ALL_JOURNALS):
    idx = 1 + i

    def make(idx=idx, journal=journal):
        @scenario(idx, f"XRD stack journal={journal}", "xrd")
        def _():
            use_journal(journal)
            idxs = [0 + i * 3, 3 + i * 3, 6 + i * 3, 9 + i * 3]
            data = [load_xrd(xrd_patterns[k % len(xrd_patterns)]) for k in idxs]
            labels = [f"sample {k}" for k in idxs]
            fig, _ax = plot_xrd(data, labels=labels, offset=1.05, legend="inline", journal=journal)
            save_both(fig, f"{idx:03d}_xrd_stack_{journal}")
    make()

# XRD 009-014: 6 palettes applied to a 4-pattern stack (default journal)
for i, pal in enumerate(QUALITATIVE_PALETTES[:6]):
    idx = 9 + i

    def make(idx=idx, pal=pal):
        @scenario(idx, f"XRD 4 patterns palette={pal}", "xrd")
        def _():
            use_journal("nature")
            use_palette(pal)
            data = [load_xrd(xrd_patterns[k]) for k in (0, 5, 10, 15)]
            labels = [f"sample {k}" for k in (0, 5, 10, 15)]
            fig, _ = plot_xrd(data, labels=labels, offset=1.1, legend="outside")
            save_both(fig, f"{idx:03d}_xrd_palette_{pal.replace('-', '_')}")
    make()


@scenario(15, "XRD single pattern with hkl annotations", "xrd")
def _s15():
    use_journal("nature")
    x, y = load_xrd(xrd_patterns[0])
    order = np.argsort(y)[::-1]
    picked = []
    for k in order:
        p = float(x[k])
        if all(abs(p - pp) > 1.5 for pp in picked):
            picked.append(p)
        if len(picked) >= 5:
            break
    hkl = {round(p, 2): lab for p, lab in zip(picked, ["(110)", "(200)", "(211)", "(220)", "(310)"])}
    fig, _ = plot_xrd((x, y), hkl=hkl)
    save_both(fig, "015_xrd_hkl")


@scenario(16, "XRD single + zoom inset", "xrd")
def _s16():
    use_journal("science")
    x, y = load_xrd(xrd_patterns[1])
    fig, ax = plot_xrd((x, y))
    yn = (y - y.min()) / (y.max() - y.min() + 1e-12)
    peak_x = float(x[int(np.argmax(yn))])
    half = (x.max() - x.min()) / 10.0
    add_inset(ax, bounds=(0.55, 0.4, 0.42, 0.45),
              xlim=(peak_x - half, peak_x + half), ylim=(0.0, 1.05))
    save_both(fig, "016_xrd_zoom_inset")


@scenario(17, "XRD reversed-stack with outside legend", "xrd")
def _s17():
    use_journal("acs")
    data = [load_xrd(xrd_patterns[k]) for k in (0, 2, 4, 6)][::-1]
    labels = [f"sample {k}" for k in (6, 4, 2, 0)]
    fig, _ = plot_xrd(data, labels=labels, offset=1.2, legend="outside")
    save_both(fig, "017_xrd_reversed_stack")


@scenario(18, "XRD 6-pattern dense stack", "xrd")
def _s18():
    use_journal("default")
    use_palette("nature-cat")
    data = [load_xrd(xrd_patterns[k]) for k in range(0, 18, 3)]
    labels = [f"#{k}" for k in range(0, 18, 3)]
    fig, _ = plot_xrd(data, labels=labels, offset=1.05, legend="inline")
    save_both(fig, "018_xrd_dense_stack")


@scenario(19, "XRD Rietveld refinement demo", "xrd")
def _s19():
    use_journal("nature")
    rng = np.random.default_rng(3)
    x, y = load_xrd(xrd_patterns[0])
    # Crop for readability
    mask = (x >= 20) & (x <= 60)
    xc, yc = x[mask], y[mask]
    yn = (yc - yc.min()) / (yc.max() - yc.min() + 1e-12)
    # synthetic calc = smoothed obs + small shift
    from numpy.lib.stride_tricks import sliding_window_view
    def smooth(arr, k=11):
        pad = np.pad(arr, k // 2, mode="edge")
        return sliding_window_view(pad, k).mean(axis=1)
    ycalc = smooth(yn, 15)
    bkg = 0.05 + 0.02 * np.linspace(0, 1, xc.size)
    arr = np.column_stack([xc, yn + bkg, ycalc + bkg, bkg])
    peaks = [float(xc[int(k)]) for k in np.argsort(yn)[::-1][:8]]
    fig, _ = plot_rietveld(arr, hkl_positions=peaks, bragg_label="Bragg")
    save_both(fig, "019_xrd_rietveld")


@scenario(20, "XRD smart xlim demo (heterogeneous ranges)", "xrd")
def _s20():
    use_journal("default")
    data = [load_xrd(xrd_patterns[k]) for k in (0, 1, 2, 3)]
    fig, _ = plot_xrd(data, labels=[f"s{k}" for k in range(4)], offset=1.1, legend="outside")
    save_both(fig, "020_xrd_smart_xlim")


@scenario(21, "XRD explicit xlim (20-60)", "xrd")
def _s21():
    use_journal("default")
    data = [load_xrd(xrd_patterns[k]) for k in (0, 5)]
    fig, _ = plot_xrd(data, labels=["a", "b"], offset=1.1, xlim=(20, 60))
    save_both(fig, "021_xrd_xlim_2060")


@scenario(22, "XRD w/ palette crameri-batlow (gradient used on lines)", "xrd")
def _s22():
    use_journal("nature")
    use_palette("crameri-batlow")
    data = [load_xrd(xrd_patterns[k]) for k in range(0, 12, 2)]
    labels = [f"#{k}" for k in range(0, 12, 2)]
    fig, _ = plot_xrd(data, labels=labels, offset=1.0, legend="none")
    save_both(fig, "022_xrd_batlow_gradient")


@scenario(23, "XRD with no legend, minimal chrome", "xrd")
def _s23():
    use_journal("wiley")
    data = [load_xrd(xrd_patterns[k]) for k in range(0, 8, 2)]
    fig, _ = plot_xrd(data, offset=1.0, legend="none")
    save_both(fig, "023_xrd_minimal")


@scenario(24, "XRD single pattern small figure (IEEE)", "xrd")
def _s24():
    use_journal("ieee")
    x, y = load_xrd(xrd_patterns[0])
    fig, _ = plot_xrd((x, y))
    save_both(fig, "024_xrd_ieee_single")


@scenario(25, "XRD 6 patterns x 6 palettes grid", "xrd")
def _s25():
    use_journal("default")
    data = [load_xrd(xrd_patterns[k]) for k in range(0, 12, 2)]
    labels = [f"#{k}" for k in range(0, 12, 2)]
    pals = ["tol-bright", "carto-bold", "nord", "okabe-ito", "nature-cat", "science-cat"]
    fig, axes = plt.subplots(2, 3, figsize=(12, 7), constrained_layout=True)
    for ax, pal in zip(axes.flatten(), pals):
        use_palette(pal)
        plot_xrd(data, ax=ax, labels=labels, offset=1.0, legend="none")
        ax.set_title(pal, fontsize=8)
    save_both(fig, "025_xrd_palette_grid_6x")


# Round out XRD section to 30 figs.
@scenario(26, "XRD annotated peak list", "xrd")
def _s26():
    use_journal("nature")
    x, y = load_xrd(xrd_patterns[7])
    fig, _ = plot_xrd((x, y))
    save_both(fig, "026_xrd_annotated_peaks")


@scenario(27, "XRD 3 patterns science preset", "xrd")
def _s27():
    use_journal("science")
    use_palette("science-cat")
    data = [load_xrd(xrd_patterns[k]) for k in (20, 24, 28)]
    fig, _ = plot_xrd(data, labels=["A", "B", "C"], offset=1.1)
    save_both(fig, "027_xrd_science_3pat")


@scenario(28, "XRD 3 patterns Elsevier preset", "xrd")
def _s28():
    use_journal("elsevier")
    use_palette("bold-qualitative")
    data = [load_xrd(xrd_patterns[k]) for k in (30, 34, 38)]
    fig, _ = plot_xrd(data, labels=["alpha", "beta", "gamma"], offset=1.05)
    save_both(fig, "028_xrd_elsevier_3pat")


@scenario(29, "XRD 5 patterns RSC preset", "xrd")
def _s29():
    use_journal("rsc")
    data = [load_xrd(xrd_patterns[k]) for k in (40, 44, 48, 52, 56)]
    fig, _ = plot_xrd(data, labels=[f"x{k}" for k in range(5)], offset=1.05, legend="outside")
    save_both(fig, "029_xrd_rsc_5pat")


@scenario(30, "XRD normalize=False raw intensity", "xrd")
def _s30():
    use_journal("default")
    x, y = load_xrd(xrd_patterns[0])
    fig, _ = plot_xrd((x, y), normalize=False)
    save_both(fig, "030_xrd_raw_intensity")


# ==================== Raman (20+) ====================
@scenario(31, "Raman 5 spectra default", "raman")
def _s31():
    use_journal("default")
    chain = load_raman_chain(5)
    if len(chain) < 2:
        raise RuntimeError("need >=2 Raman spectra")
    data = [(x, y) for _, x, y in chain]
    labels = [lab for lab, _, _ in chain]
    fig, _ = plot_raman(data, labels=labels, offset=1.1, legend="inline")
    save_both(fig, "031_raman_default_5")


for i, journal in enumerate(["nature", "science", "acs", "rsc", "wiley", "elsevier", "ieee"]):
    idx = 32 + i

    def make(idx=idx, journal=journal):
        @scenario(idx, f"Raman 4 spectra journal={journal}", "raman")
        def _():
            use_journal(journal)
            chain = load_raman_chain(4)
            if len(chain) < 2:
                raise RuntimeError("need >=2 Raman spectra")
            data = [(x, y) for _, x, y in chain]
            labels = [lab for lab, _, _ in chain]
            fig, _ = plot_raman(data, labels=labels, offset=1.1, legend="inline", journal=journal)
            save_both(fig, f"{idx:03d}_raman_{journal}")
    make()


for i, pal in enumerate(["carto-bold", "tol-vibrant", "nature-cat", "science-cat",
                         "bold-qualitative", "okabe-ito"]):
    idx = 39 + i

    def make(idx=idx, pal=pal):
        @scenario(idx, f"Raman palette={pal}", "raman")
        def _():
            use_journal("nature")
            use_palette(pal)
            chain = load_raman_chain(5)
            if len(chain) < 2:
                raise RuntimeError("need >=2 Raman spectra")
            data = [(x, y) for _, x, y in chain]
            labels = [lab for lab, _, _ in chain]
            fig, _ = plot_raman(data, labels=labels, offset=1.0, legend="outside")
            save_both(fig, f"{idx:03d}_raman_palette_{pal.replace('-', '_')}")
    make()


@scenario(45, "Raman legend=best", "raman")
def _s45():
    use_journal("default")
    chain = load_raman_chain(4)
    data = [(x, y) for _, x, y in chain]
    labels = [lab for lab, _, _ in chain]
    fig, _ = plot_raman(data, labels=labels, offset=1.0, legend="best")
    save_both(fig, "045_raman_legend_best")


@scenario(46, "Raman legend=outside", "raman")
def _s46():
    use_journal("default")
    chain = load_raman_chain(4)
    data = [(x, y) for _, x, y in chain]
    labels = [lab for lab, _, _ in chain]
    fig, _ = plot_raman(data, labels=labels, offset=1.0, legend="outside")
    save_both(fig, "046_raman_legend_outside")


@scenario(47, "Raman legend=none", "raman")
def _s47():
    use_journal("default")
    chain = load_raman_chain(5)
    data = [(x, y) for _, x, y in chain]
    fig, _ = plot_raman(data, offset=1.0, legend="none")
    save_both(fig, "047_raman_legend_none")


@scenario(48, "Raman offset=0 overlay", "raman")
def _s48():
    use_journal("default")
    chain = load_raman_chain(3)
    data = [(x, y) for _, x, y in chain]
    labels = [lab for lab, _, _ in chain]
    fig, _ = plot_raman(data, labels=labels, offset=0.0, legend="best")
    save_both(fig, "048_raman_overlay_no_offset")


@scenario(49, "Raman big offset=2.0", "raman")
def _s49():
    use_journal("nature")
    use_palette("nature-cat")
    chain = load_raman_chain(4)
    data = [(x, y) for _, x, y in chain]
    labels = [lab for lab, _, _ in chain]
    fig, _ = plot_raman(data, labels=labels, offset=2.0, legend="inline")
    save_both(fig, "049_raman_big_offset")


@scenario(50, "Raman single spectrum (minimal)", "raman")
def _s50():
    use_journal("ieee")
    chain = load_raman_chain(1)
    if not chain:
        raise RuntimeError("no Raman spectra")
    _, x, y = chain[0]
    fig, _ = plot_raman((x, y))
    save_both(fig, "050_raman_single")


# ==================== XPS (5) ====================
rng = np.random.default_rng(42)
for i, journal in enumerate(["nature", "science", "acs", "wiley", "rsc"]):
    idx = 51 + i

    def make(idx=idx, journal=journal):
        @scenario(idx, f"XPS C1s journal={journal}", "xps")
        def _():
            use_journal(journal)
            r = np.random.default_rng(100 + idx)
            x, y = synth_xps(r)
            # Build synthetic fits
            from scipy.signal import argrelextrema  # noqa: F401  just used elsewhere
            fits = []
            for c, w, h, lab in zip((285.0, 286.5, 288.3), (0.8, 0.9, 1.1), (1.0, 0.55, 0.3),
                                     ("C-C", "C-O", "O=C-O")):
                fy = h * np.exp(-0.5 * ((x - c) / w) ** 2) + 0.05
                fits.append((x, fy, lab))
            baseline = (x, 0.05 + 0.005 * (x - x.min()))
            fig, _ = plot_xps((x, y), fits=fits, baseline=baseline, label="C1s raw")
            save_both(fig, f"{idx:03d}_xps_{journal}")
    make()


@scenario(56, "XPS single (no fits)", "xps")
def _s56():
    use_journal("default")
    r = np.random.default_rng(7)
    # Fe 2p3/2 ~711 eV, 2p1/2 ~724 eV (satellite ~719 eV)
    x, y = synth_xps(
        r,
        center_list=(711.0, 719.0, 724.0),
        widths=(1.4, 1.8, 1.6),
        heights=(1.0, 0.35, 0.55),
    )
    # Retarget x to Fe 2p region by shifting the default 282-292 range.
    x = np.linspace(705.0, 735.0, x.size)
    # Recompute y on the correct x-grid.
    y = np.zeros_like(x)
    for c, w, h in zip((711.0, 719.0, 724.0), (1.4, 1.8, 1.6), (1.0, 0.35, 0.55)):
        y += h * np.exp(-0.5 * ((x - c) / w) ** 2)
    y += 0.02 * r.normal(size=x.size) + 0.05 + 0.003 * (x - x.min())
    fig, _ = plot_xps((x, y), label="Fe 2p raw")
    save_both(fig, "056_xps_single_raw")


# ==================== FTIR (5) ====================
for i, journal in enumerate(["nature", "science", "acs", "wiley", "elsevier"]):
    idx = 57 + i

    def make(idx=idx, journal=journal):
        @scenario(idx, f"FTIR stack journal={journal}", "ftir")
        def _():
            use_journal(journal)
            use_palette("nature-cat")
            r = np.random.default_rng(200 + idx)
            items = []
            labels = []
            for k, lab in enumerate(["pristine", "calcined", "activated"]):
                wn, t = synth_ftir(r)
                t += 5 * k  # offset
                # Physical constraint: transmittance <= 100%.
                t = np.clip(t, None, 100.0)
                items.append((wn, t))
                labels.append(lab)
            fig, _ = plot_ftir(items, labels=labels, mode="transmittance", offset=0.0, legend="outside")
            save_both(fig, f"{idx:03d}_ftir_{journal}")
    make()


@scenario(62, "FTIR absorbance mode", "ftir")
def _s62():
    use_journal("default")
    r = np.random.default_rng(5)
    wn, t = synth_ftir(r)
    # Proper Beer-Lambert conversion: A = -log10(T/100). Baseline at 0.
    a = -np.log10(np.clip(t, 1e-3, None) / 100.0)
    a = np.clip(a, 0.0, None)
    fig, _ = plot_ftir((wn, a), mode="absorbance", labels=["Fe$_2$O$_3$"])
    save_both(fig, "062_ftir_absorbance")


# ==================== UV-Vis (6) ====================
for i, (journal, edge) in enumerate([("nature", 450), ("science", 520), ("acs", 380), ("wiley", 600),
                                     ("elsevier", 420), ("rsc", 480)]):
    idx = 63 + i

    def make(idx=idx, journal=journal, edge=edge):
        @scenario(idx, f"UVVis journal={journal} edge={edge}", "uvvis")
        def _():
            use_journal(journal)
            use_palette("carto-bold")
            r = np.random.default_rng(300 + idx)
            items = [synth_uvvis(r, edge_nm=edge + shift) for shift in (-30, 0, 30)]
            labels = [f"Eg~{1240/(edge + shift):.2f} eV" for shift in (-30, 0, 30)]
            fig, _ = plot_uvvis(items, labels=labels)
            save_both(fig, f"{idx:03d}_uvvis_{journal}")
    make()


@scenario(69, "UVVis Tauc direct", "uvvis")
def _s69():
    use_journal("nature")
    r = np.random.default_rng(9)
    items = [synth_uvvis(r, edge_nm=e) for e in (420, 500, 560)]
    labels = [f"sample{i+1}" for i in range(3)]
    fig, ax = plot_uvvis(items, labels=labels, tauc="direct")
    # Extrapolated tangent for the first sample: pick the steepest slope region
    # of (αhν)² and draw the line back to y=0 to show the bandgap intercept.
    wl, a = items[0]
    hv = 1239.841984 / wl
    y = (a * hv) ** 2
    # Sort by hv for a monotonic trace.
    order = np.argsort(hv)
    hv_s = hv[order]; y_s = y[order]
    dy = np.gradient(y_s, hv_s)
    # Restrict search to positive slope region (rising edge).
    mask = dy > 0
    if mask.any():
        imax = int(np.argmax(dy[mask]))
        idx = int(np.flatnonzero(mask)[imax])
        # Fit a line over a small window centered at idx.
        w = 5
        lo = max(idx - w, 0); hi = min(idx + w + 1, hv_s.size)
        m, b = np.polyfit(hv_s[lo:hi], y_s[lo:hi], 1)
        if m != 0:
            xint = -b / m
            # Draw extrapolation from x-intercept up to fitted region.
            xt = np.linspace(xint, hv_s[hi - 1], 50)
            ax.plot(xt, m * xt + b, color="#B0413E", lw=0.8, ls="--",
                    label=f"Eg ≈ {xint:.2f} eV")
            ax.axvline(xint, color="#B0413E", lw=0.5, ls=":")
            ax.annotate(f"Eg = {xint:.2f} eV", xy=(xint, 0),
                        xytext=(8, 12), textcoords="offset points",
                        fontsize=6, color="#B0413E")
            ax.legend(loc="best")
    save_both(fig, "069_uvvis_tauc_direct")


@scenario(70, "UVVis Tauc indirect", "uvvis")
def _s70():
    use_journal("nature")
    r = np.random.default_rng(9)
    items = [synth_uvvis(r, edge_nm=e) for e in (420, 500, 560)]
    fig, _ = plot_uvvis(items, labels=["a", "b", "c"], tauc="indirect")
    save_both(fig, "070_uvvis_tauc_indirect")


# ==================== PL (5) ====================
for i, journal in enumerate(["nature", "science", "acs", "wiley", "elsevier"]):
    idx = 71 + i

    def make(idx=idx, journal=journal):
        @scenario(idx, f"PL journal={journal}", "pl")
        def _():
            use_journal(journal)
            use_palette("science-cat")
            r = np.random.default_rng(400 + idx)
            items = [synth_pl(r, center_nm=c) for c in (580, 620, 660, 700)]
            labels = [f"{c} nm" for c in (580, 620, 660, 700)]
            fig, _ = plot_pl(items, labels=labels, offset=0.0, legend="inline")
            save_both(fig, f"{idx:03d}_pl_{journal}")
    make()


@scenario(76, "PL normalized", "pl")
def _s76():
    use_journal("default")
    r = np.random.default_rng(1)
    items = [synth_pl(r, center_nm=c, height=h) for c, h in [(580, 0.5), (620, 1.0), (660, 0.3)]]
    fig, _ = plot_pl(items, labels=["A", "B", "C"], normalize=True, offset=0.0, legend="best")
    save_both(fig, "076_pl_normalized")


# ==================== Thermal (4) ====================
for i, journal in enumerate(["nature", "science", "acs", "wiley"]):
    idx = 77 + i

    def make(idx=idx, journal=journal):
        @scenario(idx, f"Thermal TGA journal={journal}", "thermal")
        def _():
            use_journal(journal)
            r = np.random.default_rng(500 + idx)
            T, w = synth_tga(r)
            fig, _ = plot_thermal((T, w), mode="tga")
            save_both(fig, f"{idx:03d}_thermal_tga_{journal}")
    make()


@scenario(81, "Thermal DSC only", "thermal")
def _s81():
    use_journal("default")
    r = np.random.default_rng(2)
    T, y = synth_dsc(r)
    fig, _ = plot_thermal((T, y), mode="dsc")
    save_both(fig, "081_thermal_dsc")


@scenario(82, "Thermal TGA+DSC combined", "thermal")
def _s82():
    use_journal("nature")
    r = np.random.default_rng(3)
    T, w = synth_tga(r)
    Td, d = synth_dsc(r)
    fig, _ = plot_thermal((T, w), mode="both", dsc_data=(Td, d))
    save_both(fig, "082_thermal_tga_dsc")


# ==================== Operando (15+) ====================
# 83-92: all journals & cmaps
OP_CONFIGS = [
    ("crameri-batlow", "time (s)", r"2$\theta$ ($^{\circ}$)", "intensity"),
    ("crameri-roma", "potential (V)", r"cm$^{-1}$", "Raman intensity"),
    ("viridis", "time (s)", r"2$\theta$ ($^{\circ}$)", "log intensity"),
    ("inferno", "T (K)", "energy (eV)", r"$\mu$(E)"),
    ("magma", "cycle #", r"cm$^{-1}$", "intensity"),
    ("viridis6", "time (min)", r"2$\theta$ ($^{\circ}$)", "I"),
    ("editorial", "V vs RHE", r"cm$^{-1}$", "intensity"),
    ("plasma", "time (s)", "energy (eV)", "intensity"),
]
for i, (cmap, ylab, xlab, clab) in enumerate(OP_CONFIGS):
    idx = 83 + i

    def make(idx=idx, cmap=cmap, xlab=xlab, ylab=ylab, clab=clab):
        @scenario(idx, f"Operando cmap={cmap}", "operando")
        def _():
            use_journal("nature")
            r = np.random.default_rng(600 + idx)
            Z, x, y = synth_operando(r, evolve="peak_shift")
            fig, _ = plot_operando(Z, x=x, y=y, cmap=cmap, xlabel=xlab, ylabel=ylab, cbar_label=clab)
            save_both(fig, f"{idx:03d}_operando_cmap_{cmap.replace('-', '_')}")
    make()


@scenario(91, "Operando log-Z", "operando")
def _s91():
    use_journal("science")
    r = np.random.default_rng(11)
    Z, x, y = synth_operando(r)
    Z = np.abs(Z) + 1e-3
    fig, _ = plot_operando(Z, x=x, y=y, cmap="crameri-batlow", log_z=True,
                           xlabel=r"2$\theta$ ($^{\circ}$)", ylabel="time (s)",
                           cbar_label="log intensity")
    save_both(fig, "091_operando_log_z")


@scenario(92, "Operando with contour overlay", "operando")
def _s92():
    use_journal("nature")
    r = np.random.default_rng(12)
    Z, x, y = synth_operando(r)
    fig, _ = plot_operando(Z, x=x, y=y, cmap="crameri-roma",
                           contour_levels=[0.2, 0.4, 0.6, 0.8],
                           xlabel=r"2$\theta$ ($^{\circ}$)", ylabel="time (s)",
                           cbar_label="I (a.u.)")
    save_both(fig, "092_operando_contours")


@scenario(93, "Operando Gaussian-smoothed", "operando")
def _s93():
    use_journal("science")
    r = np.random.default_rng(13)
    Z, x, y = synth_operando(r)
    fig, _ = plot_operando(Z, x=x, y=y, cmap="viridis", smooth=1.5,
                           xlabel=r"2$\theta$ ($^{\circ}$)", ylabel="time (s)",
                           cbar_label="intensity")
    save_both(fig, "093_operando_smoothed")


@scenario(94, "Operando dual-panel with line cut", "operando")
def _s94():
    use_journal("nature")
    r = np.random.default_rng(14)
    Z, x, y = synth_operando(r)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True,
                                  gridspec_kw={"width_ratios": [3, 2]})
    plot_operando(Z, x=x, y=y, ax=ax1, cmap="crameri-batlow",
                  xlabel=r"2$\theta$ ($^{\circ}$)", ylabel="time (s)", cbar_label="I")
    for j, frac in enumerate([0.0, 0.5, 1.0]):
        k = min(int(frac * (Z.shape[0] - 1)), Z.shape[0] - 1)
        ax2.plot(x, Z[k] + j * 0.5, lw=1.0, label=f"t = {y[k]:.0f} s")
    ax2.set_xlabel(r"2$\theta$ ($^{\circ}$)")
    ax2.set_ylabel("intensity + offset")
    ax2.legend(loc="upper right", fontsize=7, frameon=False)
    save_both(fig, "094_operando_dual_panel")


@scenario(95, "Operando intensity-evolution (no shift)", "operando")
def _s95():
    use_journal("nature")
    r = np.random.default_rng(15)
    Z, x, y = synth_operando(r, evolve="intensity")
    fig, _ = plot_operando(Z, x=x, y=y, cmap="crameri-batlow",
                           xlabel=r"cm$^{-1}$", ylabel="V vs RHE", cbar_label="intensity")
    save_both(fig, "095_operando_intensity_evolve")


@scenario(96, "Operando hi-res grid", "operando")
def _s96():
    use_journal("science")
    r = np.random.default_rng(16)
    Z, x, y = synth_operando(r, n_frames=120, n_bins=500)
    fig, _ = plot_operando(Z, x=x, y=y, cmap="inferno", smooth=0.8,
                           xlabel=r"2$\theta$ ($^{\circ}$)", ylabel="time (s)",
                           cbar_label="intensity")
    save_both(fig, "096_operando_hires")


@scenario(97, "Operando with log + contour", "operando")
def _s97():
    use_journal("nature")
    r = np.random.default_rng(17)
    Z, x, y = synth_operando(r)
    Z = np.abs(Z) + 1e-2
    fig, _ = plot_operando(Z, x=x, y=y, cmap="crameri-batlow", log_z=True,
                           contour_levels=5,
                           xlabel=r"energy (eV)", ylabel="T (K)", cbar_label="log abs")
    save_both(fig, "097_operando_log_contour")


# ==================== Density (15+) ====================
# 98-103: KDE journals
for i, journal in enumerate(["default", "nature", "science", "acs", "wiley", "elsevier"]):
    idx = 98 + i

    def make(idx=idx, journal=journal):
        @scenario(idx, f"Density KDE journal={journal}", "density")
        def _():
            use_journal(journal)
            r = np.random.default_rng(700 + idx)
            x = r.normal(0, 1, 2000)
            y = 0.6 * x + r.normal(0, 0.5, 2000)
            fig, _ = plot_density(x, y, kind="kde", cmap="crameri-batlow", levels=12)
            save_both(fig, f"{idx:03d}_density_kde_{journal}")
    make()


# 104-109: cmap variations
for i, cmap in enumerate(["crameri-batlow", "crameri-roma", "viridis6", "viridis", "inferno", "magma"]):
    idx = 104 + i

    def make(idx=idx, cmap=cmap):
        @scenario(idx, f"Density cmap={cmap}", "density")
        def _():
            use_journal("nature")
            r = np.random.default_rng(800 + idx)
            x = np.concatenate([r.normal(-1.5, 0.5, 1000), r.normal(1.5, 0.5, 1000)])
            y = np.concatenate([r.normal(1.0, 0.5, 1000), r.normal(-1.0, 0.5, 1000)])
            fig, _ = plot_density(x, y, kind="kde", cmap=cmap, levels=15)
            save_both(fig, f"{idx:03d}_density_cmap_{cmap.replace('-', '_')}")
    make()


@scenario(110, "Density hex", "density")
def _s110():
    use_journal("nature")
    r = np.random.default_rng(41)
    x = r.normal(0, 1, 5000)
    y = 0.7 * x + r.normal(0, 0.4, 5000)
    fig, _ = plot_density(x, y, kind="hex", cmap="crameri-batlow", gridsize=40)
    save_both(fig, "110_density_hex")


@scenario(111, "Density hex high gridsize", "density")
def _s111():
    use_journal("science")
    r = np.random.default_rng(42)
    x = r.normal(0, 1, 5000)
    y = r.normal(0, 1, 5000) + 0.4 * x
    fig, _ = plot_density(x, y, kind="hex", cmap="viridis", gridsize=80)
    save_both(fig, "111_density_hex_fine")


@scenario(112, "Density scatter+KDE contours", "density")
def _s112():
    use_journal("nature")
    r = np.random.default_rng(43)
    x = r.normal(0, 1, 1500)
    y = 0.5 * x + r.normal(0, 0.5, 1500)
    fig, _ = plot_density(x, y, kind="scatter_kde", cmap="crameri-roma", levels=8)
    save_both(fig, "112_density_scatter_kde")


@scenario(113, "Density marginal histograms", "density")
def _s113():
    use_journal("nature")
    r = np.random.default_rng(44)
    x = r.normal(0, 1, 2000)
    y = 0.6 * x + r.normal(0, 0.5, 2000)
    fig, _ = plot_density(x, y, kind="kde", marginal=True, cmap="crameri-batlow")
    save_both(fig, "113_density_marginal")


@scenario(114, "Density from real XRD 2theta vs intensity", "density")
def _s114():
    use_journal("nature")
    # Gather (2theta, normalized intensity) points from many patterns
    rng = np.random.default_rng(45)
    tts, intens = [], []
    for p in xrd_patterns[:200]:
        try:
            x, y = load_xrd(p)
            yn = (y - y.min()) / (y.max() - y.min() + 1e-12)
            mask = yn > 0.05
            tts.extend(x[mask].tolist())
            intens.extend(yn[mask].tolist())
        except Exception:
            continue
    tts = np.asarray(tts)
    intens = np.asarray(intens)
    if tts.size > 30000:
        sel = rng.choice(tts.size, 30000, replace=False)
        tts = tts[sel]
        intens = intens[sel]
    fig, ax = plot_density(tts, intens, kind="hex", cmap="crameri-batlow", gridsize=50)
    ax.set_xlabel(r"2$\theta$ ($^{\circ}$)")
    ax.set_ylabel("normalized intensity")
    save_both(fig, "114_density_xrd_real")


@scenario(115, "Density Raman peak pos vs FWHM synthetic", "density")
def _s115():
    use_journal("science")
    r = np.random.default_rng(46)
    # peaks around 1350 (D) and 1580 (G)
    pos = np.concatenate([r.normal(1350, 25, 800), r.normal(1580, 18, 800)])
    fwhm = np.concatenate([r.normal(60, 12, 800), r.normal(30, 7, 800)])
    fig, ax = plot_density(pos, fwhm, kind="kde", cmap="crameri-roma", levels=12)
    ax.set_xlabel(r"peak position (cm$^{-1}$)")
    ax.set_ylabel(r"FWHM (cm$^{-1}$)")
    save_both(fig, "115_density_raman_fwhm")


# ==================== SHAP (15+) ====================
# 116-123: bar across journals / cmaps
for i, (journal, cmap) in enumerate([("nature", "crameri-roma"), ("science", "crameri-batlow"),
                                     ("acs", "viridis"), ("rsc", "inferno"),
                                     ("wiley", "plasma"), ("elsevier", "magma"),
                                     ("ieee", "crameri-roma"), ("default", "viridis")]):
    idx = 116 + i

    def make(idx=idx, journal=journal, cmap=cmap):
        @scenario(idx, f"SHAP bar journal={journal}", "shap")
        def _():
            use_journal(journal)
            r = np.random.default_rng(900 + idx)
            sv, fv, names = synth_shap_dataset(r)
            fig, _ = plot_shap(sv, names, feature_values=fv, kind="bar", max_features=10, cmap=cmap)
            save_both(fig, f"{idx:03d}_shap_bar_{journal}")
    make()


@scenario(124, "SHAP beeswarm crameri-roma", "shap")
def _s124():
    use_journal("nature")
    r = np.random.default_rng(60)
    sv, fv, names = synth_shap_dataset(r)
    fig, _ = plot_shap(sv, names, feature_values=fv, kind="beeswarm", cmap="crameri-roma")
    save_both(fig, "124_shap_beeswarm_roma")


@scenario(125, "SHAP beeswarm crameri-batlow", "shap")
def _s125():
    use_journal("science")
    r = np.random.default_rng(61)
    sv, fv, names = synth_shap_dataset(r)
    fig, _ = plot_shap(sv, names, feature_values=fv, kind="beeswarm", cmap="crameri-batlow")
    save_both(fig, "125_shap_beeswarm_batlow")


@scenario(126, "SHAP beeswarm viridis", "shap")
def _s126():
    use_journal("nature")
    r = np.random.default_rng(62)
    sv, fv, names = synth_shap_dataset(r)
    fig, _ = plot_shap(sv, names, feature_values=fv, kind="beeswarm", cmap="viridis")
    save_both(fig, "126_shap_beeswarm_viridis")


@scenario(127, "SHAP beeswarm max_features=5", "shap")
def _s127():
    use_journal("nature")
    r = np.random.default_rng(63)
    sv, fv, names = synth_shap_dataset(r)
    fig, _ = plot_shap(sv, names, feature_values=fv, kind="beeswarm", max_features=5,
                      cmap="crameri-roma")
    save_both(fig, "127_shap_beeswarm_top5")


@scenario(128, "SHAP dependence bandgap vs Ef", "shap")
def _s128():
    use_journal("nature")
    r = np.random.default_rng(64)
    sv, fv, names = synth_shap_dataset(r)
    fig, _ = plot_shap(sv, names, feature_values=fv, kind="dependence",
                      dependence_feature="bandgap", dependence_interaction="Ef",
                      cmap="crameri-roma")
    save_both(fig, "128_shap_dep_bandgap_Ef")


@scenario(129, "SHAP dependence electroneg vs radius", "shap")
def _s129():
    use_journal("science")
    r = np.random.default_rng(65)
    sv, fv, names = synth_shap_dataset(r)
    fig, _ = plot_shap(sv, names, feature_values=fv, kind="dependence",
                      dependence_feature="electroneg", dependence_interaction="radius",
                      cmap="crameri-batlow")
    save_both(fig, "129_shap_dep_electroneg_radius")


@scenario(130, "SHAP dependence no interaction", "shap")
def _s130():
    use_journal("nature")
    r = np.random.default_rng(66)
    sv, fv, names = synth_shap_dataset(r)
    fig, _ = plot_shap(sv, names, feature_values=fv, kind="dependence",
                      dependence_feature="coord_num")
    save_both(fig, "130_shap_dep_noInteract")


@scenario(131, "SHAP bar larger feat set", "shap")
def _s131():
    use_journal("nature")
    r = np.random.default_rng(67)
    sv, fv, names = synth_shap_dataset(r, n=600, n_feat=10)
    fig, _ = plot_shap(sv, names, feature_values=fv, kind="bar", max_features=8)
    save_both(fig, "131_shap_bar_top8")


# ==================== CV (5) ====================
for i, (journal, rate) in enumerate([("nature", 10), ("science", 25), ("acs", 50),
                                      ("wiley", 100), ("elsevier", 200)]):
    idx = 132 + i

    def make(idx=idx, journal=journal, rate=rate):
        @scenario(idx, f"CV journal={journal} rate={rate}", "cv")
        def _():
            use_journal(journal)
            use_palette("nature-cat")
            r = np.random.default_rng(1000 + idx)
            datalist, labels = [], []
            for k, s in enumerate([rate // 5, rate // 2, rate, rate * 2]):
                V, j = synth_cv(r, scan_rate=float(s))
                datalist.append((V, j))
                labels.append(f"{s} mV/s")
            fig, _ = plot_cv(datalist, labels=labels)
            save_both(fig, f"{idx:03d}_cv_{journal}")
    make()


# ==================== GCD (5) ====================
for i, journal in enumerate(["nature", "science", "acs", "wiley", "elsevier"]):
    idx = 137 + i

    def make(idx=idx, journal=journal):
        @scenario(idx, f"GCD journal={journal}", "gcd")
        def _():
            use_journal(journal)
            use_palette("carto-bold")
            r = np.random.default_rng(1100 + idx)
            datalist, labels = [], []
            for cap in (120, 140, 160, 180, 200):
                x, y = synth_gcd(r, capacity=float(cap))
                datalist.append((x, y))
                labels.append(f"{cap} mAh/g")
            fig, _ = plot_gcd(datalist, labels=labels)
            save_both(fig, f"{idx:03d}_gcd_{journal}")
    make()


# ==================== Cycle (5) ====================
for i, journal in enumerate(["nature", "science", "acs", "wiley", "elsevier"]):
    idx = 142 + i

    def make(idx=idx, journal=journal):
        @scenario(idx, f"Cycle performance journal={journal}", "cycle")
        def _():
            use_journal(journal)
            r = np.random.default_rng(1200 + idx)
            cycles = np.arange(1, 201)
            cap = 180 * np.exp(-cycles / 300.0) + 5 * r.normal(size=cycles.size)
            ce = 95 + 4.5 * (1 - np.exp(-cycles / 5)) + 0.3 * r.normal(size=cycles.size)
            ce = np.clip(ce, 90, 100)
            df = pd.DataFrame({"cycle": cycles, "capacity": cap, "CE": ce})
            fig, _ = plot_cycle(df)
            save_both(fig, f"{idx:03d}_cycle_{journal}")
    make()


# ==================== EIS (5) ====================
for i, journal in enumerate(["nature", "science", "acs", "wiley", "elsevier"]):
    idx = 147 + i

    def make(idx=idx, journal=journal):
        @scenario(idx, f"EIS journal={journal}", "eis")
        def _():
            use_journal(journal)
            use_palette("okabe-ito")
            r = np.random.default_rng(1300 + idx)
            datalist, labels = [], []
            for Rct in (30, 50, 80, 120):
                zr, mi = synth_eis(r, Rct=float(Rct))
                datalist.append((zr, mi))
                labels.append(f"Rct={Rct}")
            fig, _ = plot_eis(datalist, labels=labels)
            save_both(fig, f"{idx:03d}_eis_{journal}")
    make()


# ==================== Bode (4) ====================
for i, journal in enumerate(["nature", "science", "acs", "wiley"]):
    idx = 152 + i

    def make(idx=idx, journal=journal):
        @scenario(idx, f"Bode journal={journal}", "bode")
        def _():
            use_journal(journal)
            r = np.random.default_rng(1400 + idx)
            arr = synth_bode(r)
            fig, _ = plot_bode(arr)
            save_both(fig, f"{idx:03d}_bode_{journal}")
    make()


# ==================== Tafel (4) ====================
for i, (journal, slope) in enumerate([("nature", 60), ("science", 80), ("acs", 110), ("wiley", 45)]):
    idx = 156 + i

    def make(idx=idx, journal=journal, slope=slope):
        @scenario(idx, f"Tafel journal={journal} slope={slope}", "tafel")
        def _():
            use_journal(journal)
            r = np.random.default_rng(1500 + idx)
            logj, eta = synth_tafel(r, slope_mV=float(slope))
            fig, _ = plot_tafel(np.column_stack([logj, eta]),
                               fit_range=(0.1, 0.3), label=f"{slope} mV/dec catalyst")
            save_both(fig, f"{idx:03d}_tafel_{journal}")
    make()


# ==================== Band (4) ====================
for i, journal in enumerate(["nature", "science", "acs", "wiley"]):
    idx = 160 + i

    def make(idx=idx, journal=journal):
        @scenario(idx, f"Band structure journal={journal}", "band")
        def _():
            use_journal(journal)
            r = np.random.default_rng(1600 + idx)
            arr = synth_band(r, n_bands=8)
            kpoints = [(r"$\Gamma$", 0.0), ("X", 0.25), ("M", 0.5), ("R", 0.75), (r"$\Gamma$", 1.0)]
            fig, _ = plot_band(arr, kpoints=kpoints, ylim=(-4, 4), color="#1f77b4")
            save_both(fig, f"{idx:03d}_band_{journal}")
    make()


# ==================== DOS (4) ====================
for i, (journal, orient) in enumerate([("nature", "horizontal"), ("science", "horizontal"),
                                        ("acs", "vertical"), ("wiley", "vertical")]):
    idx = 164 + i

    def make(idx=idx, journal=journal, orient=orient):
        @scenario(idx, f"DOS journal={journal} orient={orient}", "dos")
        def _():
            use_journal(journal)
            use_palette("nature-cat")
            r = np.random.default_rng(1700 + idx)
            df = synth_dos(r)
            fig, _ = plot_dos(df, orientation=orient)
            save_both(fig, f"{idx:03d}_dos_{journal}_{orient}")
    make()


# ==================== COHP (3) ====================
for i, journal in enumerate(["nature", "science", "acs"]):
    idx = 168 + i

    def make(idx=idx, journal=journal):
        @scenario(idx, f"COHP journal={journal}", "cohp")
        def _():
            use_journal(journal)
            r = np.random.default_rng(1800 + idx)
            df = synth_cohp(r)
            fig, _ = plot_cohp(df, show_icohp=True)
            save_both(fig, f"{idx:03d}_cohp_{journal}")
    make()


# ==================== Pourbaix (2) ====================
@scenario(171, "Pourbaix Fe", "pourbaix")
def _s171():
    use_journal("nature")
    fig, _ = plot_pourbaix(pourbaix_data(), ph_range=(0, 14), e_range=(-1, 2))
    save_both(fig, "171_pourbaix_Fe")


@scenario(172, "Pourbaix Fe science preset", "pourbaix")
def _s172():
    use_journal("science")
    fig, _ = plot_pourbaix(pourbaix_data(), ph_range=(0, 14), e_range=(-1, 2),
                          water_stability=True)
    save_both(fig, "172_pourbaix_Fe_science")


# ==================== Phase diagram (2) ====================
@scenario(173, "Phase diagram binary", "phase")
def _s173():
    use_journal("nature")
    fig, _ = plot_phase_diagram(phase_diagram_data(),
                                invariants=[(0.5, 520, "eutectic")])
    save_both(fig, "173_phase_binary")


@scenario(174, "Phase diagram Wiley", "phase")
def _s174():
    use_journal("wiley")
    fig, _ = plot_phase_diagram(phase_diagram_data())
    save_both(fig, "174_phase_wiley")


# ==================== General — bar (6) ====================
@scenario(175, "Bar grouped cathode capacities", "bar")
def _s175():
    use_journal("nature")
    use_palette("nature-cat")
    cats = ["LFP", "NMC111", "NMC622", "NMC811", "LNMO"]
    df = pd.DataFrame({
        "material": cats,
        "0.1C": [160, 165, 180, 195, 140],
        "1C":   [140, 150, 165, 175, 125],
        "5C":   [100, 120, 135, 150, 95],
    })
    fig, _ = plot_bar(df, xlabel="Cathode", ylabel="Capacity (mAh/g)")
    save_both(fig, "175_bar_cathode_grouped")


@scenario(176, "Bar stacked composition", "bar")
def _s176():
    use_journal("science")
    use_palette("science-cat")
    df = pd.DataFrame({
        "material": ["A", "B", "C", "D", "E"],
        "Ni": [60, 50, 30, 20, 80],
        "Co": [20, 30, 30, 20, 10],
        "Mn": [20, 20, 40, 60, 10],
    })
    fig, _ = plot_bar(df, stacked=True, ylabel="Composition (%)", xlabel="Sample")
    save_both(fig, "176_bar_stacked_composition")


@scenario(177, "Bar elemental abundance (okabe-ito)", "bar")
def _s177():
    use_journal("default")
    use_palette("okabe-ito")
    df = pd.DataFrame({
        "element": ["H", "C", "N", "O", "Si", "Fe", "Al"],
        "abundance": [1, 20, 3, 46, 27, 5, 8],
    })
    fig, _ = plot_bar(df, ylabel="Mass %", xlabel="Element")
    save_both(fig, "177_bar_abundance")


@scenario(178, "Bar journals (acs)", "bar")
def _s178():
    use_journal("acs")
    use_palette("carto-bold")
    df = pd.DataFrame({
        "catalyst": ["Pt/C", "Pd/C", "Ru/C", "Ir/C", "Ni/C"],
        "onset":    [1.23, 1.35, 1.42, 1.40, 1.52],
    })
    fig, _ = plot_bar(df, ylabel="Onset (V)", xlabel="Catalyst")
    save_both(fig, "178_bar_onset")


@scenario(179, "Bar stacked (3 products)", "bar")
def _s179():
    use_journal("nature")
    df = pd.DataFrame({
        "V": [0.0, -0.2, -0.4, -0.6, -0.8],
        "CO": [60, 50, 40, 30, 20],
        "H2": [30, 35, 40, 45, 55],
        "HCOOH": [10, 15, 20, 25, 25],
    })
    fig, _ = plot_bar(df, stacked=True, ylabel="FE (%)", xlabel="E (V)")
    save_both(fig, "179_bar_faradaic")


@scenario(180, "Bar wiley preset", "bar")
def _s180():
    use_journal("wiley")
    df = pd.DataFrame({
        "zone": ["anode", "bulk", "cathode"],
        "conductivity": [1e-3, 1e-6, 1e-4],
    })
    fig, _ = plot_bar(df, ylabel="sigma (S/cm)")
    save_both(fig, "180_bar_wiley")


# ==================== General — scatter (5) ====================
@scenario(181, "Scatter capacity vs voltage", "scatter")
def _s181():
    use_journal("nature")
    r = np.random.default_rng(80)
    V = np.linspace(3.2, 4.3, 24)
    cap = 190 - 80 * (V - 3.2) / 1.1 + r.normal(0, 5, 24)
    err = np.abs(r.normal(5, 1.5, 24))
    df = pd.DataFrame({"V": V, "capacity": cap, "err": err})
    fig, _ = plot_scatter(df, fit=True, xlabel="Upper cutoff (V)", ylabel="Capacity (mAh/g)")
    save_both(fig, "181_scatter_capacity_V")


@scenario(182, "Scatter conductivity doping", "scatter")
def _s182():
    use_journal("science")
    r = np.random.default_rng(81)
    x = np.linspace(0.5, 10, 18)
    y = 2 + 1.3 * x + r.normal(0, 1.2, 18)
    fig, _ = plot_scatter(pd.DataFrame({"dope": x, "sigma": y}), fit=True,
                         xlabel="Doping (at.%)", ylabel=r"$\sigma$ (S/cm)")
    save_both(fig, "182_scatter_cond_doping")


@scenario(183, "Scatter activation energy vs radius", "scatter")
def _s183():
    use_journal("acs")
    r = np.random.default_rng(82)
    x = r.uniform(0.5, 1.5, 30)
    y = 1.2 - 0.5 * x + r.normal(0, 0.08, 30)
    fig, _ = plot_scatter(pd.DataFrame({"radius": x, "Ea": y}), fit=True,
                         xlabel="Ionic radius (Å)", ylabel="Ea (eV)")
    save_both(fig, "183_scatter_Ea_radius")


@scenario(184, "Scatter binding vs descriptor", "scatter")
def _s184():
    use_journal("nature")
    r = np.random.default_rng(83)
    x = np.linspace(-1.5, 0.5, 20)
    y = (x - (-0.5)) ** 2 + r.normal(0, 0.04, 20)
    fig, _ = plot_scatter(pd.DataFrame({"E_OH": x, "overpotential": y}),
                         xlabel=r"$\Delta G_{OH}$ (eV)", ylabel=r"$\eta$ (V)")
    save_both(fig, "184_scatter_volcano")


@scenario(185, "Scatter no fit minimal", "scatter")
def _s185():
    use_journal("default")
    r = np.random.default_rng(84)
    x = r.uniform(0, 10, 40)
    y = r.uniform(0, 5, 40)
    fig, _ = plot_scatter(pd.DataFrame({"x": x, "y": y}), xlabel="x", ylabel="y")
    save_both(fig, "185_scatter_random")


# ==================== General — line (5) ====================
@scenario(186, "Line multi-series (4 curves)", "line")
def _s186():
    use_journal("nature")
    use_palette("nature-cat")
    x = np.linspace(0, 2 * np.pi, 200)
    df = pd.DataFrame({"x": x, "sin": np.sin(x), "cos": np.cos(x),
                       "sin2x": np.sin(2 * x), "cos/2": np.cos(x) / 2})
    fig, _ = plot_line(df, xlabel="x", ylabel="y")
    save_both(fig, "186_line_multi")


@scenario(187, "Line twin axis", "line")
def _s187():
    use_journal("science")
    x = np.linspace(0, 10, 100)
    df = pd.DataFrame({"x": x, "left1": np.sin(x), "left2": np.cos(x), "right1": 50 + 10 * x})
    fig, _ = plot_line(df, twin_cols=["right1"], xlabel="x", ylabel="left", ylabel_right="right")
    save_both(fig, "187_line_twin")


@scenario(188, "Line ACS preset 3 curves", "line")
def _s188():
    use_journal("acs")
    use_palette("carto-bold")
    x = np.linspace(0, 10, 100)
    df = pd.DataFrame({"t": x, "A": np.exp(-x/2), "B": np.exp(-x/5), "C": np.exp(-x/8)})
    fig, _ = plot_line(df, xlabel="time (s)", ylabel="signal")
    save_both(fig, "188_line_acs")


@scenario(189, "Line multi-curve with shaded region (manual)", "line")
def _s189():
    use_journal("nature")
    use_palette("nature-cat")
    x = np.linspace(0, 10, 200)
    y1 = np.sin(x) + 0.1 * np.random.default_rng(1).normal(size=x.size)
    y2 = np.cos(x) + 0.1 * np.random.default_rng(2).normal(size=x.size)
    fig, ax = plt.subplots(figsize=(6, 4), constrained_layout=True)
    ax.plot(x, y1, label="y1")
    ax.plot(x, y2, label="y2")
    ax.fill_between(x, y1 - 0.2, y1 + 0.2, alpha=0.25)
    ax.fill_between(x, y2 - 0.2, y2 + 0.2, alpha=0.25)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend(loc="best")
    save_both(fig, "189_line_shaded")


@scenario(190, "Line log-y decay", "line")
def _s190():
    use_journal("default")
    x = np.linspace(0, 10, 200)
    df = pd.DataFrame({"t": x, "exp1": np.exp(-x), "exp5": np.exp(-x/5), "exp10": np.exp(-x/10)})
    fig, ax = plot_line(df, xlabel="t", ylabel="signal")
    ax.set_yscale("log")
    save_both(fig, "190_line_log_y")


# ==================== General — heatmap (5) ====================
@scenario(191, "Heatmap 10x10 correlation diverging", "heatmap")
def _s191():
    use_journal("nature")
    r = np.random.default_rng(90)
    elements = ["Li", "Na", "K", "Mg", "Ca", "Ti", "Fe", "Co", "Ni", "Cu"]
    M = r.normal(0, 1, (10, 10))
    M = (M + M.T) / 2
    M = M / (np.max(np.abs(M)) + 1e-9)
    np.fill_diagonal(M, 1.0)
    df = pd.DataFrame(M, index=elements, columns=elements)
    fig, _ = plot_heatmap(df, annot=True, cbar_label="Pearson r", cmap="RdBu_r", center=0)
    save_both(fig, "191_heatmap_corr_diverging")


@scenario(192, "Heatmap 20x20 sequential viridis", "heatmap")
def _s192():
    use_journal("science")
    r = np.random.default_rng(91)
    m = r.uniform(0, 1, (20, 20))
    df = pd.DataFrame(m)
    fig, _ = plot_heatmap(df, cmap="viridis", cbar_label="intensity")
    save_both(fig, "192_heatmap_viridis")


@scenario(193, "Heatmap contour mode", "heatmap")
def _s193():
    use_journal("nature")
    x, y = np.meshgrid(np.linspace(-3, 3, 80), np.linspace(-3, 3, 80))
    z = np.exp(-(x ** 2 + y ** 2) / 2) - np.exp(-((x - 1) ** 2 + (y + 1) ** 2) / 0.8)
    df = pd.DataFrame(z)
    fig, _ = plot_heatmap(df, mode="contourf", cmap="RdBu_r", center=0, cbar_label="f(x,y)")
    save_both(fig, "193_heatmap_contourf")


@scenario(194, "Heatmap contour lines", "heatmap")
def _s194():
    use_journal("nature")
    x, y = np.meshgrid(np.linspace(-2, 2, 60), np.linspace(-2, 2, 60))
    z = np.sin(x) * np.cos(y)
    fig, _ = plot_heatmap(pd.DataFrame(z), mode="contour", cmap="viridis")
    save_both(fig, "194_heatmap_contour")


@scenario(195, "Heatmap viridis 15x15", "heatmap")
def _s195():
    use_journal("science")
    r = np.random.default_rng(93)
    m = np.abs(r.normal(0, 1, (15, 15)))
    fig, _ = plot_heatmap(pd.DataFrame(m), cmap="cividis", cbar_label="abs val")
    save_both(fig, "195_heatmap_batlow")


# ==================== General — box / violin (5) ====================
@scenario(196, "Box grain size 3 routes", "box")
def _s196():
    use_journal("nature")
    r = np.random.default_rng(94)
    df = pd.DataFrame({
        "Ball-milled": r.normal(50, 10, 80),
        "SPS": r.normal(80, 15, 80),
        "Furnace": r.normal(120, 25, 80),
    })
    fig, _ = plot_box_violin(df, kind="box", xlabel="route", ylabel="grain size (nm)")
    save_both(fig, "196_box_grain")


@scenario(197, "Violin capacity 4 cathodes", "box")
def _s197():
    use_journal("science")
    r = np.random.default_rng(95)
    df = pd.DataFrame({
        "LFP": r.normal(140, 8, 60),
        "NMC622": r.normal(170, 10, 60),
        "NMC811": r.normal(195, 12, 60),
        "LNMO": r.normal(135, 9, 60),
    })
    fig, _ = plot_box_violin(df, kind="violin", ylabel="Capacity (mAh/g)")
    save_both(fig, "197_violin_cathodes")


@scenario(198, "Violin stability", "box")
def _s198():
    use_journal("nature")
    r = np.random.default_rng(96)
    df = pd.DataFrame({
        "as-made": r.normal(85, 5, 100),
        "aged-1wk": r.normal(78, 8, 100),
        "aged-1mo": r.normal(65, 12, 100),
    })
    fig, _ = plot_box_violin(df, kind="violin", ylabel="Capacity retention (%)")
    save_both(fig, "198_violin_stability")


@scenario(199, "Box 5 reactors", "box")
def _s199():
    use_journal("wiley")
    r = np.random.default_rng(97)
    df = pd.DataFrame({f"reactor {i}": r.normal(80 + i * 2, 6, 50) for i in range(5)})
    fig, _ = plot_box_violin(df, kind="box", ylabel="Yield (%)")
    save_both(fig, "199_box_reactors")


@scenario(200, "Violin 6 catalysts", "box")
def _s200():
    use_journal("acs")
    r = np.random.default_rng(98)
    df = pd.DataFrame({f"cat{i+1}": r.normal(0.3 + 0.05 * i, 0.04, 80) for i in range(6)})
    fig, _ = plot_box_violin(df, kind="violin", ylabel=r"$\eta_{10}$ (V)")
    save_both(fig, "200_violin_catalysts")


# ==================== General — radar (3) ====================
@scenario(201, "Radar cathode perf", "radar")
def _s201():
    use_journal("nature")
    use_palette("nature-cat")
    axes_ = ["Capacity", "Rate", "Cycle", "Cost", "Safety"]
    data = {
        "LFP": [140, 80, 95, 90, 98],
        "NMC622": [175, 90, 75, 60, 70],
        "NMC811": [195, 92, 65, 55, 60],
    }
    fig = plt.figure(figsize=(5.5, 5), constrained_layout=True)
    ax = fig.add_subplot(111, projection="polar")
    plot_radar(data, ax=ax, categories=axes_)
    save_both(fig, "201_radar_cathodes")


@scenario(202, "Radar catalyst scorecard", "radar")
def _s202():
    use_journal("science")
    use_palette("science-cat")
    axes_ = ["Activity", "Stability", "Selectivity", "Abundance", "Cost^-1"]
    data = {
        "Pt": [95, 90, 85, 10, 20],
        "Ni": [60, 70, 65, 95, 85],
        "Co": [75, 75, 70, 60, 60],
    }
    fig = plt.figure(figsize=(5.5, 5), constrained_layout=True)
    ax = fig.add_subplot(111, projection="polar")
    plot_radar(data, ax=ax, categories=axes_)
    save_both(fig, "202_radar_catalysts")


@scenario(203, "Radar 6 axes 4 samples", "radar")
def _s203():
    use_journal("nature")
    axes_ = ["A", "B", "C", "D", "E", "F"]
    data = {
        "s1": [3, 4, 5, 2, 4, 3],
        "s2": [5, 3, 2, 5, 4, 2],
        "s3": [4, 5, 3, 3, 5, 4],
        "s4": [2, 3, 4, 5, 2, 5],
    }
    fig = plt.figure(figsize=(5.5, 5), constrained_layout=True)
    ax = fig.add_subplot(111, projection="polar")
    plot_radar(data, ax=ax, categories=axes_)
    save_both(fig, "203_radar_6axes")


# ==================== Palette showcase (14) ====================
# one scatter per palette
for i, pal in enumerate(ALL_PALETTES):
    idx = 204 + i

    def make(idx=idx, pal=pal):
        @scenario(idx, f"Palette showcase {pal}", "palette")
        def _():
            use_journal("nature")
            try:
                use_palette(pal)
            except Exception:
                pass
            r = np.random.default_rng(2000 + idx)
            fig, ax = plt.subplots(figsize=(5, 4), constrained_layout=True)
            n_groups = 6
            for k in range(n_groups):
                cx, cy = r.uniform(-2, 2), r.uniform(-2, 2)
                gx = r.normal(cx, 0.3, 25)
                gy = r.normal(cy, 0.3, 25)
                ax.scatter(gx, gy, label=f"g{k+1}", s=16, alpha=0.85)
            ax.set_xlabel("PC1")
            ax.set_ylabel("PC2")
            ax.set_title(f"palette: {pal}", fontsize=9)
            ax.legend(loc="best", fontsize=6, frameon=False, ncols=2)
            save_both(fig, f"{idx:03d}_palette_{pal.replace('-', '_')}")
    make()


# ==================== Journal showcase grid (2) ====================
@scenario(218, "Palette grid 6-panel", "palette")
def _s218():
    use_journal("default")
    r = np.random.default_rng(500)
    pals = ["tol-bright", "carto-bold", "nord", "okabe-ito", "nature-cat", "science-cat"]
    fig, axes = plt.subplots(2, 3, figsize=(12, 7.2), constrained_layout=True)
    for ax, pal in zip(axes.flatten(), pals):
        use_palette(pal)
        for k in range(5):
            x = np.linspace(0, 10, 200)
            ax.plot(x, np.sin(x + k * 0.4) + k * 0.2, label=f"s{k}")
        ax.set_title(pal, fontsize=8)
        ax.legend(loc="upper right", fontsize=6, frameon=False)
    _tag_panels(axes)
    save_both(fig, "218_palette_grid")


@scenario(219, "Journal 2x4 line grid", "journal")
def _s219():
    r = np.random.default_rng(501)
    journals = ALL_JOURNALS
    fig, axes = plt.subplots(2, 4, figsize=(14, 7.2), constrained_layout=True)
    for ax, j in zip(axes.flatten(), journals):
        use_journal(j)
        x = np.linspace(0, 10, 200)
        for k in range(4):
            ax.plot(x, np.sin(x + k * 0.4) + k * 0.2, label=f"s{k+1}")
        ax.set_title(j, fontsize=9)
        ax.legend(loc="upper right", fontsize=6, frameon=False)
    _tag_panels(axes)
    save_both(fig, "219_journal_grid")


# ==================== Multi-panel compositions (10) ====================
@scenario(220, "Multi: XRD+Raman+UVVis+PL", "multi")
def _s220():
    use_journal("nature")
    use_palette("nature-cat")
    fig, axes = make_subplots(2, 2, journal="nature", figsize=(10, 7.5), constrained_layout=True)
    x, y = load_xrd(xrd_patterns[0])
    plot_xrd((x, y), ax=axes[0, 0])
    axes[0, 0].set_title("XRD", fontsize=8)
    chain = load_raman_chain(2)
    plot_raman([(xx, yy) for _, xx, yy in chain], ax=axes[0, 1],
               labels=[lab for lab, _, _ in chain], offset=1.0, legend="inline")
    axes[0, 1].set_title("Raman", fontsize=8)
    r = np.random.default_rng(11)
    items = [synth_uvvis(r, edge_nm=e) for e in (420, 500)]
    plot_uvvis(items, ax=axes[1, 0], labels=[r"BiVO$_4$", r"WO$_3$"])
    axes[1, 0].set_title("UV-Vis", fontsize=8)
    items_pl = [synth_pl(r, center_nm=c) for c in (580, 620)]
    plot_pl(items_pl, ax=axes[1, 1], labels=[r"BiVO$_4$", r"WO$_3$"], legend="best")
    axes[1, 1].set_title("PL", fontsize=8)
    _tag_panels(axes)
    save_both(fig, "220_multi_characterization")


@scenario(221, "Multi: Band + DOS", "multi")
def _s221():
    use_journal("nature")
    fig, axes = plt.subplots(1, 2, figsize=(10, 5.2), constrained_layout=True,
                            gridspec_kw={"width_ratios": [2, 1]})
    r = np.random.default_rng(12)
    arr = synth_band(r, n_bands=8)
    kpoints = [(r"$\Gamma$", 0.0), ("X", 0.5), (r"$\Gamma$", 1.0)]
    plot_band(arr, ax=axes[0], kpoints=kpoints, ylim=(-4, 4))
    df = synth_dos(r)
    plot_dos(df, ax=axes[1], orientation="vertical")
    axes[1].set_ylim(-4, 4)
    supertitle(fig, "Band + projected DOS", y=1.02)
    _tag_panels(axes)
    save_both(fig, "221_multi_band_dos")


@scenario(222, "Multi: CV+GCD+Cycle+EIS electrochem", "multi")
def _s222():
    use_journal("nature")
    use_palette("nature-cat")
    fig, axes = make_subplots(2, 2, journal="nature", figsize=(10, 7.5),
                             constrained_layout=True)
    r = np.random.default_rng(13)
    cv_list = [synth_cv(r, scan_rate=s) for s in (10, 50, 100)]
    plot_cv(cv_list, ax=axes[0, 0], labels=["10", "50", "100 mV/s"])
    axes[0, 0].set_title("CV", fontsize=8)
    gcd_list = [synth_gcd(r, capacity=c) for c in (140, 160, 180)]
    plot_gcd(gcd_list, ax=axes[0, 1], labels=["140", "160", "180"])
    axes[0, 1].set_title("GCD", fontsize=8)
    cycles = np.arange(1, 201)
    cap = 180 * np.exp(-cycles / 400.0) + 5 * r.normal(size=cycles.size)
    ce = 95 + 4.5 * (1 - np.exp(-cycles / 5))
    plot_cycle(pd.DataFrame({"c": cycles, "Q": cap, "CE": ce}), ax=axes[1, 0])
    axes[1, 0].set_title("Cycle", fontsize=8)
    eis_list = [synth_eis(r, Rct=rc) for rc in (30, 80)]
    plot_eis(eis_list, ax=axes[1, 1], labels=["fresh", "aged"])
    axes[1, 1].set_title("EIS", fontsize=8)
    _tag_panels(axes)
    save_both(fig, "222_multi_electrochem")


@scenario(223, "Multi: COHP + DOS", "multi")
def _s223():
    use_journal("science")
    fig, axes = plt.subplots(1, 2, figsize=(10, 5.2), constrained_layout=True)
    r = np.random.default_rng(14)
    plot_cohp(synth_cohp(r), ax=axes[0])
    plot_dos(synth_dos(r), ax=axes[1], orientation="horizontal")
    _tag_panels(axes)
    save_both(fig, "223_multi_cohp_dos")


@scenario(224, "Multi: Operando + line-cut", "multi")
def _s224():
    use_journal("nature")
    r = np.random.default_rng(15)
    Z, x, y = synth_operando(r)
    fig, axes = plt.subplots(2, 1, figsize=(7, 6), constrained_layout=True,
                            gridspec_kw={"height_ratios": [3, 1]})
    plot_operando(Z, x=x, y=y, ax=axes[0], cmap="crameri-batlow",
                 xlabel="", ylabel="time (s)", cbar_label="I")
    axes[1].plot(x, Z[0], label=f"t={y[0]:.0f}", lw=1.0)
    axes[1].plot(x, Z[Z.shape[0]//2], label=f"t={y[Z.shape[0]//2]:.0f}", lw=1.0)
    axes[1].plot(x, Z[-1], label=f"t={y[-1]:.0f}", lw=1.0)
    axes[1].set_xlabel(r"2$\theta$ ($^{\circ}$)")
    axes[1].set_ylabel("I")
    axes[1].legend(loc="upper right", fontsize=7, frameon=False)
    save_both(fig, "224_multi_operando_cut")


@scenario(225, "Multi: SHAP bar + beeswarm", "multi")
def _s225():
    use_journal("nature")
    r = np.random.default_rng(16)
    sv, fv, names = synth_shap_dataset(r)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), constrained_layout=True)
    plot_shap(sv, names, feature_values=fv, kind="bar", ax=axes[0], max_features=8)
    plot_shap(sv, names, feature_values=fv, kind="beeswarm", ax=axes[1],
              max_features=8, cmap="crameri-roma")
    _tag_panels(axes)
    save_both(fig, "225_multi_shap_bar_beeswarm")


@scenario(226, "Multi: 3x3 general plots", "multi")
def _s226():
    use_journal("nature")
    use_palette("nature-cat")
    fig, axes = plt.subplots(3, 3, figsize=(13, 10), constrained_layout=True)
    r = np.random.default_rng(17)
    # (0,0) XRD
    x, y = load_xrd(xrd_patterns[0])
    plot_xrd((x, y), ax=axes[0, 0])
    # (0,1) Raman
    chain = load_raman_chain(3)
    plot_raman([(xx, yy) for _, xx, yy in chain], ax=axes[0, 1],
               labels=[lab for lab, _, _ in chain], offset=1.0, legend="inline")
    # (0,2) XPS
    xx, yy = synth_xps(r)
    plot_xps((xx, yy), ax=axes[0, 2], label="C1s")
    # (1,0) FTIR
    wn, t = synth_ftir(r)
    plot_ftir((wn, t), ax=axes[1, 0])
    # (1,1) UV-Vis
    plot_uvvis(synth_uvvis(r), ax=axes[1, 1], labels=["film"])
    # (1,2) PL
    plot_pl(synth_pl(r), ax=axes[1, 2], labels=["QD"])
    # (2,0) CV
    plot_cv(synth_cv(r), ax=axes[2, 0])
    # (2,1) EIS
    plot_eis(synth_eis(r), ax=axes[2, 1])
    # (2,2) Scatter
    xp = np.linspace(0, 10, 20)
    yp = 2 * xp + r.normal(0, 1, 20)
    plot_scatter(pd.DataFrame({"x": xp, "y": yp}), fit=True, ax=axes[2, 2])
    supertitle(fig, "huitu capability matrix", y=1.01)
    _tag_panels(axes)
    save_both(fig, "226_multi_3x3")


@scenario(227, "Multi: 2x3 operando cmap compare", "multi")
def _s227():
    use_journal("nature")
    r = np.random.default_rng(18)
    Z, x, y = synth_operando(r)
    cmaps = ["crameri-batlow", "crameri-roma", "viridis", "inferno", "magma", "plasma"]
    fig, axes = plt.subplots(2, 3, figsize=(13, 7), constrained_layout=True)
    for ax, cmap in zip(axes.flatten(), cmaps):
        plot_operando(Z, x=x, y=y, ax=ax, cmap=cmap, xlabel="x", ylabel="t", cbar_label="I")
        ax.set_title(cmap, fontsize=8)
    _tag_panels(axes)
    save_both(fig, "227_multi_operando_cmap_compare")


@scenario(228, "Multi: density 2x3 cmaps", "multi")
def _s228():
    use_journal("nature")
    r = np.random.default_rng(19)
    x = r.normal(0, 1, 2000)
    y = 0.6 * x + r.normal(0, 0.5, 2000)
    cmaps = ["crameri-batlow", "crameri-roma", "viridis", "inferno", "magma", "editorial"]
    fig, axes = plt.subplots(2, 3, figsize=(13, 7), constrained_layout=True)
    for ax, cmap in zip(axes.flatten(), cmaps):
        try:
            plot_density(x, y, ax=ax, kind="kde", cmap=cmap, levels=10)
        except Exception:
            plot_density(x, y, ax=ax, kind="kde", cmap="viridis", levels=10)
        ax.set_title(cmap, fontsize=8)
    _tag_panels(axes)
    save_both(fig, "228_multi_density_cmap_grid")


@scenario(229, "Multi: 4 journal XRD same data", "multi")
def _s229():
    x, y = load_xrd(xrd_patterns[0])
    journals = ["nature", "science", "acs", "wiley"]
    fig, axes = plt.subplots(2, 2, figsize=(9, 7), constrained_layout=True)
    for ax, j in zip(axes.flatten(), journals):
        use_journal(j)
        plot_xrd((x, y), ax=ax, journal=j)
        ax.set_title(j, fontsize=8)
    save_both(fig, "229_multi_xrd_4journals")


# ==================== Edge cases (6) ====================
@scenario(230, "Edge: tiny 3-point line", "edge")
def _s230():
    use_journal("default")
    fig, ax = plt.subplots(figsize=(5, 3.5), constrained_layout=True)
    ax.plot([1, 2, 3], [2, 4, 3], "o-")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    save_both(fig, "230_edge_tiny3")


@scenario(231, "Edge: 10k-point line", "edge")
def _s231():
    use_journal("default")
    r = np.random.default_rng(21)
    x = np.linspace(0, 100, 10000)
    y = np.sin(x) + 0.3 * r.normal(size=x.size)
    fig, ax = plt.subplots(figsize=(8, 3), constrained_layout=True)
    ax.plot(x, y, lw=0.5)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    save_both(fig, "231_edge_10k")


@scenario(232, "Edge: single color forced", "edge")
def _s232():
    use_journal("nature")
    fig, ax = plt.subplots(figsize=(5, 3.5), constrained_layout=True)
    x = np.linspace(0, 10, 100)
    for i in range(5):
        ax.plot(x, np.sin(x + i * 0.5) + i * 0.3, color="C0", alpha=0.6)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    save_both(fig, "232_edge_single_color")


@scenario(233, "Edge: all-same y", "edge")
def _s233():
    use_journal("default")
    fig, ax = plt.subplots(figsize=(5, 3.5), constrained_layout=True)
    ax.plot(np.arange(10), np.ones(10) * 5, "o-")
    ax.set_ylabel("constant")
    save_both(fig, "233_edge_constant_y")


@scenario(234, "Edge: negative-y", "edge")
def _s234():
    use_journal("nature")
    x = np.linspace(-5, 5, 100)
    y = -np.exp(-x**2)
    fig, ax = plt.subplots(figsize=(5, 3.5), constrained_layout=True)
    ax.plot(x, y, lw=1.2)
    ax.axhline(0, color="k", lw=0.3)
    ax.set_xlabel("x")
    ax.set_ylabel("y (negative)")
    save_both(fig, "234_edge_negative_y")


@scenario(235, "Edge: log-y decay 5 curves", "edge")
def _s235():
    use_journal("science")
    use_palette("nature-cat")
    fig, ax = plt.subplots(figsize=(6, 4), constrained_layout=True)
    x = np.linspace(0, 10, 200)
    for k in range(5):
        ax.semilogy(x, np.exp(-x / (k + 1)), label=f"tau={k+1}")
    ax.set_xlabel("t")
    ax.set_ylabel("I (log)")
    ax.legend(loc="best", fontsize=7, frameon=False)
    save_both(fig, "235_edge_logy")


# ==================== Extras (to push well past 220) ====================
@scenario(236, "Extra: XRD + Raman + XPS triptych", "multi")
def _s236():
    use_journal("nature")
    use_palette("nature-cat")
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)
    x, y = load_xrd(xrd_patterns[2])
    plot_xrd((x, y), ax=axes[0])
    chain = load_raman_chain(2)
    plot_raman([(xx, yy) for _, xx, yy in chain], ax=axes[1],
               labels=[lab for lab, _, _ in chain], offset=1.0, legend="inline")
    r = np.random.default_rng(300)
    xx, yy = synth_xps(r)
    plot_xps((xx, yy), ax=axes[2], label="XPS")
    _tag_panels(axes)
    save_both(fig, "236_multi_triptych")


@scenario(237, "Extra: Multi-cmap heatmap 2x2", "multi")
def _s237():
    use_journal("nature")
    r = np.random.default_rng(22)
    m = r.normal(0, 1, (12, 12))
    m = (m + m.T) / 2
    np.fill_diagonal(m, 1)
    df = pd.DataFrame(m)
    fig, axes = plt.subplots(2, 2, figsize=(10, 8), constrained_layout=True)
    for ax, cmap in zip(axes.flatten(), ["RdBu_r", "coolwarm", "PiYG", "PuOr"]):
        plot_heatmap(df, ax=ax, cmap=cmap, center=0, cbar_label="r")
        ax.set_title(cmap, fontsize=8)
    _tag_panels(axes)
    save_both(fig, "237_multi_heatmap_cmap_grid")


@scenario(238, "Extra: CV 2x2 across journals", "cv")
def _s238():
    r = np.random.default_rng(23)
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), constrained_layout=True)
    for ax, j in zip(axes.flatten(), ["nature", "science", "acs", "wiley"]):
        use_journal(j)
        cv_list = [synth_cv(r, scan_rate=s) for s in (25, 50, 100)]
        plot_cv(cv_list, ax=ax, labels=["25", "50", "100 mV/s"], journal=j)
        ax.set_title(j, fontsize=8)
    _tag_panels(axes)
    save_both(fig, "238_cv_journals_2x2")


@scenario(239, "Extra: GCD multi-rate", "gcd")
def _s239():
    use_journal("nature")
    use_palette("carto-bold")
    r = np.random.default_rng(24)
    fig, ax = plt.subplots(figsize=(6, 4), constrained_layout=True)
    for cap in (100, 130, 160, 190, 220):
        x, y = synth_gcd(r, capacity=cap)
        ax.plot(x, y, label=f"{cap} mAh/g", lw=1.0)
    ax.set_xlabel("Capacity (mAh/g)")
    ax.set_ylabel("Potential (V)")
    ax.legend(loc="best", fontsize=7, frameon=False)
    save_both(fig, "239_gcd_multirate")


@scenario(240, "Extra: Density 3-mode comparison", "density")
def _s240():
    use_journal("nature")
    r = np.random.default_rng(25)
    x = r.normal(0, 1, 2000)
    y = 0.6 * x + r.normal(0, 0.5, 2000)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)
    plot_density(x, y, ax=axes[0], kind="kde", cmap="crameri-batlow")
    axes[0].set_title("kde", fontsize=8)
    plot_density(x, y, ax=axes[1], kind="hex", cmap="crameri-batlow")
    axes[1].set_title("hex", fontsize=8)
    plot_density(x, y, ax=axes[2], kind="scatter_kde", cmap="crameri-batlow")
    axes[2].set_title("scatter_kde", fontsize=8)
    _tag_panels(axes)
    save_both(fig, "240_density_3mode_compare")


@scenario(241, "Extra: SHAP 3-kind comparison", "shap")
def _s241():
    use_journal("nature")
    r = np.random.default_rng(26)
    sv, fv, names = synth_shap_dataset(r)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), constrained_layout=True)
    plot_shap(sv, names, feature_values=fv, kind="bar", ax=axes[0], max_features=8)
    axes[0].set_title("bar", fontsize=9)
    plot_shap(sv, names, feature_values=fv, kind="beeswarm", ax=axes[1],
              max_features=8, cmap="crameri-roma")
    axes[1].set_title("beeswarm", fontsize=9)
    plot_shap(sv, names, feature_values=fv, kind="dependence", ax=axes[2],
              dependence_feature="bandgap", dependence_interaction="Ef",
              cmap="crameri-roma")
    axes[2].set_title("dependence", fontsize=9)
    _tag_panels(axes)
    save_both(fig, "241_shap_3kind_compare")


@scenario(242, "Extra: Operando 4 cmap grid", "operando")
def _s242():
    use_journal("nature")
    r = np.random.default_rng(27)
    Z, x, y = synth_operando(r)
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    cmaps = ["crameri-batlow", "crameri-roma", "viridis", "inferno"]
    for ax, cmap in zip(axes.flatten(), cmaps):
        plot_operando(Z, x=x, y=y, ax=ax, cmap=cmap,
                     xlabel=r"2$\theta$ ($^{\circ}$)", ylabel="t", cbar_label="I")
        ax.set_title(cmap, fontsize=8)
    _tag_panels(axes)
    save_both(fig, "242_operando_cmap_grid4")


@scenario(243, "Extra: FTIR 3-stack journals strip", "ftir")
def _s243():
    r = np.random.default_rng(28)
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), constrained_layout=True)
    for ax, j in zip(axes, ["nature", "science", "acs"]):
        use_journal(j)
        use_palette("nature-cat")
        items = []
        labels = []
        for k, lab in enumerate(["as-syn", "cal-300", "cal-500"]):
            wn, t = synth_ftir(r)
            t += 8 * k
            t = np.clip(t, None, 100.0)
            items.append((wn, t))
            labels.append(lab)
        plot_ftir(items, ax=ax, labels=labels, legend="inline")
        ax.set_title(j, fontsize=8)
    _tag_panels(axes)
    save_both(fig, "243_ftir_journal_strip")


@scenario(244, "Extra: UVVis journals strip", "uvvis")
def _s244():
    r = np.random.default_rng(29)
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), constrained_layout=True)
    for ax, j in zip(axes, ["nature", "science", "wiley"]):
        use_journal(j)
        use_palette("carto-bold")
        items = [synth_uvvis(r, edge_nm=e) for e in (400, 480, 560)]
        plot_uvvis(items, ax=axes[list(axes).index(ax)], labels=["a", "b", "c"], journal=j)
        ax.set_title(j, fontsize=8)
    _tag_panels(axes)
    save_both(fig, "244_uvvis_journal_strip")


@scenario(245, "Extra: Radar 2-panel compare", "radar")
def _s245():
    use_journal("nature")
    fig = plt.figure(figsize=(12, 5), constrained_layout=True)
    ax1 = fig.add_subplot(1, 2, 1, projection="polar")
    ax2 = fig.add_subplot(1, 2, 2, projection="polar")
    axes_ = ["Capacity", "Rate", "Cycle", "Cost", "Safety"]
    plot_radar({"LFP": [140, 80, 95, 90, 98], "NMC": [175, 90, 75, 60, 70]},
               ax=ax1, categories=axes_)
    ax1.set_title("Cathodes", y=1.1, fontsize=9)
    plot_radar({"Pt": [95, 90, 85, 10, 20], "Ni": [60, 70, 65, 95, 85]},
               ax=ax2, categories=["Act", "Stab", "Sel", "Abund", "Cost^-1"])
    ax2.set_title("Catalysts", y=1.1, fontsize=9)
    save_both(fig, "245_radar_2panel")


@scenario(246, "Extra: Bode 2x2 journals", "bode")
def _s246():
    r = np.random.default_rng(30)
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), constrained_layout=True)
    for ax, j in zip(axes.flatten(), ["nature", "science", "acs", "elsevier"]):
        use_journal(j)
        arr = synth_bode(r)
        plot_bode(arr, ax=ax)
        ax.set_title(j, fontsize=8)
    _tag_panels(axes)
    save_both(fig, "246_bode_journal_grid")


@scenario(247, "Extra: Tafel multi-catalyst", "tafel")
def _s247():
    use_journal("nature")
    use_palette("nature-cat")
    fig, ax = plt.subplots(figsize=(6, 4), constrained_layout=True)
    r = np.random.default_rng(31)
    for cat, slope in [("Pt", 30), ("Ir", 50), ("Ni", 110), ("Fe-N-C", 70)]:
        logj, eta = synth_tafel(r, slope_mV=float(slope))
        ax.plot(logj, eta, "o", label=f"{cat} ({slope} mV/dec)", markersize=3)
    ax.set_xlabel("log|j| (A cm$^{-2}$)")
    ax.set_ylabel(r"$\eta$ (V)")
    ax.legend(loc="best", fontsize=7, frameon=False)
    save_both(fig, "247_tafel_multi")


@scenario(248, "Extra: Phase & Pourbaix side-by-side", "multi")
def _s248():
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    use_journal("nature")
    plot_pourbaix(pourbaix_data(), ax=axes[0])
    plot_phase_diagram(phase_diagram_data(), ax=axes[1],
                      invariants=[(0.5, 520, "eutectic")])
    _tag_panels(axes)
    save_both(fig, "248_multi_pourbaix_phase")


@scenario(249, "Extra: 6-panel mega ACS", "multi")
def _s249():
    use_journal("acs")
    use_palette("carto-bold")
    r = np.random.default_rng(32)
    fig, axes = plt.subplots(2, 3, figsize=(13, 7), constrained_layout=True)
    # XRD
    x, y = load_xrd(xrd_patterns[5])
    plot_xrd((x, y), ax=axes[0, 0])
    # PL
    plot_pl([synth_pl(r, center_nm=c) for c in (580, 620, 660)],
            ax=axes[0, 1], labels=["A", "B", "C"], legend="inline")
    # XPS
    xx, yy = synth_xps(r)
    plot_xps((xx, yy), ax=axes[0, 2], label="raw")
    # Thermal TGA
    T, w = synth_tga(r)
    plot_thermal((T, w), ax=axes[1, 0], mode="tga")
    # CV
    plot_cv([synth_cv(r, 50.0), synth_cv(r, 100.0)], ax=axes[1, 1],
            labels=["50", "100 mV/s"])
    # EIS
    plot_eis([synth_eis(r)], ax=axes[1, 2])
    _tag_panels(axes)
    save_both(fig, "249_multi_6panel_acs")


@scenario(250, "Extra: Bar + scatter combo in 1 fig", "multi")
def _s250():
    use_journal("nature")
    use_palette("nature-cat")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)
    df = pd.DataFrame({
        "material": ["A", "B", "C", "D", "E"],
        "Ea": [0.5, 0.4, 0.35, 0.3, 0.28],
    })
    plot_bar(df, ax=axes[0], ylabel="Ea (eV)")
    r = np.random.default_rng(33)
    x = r.uniform(0.5, 1.5, 30)
    y = 1.2 - 0.5 * x + r.normal(0, 0.08, 30)
    plot_scatter(pd.DataFrame({"r": x, "Ea": y}), ax=axes[1], fit=True,
                 xlabel="r (Å)", ylabel="Ea (eV)")
    _tag_panels(axes)
    save_both(fig, "250_multi_bar_scatter")


@scenario(251, "Extra: Radar 8-axis", "radar")
def _s251():
    use_journal("science")
    axes_ = ["A", "B", "C", "D", "E", "F", "G", "H"]
    data = {
        "alpha": [3, 4, 5, 2, 4, 3, 5, 4],
        "beta":  [5, 3, 2, 5, 4, 2, 3, 5],
        "gamma": [4, 5, 3, 3, 5, 4, 4, 3],
    }
    fig = plt.figure(figsize=(6, 5.5), constrained_layout=True)
    ax = fig.add_subplot(111, projection="polar")
    plot_radar(data, ax=ax, categories=axes_)
    save_both(fig, "251_radar_8axis")


@scenario(252, "Extra: Operando Raman-style", "operando")
def _s252():
    use_journal("nature")
    r = np.random.default_rng(34)
    Z, _, y = synth_operando(r, n_frames=80, n_bins=400)
    wn = np.linspace(100, 1800, 400)
    # y-axis of synth_operando is time (s), not potential — match the label.
    fig, _ = plot_operando(Z, x=wn, y=y, cmap="crameri-batlow",
                          xlabel=r"Raman shift (cm$^{-1}$)",
                          ylabel="Time (s)", cbar_label="Raman intensity (a.u.)")
    save_both(fig, "252_operando_raman_style")


@scenario(253, "Extra: Heatmap annotated 6x6", "heatmap")
def _s253():
    use_journal("nature")
    r = np.random.default_rng(35)
    labels = ["Fe", "Co", "Ni", "Cu", "Mn", "Zn"]
    m = r.uniform(0, 1, (6, 6))
    # Symmetrize to reflect a physically meaningful overlap/similarity matrix.
    m = (m + m.T) / 2
    np.fill_diagonal(m, 1.0)
    df = pd.DataFrame(m, index=labels, columns=labels)
    fig, _ = plot_heatmap(df, annot=True, cmap="viridis", cbar_label="overlap")
    save_both(fig, "253_heatmap_6x6_annot")


@scenario(254, "Extra: Density marginal 2", "density")
def _s254():
    use_journal("science")
    r = np.random.default_rng(36)
    x = r.normal(0, 1, 2500)
    y = np.sin(x) + r.normal(0, 0.3, 2500)
    fig, _ = plot_density(x, y, kind="kde", marginal=True, cmap="crameri-roma")
    save_both(fig, "254_density_marginal2")


@scenario(255, "Extra: Violin + swarm overlay", "box")
def _s255():
    use_journal("nature")
    r = np.random.default_rng(37)
    groups = [r.normal(m, 1.0, 60) for m in (2, 3.5, 5)]
    df = pd.DataFrame({f"g{i+1}": g for i, g in enumerate(groups)})
    fig, ax = plot_box_violin(df, kind="violin", ylabel="value")
    # Overlay swarm (just scatter jitter)
    for i, g in enumerate(groups, start=1):
        jitter = r.uniform(-0.15, 0.15, size=g.size)
        ax.scatter(np.full_like(g, i, dtype=float) + jitter, g, s=6, color="black", alpha=0.5)
    save_both(fig, "255_violin_swarm")


# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
print("\n" + "=" * 60)
sections: dict[str, tuple[int, int]] = {}
for n, name, status, section in results:
    ok, fail = sections.get(section, (0, 0))
    if status == "OK":
        sections[section] = (ok + 1, fail)
    else:
        sections[section] = (ok, fail + 1)

total = len(results)
total_ok = sum(1 for _, _, s, _ in results if s == "OK")
total_fail = total - total_ok
print(f"SUMMARY: total={total} ok={total_ok} fail={total_fail}")
print("-" * 60)
print(f"{'section':<12s} {'OK':>6s} {'FAIL':>6s}")
for sec, (ok, fail) in sorted(sections.items()):
    print(f"{sec:<12s} {ok:>6d} {fail:>6d}")

# List failures
print("\nFailures:")
fails = [(n, name, status) for n, name, status, _ in results if not status.startswith("OK") and status != "OK"]
for n, name, status in fails:
    print(f"  [{n:03d}] {name} -> {status}")

png_files = sorted(OUT.glob("*.png"))
pdf_files = sorted(OUT.glob("*.pdf"))
print(f"\nPNG files on disk: {len(png_files)}  PDF files: {len(pdf_files)}")
print(f"Output dir: {OUT}")
