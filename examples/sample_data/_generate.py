"""Regenerate every sample data file used by the example scripts.

Run from the project root:

    python examples/sample_data/_generate.py

Files are tracked in git so the examples run without invoking this script.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RNG = np.random.default_rng(42)


def gaussian(x, center, width, amp):
    return amp * np.exp(-0.5 * ((x - center) / width) ** 2)


def lorentz(x, center, width, amp):
    return amp * (width**2) / ((x - center) ** 2 + width**2)


def write_xy(path: Path, x, y, header: str = ""):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        if header:
            f.write(f"# {header}\n")
        for xi, yi in zip(x, y):
            f.write(f"{xi:.6g}\t{yi:.6g}\n")


def gen_xrd():
    x = np.linspace(10, 80, 2000)
    peaks = [(28.4, 0.25, 1.0), (32.9, 0.22, 0.6), (47.3, 0.3, 0.55), (56.5, 0.28, 0.4), (76.4, 0.35, 0.3)]
    y = sum(gaussian(x, c, w, a) for c, w, a in peaks)
    y += RNG.normal(0, 0.005, x.size) + 0.01
    write_xy(HERE / "xrd.txt", x, y, "2theta\tintensity")

    shifts = [0.0, 0.3, -0.2]
    amps = [1.0, 0.9, 1.1]
    stack_dir = HERE / "xrd_stacked"
    for i, (s, a) in enumerate(zip(shifts, amps)):
        yi = sum(gaussian(x, c + s, w, ai * a) for c, w, ai in peaks)
        yi += RNG.normal(0, 0.005, x.size) + 0.01
        write_xy(stack_dir / f"sample_{i+1}.txt", x, yi)


def gen_xps():
    x = np.linspace(705, 735, 1200)
    baseline = 0.05 * (x - x.min()) + 0.5
    # Fe 2p3/2 and 2p1/2 doublet.
    comps = [(711.0, 1.4, 3.0), (724.2, 1.5, 1.8), (713.3, 1.8, 1.2)]
    y_components = [lorentz(x, c, w, a) for c, w, a in comps]
    y = baseline + sum(y_components) + RNG.normal(0, 0.03, x.size)
    write_xy(HERE / "xps.txt", x, y, "BE\tCPS")


def gen_raman():
    x = np.linspace(100, 3000, 2500)
    peaks = [(1350, 25, 0.7), (1580, 20, 1.0), (2700, 40, 0.5)]
    y = sum(lorentz(x, c, w, a) for c, w, a in peaks)
    y += RNG.normal(0, 0.01, x.size) + 0.05
    write_xy(HERE / "raman.txt", x, y)


def gen_cv():
    v = np.linspace(-0.2, 0.6, 400)
    sweep = np.concatenate([v, v[::-1]])
    # Redox couple with peak separation.
    i_ox = 1.5 * np.exp(-((sweep - 0.25) / 0.05) ** 2)
    i_red = -1.4 * np.exp(-((sweep - 0.18) / 0.05) ** 2)
    direction = np.concatenate([np.ones_like(v), -np.ones_like(v)])
    current = np.where(direction > 0, i_ox, i_red) + 0.15 * sweep + RNG.normal(0, 0.02, sweep.size)
    write_xy(HERE / "cv.txt", sweep, current, "V\tI")


def gen_gcd():
    capacity = np.linspace(0, 150, 500)
    # Charging curve (rising), then discharge back.
    v_charge = 3.2 + 0.8 * (1 - np.exp(-capacity / 60))
    v_discharge = 3.9 - 0.7 * (1 - np.exp(-(150 - capacity) / 60))
    cap_full = np.concatenate([capacity, capacity[::-1]])
    v_full = np.concatenate([v_charge, v_discharge[::-1]])
    write_xy(HERE / "gcd.txt", cap_full, v_full, "capacity\tvoltage")


def gen_cycle():
    n = 100
    cycles = np.arange(1, n + 1)
    capacity = 150 * np.exp(-cycles / 400) + RNG.normal(0, 1.5, n)
    ce = 95 + 4 * (1 - np.exp(-cycles / 5)) + RNG.normal(0, 0.4, n)
    df = pd.DataFrame({"cycle": cycles, "capacity": capacity, "ce": ce})
    df.to_csv(HERE / "cycle.txt", sep="\t", index=False)


def gen_eis():
    # Semicircle in the impedance plane + Warburg tail.
    theta = np.linspace(np.pi, 0, 120)
    r = 50.0
    zr = 10 + r * (1 + np.cos(theta)) / 2 * 0 + r * (1 - np.cos(theta)) / 2 * 0
    # Explicit parametric semicircle: center (Rs + Rct/2, 0), radius Rct/2.
    Rs, Rct = 10.0, 60.0
    center = Rs + Rct / 2
    zr = center + (Rct / 2) * np.cos(theta)
    zi = (Rct / 2) * np.sin(theta)
    # Warburg tail at low frequency.
    w = np.linspace(0.0, 25.0, 40)
    zr = np.concatenate([zr, zr[-1] + w])
    zi = np.concatenate([zi, zi[-1] + w])
    zr += RNG.normal(0, 0.4, zr.size)
    zi += RNG.normal(0, 0.4, zi.size)
    write_xy(HERE / "eis.txt", zr, zi, "Zreal\t-Zimag")


def gen_bar():
    df = pd.DataFrame(
        {
            "Sample": ["A", "B", "C", "D"],
            "Before": [4.2, 5.1, 3.9, 6.0],
            "After":  [5.8, 6.3, 4.4, 7.2],
            "Target": [6.0, 6.0, 6.0, 6.0],
        }
    )
    df.to_csv(HERE / "bar.csv", index=False)


def gen_scatter():
    x = np.linspace(0, 10, 25)
    y = 1.8 * x + 1.2 + RNG.normal(0, 1.2, x.size)
    err = 0.3 + 0.1 * RNG.random(x.size)
    df = pd.DataFrame({"x": x, "y": y, "yerr": err})
    df.to_csv(HERE / "scatter.csv", index=False)


def gen_line():
    t = np.linspace(0, 10, 200)
    df = pd.DataFrame(
        {
            "t": t,
            "voltage": 3.5 + 0.4 * np.sin(t),
            "current": 1.2 + 0.3 * np.cos(0.8 * t),
            "temperature": 25 + 5 * np.sin(0.2 * t) + 0.5 * RNG.standard_normal(t.size),
        }
    )
    df.to_csv(HERE / "line.csv", index=False)


def gen_ftir():
    x = np.linspace(400, 4000, 2000)
    # Transmittance baseline near 100%; dips represent absorption bands.
    dips = [(3400, 120, 40), (2920, 40, 25), (1630, 50, 30), (1050, 60, 35), (600, 40, 15)]
    y = 100.0 - sum(gaussian(x, c, w, a) for c, w, a in dips)
    y += RNG.normal(0, 0.3, x.size)
    write_xy(HERE / "ftir.txt", x, y, "wavenumber_cm-1\ttransmittance_%")


def gen_uvvis():
    wl = np.linspace(300, 800, 1000)
    # Sigmoidal band edge around 550 nm plus a broad band at 400 nm.
    edge = 1.5 / (1 + np.exp((wl - 550) / 15))
    band = gaussian(wl, 400, 40, 0.4)
    a = edge + band + RNG.normal(0, 0.01, wl.size) + 0.05
    write_xy(HERE / "uvvis.txt", wl, a, "wavelength_nm\tabsorbance")


def gen_pl():
    wl = np.linspace(400, 800, 1000)
    y = gaussian(wl, 620, 25, 1.0) + 0.05 + RNG.normal(0, 0.01, wl.size)
    write_xy(HERE / "pl.txt", wl, y, "wavelength_nm\tintensity")


def gen_thermal():
    T = np.linspace(25, 800, 800)
    # TGA: gentle water loss, then main decomposition.
    weight = 100 - 5 / (1 + np.exp(-(T - 120) / 15)) - 35 / (1 + np.exp(-(T - 450) / 25))
    weight += RNG.normal(0, 0.15, T.size)
    write_xy(HERE / "tga.txt", T, weight, "T_C\tweight_%")

    # DSC: small endothermic near 120 (water), exothermic decomposition around 450.
    heatflow = -gaussian(T, 120, 12, 0.6) + gaussian(T, 450, 30, 1.5) + RNG.normal(0, 0.02, T.size)
    write_xy(HERE / "dsc.txt", T, heatflow, "T_C\theatflow_mW/mg")


def gen_bode():
    freq = np.logspace(-1, 5, 80)
    # RC circuit-ish response: Rs + Rct/(1+j*omega*tau).
    Rs, Rct, C = 10.0, 80.0, 1e-5
    omega = 2 * np.pi * freq
    Z = Rs + Rct / (1 + 1j * omega * Rct * C)
    mag = np.abs(Z)
    phase = np.degrees(np.angle(Z))
    arr = np.column_stack([freq, mag, phase])
    np.savetxt(HERE / "bode.txt", arr, fmt="%.6g", delimiter="\t",
               header="freq_Hz\tZ_mag_ohm\tphase_deg")


def gen_tafel():
    # Linear region j from 1e-5 to 1e-2 A/cm^2, slope 120 mV/dec.
    logj = np.linspace(-6, -1, 60)
    eta = 0.15 + 0.120 * (logj - (-4)) + RNG.normal(0, 0.005, logj.size)
    # Curvature near the foot to mimic mass transport / exchange current.
    eta[logj < -5] += 0.03 * (-5 - logj[logj < -5])
    write_xy(HERE / "tafel.txt", logj, eta, "log_j\teta_V")


def gen_band():
    kpath = np.linspace(0, 1, 100)
    # Simple synthetic bands: two valence (below 0), two conduction.
    b1 = -2.5 - 1.5 * np.cos(np.pi * kpath)
    b2 = -1.2 - 0.9 * np.cos(np.pi * (kpath - 0.2))
    b3 = 1.5 + 1.2 * np.cos(np.pi * kpath)
    b4 = 2.8 + 0.6 * np.cos(np.pi * kpath)
    arr = np.column_stack([kpath, b1, b2, b3, b4])
    np.savetxt(HERE / "band.txt", arr, fmt="%.6g", delimiter="\t",
               header="k\tb1\tb2\tb3\tb4")


def gen_dos():
    E = np.linspace(-8, 6, 800)
    total = (gaussian(E, -4, 0.8, 2.0) + gaussian(E, -2, 0.5, 1.2)
             + gaussian(E, 2, 0.7, 1.5) + gaussian(E, 4, 0.9, 1.0))
    s = 0.4 * gaussian(E, -5, 1.0, 1.0)
    p = gaussian(E, -2, 0.6, 0.9) + 0.5 * gaussian(E, 3, 0.8, 1.0)
    d = gaussian(E, -4, 0.7, 1.5) + gaussian(E, 2, 0.6, 1.2)
    arr = np.column_stack([E, total, s, p, d])
    df = pd.DataFrame(arr, columns=["energy", "total", "s", "p", "d"])
    df.to_csv(HERE / "dos.txt", sep="\t", index=False)


def gen_heatmap():
    rows = [f"r{i+1}" for i in range(10)]
    cols = [f"c{i+1}" for i in range(10)]
    base = np.linspace(0, 1, 10)[:, None] + np.linspace(0, 1, 10)[None, :]
    mat = base + 0.2 * RNG.standard_normal((10, 10))
    df = pd.DataFrame(mat, index=rows, columns=cols)
    df.to_csv(HERE / "heatmap.csv")


def gen_rietveld():
    x = np.linspace(10, 80, 1200)
    peaks = [(28.4, 0.25, 1.0), (47.3, 0.30, 0.55), (56.5, 0.28, 0.4)]
    icalc = sum(gaussian(x, c, w, a) for c, w, a in peaks)
    ibkg = 0.05 + 0.0005 * (x - x.min())
    icalc = icalc + ibkg
    iobs = icalc + RNG.normal(0, 0.015, x.size)
    arr = np.column_stack([x, iobs, icalc, ibkg])
    np.savetxt(HERE / "rietveld.txt", arr, fmt="%.6g", delimiter="\t",
               header="2theta\tI_obs\tI_calc\tI_bkg")


def gen_cohp():
    E = np.linspace(-8, 4, 400)
    # Bonding lobe below E_F (negative COHP), antibonding above (positive).
    cohp = -gaussian(E, -3.0, 0.6, 1.5) + gaussian(E, 2.0, 0.7, 1.2)
    icohp = np.cumsum(cohp) * (E[1] - E[0])
    arr = np.column_stack([E, cohp, icohp])
    np.savetxt(HERE / "cohp.txt", arr, fmt="%.6g", delimiter="\t",
               header="energy_eV\t-COHP\tICOHP")


def gen_radar():
    rng = np.random.default_rng(7)
    cats = ["Capacity", "Rate", "Cycle life", "Coulombic eff.", "Cost", "Safety"]
    samples = ["Alloy A", "Alloy B", "Alloy C", "Alloy D"]
    data = rng.uniform(0.3, 1.0, (len(samples), len(cats)))
    df = pd.DataFrame(data, index=samples, columns=cats)
    df.to_csv(HERE / "radar.csv")


def gen_crystal_cif():
    cif = """data_NaCl
_cell_length_a 5.6402
_cell_length_b 5.6402
_cell_length_c 5.6402
_cell_angle_alpha 90
_cell_angle_beta 90
_cell_angle_gamma 90
_symmetry_space_group_name_H-M 'P 1'
loop_
_atom_site_label
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
Na1 0.0 0.0 0.0
Na2 0.5 0.5 0.0
Na3 0.5 0.0 0.5
Na4 0.0 0.5 0.5
Cl1 0.5 0.0 0.0
Cl2 0.0 0.5 0.0
Cl3 0.0 0.0 0.5
Cl4 0.5 0.5 0.5
"""
    (HERE / "crystal.cif").write_text(cif)


def gen_boxviolin():
    n = 30
    groups = ["A", "B", "C", "D"]
    means = [3.0, 4.5, 4.0, 5.2]
    sds = [0.7, 0.8, 0.6, 1.0]
    records = []
    for g, m, s in zip(groups, means, sds):
        vals = RNG.normal(m, s, n)
        for v in vals:
            records.append({"sample": g, "value": float(v)})
    pd.DataFrame(records).to_csv(HERE / "boxviolin.csv", index=False)


def main():
    gen_xrd()
    gen_xps()
    gen_raman()
    gen_cv()
    gen_gcd()
    gen_cycle()
    gen_eis()
    gen_bar()
    gen_scatter()
    gen_line()
    gen_ftir()
    gen_uvvis()
    gen_pl()
    gen_thermal()
    gen_bode()
    gen_tafel()
    gen_band()
    gen_dos()
    gen_heatmap()
    gen_boxviolin()
    gen_rietveld()
    gen_cohp()
    gen_radar()
    gen_crystal_cif()
    print("sample data written to", HERE)


if __name__ == "__main__":
    main()
