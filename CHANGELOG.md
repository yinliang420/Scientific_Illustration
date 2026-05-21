# Changelog

All notable changes to **huitu** are recorded here.

## [0.5.2] — 2026-05-21

Polish release after the three-round hardening loop closed (see
[`docs/hardening-case-study.html`](docs/hardening-case-study.html) for
the full engineering writeup).

### Changed

- **Dead-import sweep.** Eight stale imports removed across `huitu/`:
  `Iterable` (in `archetype.py`, `general/radar.py`, `computational/band.py`),
  `Path` (in `characterization/xrd.py`), `place_legend` (in
  `pro/ridgeline.py`), `_GRADIENT_PALETTES` top-level reference (in
  `pro/operando_pro.py`), and `numpy as np` (in `electrochem/cv.py` +
  `gcd.py`). No behavior change; pytest stays 82/82.
- **Version bump.** `pyproject.toml` 0.5.1 → 0.5.2 — the v0.5.1 string
  had lagged behind the Round 2 + Round 3 fixes that already shipped
  in the codebase via PR #2.

### Added

- **Three "fusion" examples** under `examples/nature_*.py` that
  reproduce visual patterns from `figures4papers` using huitu's own API
  (`role()`, `archetype.schematic_led`, semantic palette):
  - `nature_immunostruct_bars.py` — 4-method grouped bar with
    monotone-emphasis colour mapping.
  - `nature_vigil_trend.py` — alpha-graduated trend lines with direct
    end-of-line labels (no detached legend).
  - `nature_schematic_led_demo.py` — end-to-end `archetype.schematic_led`
    walkthrough: synthetic three-stage mechanism schematic in the hero
    panel plus real XRD/CV/EIS + a capacity-by-stage bar in the four
    support panels.
- **100-figure random gallery** at
  `real_data_test/random_gallery/render_100.py` — exercises every
  public plot entry point (all 44 `plot_*` plus 4 archetypes) with
  synthetic data + varied journal presets. 100 successful PNGs in ~14 s,
  every category reached. Output gitignored.

## [0.5.1] — 2026-05-06

Patch release: bug fixes surfaced by a 3-agent test-review-fix iteration
(`real_data_test/test_v05_features/`). All v0.5 features remain unchanged
in scope, just hardened.

### Fixed

- **`huitu.review.check_redundancy`** — three sites used `p["id"]` without a
  default, raising `KeyError` when a panel dict lacked `id`. Now produces a
  proper `PanelIssue` with `"?"` placeholder. Reproducer:
  `check_redundancy([{"question": "Q?", "encoding": "stacked_bar"}])`.
- **`huitu.review.reviewer_checklist` section policy** — explicit split
  between *core* and *opt-in* sections:
  - `figure` and `quantitative` are core: ``None`` → ``{}`` so they always
    run, surfacing missing required fields. A bare `reviewer_checklist()`
    call now correctly fails on missing core scaffolding (Fig 1 conclusion,
    final size, n / center / spread / test / source data).
  - `image` and `machine_learning` are modality opt-ins: omitting the
    parameter (`None`) skips silently; passing any dict (even ``{}``)
    enables the section. Closes a v0.5.0 regression where `machine_learning={}`
    was silently dropped.
- **`huitu.archetype.{schematic_led, dark_image_plate, clinical_triptych,
  asymmetric_hero}`** — switched to `constrained_layout=True` (was
  `False`, defeating the library-wide default). Eliminates panel-`b`
  tick labels touching panel `a`, restores the missing colorbar in
  `asymmetric_hero`'s panel `f`, and balances support panels in
  `schematic_led` when one is `equal_aspect=True` (e.g. `plot_eis`).
- **`huitu.archetype._label`** — switched panel-letter placement from
  axes-fraction (`x=-0.06, y=1.02`) to absolute point-pad (`xpad=-18,
  ypad=4`) via `ax.annotate(..., textcoords="offset points")`. Letters
  now sit in the figure margin instead of overlapping the panel's
  y-axis label on tight grids.
- **`huitu.style`** — removed `"Liberation Sans"` from the font family
  fallback stack. Never installed on macOS or vanilla Windows; matplotlib
  still falls through to `DejaVu Sans`. Eliminates ~24 `findfont` warnings
  per draw.
- **`huitu.review.PanelIssue.__str__`** — `"/".join(self.panels)` crashed
  with `TypeError` when a panel's `id` field was a non-string (int, tuple,
  None, etc.). All four sites in `check_redundancy` that pull `p["id"]`
  into the issue tuple now coerce via `str(...)`, so `PanelIssue` is safe
  to format regardless of what the caller stuffs into `id`.
- **`huitu.review.check_redundancy`** — added a duplicate-id rule: two
  panels sharing the same letter (e.g. both `"a"`) now raise a `warn`-level
  `PanelIssue`, since every Nature panel needs a unique label. Also now
  accepts generators / non-sized iterables — the body materialises the
  input into a list on entry so `len(panels)` and the multi-pass loops
  work uniformly.
- **`huitu.style.SEMANTIC_PALETTE`** and **`huitu.PALETTES`** — both
  registries are now wrapped in `types.MappingProxyType`, so accidental
  in-place mutation (`huitu.SEMANTIC_PALETTE["hero"] = "#FFFFFF"`) raises
  `TypeError` instead of silently corrupting every figure in the session.
  `PALETTES` is frozen *after* `huitu.pro` registers its premium palettes,
  so the full registry is still available — just immutable.
- **Tightened `SEMANTIC_PALETTE` freeze (Round 3 follow-up)** — backing
  storage is now a tuple-stored `_FrozenStrMap` rather than a
  `MappingProxyType(dict)`, closing a `gc.get_referents()` bypass channel
  that allowed silent corruption of `role()` lookups. Previously, an
  attacker could run `gc.get_referents(huitu.SEMANTIC_PALETTE)` to obtain
  the wrapped dict and mutate it; the snapshot now lives in a single
  immutable tuple slot, so `gc.get_referents` only surfaces the tuple and
  the class object. `_PALETTES_BACKING` remains the documented trust root
  for the `PALETTES` registry — it is intentionally writable so
  `register_pro_palettes()` can extend it, and its `__getitem__` already
  hands out defensive `list` copies.

  **Breaking-name note:** `type(huitu.SEMANTIC_PALETTE).__name__` changed
  from `'mappingproxy'` to `'_FrozenStrMap'`. The public contract
  (immutable mapping with `__getitem__`, `__contains__`, `__iter__`,
  `__len__`, `keys()`, `items()`, `values()`, `get()`, `copy()`) is
  unchanged. If you depend on the exact type name, use
  `isinstance(huitu.SEMANTIC_PALETTE, collections.abc.Mapping)` instead.
  `dict(huitu.SEMANTIC_PALETTE)` remains the documented serialization
  escape hatch and continues to round-trip through pickle / json /
  deepcopy.

### Future

- Optional placeholder-string detection in `reviewer_checklist`
  (`"todo"`, `"tbd"`, `"?"`) — needs a UX call before shipping because
  `source_data="n/a"` is sometimes legitimate.

### Tests

- 5 new end-to-end test scripts in `real_data_test/test_v05_features/`
  exercising every v0.5 feature against real sample data
  (`test_01_editable_text.py`, `..._semantic_palette`, `..._archetypes`,
  `..._redundancy`, `..._reviewer_checklist`) plus a `run_all.sh` driver.
  Used by the 3-agent iteration; output PNG/SVG dir is gitignored.
- 5 adversarial test scripts in `real_data_test/test_v06_adversarial/`
  hammering the same surface with edge-case inputs (non-string panel ids,
  generators, duplicate ids, `MappingProxyType` mutation attempts, etc.).
- 5 Round-2 adversarial scripts in `real_data_test/test_v07_adversarial/`
  probing `MappingProxyType` escape hatches (subscript / `update` / `pop`,
  `importlib.reload`, pickle / `copy.copy` / `deepcopy`, threading / fork,
  and review-module corner-cases) — the type-name checks accept either
  `'mappingproxy'` or `'_FrozenStrMap'` to track the Round-3 freeze upgrade.
- 6 Round-3 adversarial scripts in `real_data_test/test_v08_adversarial/`
  including a new `test_06_semantic_gc_bypass.py` that verifies the
  `gc.get_referents` channel is closed.
- Existing pytest suite still **82/82 passing**.

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
