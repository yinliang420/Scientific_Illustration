"""Smoke tests: every example script runs end-to-end and writes its PNG."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"
OUTPUT = EXAMPLES / "output"

# Slim state (v0.6+): six canonical example scripts. End-user plotting paths
# are exercised by `tests/test_smoke_unit.py` (parameterised over journal
# presets) and the v05/v06/v07/v08 adversarial suites under `real_data_test/`.
SCRIPTS = [
    ("quickstart.py",          "quickstart.png"),
    ("multi_panel.py",         "multi_panel.png"),
    ("bet.py",                 "bet.png"),
    ("dqdv.py",                "dqdv.png"),
    ("pdf_report.py",          "pdf_report.pdf"),
    ("reviewer_checklist.py",  None),   # text-only output; no figure asserted
]


@pytest.mark.parametrize("script, png", SCRIPTS)
def test_example_runs(script, png):
    script_path = EXAMPLES / script
    out_png = OUTPUT / png if png else None
    if out_png is not None and out_png.exists():
        out_png.unlink()

    env = dict(os.environ)
    env["MPLBACKEND"] = "Agg"
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"{script} failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    if out_png is not None:
        assert out_png.exists(), f"{script} did not produce {out_png}"
        assert out_png.stat().st_size > 0


def test_package_imports():
    import huitu

    expected = {
        "plot_xrd", "plot_xps", "plot_raman", "plot_cv", "plot_gcd",
        "plot_cycle", "plot_eis", "plot_bar", "plot_scatter", "plot_line",
        "plot_ftir", "plot_uvvis", "plot_pl", "plot_thermal",
        "plot_bode", "plot_tafel", "plot_band", "plot_dos",
        "plot_heatmap", "plot_box_violin",
        "plot_rietveld", "plot_cohp", "plot_pourbaix", "plot_phase_diagram",
        "plot_radar", "plot_crystal_ase", "plot_crystal_vesta",
        "make_subplots", "add_inset", "share_axes", "use_journal", "read_xy",
    }
    missing = expected - set(dir(huitu))
    assert not missing, f"missing symbols: {missing}"


PRESETS = ["default", "nature", "science", "acs", "rsc", "wiley", "elsevier", "ieee"]


@pytest.mark.parametrize("preset", PRESETS)
def test_use_journal_all_presets(preset, tmp_path):
    import matplotlib.pyplot as plt
    import numpy as np
    from huitu import plot_line, use_journal

    use_journal(preset)
    import pandas as pd
    df = pd.DataFrame({"x": np.arange(10), "y": np.arange(10) ** 2})
    fig, ax = plot_line(df, save=tmp_path / f"{preset}.png")
    plt.close(fig)


@pytest.mark.parametrize("preset", PRESETS)
def test_use_journal_all_presets_ftir(preset, tmp_path):
    """Confirm the new plot_ftir works across every journal preset."""
    import matplotlib.pyplot as plt
    import numpy as np
    from huitu import plot_ftir

    x = np.linspace(400, 4000, 200)
    y = 100 - 20 * np.exp(-((x - 1600) / 50) ** 2)
    fig, _ = plot_ftir((x, y), journal=preset, save=tmp_path / f"ftir_{preset}.png")
    plt.close(fig)


def test_use_journal_invalid():
    from huitu import use_journal
    with pytest.raises(ValueError):
        use_journal("not-a-journal")


def test_polymorphic_inputs(tmp_path):
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    from huitu import plot_xrd, plot_ftir, plot_uvvis, plot_pl

    x = np.linspace(10, 80, 200)
    y = np.random.default_rng(0).random(200)

    # tuple of 1-D arrays -> single pattern
    fig, _ = plot_xrd((x, y))
    plt.close(fig)

    # 2-D ndarray
    arr = np.column_stack([x, y])
    fig, _ = plot_xrd(arr)
    plt.close(fig)

    # DataFrame
    df = pd.DataFrame({"two_theta": x, "intensity": y})
    fig, _ = plot_xrd(df)
    plt.close(fig)

    # file path
    sample = ROOT / "examples" / "sample_data" / "xrd.txt"
    fig, _ = plot_xrd(sample)
    plt.close(fig)

    # list of paths -> stacked multi-input (check classifier)
    fig, _ = plot_xrd([sample, sample], labels=["a", "b"])
    plt.close(fig)

    # Same polymorphic coverage for the new 2-col plots.
    for fn, sample_name in [
        (plot_ftir, "ftir.txt"),
        (plot_uvvis, "uvvis.txt"),
        (plot_pl, "pl.txt"),
    ]:
        sp = ROOT / "examples" / "sample_data" / sample_name
        fig, _ = fn(sp)
        plt.close(fig)
        fig, _ = fn((x, y))
        plt.close(fig)
        fig, _ = fn(np.column_stack([x, y]))
        plt.close(fig)
        fig, _ = fn(pd.DataFrame({"x": x, "y": y}))
        plt.close(fig)
        fig, _ = fn([sp, sp], labels=["a", "b"])
        plt.close(fig)


def test_p1_kwargs_paths(tmp_path):
    """Guard less-exercised branches: thermal both / bode complex / dos vertical /
    heatmap contour + contourf / uvvis indirect Tauc."""
    import matplotlib.pyplot as plt
    import numpy as np
    from huitu import (
        plot_bode,
        plot_dos,
        plot_heatmap,
        plot_thermal,
        plot_uvvis,
    )

    rng = np.random.default_rng(0)

    # plot_thermal mode='both'
    t = np.linspace(30, 800, 50)
    tga = 100 - 40 * (t / 800)
    dsc = -0.5 + 0.1 * np.sin(t / 50)
    fig, ax = plot_thermal((t, tga), mode="both", dsc_data=(t, dsc),
                            save=tmp_path / "thermal_both.png")
    assert (tmp_path / "thermal_both.png").exists()
    plt.close(fig)

    # plot_bode input_format='complex'
    freq = np.logspace(-1, 5, 40)
    zr = 20 + 80 / (1 + (freq / 1e3) ** 2)
    zi = -80 * (freq / 1e3) / (1 + (freq / 1e3) ** 2)
    arr = np.column_stack([freq, zr, zi])
    fig, ax = plot_bode(arr, input_format="complex",
                         save=tmp_path / "bode_complex.png")
    assert (tmp_path / "bode_complex.png").exists()
    plt.close(fig)

    # plot_dos orientation='vertical'
    e = np.linspace(-5, 5, 100)
    total = np.exp(-(e ** 2))
    fig, ax = plot_dos((e, total), orientation="vertical",
                        save=tmp_path / "dos_vertical.png")
    assert (tmp_path / "dos_vertical.png").exists()
    plt.close(fig)

    # plot_heatmap contour + contourf
    mat = rng.random((8, 8))
    fig, ax = plot_heatmap(mat, mode="contour",
                            save=tmp_path / "heatmap_contour.png")
    assert (tmp_path / "heatmap_contour.png").exists()
    plt.close(fig)

    fig, ax = plot_heatmap(mat, mode="contourf",
                            save=tmp_path / "heatmap_contourf.png")
    assert (tmp_path / "heatmap_contourf.png").exists()
    plt.close(fig)

    # plot_uvvis tauc='indirect'
    wl = np.linspace(300, 800, 100)
    absb = 0.1 + 0.9 * np.exp(-((wl - 500) / 50) ** 2)
    fig, ax = plot_uvvis((wl, absb), tauc="indirect",
                          save=tmp_path / "uvvis_indirect.png")
    assert (tmp_path / "uvvis_indirect.png").exists()
    plt.close(fig)


def test_p2_kwargs_paths(tmp_path):
    """Guard less-exercised P2 branches: radar global norm, cohp ICOHP twin,
    pourbaix custom ph_range, rietveld hkl_positions."""
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    from huitu import plot_cohp, plot_pourbaix, plot_radar, plot_rietveld

    # radar normalize='global'
    df = pd.DataFrame(
        np.random.default_rng(0).uniform(0, 1, (3, 5)),
        index=["s1", "s2", "s3"],
        columns=[f"a{i}" for i in range(5)],
    )
    fig, _ = plot_radar(df, normalize="global",
                        save=tmp_path / "radar_global.png")
    assert (tmp_path / "radar_global.png").exists()
    plt.close(fig)

    # cohp show_icohp=True
    E = np.linspace(-5, 5, 80)
    cohp = -np.exp(-((E + 2) ** 2)) + np.exp(-((E - 1.5) ** 2))
    icohp = np.cumsum(cohp) * (E[1] - E[0])
    arr = np.column_stack([E, cohp, icohp])
    fig, _ = plot_cohp(arr, show_icohp=True,
                       save=tmp_path / "cohp_icohp.png")
    assert (tmp_path / "cohp_icohp.png").exists()
    plt.close(fig)

    # pourbaix with custom ph_range
    regions = [
        {"label": "A", "color": "tab:blue",
         "vertices": [(2, 0), (5, 0), (5, 0.5), (2, 0.5)]},
    ]
    fig, _ = plot_pourbaix(regions, ph_range=(2, 5), e_range=(-0.5, 1.0),
                            save=tmp_path / "pourbaix_custom.png")
    assert (tmp_path / "pourbaix_custom.png").exists()
    plt.close(fig)

    # rietveld with hkl_positions
    x = np.linspace(20, 60, 400)
    icalc = np.exp(-((x - 30) / 0.5) ** 2) + 0.5 * np.exp(-((x - 45) / 0.5) ** 2) + 0.05
    iobs = icalc + np.random.default_rng(0).normal(0, 0.01, x.size)
    arr = np.column_stack([x, iobs, icalc])
    fig, _ = plot_rietveld(arr, hkl_positions=[30.0, 45.0],
                            bragg_label="Bragg",
                            save=tmp_path / "rietveld_hkl.png")
    assert (tmp_path / "rietveld_hkl.png").exists()
    plt.close(fig)

    # cohp with per-bond projections kwarg
    E = np.linspace(-5, 5, 60)
    cohp = -np.exp(-((E + 2) ** 2)) + np.exp(-((E - 1.5) ** 2))
    y_s = 0.3 * np.exp(-((E + 1) ** 2))
    y_p = 0.5 * np.exp(-((E - 0.5) ** 2))
    fig, _ = plot_cohp((E, cohp), projections={"s": y_s, "p": y_p},
                       save=tmp_path / "cohp_proj.png")
    assert (tmp_path / "cohp_proj.png").exists()
    plt.close(fig)

    # phase_diagram with invariants
    from huitu import plot_phase_diagram
    regions = [{"label": "L", "color": "tab:blue",
                "vertices": [(0, 300), (1, 300), (1, 900), (0, 900)]}]
    fig, _ = plot_phase_diagram(regions,
                                invariants=[(0.3, 500, "eutectic")],
                                save=tmp_path / "phase_inv.png")
    assert (tmp_path / "phase_inv.png").exists()
    plt.close(fig)

    # radar dict-input + categories kwarg
    cats = [f"c{i}" for i in range(4)]
    dct = {"s1": [0.1, 0.5, 0.8, 0.3], "s2": [0.4, 0.2, 0.6, 0.9]}
    fig, _ = plot_radar(dct, categories=cats,
                        save=tmp_path / "radar_dict.png")
    assert (tmp_path / "radar_dict.png").exists()
    plt.close(fig)

    # share_axes with which='y' explicitly
    from huitu import make_subplots, share_axes
    fig2, axs2 = make_subplots(1, 2, journal="default", figsize=(4, 2))
    axs2[0].plot([0, 1], [0, 1])
    axs2[1].plot([0, 1], [0, 5])
    share_axes(axs2, which="y")
    fig2.savefig(tmp_path / "share_y.png")
    plt.close(fig2)


def test_crystal_vesta_fallback(tmp_path, monkeypatch):
    """plot_crystal_vesta must fall back to ASE when VESTA_BIN is unset."""
    import matplotlib.pyplot as plt
    from huitu import plot_crystal_vesta

    monkeypatch.delenv("VESTA_BIN", raising=False)
    cif = ROOT / "examples" / "sample_data" / "crystal.cif"
    out = tmp_path / "vesta_fallback.png"
    with pytest.warns(UserWarning, match="VESTA_BIN"):
        fig, _ = plot_crystal_vesta(cif, save=str(out))
    assert out.exists()
    plt.close(fig)
