"""Nature-style figure archetype layouts.

Real Nature/Science figures rarely look like a plain ``subplots(2,3)`` grid.
They follow one of a few page archetypes that put the science before the
geometry:

* **schematic-led composite** — one wide hero panel up top (mechanism /
  device / fabrication story) plus a row of supporting quantitative panels.
* **dark image plate** — a black-faced grid of microscopy / volume-rendering
  views, no spines or ticks, with high-contrast scale bars overlaid.
* **clinical triptych** — three semantically parallel rows: longitudinal
  trajectory → forest plot of effects → compact summary bars.
* **asymmetric hero** — one biologically dominant panel spans rows or
  columns, surrounded by smaller support plots.

Each helper:

1. Calls :func:`huitu.use_journal` so axes inherit the active preset (font,
   tick width, savefig DPI, editable SVG/PDF text).
2. Returns ``(fig, axes)`` where ``axes`` is a *named dict*, so caller code
   reads as scientific intent rather than grid coordinates.
3. Writes lowercase bold panel labels (``a``, ``b``, ``c`` …) by default,
   placed near each panel's top-left edge — Nature house style.

Reference: ``Yuan1z0825/nature-skills`` / ``nature-figure``.
"""

from __future__ import annotations

from string import ascii_lowercase

import matplotlib.pyplot as plt

from huitu.style import use_journal


# ── Internal helpers ────────────────────────────────────────────────────────

def _label(ax, letter: str, *, xpad: float = -18, ypad: float = 4,
           color: str = "black", size: int = 8, weight: str = "bold") -> None:
    """Place a Nature-style lowercase panel label.

    The label is anchored to the axes' top-left corner and offset by
    ``(xpad, ypad)`` *points* (positive y = up, negative x = left) so the
    letter sits in the figure margin instead of overlapping the panel's
    y-axis tick labels — a common collision under constrained layout.
    """
    ax.annotate(
        letter,
        xy=(0, 1), xycoords="axes fraction",
        xytext=(xpad, ypad), textcoords="offset points",
        ha="left", va="bottom",
        fontsize=size, fontweight=weight, color=color,
    )


def _label_inside(ax, letter: str, *, color: str = "white",
                  size: int = 8, weight: str = "bold") -> None:
    """Inside-panel label — used over dark image plates."""
    ax.text(0.02, 0.97, letter, transform=ax.transAxes,
            fontsize=size, fontweight=weight, color=color,
            ha="left", va="top")


def _strip_image_ax(ax, facecolor: str = "black") -> None:
    """Configure an axes for microscopy/imaging tiles."""
    ax.set_facecolor(facecolor)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def _flat_letters(n: int) -> list[str]:
    """First ``n`` panel letters: a, b, c, ..."""
    if n <= len(ascii_lowercase):
        return list(ascii_lowercase[:n])
    # Wrap around if absurdly large grid (aa, ab, ...)
    out = list(ascii_lowercase)
    i = 0
    while len(out) < n:
        out.append(ascii_lowercase[i // 26 - 1] + ascii_lowercase[i % 26])
        i += 1
    return out[:n]


# ── 1. Schematic-led composite ──────────────────────────────────────────────

def schematic_led(
    *,
    journal: str = "default",
    figsize: tuple[float, float] | None = None,
    n_supports: int = 4,
    hero_height_ratio: float = 2.2,
    panel_labels: bool = True,
    hspace: float = 0.18,
    wspace: float = 0.28,
):
    """Schematic-led composite: hero panel + row of quantitative supports.

    Use when a fabrication / mechanism / device schematic must be understood
    *before* the supporting evidence. The hero panel allocates ~50–60 % of
    figure height and carries the visual narrative; supporting panels are
    smaller and quieter.

    Parameters
    ----------
    journal
        Journal preset name (``"nature"``, ``"acs"`` …).
    figsize
        Override figsize. Defaults to ``(7.2, 6.2)`` in inches — Nature
        double-column page.
    n_supports
        Number of supporting panels in the bottom row. ``2`` to ``5`` is
        typical. Defaults to ``4``.
    hero_height_ratio
        Height of the hero row relative to the support row. Higher = more
        dominant hero panel. ``2.2`` ≈ 68 % hero / 32 % supports.
    panel_labels
        Whether to draw lowercase bold panel letters (a, b, c, …).
    hspace, wspace
        Retained for backward-compat; ignored under constrained layout
        (matplotlib repacks the grid automatically).

    Returns
    -------
    fig : matplotlib.figure.Figure
    axes : dict
        ``{'hero': Axes, 'supports': [Axes, ...]}``. ``axes['supports']``
        has length ``n_supports``. Panel ``a`` is the hero; ``b…`` are the
        supports left-to-right.

    Examples
    --------
    >>> import huitu
    >>> fig, ax = huitu.archetype.schematic_led(journal="nature", n_supports=3)
    >>> ax['hero'].imshow(schematic_image)             # mechanism cartoon
    >>> huitu.plot_xrd("xrd.txt", ax=ax['supports'][0])
    >>> huitu.plot_cv ("cv.txt",  ax=ax['supports'][1])
    >>> huitu.plot_eis("eis.txt", ax=ax['supports'][2])
    >>> fig.savefig("fig1.svg")
    """
    use_journal(journal)
    if figsize is None:
        figsize = (7.2, 6.2)
    fig = plt.figure(figsize=figsize, constrained_layout=True)
    gs = fig.add_gridspec(
        2, n_supports,
        height_ratios=[hero_height_ratio, 1.0],
    )
    hero = fig.add_subplot(gs[0, :])
    supports = [fig.add_subplot(gs[1, i]) for i in range(n_supports)]
    if panel_labels:
        letters = _flat_letters(1 + n_supports)
        _label(hero, letters[0])
        for ax, ltr in zip(supports, letters[1:]):
            _label(ax, ltr)
    return fig, {"hero": hero, "supports": supports}


# ── 2. Dark image plate ─────────────────────────────────────────────────────

def dark_image_plate(
    rows: int = 3,
    cols: int = 5,
    *,
    journal: str = "default",
    figsize: tuple[float, float] | None = None,
    facecolor: str = "black",
    panel_labels: bool = True,
    only_corner_label: bool = True,
    hspace: float = 0.08,
    wspace: float = 0.04,
):
    """Repeated black-faced microscopy / fluorescence grid.

    Every cell has a black facecolor, no ticks, and no spines — ready for
    ``ax.imshow(channel_image)``. Use only **inside** the image plate region;
    keep the surrounding figure background white.

    Parameters
    ----------
    rows, cols
        Grid dimensions. ``3 × 5`` is the canonical Nature whole-brain plate.
    journal
        Journal preset name.
    figsize
        Override figsize. Defaults to ``(7.2, 6.5)``.
    facecolor
        Cell background. Black (``"#000000"``) for fluorescence/volume; switch
        to white only when the modality demands it.
    panel_labels
        Draw lowercase letters inside each cell (white text, top-left).
    only_corner_label
        If ``True`` (default), label only the first cell of each row (Nature
        convention for repeated views). If ``False``, every cell is labelled.
    hspace, wspace
        Retained for backward-compat; ignored under constrained layout.

    Returns
    -------
    fig : matplotlib.figure.Figure
    axes : list[list[Axes]]
        2-D list of axes, ``axes[r][c]``.
    """
    use_journal(journal)
    if figsize is None:
        figsize = (7.2, 6.5)
    fig = plt.figure(figsize=figsize, constrained_layout=True)
    gs = fig.add_gridspec(rows, cols)
    grid: list[list[plt.Axes]] = []
    n_total = rows * cols
    letters = _flat_letters(n_total)
    idx = 0
    for r in range(rows):
        row_axes = []
        for c in range(cols):
            ax = fig.add_subplot(gs[r, c])
            _strip_image_ax(ax, facecolor=facecolor)
            if panel_labels:
                if (not only_corner_label) or c == 0:
                    _label_inside(ax, letters[idx], color="white")
            idx += 1
            row_axes.append(ax)
        grid.append(row_axes)
    return fig, grid


# ── 3. Clinical triptych ────────────────────────────────────────────────────

def clinical_triptych(
    *,
    journal: str = "default",
    figsize: tuple[float, float] | None = None,
    n_cols: int = 3,
    height_ratios: tuple[float, float, float] = (1.0, 1.35, 0.8),
    panel_labels: bool = True,
    hspace: float = 0.32,
    wspace: float = 0.32,
):
    """Three-row clinical/longitudinal layout: trajectories → effects → bars.

    Use for outcome-over-time figures that combine longitudinal lines (top),
    forest-plot effects with a dashed reference line (middle), and compact
    summary bars (bottom). Columns stay semantically parallel — column ``i``
    on every row refers to the *same* outcome.

    Parameters
    ----------
    journal
        Journal preset name.
    figsize
        Override figsize. Defaults to ``(7.2, 6.8)``.
    n_cols
        Outcomes per row. ``3`` is canonical.
    height_ratios
        Relative heights of (top, middle, bottom). The middle row is widest
        because forest plots benefit from extra vertical space.
    panel_labels
        Draw lowercase letters near each panel's top-left edge.
    hspace, wspace
        Retained for backward-compat; ignored under constrained layout.

    Returns
    -------
    fig : matplotlib.figure.Figure
    axes : dict
        ``{'top': [Axes...], 'mid': [Axes...], 'bot': [Axes...]}``.
    """
    use_journal(journal)
    if figsize is None:
        figsize = (7.2, 6.8)
    fig = plt.figure(figsize=figsize, constrained_layout=True)
    gs = fig.add_gridspec(
        3, n_cols,
        height_ratios=list(height_ratios),
    )
    top = [fig.add_subplot(gs[0, i]) for i in range(n_cols)]
    mid = [fig.add_subplot(gs[1, i]) for i in range(n_cols)]
    bot = [fig.add_subplot(gs[2, i]) for i in range(n_cols)]
    if panel_labels:
        letters = _flat_letters(3 * n_cols)
        for ax, ltr in zip(top + mid + bot, letters):
            _label(ax, ltr)
    return fig, {"top": top, "mid": mid, "bot": bot}


# ── 4. Asymmetric hero ──────────────────────────────────────────────────────

def asymmetric_hero(
    *,
    journal: str = "default",
    figsize: tuple[float, float] | None = None,
    panel_labels: bool = True,
    hspace: float = 0.25,
    wspace: float = 0.28,
):
    """Asymmetric mixed-modality figure with one dominant panel.

    Layout (3 rows × 4 cols GridSpec)::

        ┌──────────────┬──────┬─────┐
        │      a       │  b   │     │
        ├──────────────┼──────┤     │
        │      c       │  d   │  e  │   ← e spans all 3 rows
        ├──────────────┴──────┤     │
        │           f         │     │
        └─────────────────────┴─────┘

    Use when one panel is biologically/conceptually central (UMAP, circular
    genome plot, mechanism schematic) and should dominate; the rest are
    smaller supporting plots.

    Parameters
    ----------
    journal
        Journal preset name.
    figsize
        Override figsize. Defaults to ``(7.2, 5.8)``.
    panel_labels
        Draw lowercase letters near each panel's top-left edge.
    hspace, wspace
        Retained for backward-compat; ignored under constrained layout.

    Returns
    -------
    fig : matplotlib.figure.Figure
    axes : dict
        Keys ``'a'`` … ``'f'``. Panel ``'e'`` is the hero (spans all 3 rows
        of the rightmost column).
    """
    use_journal(journal)
    if figsize is None:
        figsize = (7.2, 5.8)
    fig = plt.figure(figsize=figsize, constrained_layout=True)
    gs = fig.add_gridspec(3, 4)
    ax_a = fig.add_subplot(gs[0, :2])
    ax_b = fig.add_subplot(gs[0, 2])
    ax_c = fig.add_subplot(gs[1, :2])
    ax_d = fig.add_subplot(gs[1, 2])
    ax_e = fig.add_subplot(gs[:, 3])     # hero — spans all rows
    ax_f = fig.add_subplot(gs[2, :2])
    if panel_labels:
        for ax, ltr in zip(
            [ax_a, ax_b, ax_c, ax_d, ax_e, ax_f],
            ["a", "b", "c", "d", "e", "f"],
        ):
            _label(ax, ltr)
    return fig, {"a": ax_a, "b": ax_b, "c": ax_c, "d": ax_d,
                 "e": ax_e, "f": ax_f}


# ── Public re-exports ──────────────────────────────────────────────────────

__all__ = [
    "schematic_led",
    "dark_image_plate",
    "clinical_triptych",
    "asymmetric_hero",
]
