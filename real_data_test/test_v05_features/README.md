# v0.5-feature integration tests

End-to-end tests that exercise every v0.5 feature with **real sample
data**. Each script saves figures into `./output/` and prints a one-line
verdict; `run_all.sh` runs all five and exits non-zero on any failure.

| Script | What it proves |
| --- | --- |
| `test_01_editable_text.py` | After every `huitu.use_journal(name)` the relevant matplotlib rcParams (`svg.fonttype='none'`, `pdf.fonttype=42`, `ps.fonttype=42`) are applied AND saved SVGs actually contain `<text>` nodes (i.e. text is not silently outlined). Repeats for `default`, `nature`, `acs`, `rsc` plus a math-mixed sanity render. |
| `test_02_semantic_palette.py` | Every documented role key returns a `#RRGGBB` string equal to `SEMANTIC_PALETTE[key]`; lookup is case-insensitive; unknown keys raise `KeyError`. `use_palette('semantic')` swaps the prop_cycle. Renders a real "hero vs baseline" figure with positive/negative directional fill using `examples/sample_data/line.csv`. |
| `test_03_archetypes.py` | All four archetypes (`schematic_led`, `dark_image_plate`, `clinical_triptych`, `asymmetric_hero`) build under `journal="nature"` and accept real plot helpers (`plot_xrd`, `plot_cv`, `plot_eis`, `plot_raman`, `plot_bar`, `plot_heatmap`) inside their panels. Saves both PNG + SVG and verifies the SVGs retain editable text. |
| `test_04_redundancy.py` | `check_redundancy` correctly reports: clean plan (zero issues), same-question collisions (case+whitespace insensitive), same-data-slice collisions, pie+stacked trap, ranked-bar pair, missing info-levels (overview/deviation/relationship). Tests edge cases: empty list, single panel, missing `'question'`, malformed dict without `'id'`. `print_redundancy_report` prints `[OK]`/`[REVIEW]` headers. |
| `test_05_reviewer_checklist.py` | Per-section PASS/FAIL behaviour: complete Figure+Quantitative passes; dropping a single required field flips to FAIL; ML-only / image-only invocations include the right section; passing all four sections complete passes. Edge cases: `print_report=False` is silent, `value=0` accepted, very-long values truncated, `machine_learning={}` is silently skipped. |

## Run

```bash
./run_all.sh                              # uses /Users/ylll/miniconda3/bin/python
HUITU_TEST_PYTHON=/path/to/python ./run_all.sh
```

Outputs land in `./output/` (PNG + SVG figures, plus `redundancy_log.txt`
and `reviewer_log.txt`).
