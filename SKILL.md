---
name: huitu
description: >-
  Materials-science plotting skill that turns experimental, DFT and
  electrochemistry measurements into journal-ready Python / matplotlib
  figures with a single one-line call. Use whenever the user asks to
  plot, draw, render, generate, or polish any of: XRD, XPS, Raman,
  FTIR, UV-Vis / Tauc, PL, TGA / DSC, Rietveld, BET N₂ isotherm, CV,
  GCD, cycling + CE, EIS Nyquist, Bode, Tafel, dQ/dV, band structure
  (text input or pymatgen `BSVasprun` / `BandStructureSymmLine`), DOS /
  PDOS, COHP / ICOHP, Pourbaix, binary phase diagram, crystal structure
  (ASE / VESTA), bar, scatter, line, heatmap, box/violin, radar, 2-D
  KDE density, SHAP-like bee-swarm, ridgeline, dumbbell, slope, bump,
  parallel-coords, waffle, stream-graph, connected scatter, or any of
  six in-situ / operando heatmap variants. Also triggers on multi-panel
  Nature-style layout requests (schematic-led composite, dark image
  plate, clinical triptych, asymmetric hero), multi-figure PDF report
  compositing, and pre-submission anti-redundancy or reviewer-checklist
  QA. Chinese triggers — 画图, 绘制, 出图, 画 XRD, CV 曲线, EIS 图,
  BET 等温线, dQ/dV, 能带, 态密度, 相图, 期刊配图, Nature 风格图,
  材料论文配图, 表征图, 多图组合 PDF, 冗余检查, 审稿清单, 库伦效率 — all activate the skill. Output is editable-text
  SVG / PDF (PDF text remains selectable) plus 600 dpi PNG matching
  eight journal presets (`nature`, `science`, `acs`, `rsc`, `wiley`,
  `elsevier`, `ieee`, `default`); a semantic-role palette (`hero`,
  `baseline`, `positive`, `negative`, `neutral`, `accent_*`) is
  available for hero-vs-baseline comparisons. Not for dashboards,
  interactive plotly / Bokeh / Altair, GIS, or 3-D molecular-dynamics
  rendering — those use cases should route elsewhere.
---

# huitu — materials-science plotting skill

Opinionated matplotlib/seaborn wrappers that turn the most common materials-science measurements into journal-ready figures with a one-line call. Every function accepts either a file path (two-column `.txt`/`.csv`), a NumPy `(N, 2)` array, a `(x, y)` tuple, or a `pandas.DataFrame`, and returns `(fig, ax)` so you can keep customising. (A small number of two-panel helpers — `plot_bet`, `plot_rietveld` — return `(fig, (ax1, ax2), …)` with extra payload; the per-row note in the catalogue calls those out.)

## When to use this skill

Activate **whenever** the user mentions any of:

- A specific materials-science measurement name in English or Chinese:
  `XRD / 衍射`, `XPS / 光电子能谱`, `Raman / 拉曼`, `FTIR / 红外`, `UV-Vis / 紫外可见`, `PL / 荧光`, `TGA / DSC / 热分析`, `Rietveld / 精修`, `BET / 等温线`, `CV / 循环伏安`, `GCD / 充放电`, `EIS / 阻抗 / Nyquist / Bode`, `Tafel`, `dQ/dV / 差分容量`, `band / 能带`, `DOS / PDOS / 态密度`, `COHP`, `Pourbaix / 电位-pH`, `phase diagram / 相图`, `crystal / 晶体结构`, `operando / 原位`.
- General plot families: `bar / 柱图`, `scatter / 散点`, `line / 折线`, `heatmap / 热图`, `box / violin / 箱线`, `radar / 雷达`, `KDE / density / 密度`, `SHAP`, `ridgeline / 山脊`, `bump / 排名`, `streamgraph / 河流图`, `waffle`, `parallel / 平行坐标`.
- Nature-style multi-panel layout: `schematic-led / 示意主导`, `image plate / 显微 grid`, `clinical triptych / 临床三段`, `asymmetric hero / 不对称`.
- Workflow QA: `anti-redundancy / 冗余检查`, `reviewer checklist / 审稿清单`, `figure contract / 投稿前自检`.
- Output / export: `journal-ready / 期刊级`, `Nature 风格`, `editable SVG / PDF`, `600 dpi`, `multi-page PDF / 多图组合`.
- Verbs: `plot / draw / render / generate / make / 画 / 绘制 / 出图 / 渲染 / 生成`.

## When NOT to load

- Interactive / web plotting (`plotly`, `bokeh`, `altair`, `dash`, `streamlit`).
- GIS / map plotting (`folium`, `geopandas`-led work).
- 3-D molecular dynamics rendering, ray tracing, ovito-led visualisation.
- Illustrator / Figma-first infographic layout (huitu's archetypes are
  matplotlib gridspec, not freeform vector design).
- Pure data-analysis (no figure deliverable).

## Installation (both layers needed for full functionality)

`huitu` ships as two installable layers — install **both** for an
end-to-end agent-callable plotting skill:

1. **Python package** (`pip install -e .` from the repo, or `pip install
   huitu-0.6.0-py3-none-any.whl` from a GitHub Release) — provides
   `import huitu` and the 47 `plot_*` functions + 4 archetypes that
   actually render figures.

2. **Skill bundle** (`cp -R . ~/.claude/skills/huitu/` for Claude Code,
   or `cp -R . ~/.codex/skills/huitu/` for Codex CLI) — installs this
   SKILL.md so the agent auto-activates on materials-science plotting
   queries in either English or Chinese. The skill loader reads the
   YAML frontmatter at the top of this file for its activation
   description.

Installing only the skill bundle without the Python package leaves the
agent able to read the API catalogue but unable to render figures.
Installing only the Python package without the skill bundle means you
have to `import huitu` manually — no auto-activation.

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

> The `Source` column is where the function is **implemented** inside the
> `huitu/` package. There is no separate demo file per function — calling
> conventions for every function are in its own docstring (`help(plot_xrd)`
> or your IDE's hover) plus the inline code snippets at the end of this
> section. See [`REPO_LAYOUT.md`](REPO_LAYOUT.md) for the full directory
> split and [`examples/`](examples/) for the six canonical end-to-end
> scripts (quickstart, multi-panel, BET, dQ/dV, multi-fig PDF, reviewer
> checklist).

| Plot                  | Function              | Source                                       | Notes |
| --------------------- | --------------------- | -------------------------------------------- | ----- |
| XRD (single / stacked)| `plot_xrd`            | `huitu/characterization/xrd.py`              | Optional `hkl={2theta: "(hkl)"}`; list input + `offset=` for stacks |
| XPS + fitted peaks    | `plot_xps`            | `huitu/characterization/xps.py`              | `baseline=(x,y)`, `fits=[(x,y,label), …]` |
| Raman                 | `plot_raman`          | `huitu/characterization/raman.py`            | List input for multi-spectrum stacking |
| FTIR                  | `plot_ftir`           | `huitu/characterization/ftir.py`             | Reversed x-axis; `mode='transmittance'\|'absorbance'` |
| UV-Vis / Tauc         | `plot_uvvis`          | `huitu/characterization/uvvis.py`            | `tauc='direct'\|'indirect'` switches x to photon energy |
| PL                    | `plot_pl`             | `huitu/characterization/pl.py`               | Multi-spectrum + `normalize=True` |
| TGA / DSC             | `plot_thermal`        | `huitu/characterization/thermal.py`          | `mode='tga'\|'dsc'\|'both'`; `mode='both'` needs `dsc_data=` |
| Rietveld              | `plot_rietveld`       | `huitu/characterization/rietveld.py`         | 2-panel main + residual; `hkl_positions=[...]` |
| Operando (v0.3)       | `plot_operando`       | `huitu/characterization/operando.py`         | Traditional in-situ heatmap |
| **BET isotherm** ✨ v0.6 | `plot_bet`         | `huitu/characterization/bet.py`              | 2-panel: isotherm + BET linear plot; auto V_m + S_BET annotation |
| CV                    | `plot_cv`             | `huitu/electrochem/cv.py`                    | Multi-cycle overlay via list input |
| GCD                   | `plot_gcd`            | `huitu/electrochem/gcd.py`                   | Multi-rate overlay |
| Cycling + CE          | `plot_cycle`          | `huitu/electrochem/cycle.py`                 | 3-column input → twin-Y (capacity, CE) |
| EIS (Nyquist)         | `plot_eis`            | `huitu/electrochem/eis.py`                   | Equal-aspect; list input |
| Bode                  | `plot_bode`           | `huitu/electrochem/bode.py`                  | Log freq x; twin y (\|Z\|, phase) |
| Tafel                 | `plot_tafel`          | `huitu/electrochem/tafel.py`                 | Optional `fit_range=(η_min, η_max)` |
| **dQ/dV** ✨ v0.6     | `plot_dqdv`           | `huitu/electrochem/dqdv.py`                  | Differential capacity from GCD; optional Savitzky–Golay smoothing |
| Band structure        | `plot_band`           | `huitu/computational/band.py`                | Fermi at 0; `kpoints=[(label, pos), …]`; **v0.6**: also accepts pymatgen `BSVasprun` / `BandStructureSymmLine` |
| DOS / PDOS            | `plot_dos`            | `huitu/computational/dos.py`                 | `orientation='horizontal'\|'vertical'` |
| COHP / ICOHP          | `plot_cohp`           | `huitu/computational/cohp.py`                | Bonding fill left of 0; `show_icohp=True` adds twin x |
| Pourbaix              | `plot_pourbaix`       | `huitu/computational/pourbaix.py`            | Region dict + H₂/O₂ stability lines |
| Phase diagram         | `plot_phase_diagram`  | `huitu/computational/phase_diagram.py`       | Same region-dict API; `invariants=[(x, T, label)]` |
| Crystal (ASE)         | `plot_crystal_ase`    | `huitu/computational/crystal.py`             | 3 orthogonal views; needs `pip install 'huitu[crystal]'` |
| Crystal (VESTA)       | `plot_crystal_vesta`  | `huitu/computational/crystal.py`             | Dispatcher: `VESTA_BIN` env var else ASE fallback |
| Bar (grouped/stacked) | `plot_bar`            | `huitu/general/bar.py`                       | `stacked=True` toggles mode |
| Scatter + fit         | `plot_scatter`        | `huitu/general/scatter.py`                   | `fit=True`, `yerr=…` |
| Line (twin Y)         | `plot_line`           | `huitu/general/line.py`                      | `twin_cols=[…]` |
| Heatmap               | `plot_heatmap`        | `huitu/general/heatmap.py`                   | `mode='heatmap'\|'contour'\|'contourf'`, `annot=True` |
| Box / Violin          | `plot_box_violin`     | `huitu/general/box_violin.py`                | `kind='box'\|'violin'`, long-format via `x=/y=` |
| Radar / spider        | `plot_radar`          | `huitu/general/radar.py`                     | `normalize='per_axis'\|'global'\|None` |
| Density (2-D KDE)     | `plot_density`        | `huitu/general/density.py`                   | 2-D kernel density on (x, y) |
| SHAP-like importance  | `plot_shap`           | `huitu/general/shap_like.py`                 | Bee-swarm style feature importance |
| Subplot factory       | `make_subplots`       | `huitu/layout/subplots.py`                   | Auto (a)(b)(c) panel labels |
| Zoom inset            | `add_inset`           | `huitu/layout/inset.py`                      | Dashed connector rectangle |
| Shared axes           | `share_axes`          | `huitu/layout/shared_axes.py`                | Post-hoc link limits + remove inner ticks |
| **Multi-fig PDF** ✨ v0.6 | `make_pdf_report` | `huitu/layout/pdf_report.py`                 | Compose any list of figures into a multi-page PDF; optional cover page + per-page captions |

Advanced (v0.4) families — statistical / comparison / operando — and the v0.5
archetype + role + review APIs live under `huitu/pro/*.py`, `huitu/archetype.py`,
`huitu/review.py`. See `huitu/__init__.py` for the complete export list (44 plot
functions + 4 archetypes + role + check_redundancy + reviewer_checklist).

## Inline quickstart snippets

```python
# 1. Single plot, journal preset, save — replace plot_xrd with any plot_*.
import huitu
fig, ax = huitu.plot_xrd("xrd.txt", journal="nature", save="fig1.svg")
```

```python
# 2. Multi-panel via archetype + role-based palette.
fig, ax = huitu.archetype.schematic_led(journal="nature", n_supports=3)
ax["hero"].imshow(mechanism_cartoon)
huitu.plot_xrd  ("xrd.txt",  ax=ax["supports"][0])
huitu.plot_cv   ("cv.txt",   ax=ax["supports"][1], color=huitu.role("hero"))
huitu.plot_eis  ("eis.txt",  ax=ax["supports"][2])
fig.savefig("fig1.svg")   # editable text in Illustrator
```

```python
# 3. BET isotherm (two-panel) — returns (fig, axes, metrics)
fig, (ax_iso, ax_lin), m = huitu.plot_bet((p_rel, v_ads), journal="nature")
print(f"S_BET = {m['S_BET']:.1f} m² g⁻¹  ·  V_m = {m['V_m']:.2f} cm³ g⁻¹")
```

```python
# 4. dQ/dV (multi-cycle ageing overlay)
huitu.plot_dqdv([cycle_1, cycle_50], labels=["cycle 1", "cycle 50"])
```

```python
# 5. Multi-figure PDF report — bundle every panel into one shareable file
huitu.make_pdf_report(
    [fig_xrd, fig_cv, fig_eis, fig_gcd],
    save="reports/sample_2026-05.pdf",
    title="MnO₂-Cu sample — May 2026",
    metadata=["operator = YL", "date = 2026-05-21"],
    captions=["Fig 1. XRD", "Fig 2. CV", "Fig 3. EIS", "Fig 4. GCD"],
)
```

```python
# 6. Pre-submission self-check (anti-redundancy + reviewer checklist)
huitu.print_redundancy_report(panel_plan)
huitu.reviewer_checklist(figure=..., quantitative=..., image=...)
```

The runnable versions of these six snippets live as `examples/quickstart.py`,
`examples/multi_panel.py`, `examples/bet.py`, `examples/dqdv.py`,
`examples/pdf_report.py`, `examples/reviewer_checklist.py`.

## Journal presets

Apply with `journal="..."` (or directly: `huitu.use_journal(name)`).

| Preset     | scienceplots stack         | Figure size (inches) | Base font | Axes width | Font family                          | Mathtext     |
| ---------- | -------------------------- | -------------------- | --------- | ---------- | ------------------------------------ | ------------ |
| `default`  | (none)                     | 3.5 x 2.8            | 8 pt      | 0.8        | Helvetica -> Arial -> DejaVu Sans    | `dejavusans` |
| `nature`   | `science, nature`          | 89 mm x 70 mm        | 7 pt      | 0.6        | Helvetica -> Arial -> DejaVu Sans    | `dejavusans` |
| `science`  | `science`                  | ~110 mm x 88 mm      | 7 pt      | 0.7        | Times New Roman -> serif fallback    | `stix`       |
| `acs`      | `science, notebook`        | 3.33 x 2.5           | 8 pt      | 0.8        | Helvetica -> Arial -> DejaVu Sans    | `dejavusans` |
| `rsc`      | `science`                  | 3.26 x 2.6           | 8 pt      | 0.7        | Helvetica -> Arial -> DejaVu Sans    | `dejavusans` |
| `wiley`    | `science`                  | 3.35 x 2.6           | 8 pt      | 0.8        | Helvetica -> Arial -> DejaVu Sans    | `dejavusans` |
| `elsevier` | `science`                  | 90 mm x 70 mm        | 8 pt      | 0.8        | Helvetica -> Arial -> DejaVu Sans    | `dejavusans` |
| `ieee`     | `science, ieee`            | 3.5 x 2.5            | 8 pt      | 0.8        | Times New Roman -> serif fallback    | `stix`       |

Shared across every preset: **600 dpi savefig** (journal grade), **`svg.fonttype="none"` + `pdf.fonttype=42`** so saved SVG/PDF text stays editable in Illustrator/Inkscape, black axes, ticks on all four sides, legend frame off, `text.usetex=False` so no LaTeX install required. Body text + mathtext share a sans-serif stack for Nature/ACS/RSC/Wiley/Elsevier and a serif stack for Science/IEEE, so a label like `r"2$\theta$"` renders in one family rather than mixing Helvetica and DejaVuSerif. To override per session use `huitu.use_font("Times New Roman", mathtext="stix")` after `huitu.use_journal(...)`. If `scienceplots` cannot be imported, the preset falls back to plain matplotlib rcParams with the same sizes.

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

1. Copy the closest of the six canonical `examples/*.py` next to your data, or grab a snippet from the "Inline quickstart snippets" section above.
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

## Extension roadmap

- **v0.2 (shipped)**: FTIR, UV-Vis/Tauc, PL, TGA+DSC, Bode, Tafel, band, DOS/PDOS, heatmap/contour, box/violin.
- **Shipped in v0.3**: Rietveld refinement, COHP/ICOHP, Pourbaix (E-pH), binary phase diagrams, radar/spider, post-hoc `share_axes`, crystal structure rendering (ASE and VESTA dispatcher).
- **Future**
  - pymatgen-backed band structure (`BSVasprun` / `BandStructureSymmLine`) input for `plot_band`
  - `plot_isotherm` (BET N2 adsorption/desorption)
  - Differential capacity (dQ/dV) and in-situ waterfall plots
  - Automatic report/PDF generation combining multiple panels

Contributions welcome — add a module under the appropriate subpackage, expose from `huitu/__init__.py`, ship an example script and sample data.
