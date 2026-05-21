"""One-line quickstart — XRD pattern from a 2-column text file.

The minimal "I just `pip install`d huitu, what does the API actually look like?"
demo. Replace the data path with your own to render any spectrum the same way.

Run from repo root::

    python examples/quickstart.py
"""

from pathlib import Path

import huitu

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / "quickstart.png"
OUT.parent.mkdir(exist_ok=True)

# Single function call — file path in, journal-ready figure out.
fig, ax = huitu.plot_xrd(
    str(ROOT / "sample_data" / "xrd.txt"),
    journal="nature",                       # try "acs" / "rsc" / "wiley" / …
    hkl={28.4: "(111)", 32.9: "(200)", 47.3: "(220)", 56.5: "(311)"},
    save=OUT,
)
print(f"wrote {OUT}")
