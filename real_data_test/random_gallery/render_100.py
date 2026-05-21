"""Render 100 randomized figures across all 44 ``plot_*`` functions + 4 archetypes.

For each iteration we:

* round-robin a category id (48 unique categories, 100 iters => some get extras),
* seed numpy with ``i + 1``,
* synthesize the input the function expects (or load a sample data file),
* cycle through 8 journal presets so styles vary,
* save PNG only into ``real_data_test/random_gallery/output/``,
* catch every exception, log it, and keep going.

Run from repo root::

    /Users/ylll/miniconda3/bin/python real_data_test/random_gallery/render_100.py
"""

from __future__ import annotations

import os
import sys
import time
import traceback
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Make sure the repo root is on sys.path so ``import huitu`` finds the
# editable install regardless of the CWD the script is launched from.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import huitu  # noqa: E402

SAMPLE = REPO_ROOT / "examples" / "sample_data"
OUT = REPO_ROOT / "real_data_test" / "random_gallery" / "output"
OUT.mkdir(parents=True, exist_ok=True)

JOURNALS = ["default", "nature", "science", "acs", "rsc", "wiley", "elsevier", "ieee"]


# ─── Data synthesis helpers ─────────────────────────────────────────────────


def synth_spectrum(
    rng: np.random.Generator,
    *,
    x_min: float = 100.0,
    x_max: float = 2000.0,
    n: int = 600,
    n_peaks: int = 4,
    noise: float = 0.01,
) -> tuple[np.ndarray, np.ndarray]:
    """Synthesize a smooth (x, y) spectrum with several Gaussian peaks."""
    x = np.linspace(x_min, x_max, n)
    y = np.zeros_like(x) + 0.02
    for _ in range(n_peaks):
        c = rng.uniform(x_min + 0.1 * (x_max - x_min), x_max - 0.1 * (x_max - x_min))
        w = rng.uniform((x_max - x_min) * 0.01, (x_max - x_min) * 0.05)
        h = rng.uniform(0.4, 1.0)
        y += h * np.exp(-((x - c) ** 2) / (2 * w**2))
    y += rng.normal(0, noise, size=n)
    return x, np.clip(y, 0, None)


def synth_operando(
    rng: np.random.Generator,
    *,
    n_y: int = 50,
    n_x: int = 200,
    n_peaks: int = 4,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (Z, x, y) where Z is an (n_y, n_x) operando heatmap."""
    x = np.linspace(10, 80, n_x)
    y = np.linspace(0, 1.0, n_y)
    Z = np.zeros((n_y, n_x))
    centers = rng.uniform(15, 75, size=n_peaks)
    widths = rng.uniform(0.5, 2.0, size=n_peaks)
    drifts = rng.uniform(-3, 3, size=n_peaks)
    heights = rng.uniform(0.4, 1.0, size=n_peaks)
    for i, t in enumerate(y):
        for c, w, d, h in zip(centers, widths, drifts, heights):
            Z[i] += h * np.exp(-((x - (c + d * t)) ** 2) / (2 * w**2))
    Z += rng.normal(0, 0.02, size=Z.shape)
    return np.clip(Z, 0, None), x, y


def synth_polygons(
    rng: np.random.Generator,
    *,
    n_regions: int = 4,
    x_range: tuple[float, float] = (0, 14),
    y_range: tuple[float, float] = (-1.5, 1.5),
) -> list[dict]:
    """Synthesize 3-4 polygon regions for Pourbaix/phase-diagram callers.

    We tile the x-range into vertical bands then chop them at random y cuts so
    the resulting polygons are valid (non self-intersecting). Colors come from
    the huitu role palette so they stay journal-consistent.
    """
    colors = ["#3B6FB6", "#E07A5F", "#81B29A", "#F2CC8F", "#A78ACA"]
    x_min, x_max = x_range
    y_min, y_max = y_range
    xs = np.linspace(x_min, x_max, n_regions + 1)
    regions = []
    for i in range(n_regions):
        x0, x1 = xs[i], xs[i + 1]
        y0 = y_min + rng.uniform(0, 0.15) * (y_max - y_min)
        y1 = y_max - rng.uniform(0, 0.15) * (y_max - y_min)
        # add a wiggly top so it's not a boring rectangle
        midx = (x0 + x1) / 2
        mid_y_hi = y1 + rng.uniform(-0.1, 0.1) * (y_max - y_min)
        mid_y_lo = y0 + rng.uniform(-0.05, 0.05) * (y_max - y_min)
        verts = np.array(
            [[x0, y0], [midx, mid_y_lo], [x1, y0], [x1, y1], [midx, mid_y_hi], [x0, y1]]
        )
        regions.append(
            {"vertices": verts, "label": f"R{i+1}", "color": colors[i % len(colors)]}
        )
    return regions


# ─── Category registry ──────────────────────────────────────────────────────
#
# Each entry: name -> callable(rng, journal, save_path) -> None
# The wrapper does the actual plot + savefig (PNG) and closes the figure.

def _save(fig, save_path: Path) -> None:
    fig.savefig(save_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


# Plot wrappers ────────────────────────────────────────────────────────────


def w_xrd(rng, journal, save_path):
    x, y = synth_spectrum(rng, x_min=10, x_max=80, n=800, n_peaks=rng.integers(3, 8))
    fig, _ = huitu.plot_xrd((x, y), journal=journal)
    _save(fig, save_path)


def w_xps(rng, journal, save_path):
    x, y = synth_spectrum(rng, x_min=280, x_max=295, n=400, n_peaks=2)
    baseline_y = np.minimum.accumulate(y[::-1])[::-1] * 0.6
    # one Gaussian fit component
    fit_y = 0.6 * np.exp(-((x - rng.uniform(285, 290)) ** 2) / (2 * 0.5**2))
    fig, _ = huitu.plot_xps(
        (x, y),
        baseline=(x, baseline_y),
        fits=[(x, fit_y, "C 1s sp$^2$")],
        journal=journal,
    )
    _save(fig, save_path)


def w_raman(rng, journal, save_path):
    x, y = synth_spectrum(rng, x_min=100, x_max=2000, n=900, n_peaks=5)
    fig, _ = huitu.plot_raman((x, y), journal=journal)
    _save(fig, save_path)


def w_ftir(rng, journal, save_path):
    x = np.linspace(400, 4000, 1500)
    transmittance = np.full_like(x, 100.0)
    for _ in range(rng.integers(3, 7)):
        c = rng.uniform(500, 3800)
        w = rng.uniform(20, 80)
        d = rng.uniform(8, 25)
        transmittance -= d * np.exp(-((x - c) ** 2) / (2 * w**2))
    transmittance += rng.normal(0, 0.2, size=x.size)
    fig, _ = huitu.plot_ftir((x, transmittance), journal=journal)
    _save(fig, save_path)


def w_uvvis(rng, journal, save_path):
    x = np.linspace(300, 800, 600)
    y = 0.2 + np.exp(-((x - rng.uniform(380, 600)) ** 2) / (2 * 60.0**2))
    y += rng.normal(0, 0.01, size=x.size)
    fig, _ = huitu.plot_uvvis((x, y), journal=journal)
    _save(fig, save_path)


def w_pl(rng, journal, save_path):
    x = np.linspace(400, 800, 400)
    y = np.zeros_like(x)
    for _ in range(rng.integers(1, 3)):
        c = rng.uniform(450, 750)
        w = rng.uniform(15, 50)
        h = rng.uniform(0.4, 1.0)
        y += h * np.exp(-((x - c) ** 2) / (2 * w**2))
    y += rng.normal(0, 0.005, size=x.size)
    fig, _ = huitu.plot_pl((x, y), journal=journal)
    _save(fig, save_path)


def w_thermal(rng, journal, save_path):
    T = np.linspace(25, 800, 400)
    # smooth weight loss profile
    w = 100 - 40 / (1 + np.exp(-(T - rng.uniform(300, 500)) / 30))
    w += rng.normal(0, 0.2, size=T.size)
    fig, _ = huitu.plot_thermal((T, w), mode="tga", journal=journal)
    _save(fig, save_path)


def w_rietveld(rng, journal, save_path):
    tt = np.linspace(10, 80, 1500)
    bkg = 0.05 + 0.01 * np.sin(tt * 0.3)
    calc = bkg.copy()
    for _ in range(rng.integers(5, 10)):
        c = rng.uniform(15, 75)
        w = rng.uniform(0.05, 0.15)
        h = rng.uniform(0.3, 1.5)
        calc += h * np.exp(-((tt - c) ** 2) / (2 * w**2))
    obs = calc + rng.normal(0, 0.04, size=tt.size)
    arr = np.column_stack([tt, obs, calc, bkg])
    fig, _ = huitu.plot_rietveld(arr, journal=journal)
    _save(fig, save_path)


def w_operando(rng, journal, save_path):
    Z, x, y = synth_operando(rng)
    fig, _ = huitu.plot_operando(Z, x=x, y=y, journal=journal)
    _save(fig, save_path)


def w_cv(rng, journal, save_path):
    V = np.linspace(-0.5, 0.5, 400)
    I = 0.3 * np.sin(2 * np.pi * V) + 0.1 * V + rng.normal(0, 0.01, size=V.size)
    fig, _ = huitu.plot_cv((V, I), journal=journal)
    _save(fig, save_path)


def w_gcd(rng, journal, save_path):
    cap = np.linspace(0, rng.uniform(80, 200), 200)
    volt = 3.0 + 0.5 * np.tanh((cap - cap.mean()) / 30) + rng.normal(0, 0.005, size=cap.size)
    fig, _ = huitu.plot_gcd((cap, volt), journal=journal)
    _save(fig, save_path)


def w_cycle(rng, journal, save_path):
    n = rng.integers(40, 120)
    cycles = np.arange(1, n + 1)
    cap = 150 * np.exp(-cycles / 200) + rng.normal(0, 1.5, size=n)
    ce = 95 + rng.normal(0, 0.5, size=n)
    df = pd.DataFrame({"cycle": cycles, "capacity": cap, "ce": ce})
    fig, _ = huitu.plot_cycle(df, journal=journal)
    _save(fig, save_path)


def w_eis(rng, journal, save_path):
    # Synthesize a depressed semicircle
    f = np.logspace(-1, 5, 80)
    R0 = rng.uniform(5, 15)
    Rct = rng.uniform(80, 200)
    C = rng.uniform(1e-5, 1e-4)
    om = 2 * np.pi * f
    Z = R0 + Rct / (1 + 1j * om * Rct * C)
    zr = Z.real + rng.normal(0, 1, size=f.size)
    zi = -Z.imag + rng.normal(0, 1, size=f.size)
    fig, _ = huitu.plot_eis((zr, zi), journal=journal)
    _save(fig, save_path)


def w_bode(rng, journal, save_path):
    f = np.logspace(-1, 5, 80)
    mag = 90 / (1 + (f / rng.uniform(100, 1000)) ** 2) ** 0.25
    phase = -np.degrees(np.arctan(f / rng.uniform(50, 500)))
    arr = np.column_stack([f, mag, phase])
    fig, _ = huitu.plot_bode(arr, journal=journal)
    _save(fig, save_path)


def w_tafel(rng, journal, save_path):
    logj = np.linspace(-6, 0, 100)
    eta = 0.025 + rng.uniform(0.05, 0.15) * logj + rng.normal(0, 0.005, size=logj.size)
    fig, _ = huitu.plot_tafel((logj, eta), journal=journal)
    _save(fig, save_path)


def w_band(rng, journal, save_path):
    k = np.linspace(0, 1, 100)
    cols = [k]
    for i in range(rng.integers(4, 8)):
        E0 = rng.uniform(-4, 4)
        amp = rng.uniform(0.5, 2.0)
        cols.append(E0 + amp * np.cos(np.pi * k + rng.uniform(0, np.pi)))
    arr = np.column_stack(cols)
    fig, _ = huitu.plot_band(arr, journal=journal, ylim=(-6, 6))
    _save(fig, save_path)


def w_dos(rng, journal, save_path):
    E = np.linspace(-8, 8, 400)
    total = np.zeros_like(E)
    for _ in range(rng.integers(4, 7)):
        c = rng.uniform(-7, 7)
        w = rng.uniform(0.3, 1.0)
        total += rng.uniform(0.5, 2.0) * np.exp(-((E - c) ** 2) / (2 * w**2))
    fig, _ = huitu.plot_dos((E, total), journal=journal)
    _save(fig, save_path)


def w_cohp(rng, journal, save_path):
    E = np.linspace(-8, 4, 600)
    cohp = np.sin(E * rng.uniform(0.5, 1.0)) * np.exp(-(E**2) / 30)
    icohp = np.cumsum(cohp) * (E[1] - E[0])
    arr = np.column_stack([E, cohp, icohp])
    fig, _ = huitu.plot_cohp(arr, journal=journal)
    _save(fig, save_path)


def w_pourbaix(rng, journal, save_path):
    regions = synth_polygons(rng, n_regions=4, x_range=(0, 14), y_range=(-1.5, 1.8))
    fig, _ = huitu.plot_pourbaix(regions, journal=journal)
    _save(fig, save_path)


def w_phase_diagram(rng, journal, save_path):
    regions = synth_polygons(rng, n_regions=4, x_range=(0, 1), y_range=(200, 1000))
    fig, _ = huitu.plot_phase_diagram(regions, journal=journal)
    _save(fig, save_path)


def w_crystal_ase(rng, journal, save_path):
    fig, _ = huitu.plot_crystal_ase(str(SAMPLE / "crystal.cif"), journal=journal)
    _save(fig, save_path)


def w_crystal_vesta(rng, journal, save_path):
    # dispatcher; usually falls back to ASE — let it pick its method.
    fig, _ = huitu.plot_crystal_vesta(str(SAMPLE / "crystal.cif"), journal=journal,
                                     save=str(save_path))
    # plot_crystal_vesta already wrote save_path via its save kwarg, but we still
    # want to be sure the figure is closed.
    plt.close(fig)


def w_bar(rng, journal, save_path):
    n_cat = rng.integers(4, 8)
    cats = [f"S{i+1}" for i in range(n_cat)]
    df = pd.DataFrame(
        {
            "sample": cats,
            "before": rng.uniform(2, 6, size=n_cat),
            "after": rng.uniform(4, 9, size=n_cat),
        }
    )
    fig, _ = huitu.plot_bar(df, journal=journal, ylabel="Capacity")
    _save(fig, save_path)


def w_scatter(rng, journal, save_path):
    n = rng.integers(30, 100)
    x = np.sort(rng.uniform(0, 10, size=n))
    y = 2 * x + 0.5 + rng.normal(0, 1, size=n)
    yerr = rng.uniform(0.2, 0.8, size=n)
    df = pd.DataFrame({"x": x, "y": y, "yerr": yerr})
    fig, _ = huitu.plot_scatter(df, fit=True, journal=journal)
    _save(fig, save_path)


def w_line(rng, journal, save_path):
    n = 200
    t = np.linspace(0, 10, n)
    df = pd.DataFrame(
        {
            "t": t,
            "voltage": 3.5 + 0.5 * np.sin(t),
            "current": 1.5 - 0.1 * np.cos(t),
            "temperature": 25 + 5 * np.sin(0.5 * t) + rng.normal(0, 0.3, size=n),
        }
    )
    fig, _ = huitu.plot_line(
        df, twin_cols=["temperature"], xlabel="t", ylabel="V/I", ylabel_right="T (°C)",
        journal=journal,
    )
    _save(fig, save_path)


def w_heatmap(rng, journal, save_path):
    n = rng.integers(8, 14)
    Z = rng.normal(0, 1, size=(n, n))
    Z = (Z + Z.T) / 2
    fig, _ = huitu.plot_heatmap(Z, cmap="ft-diverging", center=0.0, journal=journal)
    _save(fig, save_path)


def w_box_violin(rng, journal, save_path):
    n_groups = rng.integers(3, 6)
    rows = []
    for i in range(n_groups):
        mu = rng.uniform(-1, 2)
        sd = rng.uniform(0.3, 1.5)
        for v in rng.normal(mu, sd, size=40):
            rows.append({"sample": f"G{i+1}", "value": v})
    df = pd.DataFrame(rows)
    kind = rng.choice(["box", "violin"])
    fig, _ = huitu.plot_box_violin(df, x="sample", y="value", kind=str(kind), journal=journal)
    _save(fig, save_path)


def w_radar(rng, journal, save_path):
    n_methods = rng.integers(3, 5)
    n_axes = rng.integers(5, 8)
    vals = rng.uniform(0.2, 1.0, size=(n_methods, n_axes))
    cats = [f"Axis{i+1}" for i in range(n_axes)]
    df = pd.DataFrame(vals, columns=cats, index=[f"M{i+1}" for i in range(n_methods)])
    fig, _ = huitu.plot_radar(df, journal=journal)
    _save(fig, save_path)


def w_density(rng, journal, save_path):
    n = 500
    # bimodal blob
    x1 = rng.normal(0, 1, size=n // 2)
    x2 = rng.normal(3, 0.8, size=n - n // 2)
    y1 = rng.normal(0, 1, size=n // 2)
    y2 = rng.normal(3, 0.8, size=n - n // 2)
    x = np.concatenate([x1, x2])
    y = np.concatenate([y1, y2])
    fig, _ = huitu.plot_density(x, y, journal=journal)
    _save(fig, save_path)


def w_shap(rng, journal, save_path):
    n_samples = 80
    n_feats = rng.integers(6, 12)
    sv = rng.normal(0, 0.5, size=(n_samples, n_feats))
    fv = rng.normal(0, 1, size=(n_samples, n_feats))
    names = [f"feat{i+1}" for i in range(n_feats)]
    kind = rng.choice(["bar", "beeswarm"])
    fig, _ = huitu.plot_shap(sv, names, feature_values=fv, kind=str(kind), journal=journal)
    _save(fig, save_path)


# --- pro/advanced wrappers -----------------------------------------------


def w_ridgeline(rng, journal, save_path):
    n_rows = rng.integers(4, 8)
    dists = [rng.normal(rng.uniform(-2, 2), rng.uniform(0.5, 1.5), size=200) for _ in range(n_rows)]
    labels = [f"D{i+1}" for i in range(n_rows)]
    fig, _ = huitu.plot_ridgeline(dists, labels=labels, journal=journal)
    _save(fig, save_path)


def w_dumbbell(rng, journal, save_path):
    n = rng.integers(5, 10)
    cats = [f"Sample {i+1}" for i in range(n)]
    start = rng.uniform(20, 60, size=n)
    end = start + rng.uniform(-15, 25, size=n)
    fig, _ = huitu.plot_dumbbell(cats, start, end, journal=journal)
    _save(fig, save_path)


def w_slope(rng, journal, save_path):
    n_lines = rng.integers(4, 8)
    series = {f"S{i+1}": [rng.uniform(20, 80), rng.uniform(20, 80)] for i in range(n_lines)}
    fig, _ = huitu.plot_slope(series, x_labels=["t1", "t2"], journal=journal)
    _save(fig, save_path)


def w_bump(rng, journal, save_path):
    n_periods = rng.integers(4, 7)
    n_series = rng.integers(4, 8)
    data = {f"M{i+1}": list(rng.uniform(0, 10, size=n_periods)) for i in range(n_series)}
    x_labels = [f"P{i+1}" for i in range(n_periods)]
    fig, _ = huitu.plot_bump(data, x_labels=x_labels, journal=journal)
    _save(fig, save_path)


def w_parallel(rng, journal, save_path):
    n_rows = rng.integers(30, 80)
    n_cols = rng.integers(4, 7)
    cols = [f"f{i+1}" for i in range(n_cols)]
    df = pd.DataFrame(rng.normal(0, 1, size=(n_rows, n_cols)), columns=cols)
    df["group"] = rng.choice(["A", "B", "C"], size=n_rows)
    fig, _ = huitu.plot_parallel(df, color_by="group", journal=journal)
    _save(fig, save_path)


def w_waffle(rng, journal, save_path):
    n = rng.integers(3, 6)
    raw = rng.uniform(1, 10, size=n)
    raw = (raw / raw.sum()) * 100
    counts = raw.round().astype(int)
    labels = [f"Cat{i+1}" for i in range(n)]
    fig, _ = huitu.plot_waffle(list(counts), labels=labels, journal=journal)
    _save(fig, save_path)


def w_streamgraph(rng, journal, save_path):
    n_t = 80
    x = np.arange(n_t)
    n_cat = rng.integers(4, 7)
    series = {}
    for i in range(n_cat):
        base = np.cumsum(rng.normal(0, 0.3, size=n_t))
        series[f"Cat{i+1}"] = np.abs(base - base.min() + 0.5)
    fig, _ = huitu.plot_streamgraph(x, series, journal=journal)
    _save(fig, save_path)


def w_connected_scatter(rng, journal, save_path):
    n = rng.integers(20, 40)
    t = np.linspace(0, 2 * np.pi, n)
    x = np.cumsum(rng.normal(0.2, 0.5, size=n))
    y = np.cumsum(rng.normal(0.2, 0.5, size=n)) + 0.5 * np.sin(t)
    fig, _ = huitu.plot_connected_scatter(x, y, journal=journal)
    _save(fig, save_path)


# --- pro operando wrappers ---


def w_operando_waterfall(rng, journal, save_path):
    Z, x, y = synth_operando(rng, n_y=30)
    fig, _ = huitu.plot_operando_waterfall(Z, x=x, y=y, journal=journal)
    _save(fig, save_path)


def w_operando_xrd_echem(rng, journal, save_path):
    Z, x, y = synth_operando(rng)
    echem = 3.0 + 0.7 * np.sin(np.linspace(0, 2 * np.pi, len(y)))
    fig = huitu.plot_operando_xrd_echem(Z, x, y, echem=echem, journal=journal)
    # function returns (fig, axes_dict) or just (fig, ...); handle both
    if isinstance(fig, tuple):
        fig = fig[0]
    _save(fig, save_path)


def w_operando_3d_surface(rng, journal, save_path):
    Z, x, y = synth_operando(rng, n_y=30, n_x=80)
    fig = huitu.plot_operando_3d_surface(Z, x=x, y=y, journal=journal)
    if isinstance(fig, tuple):
        fig = fig[0]
    _save(fig, save_path)


def w_operando_diffmap(rng, journal, save_path):
    Z, x, y = synth_operando(rng)
    fig, _ = huitu.plot_operando_diffmap(Z, x=x, y=y, reference=0, journal=journal)
    _save(fig, save_path)


def w_operando_peak_evolution(rng, journal, save_path):
    n = 30
    y = np.linspace(0, 1, n)
    series = {
        "peak A position": 20 + 0.5 * np.sin(2 * np.pi * y) + rng.normal(0, 0.02, size=n),
        "peak B position": 30 + 0.3 * np.cos(2 * np.pi * y) + rng.normal(0, 0.02, size=n),
        "peak C position": 45 + 0.7 * y + rng.normal(0, 0.03, size=n),
    }
    fig, _ = huitu.plot_operando_peak_evolution(y, series, journal=journal)
    _save(fig, save_path)


def w_operando_contour(rng, journal, save_path):
    Z, x, y = synth_operando(rng)
    fig, _ = huitu.plot_operando_contour(Z, x=x, y=y, journal=journal)
    _save(fig, save_path)


# --- archetype wrappers ---


def w_archetype_schematic_led(rng, journal, save_path):
    fig, axes = huitu.archetype.schematic_led(journal=journal, n_supports=3)
    # populate hero with a fake schematic image, supports with mini plots
    hero = axes["hero"]
    hero.imshow(rng.random((30, 60)), cmap="Greys", aspect="auto")
    hero.set_xticks([])
    hero.set_yticks([])
    for ax in axes["supports"]:
        x = np.linspace(0, 10, 200)
        y = np.sin(x + rng.uniform(0, 2 * np.pi)) + 0.1 * rng.normal(size=x.size)
        ax.plot(x, y, lw=0.8)
        ax.set_xticks([])
        ax.set_yticks([])
    _save(fig, save_path)


def w_archetype_dark_image_plate(rng, journal, save_path):
    fig, grid = huitu.archetype.dark_image_plate(rows=3, cols=4, journal=journal)
    for row in grid:
        for ax in row:
            ax.imshow(rng.random((40, 40)), cmap="magma", aspect="equal")
    _save(fig, save_path)


def w_archetype_clinical_triptych(rng, journal, save_path):
    fig, axes = huitu.archetype.clinical_triptych(journal=journal, n_cols=3)
    # top: longitudinal lines
    t = np.linspace(0, 10, 100)
    for ax in axes["top"]:
        for _ in range(3):
            ax.plot(t, np.sin(t + rng.uniform(0, 2 * np.pi)) + 0.1 * rng.normal(size=t.size),
                    lw=0.8)
    # mid: forest plot
    for ax in axes["mid"]:
        n = 5
        ys = np.arange(n)
        means = rng.normal(0, 0.5, size=n)
        errs = rng.uniform(0.1, 0.4, size=n)
        ax.errorbar(means, ys, xerr=errs, fmt="o", ms=4)
        ax.axvline(0, ls="--", color="grey", lw=0.6)
        ax.set_yticks([])
    # bot: bars
    for ax in axes["bot"]:
        n = 4
        ax.bar(range(n), rng.uniform(1, 5, size=n))
        ax.set_xticks([])
    _save(fig, save_path)


def w_archetype_asymmetric_hero(rng, journal, save_path):
    fig, axes = huitu.archetype.asymmetric_hero(journal=journal)
    # populate every named axis
    t = np.linspace(0, 10, 100)
    for k in ["a", "c", "f"]:
        axes[k].plot(t, np.sin(t + rng.uniform(0, 2 * np.pi)) + 0.1 * rng.normal(size=t.size))
        axes[k].set_xticks([])
    for k in ["b", "d"]:
        axes[k].bar(range(4), rng.uniform(1, 5, size=4))
        axes[k].set_xticks([])
    # 'e' is the hero, spans rows: draw a colorful imshow
    axes["e"].imshow(rng.random((30, 12)), cmap="viridis", aspect="auto")
    axes["e"].set_xticks([])
    axes["e"].set_yticks([])
    _save(fig, save_path)


# ─── Registry ─────────────────────────────────────────────────────────────


CATEGORIES: list[tuple[str, object]] = [
    ("plot_band", w_band),
    ("plot_bar", w_bar),
    ("plot_bode", w_bode),
    ("plot_box_violin", w_box_violin),
    ("plot_bump", w_bump),
    ("plot_cohp", w_cohp),
    ("plot_connected_scatter", w_connected_scatter),
    ("plot_crystal_ase", w_crystal_ase),
    ("plot_crystal_vesta", w_crystal_vesta),
    ("plot_cv", w_cv),
    ("plot_cycle", w_cycle),
    ("plot_density", w_density),
    ("plot_dos", w_dos),
    ("plot_dumbbell", w_dumbbell),
    ("plot_eis", w_eis),
    ("plot_ftir", w_ftir),
    ("plot_gcd", w_gcd),
    ("plot_heatmap", w_heatmap),
    ("plot_line", w_line),
    ("plot_operando", w_operando),
    ("plot_operando_3d_surface", w_operando_3d_surface),
    ("plot_operando_contour", w_operando_contour),
    ("plot_operando_diffmap", w_operando_diffmap),
    ("plot_operando_peak_evolution", w_operando_peak_evolution),
    ("plot_operando_waterfall", w_operando_waterfall),
    ("plot_operando_xrd_echem", w_operando_xrd_echem),
    ("plot_parallel", w_parallel),
    ("plot_phase_diagram", w_phase_diagram),
    ("plot_pl", w_pl),
    ("plot_pourbaix", w_pourbaix),
    ("plot_radar", w_radar),
    ("plot_raman", w_raman),
    ("plot_ridgeline", w_ridgeline),
    ("plot_rietveld", w_rietveld),
    ("plot_scatter", w_scatter),
    ("plot_shap", w_shap),
    ("plot_slope", w_slope),
    ("plot_streamgraph", w_streamgraph),
    ("plot_tafel", w_tafel),
    ("plot_thermal", w_thermal),
    ("plot_uvvis", w_uvvis),
    ("plot_waffle", w_waffle),
    ("plot_xps", w_xps),
    ("plot_xrd", w_xrd),
    ("archetype.schematic_led", w_archetype_schematic_led),
    ("archetype.dark_image_plate", w_archetype_dark_image_plate),
    ("archetype.clinical_triptych", w_archetype_clinical_triptych),
    ("archetype.asymmetric_hero", w_archetype_asymmetric_hero),
]

assert len(CATEGORIES) == 48, f"expected 48 categories, got {len(CATEGORIES)}"


# ─── Main loop ────────────────────────────────────────────────────────────


def main(n_target: int = 100) -> int:
    t0 = time.time()
    counts: Counter[str] = Counter()
    failures: dict[str, list[str]] = defaultdict(list)
    skipped: set[str] = set()  # category fully skipped (e.g. import errors)

    figure_idx = 0
    cat_cursor = 0
    while figure_idx < n_target:
        name, wrapper = CATEGORIES[cat_cursor % len(CATEGORIES)]
        cat_cursor += 1

        rng = np.random.default_rng(figure_idx + 1)
        journal = JOURNALS[figure_idx % len(JOURNALS)]

        # normalize the name into a fs-safe slug
        slug = name.replace(".", "_")
        save_name = f"{figure_idx:03d}_{slug}_{journal}.png"
        save_path = OUT / save_name

        try:
            wrapper(rng, journal, save_path)
            counts[name] += 1
            figure_idx += 1
            if figure_idx % 10 == 0:
                print(f"  ... {figure_idx}/{n_target} rendered (last: {name}, journal={journal})")
        except Exception:
            # close any orphaned figures to avoid leaking memory
            plt.close("all")
            tb_line = traceback.format_exc().splitlines()[-1]
            failures[name].append(f"figure {figure_idx} [{journal}]: {tb_line}")
            # If a category fails consistently, we mark it as fully skipped
            # only after 2 failed attempts in this run, so we don't waste
            # all 100 slots on one broken plot.
            if len(failures[name]) >= 2:
                skipped.add(name)
            # do NOT increment figure_idx -- retry next category at same slot
            # but increment cat_cursor (already done) so we pick a new one
            print(f"  [FAIL] cat={name} fig={figure_idx} journal={journal}: {tb_line}")
        finally:
            # cap retries in case literally every category errored
            if cat_cursor > n_target * len(CATEGORIES) * 2:
                print("  abort: too many retries, giving up")
                break

    elapsed = time.time() - t0

    # ── Final summary ────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("RANDOM GALLERY SUMMARY")
    print("=" * 70)
    successes = sum(counts.values())
    print(f"  successes : {successes} / {n_target}")
    print(f"  failures  : {sum(len(v) for v in failures.values())}")
    print(f"  runtime   : {elapsed:.1f} s ({elapsed/60:.1f} min)")
    print(f"  output dir: {OUT}")
    print()

    print("[CATEGORIES TOUCHED]")
    for name, _ in CATEGORIES:
        c = counts.get(name, 0)
        marker = "" if c > 0 else "  <-- ZERO"
        print(f"  {name:32s} {c}{marker}")

    if failures:
        print()
        print("[FAILURES]")
        for name, msgs in failures.items():
            print(f"  {name} ({len(msgs)} failure{'s' if len(msgs)!=1 else ''})")
            for m in msgs[:3]:
                print(f"    - {m}")
            if len(msgs) > 3:
                print(f"    ... {len(msgs) - 3} more")

    if skipped:
        print()
        print("[CATEGORIES SKIPPED AFTER 2 FAILS]")
        for s in sorted(skipped):
            print(f"  - {s}")

    uncovered = [n for n, _ in CATEGORIES if counts.get(n, 0) == 0]
    covered_all = not uncovered
    print()
    if covered_all:
        print("every category covered: YES")
    else:
        print(f"every category covered: NO ({len(uncovered)} missing)")
        for u in uncovered:
            print(f"  - {u}")

    return 0 if successes >= 95 and covered_all else 1


if __name__ == "__main__":
    sys.exit(main())
