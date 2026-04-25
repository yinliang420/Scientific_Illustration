"""Shared pytest configuration.

Forces matplotlib to use the non-interactive Agg backend so the example
scripts can be executed in headless CI environments.
"""

from __future__ import annotations

import os

import matplotlib

os.environ.setdefault("MPLBACKEND", "Agg")
matplotlib.use("Agg", force=True)
