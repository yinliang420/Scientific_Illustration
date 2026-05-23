# huitu 使用指南

> 一份**完整的从安装到出图**操作手册，覆盖两类用户：
>
> - **路径 A** — 你**没有** Claude Code / Codex 等智能体平台，纯靠 Python 调用
> - **路径 B** — 你**有** Claude Code / Codex，希望让 agent 自动激活 huitu 帮你画图
>
> 两条路径**互不冲突**，可以同时使用。

---

## 目录

1. [huitu 是什么](#1-huitu-是什么)
2. [路径 A：纯 Python 用户](#2-路径-a纯-python-用户)
   - 2.1 [环境准备](#21-环境准备)
   - 2.2 [第一张图（30 秒）](#22-第一张图30-秒)
   - 2.3 [数据格式约定](#23-数据格式约定)
   - 2.4 [按图类型查源码位置](#24-按图类型查源码位置)
   - 2.5 [六个开箱即用的示范脚本](#25-六个开箱即用的示范脚本)
   - 2.6 [期刊预设与导出格式](#26-期刊预设与导出格式)
   - 2.7 [多面板拼版与 Nature archetype](#27-多面板拼版与-nature-archetype)
3. [路径 B：Claude Code / Codex 智能体用户](#3-路径-bclaude-code--codex-智能体用户)
   - 3.1 [安装 skill bundle](#31-安装-skill-bundle)
   - 3.2 [触发词：让 agent 自动激活 huitu](#32-触发词让-agent-自动激活-huitu)
   - 3.3 [如何"锁定"到某一种图](#33-如何锁定到某一种图)
   - 3.4 [典型 prompt 模板](#34-典型-prompt-模板)
4. [常见问题与故障排查](#4-常见问题与故障排查)

---

## 1. huitu 是什么

`huitu`（绘图）是一个**材料科学一键出图**的 Python 包：

- **46 个 `plot_*` 函数**，覆盖 XRD / XPS / Raman / FTIR / UV-Vis / PL / TGA-DSC / Rietveld / BET / CV / GCD / EIS / Tafel / dQ/dV / band / DOS / COHP / Pourbaix / 相图 / 晶体结构 / 散点 / 柱 / 折线 / 热图 / 箱线 / 雷达 / KDE / SHAP / ridgeline / bump / streamgraph / parallel-coords / 6 种 operando 等
- **8 个期刊预设**：`nature` / `science` / `acs` / `rsc` / `wiley` / `elsevier` / `ieee` / `default`
- **4 个 Nature 排版 archetype**：`schematic_led` / `dark_image_plate` / `clinical_triptych` / `asymmetric_hero`
- **600 dpi + 可编辑 SVG/PDF 文字**默认开启
- **投稿前 QA 工具**：`check_redundancy()` + `reviewer_checklist()`

每个 `plot_*` 都接受四种输入（路径字符串 / NumPy `(N, 2)` / `(x, y)` tuple / pandas DataFrame），都返回 `(fig, ax)` 让你继续 Matplotlib 二次加工。

---

## 2. 路径 A：纯 Python 用户

适合你的情况：**写脚本、跑 Jupyter、不依赖任何 agent 平台**。

### 2.1 环境准备

#### 基础依赖

| 依赖 | 最低版本 |
|---|---|
| Python | 3.9 / 3.10 / 3.11 / 3.12 |
| matplotlib | 3.7 |
| numpy | 1.23 |
| pandas | 1.5 |
| scipy | 1.10 |
| scienceplots | 2.0 |
| Pillow | 9.0 |

#### 推荐：用虚拟环境隔离

```bash
# conda
conda create -n huitu python=3.11 -y
conda activate huitu

# 或 venv
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows
```

#### 安装 huitu

**方式 1：从源码安装（推荐，方便调试）**

```bash
git clone https://github.com/yinliang420/Scientific_Illustration.git
cd Scientific_Illustration
pip install -e .                  # 主包
pip install -e ".[crystal]"       # 想画晶体结构再加这个（需要 ASE）
pip install -e ".[dev]"           # 想跑测试再加这个
```

**方式 2：从 wheel 安装（不需要源码）**

[Releases 页](https://github.com/yinliang420/Scientific_Illustration/releases) 下载 `huitu-0.6.3-py3-none-any.whl`：

```bash
pip install huitu-0.6.3-py3-none-any.whl
```

#### 验证安装

```bash
python -c "import huitu; print(huitu.__version__)"
# 应输出 0.6.3（或更新版本）

python -c "import huitu; print(len([n for n in dir(huitu) if n.startswith('plot_')]))"
# 应输出 46
```

### 2.2 第一张图（30 秒）

把你的 XRD 数据存成 `xrd.txt`（两列：`2θ`, `intensity`，制表符 / 空格 / 逗号分隔都行）：

```
10.00  120
10.02  118
10.04  121
...
```

然后：

```python
import huitu

huitu.plot_xrd("xrd.txt", journal="nature", save="fig1.pdf")
```

出来的 `fig1.pdf` 已经是：
- 89 × 70 mm 的 Nature 单栏尺寸
- Helvetica 字体
- 600 dpi
- PDF 里的文字**可在 Illustrator/Inkscape 里直接选中编辑**

### 2.3 数据格式约定

| 图类型 | 数据格式 |
|---|---|
| **两列谱图**（XRD / XPS / Raman / FTIR / UV-Vis / PL / CV / GCD / EIS / Tafel / Bode） | `.txt`/`.csv`，两列 `x, y`；`#`/`%` 开头视为注释；制表符、空格、逗号分隔都识别 |
| **三列循环数据**（cycling + CE） | 三列 `cycle, capacity, coulombic_efficiency`（CE 列可省） |
| **柱图 / 折线 / 散点** | CSV **必须带表头**；第一列是 category / x 轴，其余列是 series（列名 → 图例） |
| **TGA + DSC 双轴** | 两个独立的 `(x, y)`：`plot_thermal(tga_data, mode='both', dsc_data=...)` |
| **二维 operando 矩阵** | 二维 NumPy 数组 `Z[M, N]` + 一维 `x`、`y` 坐标向量 |
| **Pourbaix / 相图** | inline Python dict：`{相名: [(pH, E), …]}`（多边形顶点） |

不知道某个函数的具体输入？查 docstring：

```python
help(huitu.plot_xrd)
# 或 IDE 里直接 hover 函数名
```

### 2.4 按图类型查源码位置

**所有出图代码都在 `huitu/` 下**，按学科分子包。下表是常用查找索引（完整版见 [SKILL.md](SKILL.md) 的 Plot catalogue）：

| 你想画的图 | 函数名 | 源码位置 |
|---|---|---|
| XRD | `plot_xrd` | `huitu/characterization/xrd.py` |
| XPS（含拟合峰） | `plot_xps` | `huitu/characterization/xps.py` |
| Raman | `plot_raman` | `huitu/characterization/raman.py` |
| FTIR | `plot_ftir` | `huitu/characterization/ftir.py` |
| UV-Vis / Tauc | `plot_uvvis` | `huitu/characterization/uvvis.py` |
| PL | `plot_pl` | `huitu/characterization/pl.py` |
| TGA / DSC | `plot_thermal` | `huitu/characterization/thermal.py` |
| Rietveld（双面板） | `plot_rietveld` | `huitu/characterization/rietveld.py` |
| BET 等温线（双面板 + 自动标 S_BET） | `plot_bet` | `huitu/characterization/bet.py` |
| Operando 热图 | `plot_operando` | `huitu/characterization/operando.py` |
| CV | `plot_cv` | `huitu/electrochem/cv.py` |
| GCD | `plot_gcd` | `huitu/electrochem/gcd.py` |
| 循环 + CE 双 Y | `plot_cycle` | `huitu/electrochem/cycle.py` |
| EIS Nyquist | `plot_eis` | `huitu/electrochem/eis.py` |
| Bode | `plot_bode` | `huitu/electrochem/bode.py` |
| Tafel | `plot_tafel` | `huitu/electrochem/tafel.py` |
| dQ/dV | `plot_dqdv` | `huitu/electrochem/dqdv.py` |
| 能带（含 pymatgen 输入） | `plot_band` | `huitu/computational/band.py` |
| DOS / PDOS | `plot_dos` | `huitu/computational/dos.py` |
| COHP / ICOHP | `plot_cohp` | `huitu/computational/cohp.py` |
| Pourbaix E-pH | `plot_pourbaix` | `huitu/computational/pourbaix.py` |
| 二元相图 | `plot_phase_diagram` | `huitu/computational/phase_diagram.py` |
| 晶体结构 | `plot_crystal_ase` / `plot_crystal_vesta` | `huitu/computational/crystal.py` |
| 柱状（分组 / 堆叠） | `plot_bar` | `huitu/general/bar.py` |
| 散点 + 拟合 | `plot_scatter` | `huitu/general/scatter.py` |
| 折线（双 Y 轴） | `plot_line` | `huitu/general/line.py` |
| 热图 / 等高线 | `plot_heatmap` | `huitu/general/heatmap.py` |
| 箱线 / 小提琴 | `plot_box_violin` | `huitu/general/box_violin.py` |
| 雷达 | `plot_radar` | `huitu/general/radar.py` |
| 2D KDE | `plot_density` | `huitu/general/density.py` |
| SHAP 风格 | `plot_shap` | `huitu/general/shap_like.py` |
| Ridgeline | `plot_ridgeline` | `huitu/pro/ridgeline.py` |
| Dumbbell / Slope / Bump / Parallel / Waffle / Streamgraph / Connected | `plot_dumbbell` 等 | `huitu/pro/comparison.py` · `huitu/pro/advanced.py` |
| 6 种 operando 进阶 | `plot_operando_waterfall` 等 | `huitu/pro/operando_pro.py` |
| 拼版工具 | `make_subplots` / `add_inset` / `share_axes` / `make_pdf_report` | `huitu/layout/*.py` |
| Nature archetype（4 种） | `archetype.schematic_led` 等 | `huitu/archetype.py` |
| QA 工具 | `check_redundancy` / `reviewer_checklist` | `huitu/review.py` |

**找代码的实用技巧**：

```bash
# 直接 grep 函数名
grep -rn "def plot_xrd" huitu/

# 或者在 Python 里查
python -c "import huitu; import inspect; print(inspect.getfile(huitu.plot_xrd))"
```

### 2.5 六个开箱即用的示范脚本

仓库 `examples/` 下有六个**完整可运行**的范例，配套合成数据放在 `examples/sample_data/`：

| 脚本 | 演示什么 |
|---|---|
| `examples/quickstart.py` | 一行出 XRD，最小示范 |
| `examples/multi_panel.py` | archetype + role + 多个 `plot_*` 组合 |
| `examples/bet.py` | BET 等温线（双面板 + 自动算 S_BET / V_m） |
| `examples/dqdv.py` | 多 cycle dQ/dV 老化对比 |
| `examples/pdf_report.py` | 把若干 figure 合成多页 PDF 报告 |
| `examples/reviewer_checklist.py` | 投稿前 anti-redundancy + reviewer checklist |

运行方式：

```bash
# 在仓库根目录
python examples/quickstart.py
# 输出会进 examples/output/（gitignored，可随便重跑）
```

**推荐工作流**：找最接近你需求的那个脚本，**复制一份到你自己的项目里**，然后改数据路径 + 改几行参数就能出图。

### 2.6 期刊预设与导出格式

```python
# 全局切预设
huitu.use_journal("nature")     # 之后所有 plot_* 都用 Nature 规格
huitu.plot_xrd("xrd.txt", save="x.pdf")

# 或单图临时切
huitu.plot_xrd("xrd.txt", journal="acs", save="x.pdf")
```

| 预设 | 字号 | figsize | 默认色卡 |
|---|---|---|---|
| `default` | 8 pt | 3.5 × 2.8 in | editorial |
| `nature` | 7 pt | 89 × 70 mm | nature-cat |
| `science` | 7 pt | 110 × 88 mm | science-cat |
| `acs` | 8 pt | 3.33 × 2.5 in | bold-qualitative |
| `rsc` | 8 pt | 3.26 × 2.6 in | tol-vibrant |
| `wiley` | 8 pt | 3.35 × 2.6 in | nord |
| `elsevier` | 8 pt | 90 × 70 mm | okabe-ito |
| `ieee` | 8 pt | 3.5 × 2.5 in | carto-safe |

**导出格式建议**：

- `save="fig.pdf"` 或 `save="fig.svg"` → 文字可在 Illustrator/Inkscape 编辑（投稿首选）
- `save="fig.png"` → 600 dpi 栅格（PPT、邮件、博客）
- 同时保存多个：手动 `fig.savefig("fig.pdf"); fig.savefig("fig.png", dpi=600)`

### 2.7 多面板拼版与 Nature archetype

**简单两图并排**：

```python
from huitu import make_subplots, plot_xrd, plot_raman

fig, axes = make_subplots(1, 2, journal="acs")
plot_xrd("xrd.txt",   ax=axes[0])
plot_raman("raman.txt", ax=axes[1])
fig.savefig("panel.pdf")     # 自动加 (a)(b) panel label
```

**Nature 风格论证型排版（v0.5）**：

```python
import huitu

# 顶部一个大示意图 + 底下三个支撑性 quantitative panel
fig, ax = huitu.archetype.schematic_led(journal="nature", n_supports=3)
ax["hero"].imshow(mechanism_cartoon)
huitu.plot_xrd("xrd.txt", ax=ax["supports"][0])
huitu.plot_cv ("cv.txt",  ax=ax["supports"][1], color=huitu.role("hero"))
huitu.plot_eis("eis.txt", ax=ax["supports"][2])
fig.savefig("fig1.svg")
```

四个 archetype 各自适用场景：

| Archetype | 适用 |
|---|---|
| `schematic_led` | 机理 / 材料论文最常见 — 顶部大示意图 + 底部 quant 支撑 |
| `dark_image_plate` | 显微 / 荧光 / TEM grid，黑底无 spine |
| `clinical_triptych` | 纵向研究 → forest plot → summary bars 三段式 |
| `asymmetric_hero` | UMAP / 圆形基因组 / 单张大图占满一列，其他小图围绕 |

**多图组合 PDF 报告（v0.6）**：

```python
huitu.make_pdf_report(
    [fig_xrd, fig_cv, fig_eis, fig_gcd],
    save="reports/sample.pdf",
    title="MnO₂-Cu sample — 2026-05",
    captions=["Fig 1. XRD", "Fig 2. CV", "Fig 3. EIS", "Fig 4. GCD"],
)
```

---

## 3. 路径 B：Claude Code / Codex 智能体用户

适合你的情况：**装了 Claude Code 或 Codex CLI**，希望直接用"画 XRD"这种自然语言让 agent 自动写出 huitu 代码、保存图。

### 3.1 安装 skill bundle

skill bundle 是放在固定目录的 `SKILL.md` + 配套代码，agent 启动时会扫描这个目录、根据 frontmatter 决定是否激活。

> ⚠️ **两层都要装**：skill bundle 让 agent 知道"该用 huitu"，pip 包让 agent 真正能执行 `plot_xrd(...)` 出图。**仅装 skill 不装 pip 包 → agent 看得见 API 但跑不出图**。先按 [§2.1 环境准备](#21-环境准备) 装好 pip 包，再做下面的 skill 安装。

#### Claude Code

```bash
# 把整个 huitu_skills 仓库复制到 ~/.claude/skills/huitu/
cp -R Scientific_Illustration ~/.claude/skills/huitu

# 或者保留软链（git pull 后自动跟新）
ln -s "$PWD/Scientific_Illustration" ~/.claude/skills/huitu
```

验证：

```bash
ls ~/.claude/skills/huitu/SKILL.md && head -3 ~/.claude/skills/huitu/SKILL.md
# 应输出: ---  / name: huitu  / description: >-
```

下次开 Claude Code 会话，只要你的输入命中触发词（见下节），huitu 就会自动加载。

#### Codex CLI

```bash
mkdir -p ~/.codex/skills/
cp -R Scientific_Illustration ~/.codex/skills/huitu
head -3 ~/.codex/skills/huitu/SKILL.md
```

#### 卸载

```bash
rm -rf ~/.claude/skills/huitu     # Claude Code
rm -rf ~/.codex/skills/huitu      # Codex
```

不影响 pip 包。两条路径互不干扰。

### 3.2 触发词：让 agent 自动激活 huitu

skill 的激活由 `SKILL.md` 顶部的 YAML `description` 字段控制——**只要你的输入命中下列任何关键词，agent 就会自动加载 huitu**，不需要你手动说"用 huitu 画"。

#### 中文触发词

| 类别 | 关键词 |
|---|---|
| **动词** | 画 / 绘制 / 出图 / 渲染 / 生成 |
| **表征** | XRD / 衍射 · XPS / 光电子能谱 · Raman / 拉曼 · FTIR / 红外 · UV-Vis / 紫外可见 · PL / 荧光 · TGA / DSC / 热分析 · Rietveld / 精修 · BET / 等温线 |
| **电化学** | CV / 循环伏安 · GCD / 充放电 · EIS / 阻抗 / Nyquist / Bode · Tafel · dQ/dV / 差分容量 · 库伦效率 |
| **DFT** | 能带 · DOS / PDOS / 态密度 · COHP · Pourbaix / 电位-pH · 相图 · 晶体结构 |
| **原位** | operando / 原位 |
| **排版 / QA** | 期刊配图 · Nature 风格图 · 材料论文配图 · 多图组合 PDF · 冗余检查 · 审稿清单 |
| **图种** | 柱图 · 散点 · 折线 · 热图 · 箱线 · 雷达 · 密度 · 山脊 · 排名 · 河流图 · 平行坐标 |

#### 英文触发词

| 类别 | 关键词 |
|---|---|
| **动词** | plot / draw / render / generate / make |
| **表征** | XRD / XPS / Raman / FTIR / UV-Vis / Tauc / PL / TGA / DSC / Rietveld / BET |
| **电化学** | CV / GCD / cycling / EIS / Nyquist / Bode / Tafel / dQ/dV |
| **DFT** | band structure / DOS / PDOS / COHP / Pourbaix / phase diagram / crystal |
| **原位** | operando / in-situ |
| **排版** | schematic-led / image plate / clinical triptych / asymmetric hero / multi-panel / Nature-style |
| **QA** | anti-redundancy / reviewer checklist / figure contract |
| **图种** | bar / scatter / line / heatmap / box / violin / radar / KDE / SHAP / ridgeline / bump / streamgraph / parallel-coords / waffle |
| **格式** | journal-ready / 600 dpi / editable SVG / editable PDF / multi-page PDF |

完整清单见 [SKILL.md](SKILL.md) 的 `## When to use this skill` 段落。

#### 不会激活 huitu 的场景

下列情况 huitu **故意不激活**（避免抢错事）：

- 交互式 / web 绘图（`plotly` / `bokeh` / `altair` / `dash` / `streamlit`）
- GIS / 地图（`folium` / `geopandas`）
- 3D 分子动力学渲染（`ovito` / 光线追踪）
- 纯 Illustrator / Figma 自由排版
- 纯数据分析（没有图形交付物）

### 3.3 如何"锁定"到某一种图

agent 加载 huitu 之后，下一步是**让它选对函数**。锁定精度从低到高：

#### 锁定级别 1：只说图类（agent 自己猜函数）

```
帮我画一张 XRD
```

agent 会推断 → `plot_xrd`。够用但**模糊场景下可能猜错**（"画热图" 可能选 `plot_heatmap` 也可能选 `plot_operando`）。

#### 锁定级别 2：图类 + 数据特征

```
我有一个 XRD 数据，文件 data/sample.txt，两列，第一列 2θ，第二列 intensity，
要 Nature 期刊格式，保存成 fig1.pdf
```

agent 现在能确定：
- 函数 = `plot_xrd`
- 输入 = `"data/sample.txt"`
- `journal="nature"`
- `save="fig1.pdf"`

这是**推荐的默认精度**。

#### 锁定级别 3：直接点名函数

```
用 huitu.plot_dqdv 画我的多 cycle 数据，cycle 1 / 50 / 200 三条曲线叠在一起
```

或：

```
用 archetype.schematic_led 排版，hero 放示意图，3 个 support 分别放 XRD / CV / EIS
```

agent 直接照搬，不再"猜哪个函数最像"。**当你已经知道想要哪个函数时用这个**。

#### 锁定级别 4：贴关键参数

最严格 — 当默认 quirk 跟你的数据约定不一样时（比如 EIS 的虚部符号、Tafel 的拟合区间）：

```
画 Tafel 曲线，数据 tafel.csv，拟合区间 η ∈ [50, 200] mV，期刊 acs
```

→ agent 会带 `fit_range=(0.05, 0.2)` 调 `plot_tafel`。

#### 容易猜错的几对函数（建议显式点名）

| 含糊说法 | 可能命中 | 推荐说法 |
|---|---|---|
| "画 operando 图" | `plot_operando` / `plot_operando_xrd_echem` / `plot_operando_waterfall` / `plot_operando_3d_surface` / `plot_operando_diffmap` / `plot_operando_peak_evolution` / `plot_operando_contour` | "画 operando XRD + 电化学双轴" → `plot_operando_xrd_echem`；"原位 waterfall" → `plot_operando_waterfall` |
| "画热图" | `plot_heatmap` / `plot_operando` | 明确说"普通二维矩阵热图" 或 "原位 operando 热图" |
| "画带 fit 的散点" | `plot_scatter` | 加 `fit=True`：直接说"用 plot_scatter 加线性拟合" |
| "画晶体结构" | `plot_crystal_ase` / `plot_crystal_vesta` | 没装 VESTA 就说"用 ASE 渲染晶体结构" |
| "画 cycle" | `plot_cycle`（电化学循环） vs `plot_bump`（排名变化） | 说清楚是"电池循环 + CE" 还是"年份排名变化" |

### 3.4 典型 prompt 模板

直接套用：

#### 模板 A — 单图

```
我的 {图类型} 数据在 {路径}，{描述列含义}，
用 huitu 出图，期刊预设 {nature/acs/...}，保存为 {filename}
```

例子：

```
我的 XRD 数据在 data/MnO2.txt，第一列 2θ，第二列 intensity，
用 huitu 出图，期刊预设 nature，保存为 figs/MnO2_xrd.pdf
```

#### 模板 B — 多面板

```
帮我用 huitu archetype {archetype 名} 排版，
{每个面板放什么图、对应哪份数据}，
期刊 {nature/...}，存成 {filename}
```

例子：

```
用 archetype.schematic_led 排版，n_supports=3。
hero 面板放 schematic.png；
support 0 放 plot_xrd(data/xrd.txt)；
support 1 放 plot_cv(data/cv.txt)，颜色用 role("hero")；
support 2 放 plot_eis(data/eis.txt)。
期刊 nature，存成 figs/fig1.svg
```

#### 模板 C — 自动比较 + 二次编辑

```
先用 plot_dqdv 画 cycle 1 / 50 / 200 三条叠加；
然后在峰值 3.7 V 处加红色 axvline 和 "(de-)lithiation" 注释；
再加一个 zoom inset 看 3.5–3.9 V 范围；
存成 figs/dqdv.pdf 和 .png
```

agent 会顺序调用 `plot_dqdv` → `ax.axvline` → `ax.annotate` → `add_inset` → `fig.savefig` 两次。

#### 模板 D — 投稿前 QA

```
我的 figure 1 有 5 个 panel：
(a) 反应机理 schematic
(b) plot_xrd（4 个样品叠加）
(c) plot_cycle（500 圈 capacity + CE）
(d) plot_eis（4 个样品的 Nyquist）
(e) plot_dqdv（cycle 1 vs 200）
帮我跑 huitu.check_redundancy 和 reviewer_checklist，
告诉我有没有冗余、有没有 Nature 投稿 checklist 漏掉的字段
```

---

## 4. 常见问题与故障排查

### Q1：`pip install` 报错说找不到 scienceplots？

```bash
pip install scienceplots
# 或更新整个解析器
pip install -U pip setuptools wheel
pip install -e .
```

### Q2：图里 `cm⁻¹` 显示成方块 / 字体不对？

huitu v0.6.3 已把所有单位 superscript 改成 mathtext（`r"cm$^{-1}$"`），渲染跨字体一致。如果你自己加 label 也建议用 mathtext，不要直接打 unicode 上下标。

### Q3：导出 SVG 后在 Illustrator 里文字不能选中？

确认你的 huitu ≥ v0.5.0。`use_journal()` 会自动设置：

```python
svg.fonttype = "none"
pdf.fonttype = 42
```

如果你手动覆盖了 `rcParams`，记得保留这两项。

### Q4：Claude Code 没自动激活 huitu？

按顺序检查：

1. `ls ~/.claude/skills/huitu/SKILL.md` — 文件存在？
2. `head -3 ~/.claude/skills/huitu/SKILL.md` — 前三行是 frontmatter `---` / `name:` / `description:`？
3. 你的输入是否包含 [§3.2](#32-触发词让-agent-自动激活-huitu) 列出的关键词？
4. 重启 Claude Code 会话（skill 列表只在会话启动时扫描）

### Q5：在集群 / 无图形界面环境出图？

```python
import matplotlib
matplotlib.use("Agg")  # 必须在 import huitu 之前
import huitu

huitu.plot_xrd("xrd.txt", save="fig.pdf")
# 不要调用 plt.show()，直接 save
```

### Q6：想加一种 huitu 还没覆盖的图类型？

四步：

1. 在对应 `huitu/<subpackage>/` 下加 `<name>.py`，写 `plot_<name>` 函数
2. 在 `huitu/__init__.py` 顶层 import 并加进 `__all__`
3. 在 `SKILL.md` 的 Plot catalogue 表格加一行
4. 在 `tests/test_smoke.py` 参数化列表里加期刊覆盖

详见 [REPO_LAYOUT.md](REPO_LAYOUT.md#add-a-new-plot-type)。

### Q7：测试有没有覆盖我的用法？

```bash
python -m pytest tests/ -q
# 应输出 237 passed
```

视觉抽查：

```bash
python tests/visual_audit/render_all.py
# 在 tests/visual_audit/output/ 下生成 52 张 PNG（gitignored，可随便重跑）
```

---

## 延伸阅读

- [README.md](README.md) — 项目主页 + 调色板 + 路线图
- [SKILL.md](SKILL.md) — 完整 API catalog + 期刊预设详表 + 每个函数的 quirk
- [REPO_LAYOUT.md](REPO_LAYOUT.md) — 仓库目录结构 + 如何加新图类型
- [CHANGELOG.md](CHANGELOG.md) — 版本变更
- `examples/` — 六个可直接跑的示范脚本
- `docs/showcase/` — 九张 README 用的 HD 展示图（`python docs/showcase/render.py` 一键重生）
