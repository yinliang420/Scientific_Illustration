"""Compatibility shim — licensing has been removed.

All functions that used to live behind a license gate are now part of the
standard huitu API. This module is kept so that old code that still calls
``huitu.pro.activate(...)``, imports ``ProLicenseError``, or calls
``require_pro(...)`` keeps working without modification.

Everything here is a no-op: activation always succeeds, ``is_active()``
always reports ``True``, and ``require_pro()`` never raises.
"""

from __future__ import annotations


class ProLicenseError(RuntimeError):
    """Deprecated — retained only so legacy ``except`` clauses keep working.

    Huitu no longer gates any features behind a license, so this exception is
    never raised by the library itself.
    """


def activate(key: str | None = None) -> bool:  # noqa: ARG001 — kept for API compat
    """No-op activation. Always returns ``True``.

    The ``key`` argument is ignored; it is accepted only so that existing
    calls like ``huitu.pro.activate("HUITU-PRO-...")`` keep working.
    """
    return True


def is_active() -> bool:
    """Always ``True`` — every feature is available by default."""
    return True


def require_pro(feature: str = "this feature") -> None:  # noqa: ARG001
    """No-op guard. Previously raised when a license was missing."""
    return None


def deactivate() -> None:
    """No-op. Retained for API compatibility."""
    return None
