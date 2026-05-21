# Repo layout

`huitu` is a single Python package. This file is the one-stop reference for
"where does X live and why."

```
huitu_skills/                      ← repo root (= the GitHub repo)
├── huitu/                         ← THE LIBRARY (all plotting code lives here)
│   ├── __init__.py                ← public API surface — re-exports 44 plot_* + role + archetype + …
│   ├── style.py                   ← 8 journal presets + 55 palettes + _FrozenStrMap + _PALETTES_BACKING
│   ├── archetype.py               ← 4 Nature-style layouts (schematic_led / dark_image_plate / …)
│   ├── review.py                  ← check_redundancy + reviewer_checklist
│   ├── _common.py                 ← internal helpers (coerce_xy, prepare_axes, finalize, …)
│   ├── characterization/          ← 1 module per spectroscopy: xrd · xps · raman · ftir · uvvis · pl · thermal · rietveld · operando · bet (v0.6)
│   ├── electrochem/               ← cv · gcd · cycle · eis · bode · tafel · dqdv (v0.6)
│   ├── computational/             ← band · dos · cohp · pourbaix · phase_diagram · crystal
│   ├── general/                   ← bar · scatter · line · heatmap · box_violin · radar · density · shap_like
│   ├── layout/                    ← subplots · inset · shared_axes · pdf_report (v0.6)
│   ├── pro/                       ← legacy alias namespace (v0.4 advanced + operando charts)
│   └── readers/                   ← txt/csv input normalisation
│
├── tests/                         ← pytest unit tests (82, all green)
│
├── examples/                      ← THIN DEMOS (~10–30 lines each) showing how to call huitu
│   ├── xrd_single.py              ← e.g. `from huitu import plot_xrd; plot_xrd(...)`
│   ├── …                          ← one demo per plot family
│   ├── output/                    ← demo PNG outputs (TRACKED — used as showcase images)
│   └── sample_data/               ← synthetic two-column txt files for demos
│
├── real_data_test/                ← END-TO-END / ADVERSARIAL test suites (NOT pytest)
│   ├── test_v05_features/         ← v0.5 features end-to-end
│   ├── test_v06_adversarial/      ← Round 1: 67 functional bug cases
│   ├── test_v07_adversarial/      ← Round 2: 56 MappingProxy attack cases
│   ├── test_v08_adversarial/      ← Round 3: 96 boundary + gc-bypass cases
│   ├── random_gallery/            ← 100-figure stress-test script (output gitignored)
│   ├── test_pro_gallery.py        ← 322-scenario advanced gallery
│   └── output_* (gitignored)      ← regenerable outputs, never tracked
│
├── docs/
│   ├── hardening-case-study.html  ← 3-round 4-agent hardening engineering writeup
│   ├── showcase/                  ← README hero images (bug-by-round + tests-by-round charts)
│   └── inspirations/              ← Read-only mirror of Yuan1z0825/nature-skills (figures4papers + 5 sibling skills)
│
├── tools/                         ← maintenance scripts (NOT shipped in wheel)
│   └── render_hardening_charts.py ← regenerates the case-study charts using huitu itself
│
├── README.md         ← project entry point (badges + quickstart + 📑 hardening case study link)
├── SKILL.md          ← full plot catalogue with `Source` and `Demo` columns
├── USAGE.md          ← Chinese-language hands-on guide
├── CHANGELOG.md      ← version-by-version changes
├── LICENSE           ← MIT
├── MANIFEST.in       ← controls what ships in the wheel (excludes examples/ + tests/ + real_data_test/)
└── pyproject.toml    ← package metadata + dependencies
```

## What goes on GitHub vs what stays local

The repo is **lean by design**. Everything in the tree above is tracked. The
`.gitignore` deliberately excludes:

| Excluded path | Reason |
|---|---|
| `build/`, `dist/`, `*.egg-info/`, `.pytest_cache/` | Python build artefacts — regenerable |
| `__pycache__/`, `*.pyc`, `.DS_Store` | Caches / OS noise |
| `real_data_test/output*/`, `real_data_test/test_v*_*/output/` | Generated test outputs (~270 MB) |
| `xrd_real_patterns_*/` | Local raw experimental data |
| `docs/inspirations/figures4papers/**/*.png` | Demo-renderer outputs (regenerable by running the upstream scripts) |
| `reports/` | Per-turn private modification notes |
| `.claude/`, `.cursor/`, `.vscode/`, `.idea/` | Editor / agent state |

`git ls-files` is the authoritative list of "what reaches GitHub." If you ever
suspect drift between what's tracked and what's local, `git ls-files | sort`
and `ls -la` side-by-side tell the truth.

## "Where's the actual plotting code?"

**Only in `huitu/`.** The `examples/` directory is just thin demonstration
scripts that call into `huitu`. If you want to read or modify how `plot_xrd`
works, open `huitu/characterization/xrd.py`. The `Source` column in
[`SKILL.md`](SKILL.md) lists every function's file directly so this never has
to be guessed.

## Add a new plot type

1. **Write the function** in the appropriate subpackage:
   `huitu/<characterization|electrochem|computational|general|layout>/<name>.py`
2. **Export from the top level** in `huitu/__init__.py` (both the import line and the `__all__` entry).
3. **Add a demo** in `examples/<name>.py` (10–30 lines — just a call site).
4. **Add a row** to the `Plot catalogue` table in [`SKILL.md`](SKILL.md) with
   the function name, `Source` path, `Demo` path, and a one-line note.
5. **Add a pytest** in `tests/test_smoke.py` (parameterised list) covering the
   journal presets that matter.
6. **Add a CHANGELOG entry** under the upcoming version.

Run `pytest tests/ -q` after each step.
