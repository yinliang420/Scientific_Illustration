"""Flexible two-column reader for .txt / .csv files."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Tuple, Union

import numpy as np
import pandas as pd

PathLike = Union[str, Path]


def read_xy(path: PathLike) -> Tuple[np.ndarray, np.ndarray]:
    """Return `(x, y)` numeric arrays from a two-column text file.

    Accepts comma-, whitespace-, or tab-separated files, an optional header
    row, and both ``#`` and ``%`` comment markers. The first two numeric
    columns are returned.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)

    # pandas supports only a single comment char; pre-strip '%' lines.
    raw = p.read_text()
    cleaned = "\n".join(
        line for line in raw.splitlines() if not line.lstrip().startswith("%")
    )
    buf = io.StringIO(cleaned)

    try:
        df = pd.read_csv(buf, sep=None, engine="python", comment="#", header=None)
    except Exception:
        buf.seek(0)
        df = pd.read_csv(buf, sep=r"\s+", engine="python", comment="#", header=None)

    # Drop a non-numeric header row if present; coerce remainder to numeric.
    df = df.apply(pd.to_numeric, errors="coerce").dropna(how="all")

    if df.shape[1] < 2:
        raise ValueError(f"{p}: need at least two numeric columns")

    x = df.iloc[:, 0].to_numpy(dtype=float)
    y = df.iloc[:, 1].to_numpy(dtype=float)
    mask = ~(np.isnan(x) | np.isnan(y))
    return x[mask], y[mask]
