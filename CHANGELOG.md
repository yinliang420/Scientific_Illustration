# Changelog

All notable changes to **huitu** are recorded here.

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
