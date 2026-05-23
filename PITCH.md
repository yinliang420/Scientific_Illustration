# huitu — 把 matplotlib 变成"一行出图"的材料学绘图引擎

> **写一行 Python，拿到一张 Nature 投得出去的图。**
> 不用调字号、不用查模板、不用 Illustrator 再修一遍——`save="fig.pdf"` 就是终稿。

---

## 🎯 一句话

**`huitu` 把材料科学论文里最常见的 46 种图，做成了一行函数。**

```python
import huitu
huitu.plot_xrd("xrd.txt", journal="nature", save="fig1.pdf")
```

完成。这张 PDF：

- ✅ 89 × 70 mm Nature 单栏尺寸
- ✅ Helvetica 7 pt（Nature 规范）
- ✅ 600 dpi（达到印刷线）
- ✅ **PDF 文字可在 Illustrator 选中编辑**（不是栅格化路径）
- ✅ 四面有刻度、图例无边框、黑色坐标轴（期刊默认要求）

直接附在投稿包里，不用再过 PS。

---

## 💔 你之前是不是这样过

- 📐 翻 Nature 的 figure guidelines 翻了 40 分钟，确认 single-column 是 89 mm 还是 88 mm
- 🔠 改完 `rcParams['font.family']`，发现 `2θ` 里的 θ 跟正文 Helvetica 不一致
- 🖼 用 `plt.savefig(...)` 出 SVG，Illustrator 里发现字全变成 path，没法改字号
- 🎨 找配色搜了三十张博客，最后还是用了 matplotlib 默认 `C0/C1/C2`
- 📊 多面板拼图用 `subplot(2, 3)` 拼了一晚上，间距永远是不对的
- 🔬 同事新发了 BET 数据，你又得现写 Langmuir 拟合脚本

**huitu 把这些痛点一次性 commit 掉了。**

---

## ⚡ Before / After

### Before（vanilla matplotlib，~ 40 行）

```python
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    "font.family": "Helvetica",
    "font.size": 7,
    "axes.linewidth": 0.6,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.top": True,
    "ytick.right": True,
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "savefig.dpi": 600,
})

data = np.loadtxt("xrd.txt")
two_theta, intensity = data[:, 0], data[:, 1]
intensity = (intensity - intensity.min()) / (intensity.max() - intensity.min())

fig, ax = plt.subplots(figsize=(89/25.4, 70/25.4))
ax.plot(two_theta, intensity, lw=0.8, color="#0072B2")
ax.set_xlabel(r"2$\theta$ (°)")
ax.set_ylabel("Intensity (a.u.)")
ax.set_yticks([])
ax.set_xlim(two_theta.min(), two_theta.max())
ax.tick_params(which="both", length=2, width=0.5)
for spine in ax.spines.values():
    spine.set_linewidth(0.6)
fig.tight_layout(pad=0.3)
fig.savefig("fig1.pdf")
plt.close(fig)
```

### After（huitu，1 行）

```python
import huitu
huitu.plot_xrd("xrd.txt", journal="nature", save="fig1.pdf")
```

**40 行 → 1 行。结果还更好**——因为 huitu 默认会处理你 vanilla 版本忘记的事情（比如 mathtext 字体跟正文统一、stack 多条曲线的 offset 自适应、(hkl) 标注边界保护）。

---

## 🚀 三个杀手级特性

### 1. 一行覆盖整个材料学测试矩阵

| 类别 | 函数 |
|---|---|
| **表征** | `plot_xrd` · `plot_xps` · `plot_raman` · `plot_ftir` · `plot_uvvis` · `plot_pl` · `plot_thermal` · `plot_rietveld` · `plot_bet` · `plot_operando` |
| **电化学** | `plot_cv` · `plot_gcd` · `plot_cycle` · `plot_eis` · `plot_bode` · `plot_tafel` · `plot_dqdv` |
| **第一性原理** | `plot_band` · `plot_dos` · `plot_cohp` · `plot_pourbaix` · `plot_phase_diagram` · `plot_crystal_*` |
| **统计 / Operando 进阶** | `plot_ridgeline` · `plot_bump` · `plot_streamgraph` · `plot_parallel` · 6 种 operando 变体 · … |
| **通用** | `plot_bar` · `plot_scatter` · `plot_line` · `plot_heatmap` · `plot_box_violin` · `plot_radar` · `plot_density` · `plot_shap` |

**46 个函数**，全部统一接口（吃路径 / NumPy / tuple / DataFrame 四选一，返回 `(fig, ax)`）。

### 2. 8 个期刊预设 + 4 个 Nature archetype

切预设，整页字号 / 字体 / 尺寸 / 配色一起对齐。**改 `journal="nature"` 为 `journal="acs"` 就直接换成 ACS 规范**，不用再改任何代码。

```python
huitu.use_journal("nature")        # 89×70 mm Helvetica 7pt
# 或
huitu.use_journal("acs")           # 3.33×2.5 in bold-qualitative 色卡
```

四个 archetype 直接按**论证类型**而不是 `subplot(2,3)` 拼图：

| Archetype | 适用 |
|---|---|
| `schematic_led` | 机理 + 量化支撑（材料论文 80% 的 Figure 1） |
| `dark_image_plate` | 显微 / 荧光 grid，黑底无 spine |
| `clinical_triptych` | 纵向 → forest → summary 三段式 |
| `asymmetric_hero` | UMAP / 圆形基因组占满一列 |

### 3. **投稿前 QA 自动跑** — 这是 huitu 最特别的部分

```python
huitu.print_redundancy_report(panels)
# → 自动检查：两个 panel 是否在回答同一问题？
#    是否缺 Overview → Deviation → Relationship 信息层级？
#    是否同一份数据被堆叠柱 + 饼图重复表达？

huitu.reviewer_checklist(figure=..., quantitative=..., image=...)
# → 跑 Springer Nature & Cell-family 真实 pre-submission checklist
#    n / replicates / center / spread / test / source data / scale bar / …
```

**审稿人会挑的字段，投稿前自己先挑一遍。**

---

## 🎁 顺便送你的

- **可编辑 SVG / PDF 文字**（`svg.fonttype="none"` + `pdf.fonttype=42`）——评审审完让你"改一下字号"不用重新出图
- **55 个调色板**（ggsci npg/aaas/jco/lancet/nejm · MetBrewer · Financial Times · Crameri · Nord · Okabe-Ito …），`huitu.use_palette("met-hiroshige")` 全局切
- **18 键语义调色板**：`huitu.role("hero")` / `role("baseline")` / `role("positive")` / `role("negative")`——整页配色按"科学角色"对齐
- **600 dpi 默认**——发邮件给导师不会糊
- **`make_pdf_report(...)`**——把若干 figure 一键合成多页 PDF，封面 + caption 都生成好

---

## 🤖 双重身份：Python 包 + 智能体 Skill

### 身份 A：写代码

```bash
pip install huitu-0.6.3-py3-none-any.whl
```

然后 `import huitu` 就完事。配 Jupyter / 脚本 / pipeline 都行。

### 身份 B：让 Claude Code / Codex 替你写

把仓库复制到 `~/.claude/skills/huitu/` 或 `~/.codex/skills/huitu/`：

```bash
cp -R Scientific_Illustration ~/.claude/skills/huitu
```

下次直接对 agent 说：

> "我有一份 XRD 数据在 `data/sample.txt`，帮我用 Nature 格式画出来"

agent **自动加载 huitu**，写好代码、跑出图、保存到你指定路径——你完全不用 `import` 也不用查函数名。

中文 / 英文触发词都支持：
- 中文：`画 XRD` / `CV 曲线` / `BET 等温线` / `期刊配图` / `审稿清单`
- 英文：`plot XRD` / `Nyquist plot` / `journal-ready figure` / `reviewer checklist`

---

## 📈 展示一下成品

九张 README 头图，涵盖 huitu 的全部 plot surface（一键 `python docs/showcase/render.py` 重生，无需任何手工数据）：

| Nature 多面板 | Rietveld 精修 | Operando XRD + 电化学 |
|---|---|---|
| ![archetype](docs/showcase/01_archetype_schematic_led.png) | ![rietveld](docs/showcase/02_rietveld_refinement.png) | ![operando](docs/showcase/03_operando_xrd_echem.png) |

| BET 等温线 | dQ/dV 多 cycle | Bump 排名演化 |
|---|---|---|
| ![bet](docs/showcase/04_bet_isotherm.png) | ![dqdv](docs/showcase/05_dqdv_multi_cycle.png) | ![bump](docs/showcase/06_bump_publications.png) |

| Ridgeline 分布 | Pourbaix E-pH | 调色板目录 |
|---|---|---|
| ![ridgeline](docs/showcase/07_ridgeline_distributions.png) | ![pourbaix](docs/showcase/08_pourbaix_diagram.png) | ![palettes](docs/showcase/09_palette_catalog.png) |

---

## 🥊 跟其他方案比

| | matplotlib | seaborn | scienceplots | proplot | **huitu** |
|---|:---:|:---:|:---:|:---:|:---:|
| 通用绘图 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 期刊级 rcParams（Nature/Science 模板） | ❌ | ❌ | ✅ | 部分 | ✅ |
| **材料学专用 API**（XRD / EIS / BET / dQ/dV …） | ❌ | ❌ | ❌ | ❌ | ✅ 46 个 |
| **DFT 数据**（band / DOS / COHP / Pourbaix） | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Operando 热图**（6 种变体） | ❌ | ❌ | ❌ | ❌ | ✅ |
| **可编辑 SVG / PDF 文字默认** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **语义调色板**（hero / baseline / positive / negative） | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Nature 排版 archetype** | ❌ | ❌ | ❌ | ❌ | ✅ 4 个 |
| **anti-redundancy 检查** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **reviewer pre-submission checklist** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **agent skill bundle**（Claude/Codex 自动激活） | ❌ | ❌ | ❌ | ❌ | ✅ |

`huitu` 不是要取代 matplotlib——而是把材料学**重复 50 次的样板代码**封装掉。底下还是 matplotlib，你拿到 `(fig, ax)` 之后想自由 customise 随时可以。

---

## 🧪 质量保证

- **237 个 pytest** 全绿（每个函数 × 8 期刊预设的笛卡尔积全覆盖）
- **52 图 visual_audit harness**——一键重生所有 demo 图，做版本回归
- **6 轮对抗式 polish 迭代**（v0.5.1 / 0.5.2 / 0.6.1 / 0.6.2 / 0.6.3）—— 累计修了 100+ 视觉 bug
- **Python 3.9 / 3.10 / 3.11 / 3.12** 均支持
- **MIT 协议**——商用 / 教学 / fork 随便

---

## 🚦 30 秒上手

```bash
# 1. 装
git clone https://github.com/yinliang420/Scientific_Illustration.git
cd Scientific_Illustration
pip install -e .

# 2. 跑
python -c "
import huitu, numpy as np
x = np.linspace(10, 80, 1000)
y = np.exp(-(x - 32.9)**2 / 4) + np.exp(-(x - 36.5)**2 / 6) + 0.1
huitu.plot_xrd((x, y), journal='nature', save='hello_huitu.pdf')
"

# 3. 打开 hello_huitu.pdf —— 这就是你的第一张 Nature 投得出去的 XRD
```

下一步：
- **想详细学**？看 [USAGE.md](USAGE.md)（从环境准备到投稿 QA 的完整 596 行手册）
- **想看完整 API**？看 [SKILL.md](SKILL.md)（46 个函数 + quirk + 数据格式）
- **想看怎么扩展**？看 [REPO_LAYOUT.md](REPO_LAYOUT.md)
- **想直接抄示范**？看 `examples/` 六个可跑脚本

---

## 📣 适合谁

| 你是… | huitu 给你的价值 |
|---|---|
| **材料 / 化学博士生** | 把"做实验 → 画图 → 投稿"链路上**画图**这一环砍到 1 行 |
| **课题组 PI / 投稿编辑** | 整个组配色 / 字号 / 尺寸自动对齐，毕业季再不用收一堆风格各异的 figure |
| **AI / 数据科学家做材料** | 直接拿到带 Nature 模板的 plot，不用每次为新合作者重写绘图代码 |
| **Claude Code / Codex 重度用户** | skill 自动激活，自然语言出图，不用打开 IDE |
| **课程助教 / 教材作者** | 数据科学课用 `huitu.print_redundancy_report` 教学生"信息层级"，比讲 50 页 PPT 直观 |

---

## 🎬 结语

> 你的研究值得一张配得上它的图。
>
> 你不应该把博士的时间花在 `plt.rcParams.update(...)` 上。
>
> **`pip install huitu` —— 把绘图的事情交出去，把时间还给科学。**

---

[![GitHub](https://img.shields.io/badge/GitHub-Scientific__Illustration-181717?logo=github)](https://github.com/yinliang420/Scientific_Illustration)
[![Python](https://img.shields.io/badge/python-3.9--3.12-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![DPI](https://img.shields.io/badge/output-600%20dpi-brightgreen)]()
[![Editable](https://img.shields.io/badge/SVG%2FPDF-editable--text-1a73e8)]()
[![Tests](https://img.shields.io/badge/tests-237%20passed-success)]()
