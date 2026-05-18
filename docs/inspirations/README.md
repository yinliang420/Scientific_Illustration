# Inspirations

Reference material adapted from upstream open-source projects to inform
`huitu`'s API design, plot defaults, and figure-archetype heuristics.

Everything in this folder is **read-only documentation / sample code** —
nothing here is imported by the `huitu` Python package. It's here so you
can `git clone` huitu and immediately see what a "Nature Machine
Intelligence-style" figure script looks like, without chasing through
half a dozen paper repos.

---

## Sources

| Folder | Upstream | License | Snapshot |
|---|---|---|---|
| `figures4papers/` | [`Yuan1z0825/nature-skills`](https://github.com/Yuan1z0825/nature-skills) → `skills/nature-figure/assets/figures4papers/` (originally from [`ChenLiu-1996/figures4papers`](https://github.com/ChenLiu-1996/figures4papers)) | MIT | Upstream commit `11e47b9` (2026-05-18) |
| `skills/` | [`Yuan1z0825/nature-skills`](https://github.com/Yuan1z0825/nature-skills) → `skills/nature-*/` | MIT (Copyright © 2026 Yuan Yizhe) | Upstream commit `11e47b9` (2026-05-18) |

Both upstream collections are MIT-licensed; copies here preserve that license. No file has been modified — only filtered (we keep `.py` scripts but skip the 24 MB of rendered PNG / raw data; regenerate locally if needed).

---

## `figures4papers/` — real-paper plotting scripts

Nine plotting projects extracted from published *Nature Machine
Intelligence* / top-venue papers. Each project has a `plot_*.py`
script + a `raw_data.py` data loader. Use them as **visual /
code references** when designing a new huitu function or an archetype
layout.

| Project | Domain | Chart family | huitu equivalent |
|---|---|---|---|
| `figure_ImmunoStruct/` | Immunology ML | Grouped bar + ablation bar | `plot_bar(grouped=True)` · `archetype.schematic_led` |
| `figure_CellSpliceNet/` | RNA splicing | Compact comparison + ablation | `plot_bar` · `archetype.clinical_triptych` (row 3) |
| `figure_brainteaser/` | LLM reasoning | Composition / category / sub-category bars + self-correction trends | `plot_bar(stacked=True)` · `plot_line` · `plot_streamgraph` |
| `figure_VIGIL/` | Vision-language | Radar/polar + post-training trend lines | `plot_radar` · `plot_line` (twin-y) |
| `figure_ophthal_review/` | Clinical review | Time trend + composition heatmap | `plot_line` · `plot_heatmap` |
| `figure_RNAGenScape/` | RNA generation | Heatmaps, manifold, sweep, optimization | `plot_heatmap` · `plot_density` · `plot_scatter(fit=True)` |
| `figure_Dispersion/` | DL theory | Conceptual 3D sphere + observation panels | `archetype.schematic_led['hero']` + custom `ax.imshow` |
| `figure_Cflows/` | Diffusion | Trajectory illustrations + gene-regulation comparisons + ablation | `archetype.asymmetric_hero` · `plot_streamgraph` · `plot_bar` |
| `figure_FPGM/` | Image processing | Frequency-prior distribution motivation | `plot_density` · `plot_line` |

### Chart-family routing — "想画 X 该看谁"

| 你想画的图 | 先看哪个 demo | 配套 huitu 函数 |
|---|---|---|
| 多方法 grouped bar 对比 | `figure_ImmunoStruct/plot_bars.py` | `plot_bar` + `huitu.role("hero")` / `role("baseline")` |
| Ablation bar（同色系 alpha 渐变） | `figure_CellSpliceNet/plot_ablation.py` | `plot_bar` 自己手动叠 alpha |
| Radar / polar 多 benchmark 对比 | `figure_VIGIL/plot_comparison_radar.py` | `plot_radar` |
| 训练曲线 trend | `figure_VIGIL/plot_posttraining.py`, `figure_ophthal_review/plot_trend.py` | `plot_line` |
| Heatmap / 矩阵 | `figure_RNAGenScape/plot_*` | `plot_heatmap` |
| 概念性 3D / 球体示意 | `figure_Dispersion/plot_illustration.py`, `figure_Cflows/diffusion_swiss_roll.py` | `archetype.schematic_led['hero']` + `ax.imshow` |
| Sweep / 优化进度 | `figure_RNAGenScape/plot_sweep.py` | `plot_line` + `plot_scatter` 叠加 |
| Composition / 堆叠贡献 | `figure_brainteaser/plot_correctness_*` | `plot_bar(stacked=True)` · `plot_streamgraph` |

### Prerequisites per demo — not all of them run "out of the box"

6 of the 9 projects run on a vanilla `matplotlib + numpy` install. The
other 3 need extra setup. Verified by running each demo locally
(2026-05-18, Python 3.13, matplotlib 3.10):

| Project | Status | What's needed |
|---|---|---|
| `figure_CellSpliceNet`   | ✅ runs immediately | — |
| `figure_Cflows`          | ✅ runs immediately | — |
| `figure_Dispersion`      | ✅ for `plot_idea.py`; ⚠️ `plot_illustration.py` needs **LaTeX** (`text.usetex=True`) | install MacTeX/TeX Live or set `usetex=False` |
| `figure_ImmunoStruct`    | ✅ runs immediately | — (data inlined in `raw_data.py`) |
| `figure_VIGIL`           | ✅ runs immediately | — |
| `figure_brainteaser`     | ✅ runs immediately | — |
| `figure_FPGM`            | ❌ needs **external `./data/` directory** | not shipped (upstream omits it too); provide your own `.npy`/`.pt` frequency-prior tensors |
| `figure_RNAGenScape`     | ❌ needs **LaTeX** (`text.usetex=True`) | install MacTeX/TeX Live, or patch the scripts to set `usetex=False` |
| `figure_ophthal_review`  | ❌ needs **LaTeX + seaborn** | `pip install seaborn` *and* install a TeX distribution |

### Run them locally (optional)

```bash
cd docs/inspirations/figures4papers/figure_ImmunoStruct/
python plot_bars.py    # PNG outputs land in figures/ (gitignored)
```

Each script is self-contained and uses only `matplotlib + numpy` unless
flagged above. The huitu `SKILL.md` (top-level) carries the same
prerequisite table so Claude sessions can warn users before pointing them
at a demo that won't run on their machine.

---

## `skills/` — Nature-tier writing / search workflows

Five Claude Code skills that complement `huitu`'s plotting focus:

| Skill | What it does |
|---|---|
| [`nature-citation/`](skills/nature-citation/) | Auto-add Nature/Science/Cell-family citations to manuscript text; splits prose into citable segments and exports `EndNote/RIS/Zotero RDF`. |
| [`nature-academic-search/`](skills/nature-academic-search/) | Multi-source literature search via MCP (PubMed, CrossRef, arXiv) + `.nbib/.ris/.bib` format conversion. Ships its own MCP server. |
| [`nature-writing/`](skills/nature-writing/) | Draft full Nature-style manuscript sections (abstract / intro / results / discussion) from claims, figures, or Chinese drafts. |
| [`nature-response/`](skills/nature-response/) | Point-by-point reviewer-response letters for major/minor revisions. |
| [`nature-reader/`](skills/nature-reader/) | Bilingual Chinese-English side-by-side Markdown reader for papers (preserves figure/table placement and source anchors). |

### Installing as Claude Code skills (optional)

These are *Claude Code* skills, not Python packages. To actually use them:

```bash
# Copy any subset you want to your global skills dir:
cp -R docs/inspirations/skills/nature-citation ~/.claude/skills/
cp -R docs/inspirations/skills/nature-academic-search ~/.claude/skills/
# … and so on
```

After that, `/skill` invocation in any Claude Code session will list them.

---

## Why mirror instead of submodule?

A git submodule would tie huitu's CI / clone speed to upstream's churn
(upstream emits ~20 "chore: refresh star history chart" commits per day).
Mirroring a single snapshot keeps this folder stable and lets us cherry-pick
only the pieces relevant to materials-science plotting. Upgrading is one
`rsync` + an attribution-file bump away.

---

## License + attribution

Both source collections are MIT (Copyright © 2026 Yuan Yizhe;
`figures4papers` further attributes [`ChenLiu-1996/figures4papers`](https://github.com/ChenLiu-1996/figures4papers)). The MIT
license is preserved here under [`LICENSE-UPSTREAM`](LICENSE-UPSTREAM). If you adapt one of
the demos in your own work, retain the same MIT notice.
