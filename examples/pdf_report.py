"""Multi-figure PDF report demo (v0.6).

Bundles 4 figures (XRD + CV + EIS + GCD) into a single PDF with a cover
page and per-figure captions. Demonstrates the typical "share a complete
characterisation campaign in one document" workflow.
"""

from pathlib import Path

import huitu

ROOT = Path(__file__).resolve().parent
SAMPLE = ROOT / "sample_data"
OUT = ROOT / "output" / "pdf_report.pdf"
OUT.parent.mkdir(exist_ok=True)

# Build four figures using huitu's standard plot_* API.
fig_xrd, _ = huitu.plot_xrd(str(SAMPLE / "xrd.txt"), journal="nature")
fig_cv, _ = huitu.plot_cv(str(SAMPLE / "cv.txt"), journal="nature")
fig_eis, _ = huitu.plot_eis(str(SAMPLE / "eis.txt"), journal="nature")
fig_gcd, _ = huitu.plot_gcd(str(SAMPLE / "gcd.txt"), journal="nature")

# Compose into one multi-page PDF — cover page + 4 figures with captions.
out_path = huitu.make_pdf_report(
    [fig_xrd, fig_cv, fig_eis, fig_gcd],
    save=OUT,
    title="Sample MnO₂-Cu characterisation",
    subtitle="Full electrochemical workup",
    metadata=[
        "sample      = MnO₂-Cu (Cu-doped)",
        "operator    = YL",
        "date        = 2026-05-21",
        "instrument  = D8 Advance / Biologic VMP3",
    ],
    captions=[
        "Fig 1. XRD pattern (Cu Kα, 10–80°).",
        "Fig 2. CV at 5 mV s⁻¹ (vs. ref.) — three cycles overlaid.",
        "Fig 3. EIS Nyquist plot at OCV.",
        "Fig 4. Galvanostatic charge–discharge at 0.5 / 1 / 2 C.",
    ],
)
print(f"wrote {out_path}")
