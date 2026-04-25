"""Test huitu against real materials-science data.

Generates:
- xrd_cnrs.pdf: stacked XRD from 3 CNRS JSON patterns (Nature preset)
- raman_stack.pdf: stacked Raman spectra (ACS preset)
- xafs_compare.pdf: XAFS absorption edges (Wiley preset)
- combined_panel.pdf: 2x2 panel showcasing all three + XRD zoom inset
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Ensure local huitu installed
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import huitu
from huitu import (
    plot_xrd, plot_raman, plot_line, make_subplots, add_inset,
    use_journal, use_palette, list_palettes, PALETTES,
)

OUT = Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)

XRD_DIR = Path("/Users/ylll/phd/coding/huitu_skills/xrd_real_patterns_2026-04-23/opxrd/CNRS")
RAMAN_ROOT = Path("/Users/ylll/phd/coding/raman/data")
XAFS_ROOT = Path("/Users/ylll/phd/coding/xafs/data")


# ---------- helpers ----------
def load_xrd(pattern_path: Path):
    d = json.loads(pattern_path.read_text())
    x = np.asarray(d["two_theta_values"], dtype=float)
    y = np.asarray(d["intensities"], dtype=float)
    return x, y


def first_xlsx_in(dir_: Path) -> Path | None:
    for p in dir_.glob("images/*.xlsx"):
        if not p.name.startswith("."):
            return p
    return None


def load_spectrum_xlsx(xlsx: Path):
    df = pd.read_excel(xlsx)
    return df["X"].to_numpy(dtype=float), df["Y"].to_numpy(dtype=float)


def load_chemical_label(chem_json: Path) -> str:
    d = json.loads(chem_json.read_text())
    # first entry
    first = next(iter(d.values()))
    formulas = first.get("chemical_formulas", ["?"])
    return formulas[0] if formulas else "?"


# ---------- 1. XRD (CNRS patterns) ----------
print("=== XRD ===")
xrd_patterns = [XRD_DIR / f"pattern_{i}.json" for i in (0, 5, 10)]
xrd_data = []
labels = []
for p in xrd_patterns:
    x, y = load_xrd(p)
    # Normalize for stacking
    y_norm = (y - y.min()) / (y.max() - y.min())
    xrd_data.append((x, y_norm))
    # Parse label from inside JSON's "label" field
    d = json.loads(p.read_text())
    try:
        lbl = json.loads(d["label"])["phases"][0]
        # extract chemical — just get first couple tokens
        labels.append(f"pattern_{p.stem.split('_')[1]}")
    except Exception:
        labels.append(p.stem)
    print(f"  {p.name}: {len(x)} points, 2θ range {x.min():.1f}-{x.max():.1f}°")

use_journal("nature")
fig, ax = plot_xrd(xrd_data, labels=labels, offset=0.6,
                   save=str(OUT / "xrd_cnrs.pdf"))
print(f"  -> xrd_cnrs.pdf")
# PNG for preview
fig.savefig(OUT / "xrd_cnrs.png", dpi=600, bbox_inches="tight")


# ---------- 2. Raman ----------
print("\n=== Raman ===")
raman_dirs = sorted([d for d in RAMAN_ROOT.iterdir() if d.is_dir()])[:3]
raman_data = []
raman_labels = []
for d in raman_dirs:
    xlsx = first_xlsx_in(d)
    if xlsx is None:
        print(f"  skip {d.name} (no xlsx)")
        continue
    x, y = load_spectrum_xlsx(xlsx)
    # Normalize
    y_norm = (y - y.min()) / (y.max() - y.min())
    raman_data.append((x, y_norm))
    chem_json = d / "chemical_formulas_raman.json"
    label = load_chemical_label(chem_json) if chem_json.exists() else d.name[:8]
    raman_labels.append(label[:20])  # trim long formulas
    print(f"  {d.name[:8]}: {label[:40]} - {len(x)} points, {x.min():.0f}-{x.max():.0f} cm-1")

use_journal("acs")
fig, ax = plot_raman(raman_data, labels=raman_labels, offset=1.05,
                     save=str(OUT / "raman_stack.pdf"))
print(f"  -> raman_stack.pdf")
fig.savefig(OUT / "raman_stack.png", dpi=600, bbox_inches="tight")


# ---------- 3. XAFS (use plot_line as XAFS isn't a dedicated huitu plot) ----------
print("\n=== XAFS ===")
xafs_dirs = sorted([d for d in XAFS_ROOT.iterdir() if d.is_dir()])[:3]
xafs_series = []  # build long DataFrame for plot_line
all_x, cols = None, {}
xafs_labels = []
for i, d in enumerate(xafs_dirs):
    xlsx = first_xlsx_in(d)
    if xlsx is None:
        continue
    x, y = load_spectrum_xlsx(xlsx)
    chem_json = d / "chemical_formulas_exafs.json"
    label = load_chemical_label(chem_json) if chem_json.exists() else d.name[:8]
    xafs_labels.append(label)
    xafs_series.append((x, y, label))
    print(f"  {d.name[:8]}: {label} - {len(x)} points, {x.min():.0f}-{x.max():.0f} eV")

# Since each XAFS has its own energy grid, plot via matplotlib directly on plot_line-compatible ax
use_journal("wiley")
fig, axes = make_subplots(1, 1)
ax = axes if not hasattr(axes, "__iter__") else axes
import matplotlib.pyplot as plt
ax = plt.gca()
for x, y, lbl in xafs_series:
    ax.plot(x, y, label=lbl, linewidth=1.2)
ax.set_xlabel("Photon energy (eV)")
ax.set_ylabel("Absorption (a.u.)")
ax.legend(frameon=False, fontsize=7)
fig = ax.figure
fig.savefig(OUT / "xafs_compare.pdf")
fig.savefig(OUT / "xafs_compare.png", dpi=600, bbox_inches="tight")
print(f"  -> xafs_compare.pdf")


# ---------- 4. Combined panel (2x2) ----------
print("\n=== Combined panel ===")
use_journal("nature")
fig, axes = make_subplots(2, 2)

# (a) XRD single with inset
x0, y0 = load_xrd(xrd_patterns[0])
y0n = (y0 - y0.min()) / (y0.max() - y0.min())
plot_xrd((x0, y0n), ax=axes[0, 0])
# inset showing a zoomed peak region (grab top-3 peak x)
top_idx = np.argsort(y0n)[-1]
peak_x = x0[top_idx]
add_inset(axes[0, 0],
          bounds=(0.55, 0.5, 0.42, 0.42),
          xlim=(peak_x - 1.5, peak_x + 1.5),
          ylim=(0, 1.05))

# (b) Raman single
if raman_data:
    xr, yr = raman_data[0]
    plot_raman((xr, yr), ax=axes[0, 1])

# (c) XAFS overlay
for x, y, lbl in xafs_series:
    axes[1, 0].plot(x, y, label=lbl, linewidth=1.0)
axes[1, 0].set_xlabel("Photon energy (eV)")
axes[1, 0].set_ylabel("Absorption (a.u.)")
axes[1, 0].legend(frameon=False, fontsize=6)

# (d) Stacked XRD mini
plot_xrd(xrd_data, labels=labels, offset=0.5, ax=axes[1, 1])

fig.savefig(OUT / "combined_panel.pdf")
fig.savefig(OUT / "combined_panel.png", dpi=600, bbox_inches="tight")
print(f"  -> combined_panel.pdf")

# ---------- 5. Palette preview (showcase the 9 curated palettes) ----------
print("\n=== Palette preview ===")
use_journal("default")
import matplotlib.pyplot as plt
names = list_palettes()
fig, axes = plt.subplots(len(names), 1, figsize=(6.5, 0.55 * len(names)),
                         constrained_layout=True)
for ax, name in zip(axes, names):
    colors = PALETTES[name]
    for i, c in enumerate(colors):
        ax.add_patch(plt.Rectangle((i, 0), 1, 1, facecolor=c, edgecolor="none"))
    ax.set_xlim(0, max(len(c) for c in PALETTES.values()))
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_xticks([])
    for side in ("top", "right", "bottom", "left"):
        ax.spines[side].set_visible(False)
    ax.text(-0.2, 0.5, name, ha="right", va="center", fontsize=8,
            transform=ax.get_yaxis_transform())
fig.suptitle("huitu curated palettes", fontsize=9, y=1.02)
fig.savefig(OUT / "palettes.pdf", bbox_inches="tight")
fig.savefig(OUT / "palettes.png", dpi=600, bbox_inches="tight")
print(f"  -> palettes.pdf  ({len(names)} palettes)")


print("\nAll outputs:")
for f in sorted(OUT.iterdir()):
    print(f"  {f.name}  ({f.stat().st_size // 1024} KB)")
