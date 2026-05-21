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
├── tests/                         ← pytest unit tests (57, all green)
│
├── examples/                      ← SIX CANONICAL DEMOS (slim — full per-function calling conventions live in each plot_*'s docstring)
│   ├── quickstart.py              ← one-line plot_xrd with journal preset
│   ├── multi_panel.py             ← archetype + role + plot_* combined
│   ├── bet.py                     ← BET isotherm (v0.6)
│   ├── dqdv.py                    ← differential capacity (v0.6)
│   ├── pdf_report.py              ← multi-figure PDF report (v0.6)
│   ├── reviewer_checklist.py      ← anti-redundancy + reviewer-checklist QA
│   ├── output/                    ← generated demo outputs (gitignored — regenerable)
│   └── sample_data/               ← synthetic two-column txt files for demos
│
├── docs/showcase/                 ← README hero images (6 PNGs used in the Showcase grid)
│
├── README.md         ← project entry point (badges + quickstart + showcase grid)
├── SKILL.md          ← full plot catalogue with `Source` column + inline quickstart snippets
├── CHANGELOG.md      ← version-by-version changes
├── LICENSE           ← MIT
├── MANIFEST.in       ← controls what ships in the wheel (excludes examples/ + tests/)
└── pyproject.toml    ← package metadata + dependencies
```

## What goes on GitHub vs what stays local

The repo is **lean by design**. Everything in the tree above is tracked. The
`.gitignore` deliberately excludes:

| Excluded path | Reason |
|---|---|
| `build/`, `dist/`, `*.egg-info/`, `.pytest_cache/` | Python build artefacts — regenerable |
| `__pycache__/`, `*.pyc`, `.DS_Store` | Caches / OS noise |
| `examples/output/` | Generated example outputs (regenerable) |
| `xrd_real_patterns_*/` | Local raw experimental data |
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
3. **Add a row** to the `Plot catalogue` table in [`SKILL.md`](SKILL.md) with
   the function name, `Source` path, and a one-line note. If the function
   warrants top-level visibility, add an entry to the "Inline quickstart
   snippets" subsection of the same file.
4. **Add a pytest** in `tests/test_smoke.py` covering the journal presets
   that matter (use the parameterised `test_use_journal_all_presets` pattern).
5. **Add a CHANGELOG entry** under the upcoming version.
6. *(Optional)* If the function is one of the six canonical workflow
   demonstrations, add an `examples/<name>.py` script — but the per-function
   calling conventions live in the function's docstring (`help(plot_*)`),
   not as a one-script-per-function fixture.

Run `pytest tests/ -q` after each step.
