# huitu

> 材料科学一键式科研绘图工具包 — Journal-ready figures for materials-science papers.

[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Matplotlib](https://img.shields.io/badge/matplotlib-3.7%2B-11557c)](https://matplotlib.org/)
[![Style](https://img.shields.io/badge/output-600%20dpi-brightgreen)]()
[![SVG](https://img.shields.io/badge/SVG%2FPDF-editable--text-1a73e8)]()

`huitu` 把 matplotlib + scienceplots 包装成"一行出图"的体验：

* **44 个 ready-to-use 绘图函数**，覆盖材料学论文里最常见的表征 / 电化学 /
  第一性原理 / 高级统计 / 原位 (operando) 谱图。
* **8 大期刊预设**（Nature / Science / ACS / RSC / Wiley / Elsevier / IEEE
  / default），尺寸、字号、字重、刻度、配色一次性符合规范。
* **600 dpi 默认保存**，达到 Nature/Science/RSC 印刷标准，永远不糊。
* **可编辑 SVG/PDF 文字** ✨ — 默认 `svg.fonttype="none"` + `pdf.fonttype=42`，
  保存出来的图在 Illustrator / Inkscape 里能选中改字，不再被栅格成路径。
* **语义调色板** ✨ — `huitu.role("hero")` / `role("baseline")` / `role("positive")`
  按"科学角色"取色，整页所有 panel 都能保持配色一致。
* **4 大 Nature 排版 archetype** ✨ —
  `archetype.schematic_led` / `dark_image_plate` / `clinical_triptych` /
  `asymmetric_hero`，按论证类型而不是 `subplot(2,3)` 拼图。
* **投稿 QA 工具** ✨ — `check_redundancy()` 检查多 panel 信息是否冗余，
  `reviewer_checklist()` 给出 reviewer 可能挑刺的字段清单。
* **55 个调色板**（ggsci / Met-Brewer / Financial Times / Tol / Okabe-Ito /
  CARTO / Crameri / Nord / Editorial …），无需额外安装。

```python
import huitu

huitu.use_journal("nature")
huitu.plot_xrd("data.txt", save="fig1.svg")          # ✨ SVG 文字可编辑
huitu.plot_ridgeline(distributions, save="ridge.png")
huitu.plot_operando_xrd_echem(Z, x=q, y=t, echem=V, save="operando.pdf")

# v0.5 新加：用语义角色取色
ax.plot(t, y_mine, color=huitu.role("hero"),     label="Ours")
ax.plot(t, y_ref,  color=huitu.role("baseline"), label="Ref")

# v0.5 新加：4 大 Nature archetype 排版
fig, ax = huitu.archetype.schematic_led(journal="nature", n_supports=4)
ax["hero"].imshow(schematic_image)
huitu.plot_xrd("xrd.txt", ax=ax["supports"][0])
```

---

## 🖼 Showcase

| Palettes | Bump (rank evolution) | Operando waterfall |
|---|---|---|
| ![palettes](docs/showcase/001_pro_palette_catalog.png) | ![bump](docs/showcase/089_bump_paper_counts_by_technique.png) | ![waterfall](docs/showcase/168_op_waterfall_XRD_charge.png) |

| Operando XRD + electrochem | Operando diffmap | Operando contour |
|---|---|---|
| ![xrdec](docs/showcase/188_op_xrdec_XRD_galvanostatic_cycle_1.png) | ![diffmap](docs/showcase/202_op_diff_XRD_d-intensity_vs_pristi.png) | ![contour](docs/showcase/218_op_contour_XRD_contour_filled.png) |

> 完整 322 张高级图 gallery 在 `real_data_test/test_pro_gallery.py`，跑一次
> 即可在本地生成。

---

## 📦 安装

### 从源码装（推荐）

```bash
git clone https://github.com/yinliang420/Scientific_Illustration.git
cd Scientific_Illustration
pip install -e .                  # 主包
pip install -e ".[crystal]"       # 加上 ASE 晶体渲染
pip install -e ".[dev]"           # 加上 pytest / build / twine
```

### 从 wheel 装（分享给同事）

到 [Releases](https://github.com/yinliang420/Scientific_Illustration/releases) 页面下载最新的 `huitu-0.5.1-py3-none-any.whl`，或在本地自行打包：

```bash
pip install build && python -m build
# → dist/huitu-0.5.1-py3-none-any.whl
pip install dist/huitu-0.5.1-py3-none-any.whl
```

依赖：Python ≥ 3.9、matplotlib ≥ 3.7、numpy ≥ 1.23、pandas ≥ 1.5、
scipy ≥ 1.10、scienceplots ≥ 2.0、Pillow ≥ 9.0。

---

## 🚀 快速开始

```python
import huitu

# 1. 单图
huitu.plot_xrd("xrd.txt", journal="nature", save="xrd.pdf")

# 2. 多面板拼版
fig, axes = huitu.make_subplots(1, 2, journal="acs")
huitu.plot_xrd("xrd.txt",   ax=axes[0])
huitu.plot_raman("raman.txt", ax=axes[1])
fig.savefig("panel.pdf")

# 3. 高级统计图（v0.4 新加）
huitu.plot_ridgeline(distributions, labels=samples, save="ridge.png")
huitu.plot_bump(rankings, x_labels=years, save="bump.png")

# 4. Operando / 原位（v0.4 新加）
huitu.plot_operando_xrd_echem(
    Z,                           # 2D intensity matrix (M, N)
    x=two_theta, y=time,
    echem=voltage,
    xlabel=r"2$\theta$ (°)", ylabel="time (s)", ec_label="E (V)",
    save="operando.png",
)
```

每个 `plot_*` 函数都返回 `(fig, ax)`，并接受四种输入：路径字符串 / NumPy
`(N, 2)` 数组 / `(x, y)` 元组 / pandas DataFrame。

---

## 📑 覆盖的图类型（44 个）

| 类别 | 函数 |
|---|---|
| 表征谱图 | `plot_xrd` · `plot_xps` · `plot_raman` · `plot_ftir` · `plot_uvvis` · `plot_pl` · `plot_thermal` · `plot_rietveld` · `plot_operando` |
| 电化学 | `plot_cv` · `plot_gcd` · `plot_cycle` · `plot_eis` · `plot_bode` · `plot_tafel` |
| 第一性原理 | `plot_band` · `plot_dos` · `plot_cohp` · `plot_pourbaix` · `plot_phase_diagram` |
| 晶体结构 | `plot_crystal_ase` · `plot_crystal_vesta` |
| 通用数据图 | `plot_bar` · `plot_scatter` · `plot_line` · `plot_heatmap` · `plot_box_violin` · `plot_radar` · `plot_density` · `plot_shap` |
| **统计 / 比较** ✨ | `plot_ridgeline` · `plot_dumbbell` · `plot_slope` · `plot_bump` · `plot_parallel` · `plot_waffle` · `plot_streamgraph` · `plot_connected_scatter` |
| **原位 / Operando** ✨ | `plot_operando_waterfall` · `plot_operando_xrd_echem` · `plot_operando_3d_surface` · `plot_operando_diffmap` · `plot_operando_peak_evolution` · `plot_operando_contour` |
| 排版 | `make_subplots` · `add_inset` · `share_axes` · `panel_tag` · `supertitle` |
| **Nature archetype** ✨ v0.5 | `archetype.schematic_led` · `archetype.dark_image_plate` · `archetype.clinical_triptych` · `archetype.asymmetric_hero` |
| **投稿 QA** ✨ v0.5 | `role` · `check_redundancy` · `print_redundancy_report` · `reviewer_checklist` |

✨ = v0.4 新增统计/operando（原本付费 Pro），v0.5 新加 Nature 风格 archetype + QA 工具。

---

## ✨ v0.5 — Nature-style 升级

### 1. 可编辑 SVG / PDF（不用动代码，改个 rcParams 默认值）

每个期刊预设现在都包含：

```python
"svg.fonttype": "none"   # 文本保留为 <text> 节点
"pdf.fonttype": 42       # PDF 嵌入 TrueType
"ps.fonttype":  42
```

保存出来的 `.svg`、`.pdf` 文字都能在 Illustrator / Inkscape 选中、改字号、对齐 ——
评审拿到 figure 不会被"文字变成贝塞尔曲线"卡住。

### 2. 语义调色板：按"科学角色"取色

```python
ax.plot(t, y_mine, color=huitu.role("hero"),     label="Ours")
ax.plot(t, y_ref,  color=huitu.role("baseline"), label="Reference")
ax.scatter(xg, yg, color=huitu.role("positive"), marker="^")  # 涨
ax.scatter(xd, yd, color=huitu.role("negative"), marker="v")  # 跌
```

18 个角色键值对：

| 类别 | 键 | 用途 |
|---|---|---|
| 自己的方法 | `hero` / `hero_2` / `hero_soft` | 主方法、第二变体、第三变体 |
| 对照 / 参比 | `baseline` / `baseline_2` / `baseline_soft` | 控制组、副参比 |
| 方向性 | `positive` / `positive_soft` / `negative` / `negative_soft` | 涨 ↑ / 跌 ↓ |
| 中性 | `neutral` / `neutral_light` / `neutral_dark` / `neutral_black` | 背景、参考线 |
| 强调 | `accent_gold` / `accent_teal` / `accent_violet` / `accent_magenta` | callout、荧光通道 |

也可以一次性切换全图：`huitu.use_palette("semantic")`。

### 3. 四大 Nature 排版 archetype

```python
# 顶部 schematic + 底部 quant supports（材料/机理论文最常用）
fig, ax = huitu.archetype.schematic_led(journal="nature", n_supports=4)
ax["hero"].imshow(schematic_image)
huitu.plot_xrd("xrd.txt",   ax=ax["supports"][0])
huitu.plot_eis("eis.txt",   ax=ax["supports"][1])
huitu.plot_cycle("life.txt",ax=ax["supports"][2])
huitu.plot_cv("cv.txt",     ax=ax["supports"][3])

# 显微 / 荧光黑底 grid
fig, grid = huitu.archetype.dark_image_plate(rows=3, cols=5, journal="nature")
for r, row in enumerate(grid):
    for c, ax in enumerate(row):
        ax.imshow(microscopy[r][c])

# 临床 / 纵向"三段"：trajectories → forest → summary bars
fig, ax = huitu.archetype.clinical_triptych()  # ax['top'/'mid'/'bot'] 各 3 列

# 不对称：一个 panel 跨 3 行（UMAP / 圆形基因组图 / 大示意图）
fig, ax = huitu.archetype.asymmetric_hero()
ax["e"].set_title("hero panel")  # 跨行
```

每个 archetype 自动调用 `use_journal()`，画好小写粗体 panel label（a / b / c …），
继承当前预设的 600 dpi + 可编辑 SVG 默认值。

### 4. Anti-redundancy 检查

```python
huitu.print_redundancy_report([
    {"id": "a", "question": "What is the composition?",
     "encoding": "stacked_bar",     "level": "overview"},
    {"id": "b", "question": "What is atypical per group?",
     "encoding": "z_score_heatmap", "level": "deviation"},
    {"id": "c", "question": "How do tumor and immune % co-vary?",
     "encoding": "bubble_scatter",  "level": "relationship"},
])
# → [OK] no redundancy issues detected (3 panels).
```

会自动报警的情况：

- 两个 panel 在回答**同一个**科学问题
- 同一份 data slice 被两种图重复表达（堆叠柱 + 饼图）
- 缺少 **Overview → Deviation → Relationship** 三层信息层级中的某一层
- 两个 ranked-bar（应该把其中一个换成散点 / 气泡）

### 5. Reviewer-risk checklist

```python
rep = huitu.reviewer_checklist(
    figure={
        "core_conclusion": "Cu-doped MnO2 raises capacity by 32 %",
        "archetype": "schematic-led",
        "final_size": "183 mm × 130 mm",
    },
    quantitative={
        "n": "n=12 cells / group",
        "biological_replicates": 3,
        "center": "median", "spread": "IQR",
        "test": "two-sided Wilcoxon",
        "source_data": "fig3.csv",
    },
    image={"scale_bar": "50 µm", "raw_file": "raw/fig3a.tif"},
)
# 打印 PASS / FAIL，列出 [OK] [!!] required 缺失 / [??] recommended 缺失
# 还返回结构化 dict 给 CI 用：rep["pass"], rep["n_required_missing"]
```

四个可选 metadata 块：`figure` / `quantitative` / `image` / `machine_learning`。
每条对应 Springer Nature & Cell-family 期刊真实的 pre-submission checklist。

---

## 💡 Inspirations / 参考素材（v0.5.1 新加）

`docs/inspirations/` 是个**只读参考库**，不被 huitu 包导入，但 `git clone` 之后立刻就有：

### `figures4papers/` — 9 个真实 paper 画图代码

从 [`Yuan1z0825/nature-skills`](https://github.com/Yuan1z0825/nature-skills) → [`ChenLiu-1996/figures4papers`](https://github.com/ChenLiu-1996/figures4papers) 镜像，覆盖 NMI / ICML / NeurIPS / clinical review 风格：

| 你想画的图 | 看哪个 demo | 配套 huitu 函数 |
|---|---|---|
| 多方法 grouped bar | `figure_ImmunoStruct/plot_bars.py` | `plot_bar` + `huitu.role("hero" / "baseline")` |
| Ablation bar（alpha 渐变） | `figure_CellSpliceNet/plot_ablation.py` | `plot_bar` |
| Radar / polar 多 benchmark | `figure_VIGIL/plot_comparison_radar.py` | `plot_radar` |
| 训练 / 时间 trend | `figure_VIGIL/plot_posttraining.py` | `plot_line` |
| Heatmap / 矩阵 | `figure_RNAGenScape/plot_*` | `plot_heatmap` |
| 概念 3D 球体 / 示意 | `figure_Dispersion/plot_illustration.py` | `archetype.schematic_led['hero']` + `imshow` |
| Composition / 堆叠 | `figure_brainteaser/plot_correctness_*` | `plot_bar(stacked=True)` |

> ⚠️ 9 个 demo 里 **6 个开箱即跑**，3 个需要 LaTeX 或外部数据 —— 详见 [`docs/inspirations/README.md`](docs/inspirations/) 里的前置依赖表。

### `skills/` — 5 个 Nature 风 Claude Code skill

```bash
cp -R docs/inspirations/skills/nature-citation       ~/.claude/skills/   # 自动加 CNS 引用
cp -R docs/inspirations/skills/nature-academic-search ~/.claude/skills/  # PubMed/CrossRef/arXiv 搜索（带 MCP）
cp -R docs/inspirations/skills/nature-writing        ~/.claude/skills/   # 整段 Nature 写作
cp -R docs/inspirations/skills/nature-response       ~/.claude/skills/   # Reviewer 回复信
cp -R docs/inspirations/skills/nature-reader         ~/.claude/skills/   # 中英对照阅读器
```

`huitu` 主仓库本身专注于 plotting；这 5 个 skill 是配套的写作工作流，可选装。

---

## 🎨 调色板

```python
huitu.list_palettes()              # 55 个，按字母排序
huitu.use_palette("met-hiroshige") # 全局应用
cmap = huitu.get_cmap("crameri-batlow")
```

* **ggsci** — npg, aaas, jco, lancet, jama, nejm, frontiers, bmj, futurama,
  simpsons, startrek, tron, uchicago, d3, observable10
* **MetBrewer** — hiroshige, hokusai1/3, isfahan1, vangogh3, cassatt2,
  okeeffe2, tam, archambault, renoir, manet, derain, juarez, redon, johnson,
  egypt, klimt, kandinsky, monet
* **Financial Times** — categorical, diverging, sequential, night
* **基础** — tol-bright/muted/vibrant, okabe-ito, carto-safe/bold, nord,
  editorial, viridis6, nature-cat, nature-muted, science-cat, crameri-batlow,
  crameri-roma, bold-qualitative

---

## 📐 期刊预设

| 预设 | 默认色卡 | figsize | DPI |
|---|---|---|---|
| `default` | editorial | 3.5 × 2.8 in | 600 |
| `nature` | nature-cat | 89 × 70 mm | 600 |
| `science` | science-cat | 110 × 88 mm | 600 |
| `acs` | bold-qualitative | 3.33 × 2.5 in | 600 |
| `rsc` | tol-vibrant | 3.26 × 2.6 in | 600 |
| `wiley` | nord | 3.35 × 2.6 in | 600 |
| `elsevier` | okabe-ito | 90 × 70 mm | 600 |
| `ieee` | carto-safe | 3.5 × 2.5 in | 600 |

---

## 📚 文档

* **[USAGE.md](USAGE.md)** — 中文实操指南（推荐新手起步）
* **[SKILL.md](SKILL.md)** — 完整 API catalog · 期刊预设详表 · quirks · 数据格式规范
* **[CHANGELOG.md](CHANGELOG.md)** — 版本变更记录
* **[docs/inspirations/](docs/inspirations/)** — 9 个真实 paper 画图脚本（`figures4papers`）+ 5 个 Nature 风 skill（citation / search / writing / response / reader），带 chart-family 路由表 ✨ v0.5.1
* `examples/` — 31 个可独立运行的脚本，附合成样例数据
* `real_data_test/test_pro_gallery.py` — 322 个高级图场景
* `real_data_test/test_v05_features/` — v0.5 features 端到端测试（5 个脚本 + `run_all.sh`）

---

## 🧪 测试

```bash
# 单元测试
python -m pytest tests/ -v
# 82 passed (53 旧 + 29 v0.5 Nature features)

# v0.5 features 端到端测试（5 个脚本，21 个输出图）
bash real_data_test/test_v05_features/run_all.sh
# [ALL OK] every script passed

# 整套高级图 gallery（生成 322 张 600 dpi PNG + PDF）
python real_data_test/test_pro_gallery.py
# ===== huitu.pro gallery — 322 OK / 0 FAIL =====
```

---

## 📂 项目结构

```
huitu/
├── __init__.py                  # 44 plot_* + role + archetype + QA 顶层 API
├── style.py                     # 8 期刊预设 + 55 调色板（含 semantic）+ 600 dpi + 可编辑 SVG/PDF
├── archetype.py                 # ✨ v0.5 — 4 个 Nature 排版 (schematic_led / dark_image_plate / clinical_triptych / asymmetric_hero)
├── review.py                    # ✨ v0.5 — check_redundancy + reviewer_checklist
├── _common.py                   # 输入归一化 / axes 准备 / 注释边界保护
├── readers/txt_csv.py           # 支持 # / % 注释，tab/空白/逗号分隔
├── characterization/            # xrd, xps, raman, ftir, uvvis, pl, thermal, rietveld, operando
├── electrochem/                 # cv, gcd, cycle, eis, bode, tafel
├── computational/               # band, dos, cohp, pourbaix, phase_diagram, crystal
├── general/                     # bar, scatter, line, heatmap, box_violin, radar, density, shap
├── layout/                      # subplots, inset, shared_axes
└── pro/                         # legacy 命名空间 — v0.4 起作为别名
    ├── palettes.py              # 39 个 premium 调色板
    └── ridgeline.py / comparison.py / advanced.py / operando_pro.py
examples/                        # 31 个可运行脚本 + sample_data/
tests/                           # 82 个 pytest（53 旧 + 29 v0.5）
real_data_test/
├── test_pro_gallery.py          # 322 场景大图库
└── test_v05_features/           # ✨ v0.5 features 端到端测试（5 个脚本 + run_all.sh）
docs/
├── showcase/                    # README 用的 6 张展示图
└── inspirations/                # ✨ v0.5.1 — 9 真实 paper demo + 5 Nature skill（只读参考库）
    ├── figures4papers/          # ImmunoStruct / CellSpliceNet / VIGIL / brainteaser / ...
    └── skills/                  # nature-citation / -academic-search / -writing / -response / -reader
```

---

## 🚢 打包 & 分发

```bash
pip install build
python -m build           # → dist/huitu-0.5.1-py3-none-any.whl + .tar.gz
```

把 `.whl` 发给同事即可：

```bash
pip install huitu-0.5.1-py3-none-any.whl
```

---

## 🗺 路线图

* **v0.1** — 10 MVP 图（XRD/XPS/Raman/CV/GCD/Cycle/EIS/Bar/Scatter/Line）
* **v0.2** — +10：FTIR / UV-Vis / PL / TGA-DSC / Bode / Tafel / Band / DOS / Heatmap / Box-Violin
* **v0.3** — +7：Rietveld / COHP / Pourbaix / Phase diagram / Radar / Crystal + `share_axes`
* **v0.4** — +14 高级 / 原位图，Pro 全开，600 dpi 默认，39 个 premium 调色板，标签边界严格保护
* **v0.5.0** — Nature-style 升级：可编辑 SVG/PDF 文字 · 18-key 语义调色板（`role()`） · 4 大排版 archetype（schematic-led / dark image plate / clinical triptych / asymmetric hero） · anti-redundancy 检查 · reviewer-risk checklist
* **v0.5.1 (current)** — 3-agent test-review-fix 迭代修的 6 个 bug + 1 个 reviewer_checklist regression；`docs/inspirations/` 镜像 9 个真实 paper demo + 5 个 Nature 风 skill 作为参考库
* **v0.6 (planned)** — pymatgen 原生 `BSVasprun` 输入 · BET 等温线 · dQ/dV 曲线 · 多图组合 PDF 导出

---

## 🤝 贡献

新加一种图的最小步骤：

1. 在对应 `huitu/<subpackage>/` 下写新 `plot_*` 函数
2. 在 `huitu/__init__.py` 顶层导出
3. 在 `examples/<name>.py` 写一份可独立运行的样例脚本
4. 在 `tests/test_smoke.py` 参数化列表里加一行

---

## 📄 License

MIT — 详见 [LICENSE](LICENSE)。
