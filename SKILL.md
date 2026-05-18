# huitu — materials-science plotting skill

Opinionated matplotlib/seaborn wrappers that turn the most common materials-science measurements into journal-ready figures with a one-line call. Every function accepts either a file path (two-column `.txt`/`.csv`), a NumPy `(N, 2)` array, a `(x, y)` tuple, or a `pandas.DataFrame`, and returns `(fig, ax)` so you can keep customising.

## Quick start

```python
from huitu import plot_xrd

plot_xrd("data/xrd.txt", journal="nature", save="fig1.pdf")
```

```python
from huitu import make_subplots, plot_xrd, plot_raman

fig, axes = make_subplots(1, 2, journal="acs")
plot_xrd("xrd.txt", ax=axes[0])
plot_raman("raman.txt", ax=axes[1])
fig.savefig("panel.pdf")
```

## Plot catalogue

| Plot                | Function         | Example script                     | Notes                                          |
| ------------------- | ---------------- | ---------------------------------- | ---------------------------------------------- |
| XRD (single)        | `plot_xrd`       | `examples/xrd_single.py`           | Optional `hkl={2theta: "(hkl)"}`               |
| XRD (stacked)       | `plot_xrd`       | `examples/xrd_stacked.py`          | Pass a list of files + `offset`                |
| XPS + fitted peaks  | `plot_xps`       | `examples/xps_fitting.py`          | `baseline=(x,y)`, `fits=[(x,y,label), ...]`    |
| Raman               | `plot_raman`     | `examples/raman.py`                | Pass a list for multi-spectrum stacking        |
| CV                  | `plot_cv`        | `examples/cv.py`                   | Multi-cycle overlay via list input             |
| GCD                 | `plot_gcd`       | `examples/gcd.py`                  | Multi-rate overlay via list input              |
| Cycling + CE        | `plot_cycle`     | `examples/cycle.py`                | 3-column input -> twin Y (capacity, CE)        |
| EIS (Nyquist)       | `plot_eis`       | `examples/eis.py`                  | Equal-aspect; list input for multi-sample      |
| Bar (grouped/stack) | `plot_bar`       | `examples/bar.py`                  | `stacked=True` toggles mode                    |
| Scatter + fit       | `plot_scatter`   | `examples/scatter.py`              | `fit=True`, `yerr=...`                         |
| Line (twin Y)       | `plot_line`      | `examples/line.py`                 | `twin_cols=[...]`                              |
| Subplot factory     | `make_subplots`  | `examples/subplots_demo.py`        | Auto (a)(b)(c) labels                          |
| Zoom inset          | `add_inset`      | `examples/inset_demo.py`           | Dashed connector rectangle                     |
| FTIR (v0.2)         | `plot_ftir`      | `examples/ftir.py`                 | Reversed x-axis; `mode='transmittance'\|'absorbance'` |
| UV-Vis / Tauc (v0.2)| `plot_uvvis`     | `examples/uvvis.py`                | `tauc='direct'\|'indirect'` switches to photon energy |
| PL (v0.2)           | `plot_pl`        | `examples/pl.py`                   | Multi-spectrum + `normalize=True`              |
| Thermal TGA/DSC (v0.2)| `plot_thermal` | `examples/thermal.py`              | `mode='tga'\|'dsc'\|'both'`; `mode='both'` requires passing a second file via `dsc_data=` |
| Bode (v0.2)         | `plot_bode`      | `examples/bode.py`                 | Log freq x; twin y (`\|Z\|` log, phase deg)     |
| Tafel (v0.2)        | `plot_tafel`     | `examples/tafel.py`                | Optional `fit_range=(eta_min, eta_max)` overlay |
| Band structure (v0.2)| `plot_band`     | `examples/band.py`                 | Fermi line at 0; `kpoints=[(label, pos), ...]`  |
| DOS / PDOS (v0.2)   | `plot_dos`       | `examples/dos.py`                  | `orientation='horizontal'\|'vertical'`, projections  |
| Heatmap (v0.2)      | `plot_heatmap`   | `examples/heatmap.py`              | `mode='heatmap'\|'contour'\|'contourf'`, `annot=True` |
| Box / Violin (v0.2) | `plot_box_violin`| `examples/box_violin.py`           | `kind='box'\|'violin'`, long-format via `x=/y=` |
| Rietveld (v0.3)     | `plot_rietveld`  | `examples/rietveld.py`             | 2-panel: main (obs/calc/bkg) + difference; `hkl_positions=[...]` |
| COHP / ICOHP (v0.3) | `plot_cohp`      | `examples/cohp.py`                 | Bonding fill left of 0, antibonding right; `show_icohp=True` adds twin x |
| Pourbaix (v0.3)     | `plot_pourbaix`  | `examples/pourbaix.py`             | Accepts list of `{label, vertices, color}`; H$_2$/O$_2$ stability lines overlaid |
| Phase diagram (v0.3)| `plot_phase_diagram` | `examples/phase_diagram.py`    | Same region-dict API as Pourbaix; `invariants=[(x, T, label)]` |
| Radar / spider (v0.3)| `plot_radar`    | `examples/radar.py`                | `normalize='per_axis'\|'global'\|None` |
| Shared axes (v0.3)  | `share_axes`     | `examples/shared_axes_demo.py`     | Post-hoc link limits, remove inner tick labels |
| Crystal (ASE) (v0.3)| `plot_crystal_ase` | `examples/crystal_ase.py`        | 3 orthogonal views; requires `pip install 'huitu[crystal]'` |
| Crystal (VESTA) (v0.3)| `plot_crystal_vesta` | `examples/crystal_vesta.py`  | Dispatcher: uses `VESTA_BIN` env var if set, else ASE |

## Journal presets

Apply with `journal="..."` (or directly: `huitu.use_journal(name)`).

| Preset     | scienceplots stack         | Figure size (inches) | Base font | Axes width |
| ---------- | -------------------------- | -------------------- | --------- | ---------- |
| `default`  | (none)                     | 3.5 x 2.8            | 8 pt      | 0.8        |
| `nature`   | `science, nature`          | 89 mm x 70 mm        | 7 pt      | 0.6        |
| `science`  | `science`                  | ~110 mm x 88 mm      | 7 pt      | 0.7        |
| `acs`      | `science, notebook`        | 3.33 x 2.5           | 8 pt      | 0.8        |
| `rsc`      | `science`                  | 3.26 x 2.6           | 8 pt      | 0.7        |
| `wiley`    | `science`                  | 3.35 x 2.6           | 8 pt      | 0.8        |
| `elsevier` | `science`                  | 90 mm x 70 mm        | 8 pt      | 0.8        |
| `ieee`     | `science, ieee`            | 3.5 x 2.5            | 8 pt      | 0.8        |

Shared across every preset: Helvetica -> Arial -> DejaVu Sans font stack, **600 dpi savefig** (journal grade), **`svg.fonttype="none"` + `pdf.fonttype=42`** so saved SVG/PDF text stays editable in Illustrator/Inkscape, black axes, ticks on all four sides, legend frame off, `text.usetex=False` so no LaTeX install required. If `scienceplots` cannot be imported, the preset falls back to plain matplotlib rcParams with the same sizes.

## Nature-style helpers (v0.5)

Five additions that turn `huitu` from "data → figure" into "conclusion → figure":

| Helper                                | What it does                                                                                       |
| ------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `huitu.role(name)`                    | Look up a hex color by *scientific role* (`hero` / `baseline` / `positive` / `negative` / …)        |
| `huitu.use_palette("semantic")`       | Switch the color cycle to the role-based palette (hero → baseline → accent → neutral)             |
| `huitu.archetype.schematic_led`       | Hero panel + supporting quant row — the canonical materials/mechanism layout                       |
| `huitu.archetype.dark_image_plate`    | Black-faced microscopy / fluorescence grid (no spines, no ticks, ready for `imshow`)               |
| `huitu.archetype.clinical_triptych`   | 3-row × 3-col layout: longitudinal → forest → summary, columns kept semantically parallel         |
| `huitu.archetype.asymmetric_hero`     | 3 × 4 grid with one panel spanning all rows (UMAP, circular plot, dominant schematic)             |
| `huitu.check_redundancy(panels)`      | Warn when two panels answer the same question, share a data slice, or skip the info hierarchy     |
| `huitu.print_redundancy_report(...)`  | Pretty-prints the above to stdout                                                                  |
| `huitu.reviewer_checklist(...)`       | Pre-submission checklist (n / replicates / center / spread / test / source data / scale bar / …) |

Use them either standalone or in combination with the `plot_*` functions:

```python
fig, ax = huitu.archetype.schematic_led(journal="nature", n_supports=3)
huitu.plot_xrd("xrd.txt", ax=ax["supports"][0])
huitu.plot_eis("eis.txt", ax=ax["supports"][1])
huitu.plot_cycle("cyc.txt", ax=ax["supports"][2])
fig.savefig("fig1.svg")        # text remains editable in Illustrator
```

## Two usage modes

### Mode A — one-liner

Best when the defaults already look right.

```python
from huitu import plot_cycle
plot_cycle("cycle.txt", journal="nature", save="cycle.pdf")
```

### Mode B — copy a template and edit

When you need custom colours, annotations, extra axes, or mixed panels:

1. Copy the closest `examples/*.py` next to your data.
2. Edit freely — every plot returns `(fig, ax)` so you still own the Matplotlib object.

```python
from huitu import plot_xrd, add_inset
fig, ax = plot_xrd("xrd.txt", journal="acs")
ax.axvline(32.9, color="red", lw=0.5)
ax.annotate("(200)", xy=(32.9, 0.7), xytext=(35, 0.85), arrowprops=dict(arrowstyle="->"))
add_inset(ax, bounds=(0.55, 0.45, 0.4, 0.45), xlim=(30, 35), ylim=(0.3, 1.05))
fig.savefig("custom.pdf")
```

## Plot quirks

| Plot          | Quirk                                                                 |
| ------------- | --------------------------------------------------------------------- |
| `plot_xps`    | X axis inverted (binding energy decreases left -> right)              |
| `plot_cycle`  | Twin right Y axis for Coulombic efficiency when input has 3 columns    |
| `plot_line`   | Twin right Y axis for columns listed in `twin_cols`                   |
| `plot_eis`    | Equal aspect ratio; `negate_imag=True` to flip raw Z''                |
| `plot_xrd`    | Y axis has no ticks; stacking offsets normalized patterns             |
| `plot_raman`  | Y axis has no ticks; stacked offset via `offset`                      |
| `plot_bar`    | Expects CSV **with** a header row; first column is the category axis   |
| `plot_line`   | Expects CSV **with** a header row; column names become legend labels   |
| `plot_ftir`   | X axis reversed (4000 -> 400 cm$^{-1}$); `mode` toggles transmittance/absorbance label |
| `plot_uvvis`  | `tauc='direct'` plots $(\alpha h\nu)^2$ vs eV; `'indirect'` uses exponent 1/2 |
| `plot_thermal`| `mode='both'` draws TGA on left axis, DSC on twin right (requires `dsc_data=`) |
| `plot_bode`   | Log-scaled x (freq) and log-scaled left y (`\|Z\|`); phase on twin right |
| `plot_tafel`  | `fit_range=(eta_min, eta_max)` selects the linear region; slope reported in mV/dec |
| `plot_band`   | Fermi level assumed at 0 eV; high-symmetry points via `kpoints=[(label, k), ...]` |
| `plot_dos`    | `orientation='vertical'` rotates the plot so it can sit next to `plot_band` |
| `plot_heatmap`| `mode='heatmap'` uses `imshow(aspect='auto')`; `'contour'`/`'contourf'` swap renderer |
| `plot_box_violin` | For long-format DataFrame pass `x=` (grouping col) and `y=` (value col)  |
| `plot_cohp`    | Raw-COHP convention: x = COHP; bonding COHP < 0 (left fill), antibonding COHP > 0 (right fill). `show_icohp=True` requires a 3rd column; the returned `ax` is the primary COHP axes and the ICOHP twin is `ax.figure.axes[1]` |
| `plot_pourbaix` | Water stability lines at 25 degC, 1 atm: `E = -0.05916 * pH` (H$_2$) and `E = 1.229 - 0.05916 * pH` (O$_2$); disable with `water_stability=False`. Regions are closed polygons of `(pH, E)` vertices. Mode A for this plot means inline-constructing region dicts; there is no standard file format |
| `plot_phase_diagram` | Same polygon API as Pourbaix. Scope is 2-D region drawing only — no CALPHAD math. Mode A means inline-constructing region dicts; no standard file format |
| `plot_rietveld` | Always creates its own 2-row layout; passing `ax` triggers a warning and is ignored. Diff panel is centred on zero (`axhline(0)`). Breaking change from v0.3: no `offset` kwarg |
| `plot_radar`   | Default normalization is per-axis; use `normalize='global'` for uniform scaling or `None` to plot raw values |
| `plot_crystal_ase` | Requires ASE (`pip install 'huitu[crystal]'`); always returns `(fig, axes)` with 3 orthogonal views |
| `plot_crystal_vesta` | Falls back silently to ASE when `VESTA_BIN` env var is unset or missing from `PATH` |

## Data format expectations (MVP)

- **Two-column spectra** (XRD, XPS, Raman, CV, GCD, EIS): tab/comma/whitespace-separated `.txt`/`.csv` with columns `x, y`. Header row optional; `#` and `%` lines treated as comments.
- **Cycling**: three columns `cycle, capacity, coulombic_efficiency` (CE optional).
- **Bar / line / scatter**: CSV with a header row; first column = category or x-axis, remaining columns = series.

Pre-generated synthetic samples live under `examples/sample_data/` (regenerate with `python examples/sample_data/_generate.py`).

## Bundled reference demos (`docs/inspirations/figures4papers/`)

`huitu` ships a read-only snapshot of nine real-paper plotting scripts from
[`Yuan1z0825/nature-skills`](https://github.com/Yuan1z0825/nature-skills) /
[`ChenLiu-1996/figures4papers`](https://github.com/ChenLiu-1996/figures4papers).
These are **reference cookbooks**, not part of huitu's import surface.
Use them as visual examples for `plot_*` and `archetype.*` patterns. Each
project sits in its own folder and is intended to be run from that folder:

```bash
cd docs/inspirations/figures4papers/figure_ImmunoStruct/
python plot_bars.py    # PNG lands in figures/ (gitignored)
```

### Demo prerequisites — different demos need different data sources

Before running or pointing a user at a specific demo, check this table.
Six demos run out of the box on `matplotlib + numpy` only; three need
extra setup. If a user only has `matplotlib + numpy + pandas` installed,
prefer the green ones.

| Project | Runs out of the box? | Extra requirement |
|---|---|---|
| `figure_CellSpliceNet`   | ✅ | — |
| `figure_Cflows`          | ✅ | — |
| `figure_Dispersion`      | ✅ for `plot_idea.py` · ⚠️ `plot_illustration.py` needs LaTeX | `text.usetex=True` |
| `figure_ImmunoStruct`    | ✅ | — (data is inlined in `raw_data.py`) |
| `figure_VIGIL`           | ✅ | — |
| `figure_brainteaser`     | ✅ | — |
| `figure_FPGM`            | ❌ | **External data**: needs `./data/` directory with project-specific `.npy` / `.pt` files (not shipped — upstream omits it too). User must provide their own dataset before running. |
| `figure_RNAGenScape`     | ❌ | **LaTeX**: scripts set `plt.rcParams['text.usetex'] = True` and use real LaTeX in axis labels. Install MacTeX (macOS) / TeX Live (Linux/Windows) or patch the scripts to set `usetex=False`. |
| `figure_ophthal_review`  | ❌ | **LaTeX + seaborn**: same `usetex=True` requirement; also `import seaborn as sns`. Install `seaborn` via pip plus a TeX distribution. |

### When pointing a user at a demo

1. **First check the table above** — confirm the demo doesn't need a data
   source or environment the user lacks.
2. **If the user needs a chart like one of the LaTeX-dependent demos** but
   doesn't have LaTeX, suggest patching the script: replace
   `plt.rcParams['text.usetex'] = True` with `False`, or remove
   LaTeX-flavored math (`$\\frac{a}{b}$` → `a / b`) before running.
3. **If the user needs `figure_FPGM`**, ask whether they already have the
   pre-trained frequency-prior tensors they want to plot; without those,
   the script can't produce a meaningful figure regardless of environment.
4. **Never silently swallow these failures** — if a demo doesn't run, tell
   the user *which* missing dependency is the cause (data dir / LaTeX /
   seaborn) and what to do about it.

The chart-family routing table in
[`docs/inspirations/README.md`](docs/inspirations/README.md) maps each demo
to the closest huitu function, so for most use-cases you can read the demo
for pattern reference without actually executing it.

## Extension roadmap

- **v0.2 (shipped)**: FTIR, UV-Vis/Tauc, PL, TGA+DSC, Bode, Tafel, band, DOS/PDOS, heatmap/contour, box/violin.
- **Shipped in v0.3**: Rietveld refinement, COHP/ICOHP, Pourbaix (E-pH), binary phase diagrams, radar/spider, post-hoc `share_axes`, crystal structure rendering (ASE and VESTA dispatcher).
- **Future**
  - pymatgen-backed band structure (`BSVasprun` / `BandStructureSymmLine`) input for `plot_band`
  - `plot_isotherm` (BET N2 adsorption/desorption)
  - Differential capacity (dQ/dV) and in-situ waterfall plots
  - Automatic report/PDF generation combining multiple panels

Contributions welcome — add a module under the appropriate subpackage, expose from `huitu/__init__.py`, ship an example script and sample data.
