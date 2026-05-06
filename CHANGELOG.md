# Changelog

All notable changes to **huitu** are recorded here.

## [0.5.0] — 2026-05-06

Five Nature-style upgrades inspired by the
[`Yuan1z0825/nature-skills`](https://github.com/Yuan1z0825/nature-skills)
reference collection. The headline goal: turn `huitu` from "data → figure"
into "conclusion → figure", and make the saved file something an editor or
co-author can edit, not just admire.

### Added

- **Editable SVG/PDF text** — every preset (`default` / `nature` / `science` /
  `acs` / `rsc` / `wiley` / `elsevier` / `ieee`) now sets
  `svg.fonttype="none"`, `pdf.fonttype=42`, `ps.fonttype=42`. Text saved to
  `.svg` stays as `<text>` nodes (selectable, editable in
  Illustrator / Inkscape) instead of outlined paths; `.pdf` text is searchable
  and copy-able. No API change required — just save and the file is editable.
- **Semantic role palette** — new `huitu.role(name)` lookup and a
  `"semantic"` palette name. Map color to *scientific role* rather than
  category index:

  ```python
  ax.plot(x, y_mine, color=huitu.role("hero"),     label="Ours")
  ax.plot(x, y_ref,  color=huitu.role("baseline"), label="Baseline")
  ax.scatter(xg, yg, color=huitu.role("positive"), marker="^")  # gain
  ax.scatter(xd, yd, color=huitu.role("negative"), marker="v")  # drop
  ```

  18 keyed roles: `hero` / `hero_2` / `hero_soft`, `baseline` / `baseline_2` /
  `baseline_soft`, `positive` / `positive_soft`, `negative` / `negative_soft`,
  `neutral` / `neutral_light` / `neutral_dark` / `neutral_black`,
  `accent_gold` / `accent_teal` / `accent_violet` / `accent_magenta`. The
  `SEMANTIC_PALETTE` dict is also exported.
- **Four Nature-style figure archetypes** — new `huitu.archetype` module:
  - `archetype.schematic_led(n_supports=4)` — hero panel up top + a row of
    supporting quant panels; returns `{"hero": Axes, "supports": [Axes…]}`.
  - `archetype.dark_image_plate(rows=3, cols=5)` — black-faced microscopy /
    fluorescence grid with no spines or ticks; ready for `ax.imshow(...)`.
  - `archetype.clinical_triptych(n_cols=3)` — three semantically parallel
    rows (longitudinal → forest → summary); returns
    `{"top": [Axes…], "mid": [Axes…], "bot": [Axes…]}`.
  - `archetype.asymmetric_hero()` — 3 × 4 layout with one panel (`'e'`) that
    spans all rows; returns `{"a"…"f": Axes}`.

  Every archetype calls `use_journal()`, draws lowercase bold panel labels
  (Nature house style), and inherits the active preset's editable-text and
  600 dpi defaults.
- **Anti-redundancy panel checker** — `huitu.check_redundancy(panels)` and
  `huitu.print_redundancy_report(panels)` audit a multi-panel plan against
  the *Overview → Deviation → Relationship* hierarchy and surface common
  traps: same scientific question, same data slice in two visual forms,
  pie + stacked bar, two ranked-bar panels, missing information level.
  Returns a list of `PanelIssue(severity, panels, message)`.
- **Reviewer-risk checklist** — `huitu.reviewer_checklist(...)` accepts up
  to four metadata dicts (`figure`, `quantitative`, `image`,
  `machine_learning`) and produces a structured pass/fail report that flags
  every missing required field with a one-line hint. Targets the Nature /
  Springer pre-submission checklist (n, replicates, center, spread, test,
  correction, p-value display, source data, scale bar, image-integrity log,
  ML split / seeds / metric / baseline). Pretty-prints by default, returns a
  structured dict for CI gating.

### Changed

- `huitu/__init__.py` exports the five new public names: `role`,
  `SEMANTIC_PALETTE`, `archetype`, `check_redundancy`,
  `print_redundancy_report`, `reviewer_checklist`, `PanelIssue`.
- `pyproject.toml` URLs now point at the published GitHub repo
  (`yinliang420/Scientific_Illustration`).

### Tests

- 29 new pytest cases in `tests/test_nature_features.py` (parameterised over
  all 8 presets for editable text, plus end-to-end SVG-write check). Total
  suite: **82 tests**, all passing.

## [0.4.0] — 2026-04-25

Major release — Pro features merged, journal-grade DPI by default,
strict label-clearance guarantees.

### Added
- **14 advanced plot types** — formerly `huitu.pro.*`, now available
  directly from `huitu` and always enabled (no license / activation):
  - Statistical / comparison: `plot_ridgeline`, `plot_dumbbell`,
    `plot_slope`, `plot_bump`, `plot_parallel`, `plot_waffle`,
    `plot_streamgraph`, `plot_connected_scatter`
  - Operando / *in-situ* characterization: `plot_operando_waterfall`,
    `plot_operando_xrd_echem`, `plot_operando_3d_surface`,
    `plot_operando_diffmap`, `plot_operando_peak_evolution`,
    `plot_operando_contour`
- **39 premium palettes** — ggsci (NPG/AAAS/JCO/Lancet/JAMA/NEJM/Frontiers/
  BMJ/Futurama/Simpsons/StarTrek/Tron/uchicago/D3/Observable10), Met-Brewer
  (Hiroshige, Hokusai 1/3, Isfahan1, Van Gogh3, Cassatt2, Okeeffe2, Tam,
  Archambault, Renoir, Manet, Derain, Juarez, Redon, Johnson, Egypt, Klimt,
  Kandinsky, Monet), and Financial Times (categorical / diverging /
  sequential / night). Discoverable through standard `use_palette()` /
  `get_cmap()` APIs.
- Shared layout helpers: `marker_clearance_pts()` and
  `expand_xlim_for_annos()` in `huitu._common`.

### Changed
- **DPI defaults raised to journal-grade 600 dpi** across all
  presets (`default`, `nature`, `science`, `acs`, `rsc`, `wiley`,
  `elsevier`, `ieee`). `finalize()` now reads `savefig.dpi` from the
  active preset. Replace the previous 200 dpi raster output.
- **Strict label-clearance for `plot_bump` / `plot_slope` /
  `plot_connected_scatter`** — endpoint annotations are now offset by
  `marker_radius + pad`, never overlap the marker, and `xlim` is
  auto-expanded post-draw so end-of-line text never clips against the
  axes spine or the saved figure's bbox.

### Removed
- The Pro / VIP license gate. `huitu.pro.activate()` /
  `is_active()` / `require_pro()` are kept as no-ops for
  backwards-compatibility, and the legacy `huitu.pro.<func>` import
  paths still work as aliases.

### Fixed
- Bump / slope / connected-scatter end labels overlapping markers
  and clipping at figure edges.
- `crameri-vik` palette name corrected to the registered
  `crameri-roma` in the gallery test.

## [0.3.0]

- Added Rietveld, COHP, Pourbaix, phase diagram, radar, crystal renders
  + `share_axes` layout helper. (27 plot types total.)

## [0.2.0]

- Added FTIR, UV-Vis, PL, TGA-DSC, Bode, Tafel, band, DOS, heatmap,
  box-violin. (20 plot types total.)

## [0.1.0]

- Initial release: 10 MVP plots — XRD, XPS, Raman, CV, GCD, cycle, EIS,
  bar, scatter, line — and 8 journal presets.
