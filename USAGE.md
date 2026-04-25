# huitu 使用指南

面向科研一线使用者的实操手册。按「我想画什么图」的场景组织，复制粘贴即用。

**阅读顺序建议：** 先看 [1. 五分钟上手](#1-五分钟上手) 跑通第一张图，再按需跳到对应章节。

---

## 目录

1. [五分钟上手](#1-五分钟上手)
2. [数据格式约定](#2-数据格式约定)
3. [期刊预设怎么选](#3-期刊预设怎么选)
4. [表征谱图（XRD / XPS / Raman / FTIR / UV-Vis / PL / TGA-DSC / Rietveld）](#4-表征谱图)
5. [电化学（CV / GCD / 循环 / EIS / Bode / Tafel）](#5-电化学)
6. [DFT 计算（Band / DOS / COHP / Pourbaix / 相图）](#6-dft-计算)
7. [晶体结构](#7-晶体结构)
8. [通用数据图（Bar / Scatter / Line / Heatmap / Box-Violin / Radar）](#8-通用数据图)
9. [拼图 / 插图 / 共享坐标](#9-拼图--插图--共享坐标)
10. [定制化：从模式 A 切到模式 B](#10-定制化从模式-a-切到模式-b)
11. [常见坑与调试](#11-常见坑与调试)

---

## 1. 五分钟上手

### 安装
```bash
cd huitu_skills
pip install -e .
# 如果要画晶体结构
pip install -e ".[crystal]"
```

### 跑一张示例图
```bash
python examples/xrd_single.py
# 输出：examples/output/xrd_single.png
```

### 自己的数据最小示例
```python
from huitu import plot_xrd

plot_xrd("my_xrd.txt", journal="nature", save="fig1.pdf")
```

就这样。`my_xrd.txt` 可以是两列 `2θ  intensity` 的纯文本（空格 / tab / 逗号都行，`#` 或 `%` 开头的行自动跳过）。

---

## 2. 数据格式约定

### 两列谱图（XRD / XPS / Raman / FTIR / UV-Vis / PL / CV / GCD / EIS / ...）
```
# 可以有注释行
2theta  intensity
10.0    125.3
10.1    130.7
...
```
首列是 x，次列是 y。**不强制要求表头**。

### 多曲线堆叠
把**多个文件路径**组成 list 传进去：
```python
from huitu import plot_xrd
plot_xrd(["sample_A.txt", "sample_B.txt", "sample_C.txt"],
         offset=0.5, labels=["A", "B", "C"], save="stack.pdf")
```

### 电化学循环图（3 列）
```
cycle  capacity  coulombic_efficiency
1      185.2     99.1
2      181.7     99.4
```
第 3 列（CE）自动放到右侧 twin Y 轴。

### Bar / Line / Scatter（CSV 带表头）
```csv
sample,property1,property2,property3
A,1.2,3.4,5.6
B,2.1,4.5,6.7
```
第一列通常是类别或 x，其余列是数据系列。表头会自动作为 legend。

### 直接传数组
所有函数都接受：
- 文件路径（str / Path）
- NumPy `(N, 2)` 数组
- `(x, y)` 元组
- pandas DataFrame

```python
import numpy as np
x = np.linspace(10, 80, 1000)
y = np.exp(-((x-32.9)**2)/0.05)
plot_xrd((x, y), save="synthetic.pdf")
```

---

## 3. 期刊预设怎么选

8 个预设，覆盖绝大多数材料学期刊。直接传 `journal="..."`，或全局设一次：

```python
from huitu import use_journal
use_journal("nature")    # 之后所有图都用 Nature 规范
```

| 预设 | 代表期刊 | 图宽 | 字号 | 使用场景 |
|---|---|---|---|---|
| `nature` | Nature / Nature Energy / Nature Mater / NC | 89 mm | 7 pt | 最严格，单栏紧凑 |
| `science` | Science / Science Adv. | ~110 mm | 7 pt | Science 系列 |
| `acs` | JACS / ACS Nano / ACS Energy Letters | 3.33 in | 8 pt | ACS 全系列 |
| `rsc` | EES / JMCA / Chem Sci / Chem Comm | 3.26 in | 8 pt | RSC 全系列 |
| `wiley` | Angew / Adv Mater / Adv Energy Mater | 3.35 in | 8 pt | Wiley 全系列 |
| `elsevier` | Nano Energy / Joule / Carbon | 90 mm | 8 pt | Elsevier 全系列 |
| `ieee` | IEEE Trans / Electron Device Lett | 3.5 in | 8 pt | 工程类期刊 |
| `default` | 通用 SCI | 3.5 in | 8 pt | 不确定投哪就用这个 |

**共同默认**：Arial/Helvetica 字体栈、600 dpi、黑色坐标轴、内向刻度四边、legend 无边框、`bbox='tight'`、Tol/Okabe-Ito 色盲友好配色。

---

## 4. 表征谱图

### XRD
```python
from huitu import plot_xrd

# 单谱
plot_xrd("xrd.txt", journal="nature", save="xrd.pdf")

# 多谱堆叠 + hkl 标注
plot_xrd(["A.txt", "B.txt", "C.txt"],
         labels=["As-prep", "500 °C", "800 °C"],
         offset=0.5,
         hkl={32.9: "(200)", 47.1: "(220)"},
         save="xrd_stack.pdf")
```

### XPS（含分峰拟合）
```python
from huitu import plot_xps

plot_xps("xps_raw.txt",
         baseline=(x_bkg, y_bkg),
         fits=[(x_fit1, y_fit1, "Co 2p3/2"),
               (x_fit2, y_fit2, "Co 2p1/2 sat.")],
         save="xps.pdf")
```
X 轴自动反向（高结合能在左）。

### Raman
```python
from huitu import plot_raman
plot_raman(["sample1.txt", "sample2.txt"], offset=200, save="raman.pdf")
```

### FTIR
```python
from huitu import plot_ftir
plot_ftir("ftir.txt", mode="transmittance", save="ftir.pdf")  # 或 mode="absorbance"
```
波数从 4000 → 400 自动反转。

### UV-Vis + Tauc
```python
from huitu import plot_uvvis

# 原始吸收谱
plot_uvvis("uvvis.txt", save="uvvis.pdf")

# Tauc 直接跃迁（(αhν)² vs hν）
plot_uvvis("uvvis.txt", tauc="direct", save="tauc_direct.pdf")

# 间接跃迁
plot_uvvis("uvvis.txt", tauc="indirect", save="tauc_indirect.pdf")
```

### PL 荧光
```python
from huitu import plot_pl
plot_pl(["s1.txt", "s2.txt"], normalize=True, save="pl.pdf")
```

### TGA / DSC
```python
from huitu import plot_thermal

# 只画 TGA
plot_thermal("tga.txt", mode="tga", save="tga.pdf")

# TGA + DSC 共图（左 Y：weight%，右 Y：heat flow）
plot_thermal("tga.txt", mode="both", dsc_data="dsc.txt", save="tgdsc.pdf")
```

### Rietveld 精修
```python
from huitu import plot_rietveld

# 输入 4 列：2θ, I_obs, I_calc, I_bkg
plot_rietveld("rietveld.txt",
              hkl_positions=[32.9, 47.1, 56.5],  # Bragg 位置刻度条
              save="rietveld.pdf")
```
固定 2 面板布局（上主图 + 下差值）；传 `ax=` 会被忽略并提示。

---

## 5. 电化学

### CV
```python
from huitu import plot_cv
plot_cv(["cycle1.txt", "cycle10.txt", "cycle100.txt"],
        labels=["1st", "10th", "100th"], save="cv.pdf")
```

### 充放电曲线（GCD）
```python
from huitu import plot_gcd
plot_gcd(["0.1C.txt", "0.5C.txt", "1C.txt", "2C.txt"],
         labels=["0.1C", "0.5C", "1C", "2C"], save="gcd.pdf")
```

### 循环 + 库仑效率（twin Y）
```python
from huitu import plot_cycle
# 3 列输入：cycle, capacity, CE
plot_cycle("cycle.txt", save="cycle.pdf")
```

### EIS（Nyquist）
```python
from huitu import plot_eis

# 数据已是 (Z', -Z''): 默认
plot_eis("eis.txt", save="nyquist.pdf")

# 数据是原始 (Z', Z''): 自动取负
plot_eis("eis_raw.txt", negate_imag=True, save="nyquist.pdf")
```
等比例坐标（`adjustable='box'`）。

### Bode（|Z| + phase）
```python
from huitu import plot_bode
# 3 列：freq, |Z|, phase
plot_bode("bode.txt", save="bode.pdf")

# 如果只有复阻抗：freq, Z', Z''
plot_bode("bode_complex.txt", input_format="complex", save="bode.pdf")
```

### Tafel（线性段自动拟合）
```python
from huitu import plot_tafel
# 输入 2 列：log|j|, η
plot_tafel("tafel.txt",
           fit_range=(0.10, 0.35),  # η 窗口（V）
           save="tafel.pdf")
# 斜率自动以 mV/dec 显示在 legend
```

---

## 6. DFT 计算

### 能带结构
```python
from huitu import plot_band
# 输入：第 1 列 k-path，其余列是每条能带（Fermi 已移到 0）
plot_band("band.txt",
          kpoints=[("Γ", 0.0), ("M", 0.5), ("K", 0.7), ("Γ", 1.0)],
          save="band.pdf")
```

### DOS / PDOS
```python
from huitu import plot_dos
# 标准横向
plot_dos("dos.txt",
         projections={"s": y_s, "p": y_p, "d": y_d},
         save="dos.pdf")

# 纵向（方便与 band 并排）
plot_dos("dos.txt", orientation="vertical", save="dos_v.pdf")

# 并排 band + DOS
from huitu import make_subplots
fig, axes = make_subplots(1, 2, width_ratios=[3, 1], sharey=True)
plot_band("band.txt", ax=axes[0])
plot_dos("dos.txt", orientation="vertical", ax=axes[1])
fig.savefig("band_dos.pdf")
```

### COHP / ICOHP
```python
from huitu import plot_cohp
# 输入 2 列：energy, cohp（**raw COHP，成键为负**）
plot_cohp("cohp.txt", save="cohp.pdf")
# 左侧（COHP<0）填成键色，右侧（COHP>0）填反键色

# 叠加 ICOHP（twin x）
plot_cohp("cohp.txt", show_icohp=True, save="cohp_icohp.pdf")
```

### Pourbaix（E-pH）图
```python
from huitu import plot_pourbaix

regions = [
    {"label": "Fe",      "vertices": [(0, -0.6), (6, -0.6), (6, -0.4), (0, -0.4)]},
    {"label": "Fe²⁺",    "vertices": [(0, -0.4), (8, -0.4), (8, 0.8), (0, 0.8)]},
    {"label": "Fe₂O₃",   "vertices": [(8, -0.4), (14, -0.4), (14, 2), (8, 2)]},
]
plot_pourbaix(regions, save="pourbaix.pdf")
# H₂/O₂ 稳定线自动绘制
```

### 相图（二元合金）
```python
from huitu import plot_phase_diagram

regions = [
    {"label": "α",   "vertices": [...]},
    {"label": "β",   "vertices": [...]},
    {"label": "α+β", "vertices": [...]},
]
plot_phase_diagram(regions,
                   invariants=[(0.3, 500, "eutectic")],
                   xlabel="Sn content",
                   save="phase.pdf")
```

---

## 7. 晶体结构

### ASE 三视图（免费路径）
```bash
pip install -e ".[crystal]"   # 安装 ASE
```
```python
from huitu import plot_crystal_ase
plot_crystal_ase("structure.cif",
                 radii=0.5,
                 rotation="15x,15y,0z",
                 save="crystal.png")
```
自动 1×3 三视图（xy / xz / yz）。

### VESTA（画质最好，需要 VESTA 安装）
```bash
export VESTA_BIN=/path/to/vesta_wrapper.sh
```
其中 `vesta_wrapper.sh` 是你自己写的脚本，接收两个位置参数：`$1` 输入 CIF，`$2` 输出 PNG。
```python
from huitu import plot_crystal_vesta
plot_crystal_vesta("structure.cif", save="crystal.png")
```
如果 `VESTA_BIN` 未设置或不存在，自动回落到 ASE 并给出 warning。

---

## 8. 通用数据图

### Bar（分组 / 堆叠）
```python
from huitu import plot_bar
plot_bar("data.csv", save="bar.pdf")               # 分组
plot_bar("data.csv", stacked=True, save="bar.pdf") # 堆叠
```

### Scatter（带拟合线 / 误差棒）
```python
from huitu import plot_scatter
plot_scatter("xy.csv", fit=True, yerr=yerr_array, save="scatter.pdf")
# 有 yerr 时自动加权拟合
```

### Line（双 Y）
```python
from huitu import plot_line
# 如 CSV 列为: x, capacity, voltage — voltage 放到右侧
plot_line("data.csv", twin_cols=["voltage"], save="line.pdf")
```

### Heatmap / Contour
```python
from huitu import plot_heatmap
plot_heatmap("matrix.csv", annot=True, save="heat.pdf")              # 标注数值
plot_heatmap("matrix.csv", mode="contourf", save="contourf.pdf")
```

### Box / Violin
```python
from huitu import plot_box_violin
# 长格式 DataFrame：列 [sample, value]
plot_box_violin(df, x="sample", y="value", kind="violin", save="violin.pdf")
```

### Radar
```python
from huitu import plot_radar
import pandas as pd
df = pd.DataFrame({
    "Capacity": [0.8, 0.6, 0.9],
    "Rate":     [0.7, 0.9, 0.5],
    "Cycle":    [0.9, 0.7, 0.8],
}, index=["S1", "S2", "S3"])
plot_radar(df, normalize="per_axis", save="radar.pdf")
```

---

## 9. 拼图 / 插图 / 共享坐标

### `make_subplots`（自动 (a)(b)(c) 标签）
```python
from huitu import make_subplots, plot_xrd, plot_raman, plot_xps
fig, axes = make_subplots(2, 2, journal="acs")
plot_xrd("xrd.txt",     ax=axes[0, 0])
plot_raman("raman.txt", ax=axes[0, 1])
plot_xps("xps.txt",     ax=axes[1, 0])
plot_xps("xps2.txt",    ax=axes[1, 1])
fig.savefig("panel.pdf")
```

### `add_inset`（局部放大）
```python
from huitu import plot_xrd, add_inset
fig, ax = plot_xrd("xrd.txt")
add_inset(ax, bounds=(0.55, 0.45, 0.4, 0.45),
          xlim=(30, 35), ylim=(0.3, 1.05))
fig.savefig("xrd_inset.pdf")
```

### `share_axes`（事后共享坐标）
```python
from huitu import make_subplots, share_axes
fig, axes = make_subplots(2, 2)
# ... 每个子图独立画 ...
share_axes(axes, which="both")  # 或 'x' / 'y'
```

---

## 10. 定制化：从模式 A 切到模式 B

**模式 A** 一行出图，适合默认配色就够用的场景。
**模式 B** 拷贝模板自由改，适合需要：
- 换特定颜色（期刊要求 CMYK / 单色）
- 加自定义 annotation / arrow
- 手动调整坐标轴范围 / 刻度
- 混合多种图（比如 XRD 主图 + inset 放大 + 自定义 hkl 标注 + 峰位箭头）

**切换步骤：**
1. 找到最接近你需求的 `examples/xxx.py`
2. 复制到你的工作目录：`cp examples/xrd_stacked.py my_fig.py`
3. 改数据路径、改参数、加自定义代码

**示例：XRD + 自定义标注 + inset**
```python
from huitu import plot_xrd, add_inset

fig, ax = plot_xrd("xrd.txt", journal="acs")

# 自定义：画一条辅助红线 + 箭头标注
ax.axvline(32.9, color="red", lw=0.5)
ax.annotate("(200)", xy=(32.9, 0.7), xytext=(35, 0.85),
            arrowprops=dict(arrowstyle="->"))

# 加局部放大
add_inset(ax, bounds=(0.55, 0.45, 0.4, 0.45),
          xlim=(30, 35), ylim=(0.3, 1.05))

fig.savefig("custom.pdf")
```

---

## 11. 常见坑与调试

### Q1：图出来字太小 / 太大？
`use_journal("...")` 会覆盖所有字号。想全局放大：
```python
import matplotlib as mpl
mpl.rcParams.update({"font.size": 10})  # 在 use_journal() 之后调
```

### Q2：保存 PDF 中文乱码？
matplotlib 的 Arial 字体栈不带中文。加：
```python
import matplotlib as mpl
mpl.rcParams["font.sans-serif"] = ["Arial Unicode MS", "SimHei"] + mpl.rcParams["font.sans-serif"]
```

### Q3：我的 XPS 数据是升序结合能，出图想反向？
`plot_xps` 自动反向 x 轴，不用手动处理。

### Q4：EIS 数据 Z'' 是正的（仪器原始输出）？
传 `negate_imag=True`。

### Q5：Nyquist 图看起来被压扁？
默认 `adjustable="box"`。如果你手动设了 `ax.set_aspect(...)` 会冲突——注释掉你的手动设置。

### Q6：Rietveld 函数不接受我传的 `ax`？
它固定 2 面板布局，`ax=` 参数会被忽略并给 warning。这是设计选择。

### Q7：COHP 图的成键/反键颜色反了？
`huitu` 使用 **raw COHP 约定**（成键 < 0，左填）。如果你的文件存的是 `-COHP`，先乘以 `-1`。

### Q8：VESTA 没装，能画晶体结构吗？
能。`plot_crystal_vesta` 自动回落到 ASE；或直接用 `plot_crystal_ase`。

### Q9：`pip install -e .` 装不上 scienceplots？
scienceplots 是可选的，缺失时 `use_journal` 会打印警告并回落到纯 matplotlib，不影响图能出来。

### Q10：样本数据文件长啥样？
`examples/sample_data/` 里每种图都有一份合成数据。`python examples/sample_data/_generate.py` 可以重新生成。

### 测试是否都通过
```bash
python -m pytest tests/ -q
# 53 passed
```

---

## 进一步阅读

- [SKILL.md](SKILL.md) — 完整 API catalog、期刊预设详表、所有 quirks（推荐当字典查）
- [README.md](README.md) — 项目概览、安装、路线图
- `examples/` — 31 个可直接运行的模板脚本
