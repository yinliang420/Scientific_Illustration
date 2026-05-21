"""Multi-figure PDF report — one figure per page, optional cover + captions.

Compose any list of matplotlib figures into a single multi-page PDF, with
optional cover page and per-page captions. Useful for sharing a full
characterisation campaign as one document (each figure stays at huitu's
journal-grade 600 dpi defaults, and PDF text remains selectable thanks
to ``pdf.fonttype=42`` set globally in :mod:`huitu.style`).

Reference: matplotlib's ``PdfPages`` API.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from huitu.style import role, use_journal


def _coerce_path(path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _render_cover(
    pdf: PdfPages,
    title: str,
    subtitle: str | None,
    metadata_lines: Sequence[str],
    journal: str,
) -> None:
    """Draw a simple cover page: title + optional subtitle + metadata table."""
    use_journal(journal)
    fig = plt.figure(figsize=(8.27, 11.69))   # A4 portrait
    fig.patch.set_facecolor("white")

    # Big title.
    fig.text(0.5, 0.78, title, ha="center", va="center",
             fontsize=22, fontweight="bold", color=role("hero"))
    if subtitle:
        fig.text(0.5, 0.72, subtitle, ha="center", va="center",
                 fontsize=12, color=role("neutral_dark"))

    # Metadata block (one line each, left-aligned in a centred column).
    if metadata_lines:
        block = "\n".join(metadata_lines)
        fig.text(0.5, 0.45, block, ha="center", va="center",
                 fontsize=10, color=role("neutral_dark"),
                 family="monospace")

    # Footer.
    fig.text(0.5, 0.06,
             "Generated with huitu — journal-ready figures for materials science",
             ha="center", va="center", fontsize=8,
             color=role("neutral"))

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def _attach_caption(fig, caption: str) -> None:
    """Anchor a caption below the figure's existing content."""
    fig.text(
        0.5, 0.01, caption,
        ha="center", va="bottom",
        fontsize=8, color=role("neutral_dark"),
        wrap=True,
    )


def make_pdf_report(
    figures: Iterable,
    save,
    *,
    title: str | None = None,
    subtitle: str | None = None,
    metadata: Sequence[str] = (),
    captions: Sequence[str | None] | None = None,
    journal: str = "default",
    keep_open: bool = False,
) -> Path:
    """Compose ``figures`` into a multi-page PDF.

    Parameters
    ----------
    figures
        Iterable of :class:`matplotlib.figure.Figure`. The order in the
        iterable is the order on disk.
    save
        Output PDF path. Parent directories are created.
    title
        If given, a cover page is rendered using this string as the headline.
    subtitle
        Optional second line on the cover.
    metadata
        List of key/value-style strings displayed below the cover headline,
        e.g. ``["sample = MnO2-Cu", "operator = YL", "date = 2026-05-21"]``.
    captions
        Optional caption per figure (same length as ``figures``). Strings
        are anchored below each figure as `fig.text(0.5, 0.01, ...)`. Use
        ``None`` to skip a page's caption.
    journal
        Journal preset name (cover-page only; the figure pages keep
        whatever preset they were drawn with).
    keep_open
        If ``True``, figures are *not* closed after writing — handy when
        the caller wants to keep working with them. Default ``False``
        closes every figure with :func:`matplotlib.pyplot.close` to free
        memory.

    Returns
    -------
    pathlib.Path
        The absolute path of the saved PDF.

    Examples
    --------
    >>> import huitu
    >>> fig1, _ = huitu.plot_xrd("xrd.txt")
    >>> fig2, _ = huitu.plot_cv("cv.txt")
    >>> huitu.make_pdf_report(
    ...     [fig1, fig2],
    ...     save="reports/sample_2026-05.pdf",
    ...     title="MnO2 / Cu sample — May 2026",
    ...     metadata=["sample = MnO2-Cu", "operator = YL"],
    ...     captions=["Fig 1. XRD", "Fig 2. CV at 5 mV s⁻¹"],
    ... )
    """
    fig_list = list(figures)
    if not fig_list:
        raise ValueError("make_pdf_report needs at least one figure")
    if captions is not None and len(captions) != len(fig_list):
        raise ValueError(
            f"captions length {len(captions)} does not match "
            f"figures length {len(fig_list)}"
        )

    out_path = _coerce_path(save)

    with PdfPages(out_path) as pdf:
        if title is not None:
            _render_cover(pdf, title, subtitle, metadata, journal)
        for i, fig in enumerate(fig_list):
            cap = captions[i] if captions is not None else None
            if cap:
                _attach_caption(fig, cap)
            pdf.savefig(fig, bbox_inches="tight")
            if not keep_open:
                plt.close(fig)

    return out_path
