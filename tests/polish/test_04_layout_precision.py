"""Polish test 04 — layout precision (the user's big complaint).

User said (verbatim):

> "对于 layout 这个部分，能够再实现一些精细吗，现在看来还是有点儿问题，有的图
>  还是会有遮挡线。"

Concrete defects from the showcase pictures:
  * Pourbaix water-stability dashed lines pass through region labels
  * Pourbaix polygons may not tile cleanly (triangular gap)
  * Title color sometimes grey while axis labels are black
  * Multi-panel colorbar can clip the panel below
  * plot_operando_xrd_echem title overlaps the top-mounted colorbar
  * plot_rietveld residual-panel y-axis label clips figure edge
  * archetype.schematic_led panel letter can sit on top of subtitle text
  * plot_dqdv legend may overlap a tall peak at high V

Each case asserts on **pixel-level** geometry after a ``fig.canvas.draw()``
so the test catches regressions even when the figure "looks fine" to a human.
"""

from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pytest

from .conftest import (
    bbox_inside,
    bbox_overlaps,
    line_text_overlap,
    report,
    sample,
)


# ── 1. Pourbaix: dashed lines must not pass through region label text ──────

def test_case_01_pourbaix_dashed_lines_clear_labels():
    """case_01: H2/H2O dashed line does not cross the centroid label of a region.

    Construct a region whose centroid falls near ``y = -0.05916 * pH`` so the
    overlap is geometrically forced. We assert that the rendered text bbox
    does NOT overlap the line's window-extent. A pass would mean huitu has
    rerouted/blocked the labels (white halo, smart placement, etc).
    """
    import huitu

    # Centroid at (5, -0.15) sits exactly on the H2 line for pH=5.
    # We deliberately design a region whose centroid is on the line.
    huitu.use_journal("default")
    regions = [
        {"label": "Phase A", "color": "tab:blue",
         "vertices": [(2, -0.5), (8, -0.5), (8, 0.2), (2, 0.2)]},
    ]
    fig, ax = huitu.plot_pourbaix(regions)
    fig.canvas.draw()
    # The region's centroid label is the first ax.texts entry (legend texts
    # are attached to ax separately).
    region_texts = [t for t in ax.texts if "Phase" in t.get_text()]
    dashed = [l for l in ax.lines if l.get_linestyle() == "--"]
    overlap = False
    for line in dashed:
        for txt in region_texts:
            if line_text_overlap(ax, line, txt):
                overlap = True
                break
    plt.close(fig)
    ok = not overlap
    report(1, "Pourbaix dashed H2O lines clear region labels",
           ok, "H2/H2O lines overlap region centroid label — user's exact complaint")
    assert ok


def test_case_02_pourbaix_polygons_tile_cleanly():
    """case_02: adjacent Pourbaix polygons share an edge with no gap.

    Two regions sharing the edge ``y=0`` must produce a combined region with
    zero gap. We sample the rendered figure at the seam and check that the
    pixel has a non-white color value.
    """
    import huitu

    huitu.use_journal("default")
    regions = [
        {"label": "A", "color": "#0044aa",
         "vertices": [(0, -1), (5, -1), (5, 0), (0, 0)]},
        {"label": "B", "color": "#aa4400",
         "vertices": [(0, 0), (5, 0), (5, 1), (0, 1)]},
    ]
    fig, ax = huitu.plot_pourbaix(regions, water_stability=False)
    fig.canvas.draw()
    # Sample a column of pixels right through the seam in display coords.
    x_data = 2.5
    y_data = 0.0  # shared edge
    px, py = ax.transData.transform((x_data, y_data))
    # Use figure as an array
    buf = fig.canvas.tostring_argb()
    w, h = fig.canvas.get_width_height()
    arr = np.frombuffer(buf, dtype=np.uint8).reshape(h, w, 4)
    # ARGB -> get pixel
    px_i, py_i = int(px), int(h - py)  # invert y
    px_i = max(0, min(w - 1, px_i))
    py_i = max(0, min(h - 1, py_i))
    a, r, g, b = arr[py_i, px_i]
    # Pure white pixel = (255,255,255,255). A polygon edge with alpha=0.45
    # over white gives a tinted pixel.
    not_white = not (r > 240 and g > 240 and b > 240)
    plt.close(fig)
    report(2, "Pourbaix polygon seam pixel is tinted, not white",
           not_white,
           f"seam pixel rgb=({r},{g},{b}) suggests tile gap")
    assert not_white


# ── 3. Title color matches axis-label color ────────────────────────────────

@pytest.mark.parametrize("journal", ["default", "nature", "science", "acs"])
def test_case_03_title_color_matches_labels(journal):
    """case_03: ``ax.title`` color matches ``ax.xaxis.label`` color.

    The showcase Pourbaix figure had a grey title and black axis labels —
    visually inconsistent. We assert they agree after a baseline ``set_title``
    call.
    """
    import huitu

    huitu.use_journal(journal)
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    ax.set_title("Test title")
    ax.set_xlabel("X label")
    ax.set_ylabel("Y label")
    fig.canvas.draw()
    title_color = mpl.colors.to_rgba(ax.title.get_color())
    xlabel_color = mpl.colors.to_rgba(ax.xaxis.label.get_color())
    plt.close(fig)
    ok = title_color == xlabel_color
    report(3, f"title color == xlabel color (journal={journal})",
           ok, f"title={title_color} xlabel={xlabel_color}")
    assert ok


# ── 4. Multi-panel colorbar must not clip neighbours ───────────────────────

def test_case_04_subplots_colorbar_no_clip():
    """case_04: a colorbar in panel a does not clip into panel b under
    constrained layout."""
    import huitu

    huitu.use_journal("default")
    fig, axes = huitu.make_subplots(1, 2, journal="default", figsize=(6, 3))
    im = axes[0].imshow(np.random.default_rng(0).random((10, 10)))
    cbar = fig.colorbar(im, ax=axes[0])
    fig.canvas.draw()
    cbar_bbox = cbar.ax.get_window_extent()
    panel_b_bbox = axes[1].get_window_extent()
    overlap = bbox_overlaps(cbar_bbox, panel_b_bbox)
    plt.close(fig)
    ok = not overlap
    report(4, "subplot colorbar does not overlap neighbouring panel",
           ok, "colorbar bbox intersects panel b — visible clip")
    assert ok


# ── 5. plot_operando_xrd_echem: top colorbar shouldn't overlap heatmap ─────

def test_case_05_operando_xrd_echem_layout():
    """case_05: top-mounted colorbar in operando_xrd_echem does not overlap
    the heatmap axes."""
    import huitu

    huitu.use_journal("default")
    M, N = 30, 100
    Z = np.random.default_rng(0).random((M, N))
    x = np.linspace(10, 30, N)
    y = np.arange(M)
    echem = np.linspace(2.5, 4.2, M)
    fig, (ax_map, ax_ec) = huitu.plot_operando_xrd_echem(
        Z, x=x, y=y, echem=echem,
    )
    fig.canvas.draw()
    # The colorbar lives in a child axes; find it by axis type
    cb_axes = [a for a in fig.axes if a not in (ax_map, ax_ec)]
    ax_map_bbox = ax_map.get_window_extent()
    bad = False
    for cba in cb_axes:
        cb_bbox = cba.get_window_extent()
        # The colorbar should sit ABOVE ax_map (not inside it).
        if bbox_overlaps(cb_bbox, ax_map_bbox):
            # Allow tiny overlap (1 px) — but anything substantial = bad.
            x_ovr = min(cb_bbox.x1, ax_map_bbox.x1) - max(cb_bbox.x0, ax_map_bbox.x0)
            y_ovr = min(cb_bbox.y1, ax_map_bbox.y1) - max(cb_bbox.y0, ax_map_bbox.y0)
            if x_ovr > 5 and y_ovr > 5:
                bad = True
                break
    plt.close(fig)
    ok = not bad
    report(5, "operando_xrd_echem colorbar sits outside heatmap axes",
           ok, "top-mounted colorbar substantially overlaps heatmap")
    assert ok


# ── 6. Rietveld residual y-label clipping ──────────────────────────────────

def test_case_06_rietveld_residual_label_no_clip(tmp_path):
    """case_06: residual-panel ylabel ("diff") does not clip beyond figure bbox.

    The residual panel is narrow; on tight layouts the ylabel sometimes
    extends past the figure's left edge. We check that the ylabel's
    bbox is entirely inside the figure's bbox after savefig.
    """
    import huitu

    huitu.use_journal("default")
    x = np.linspace(20, 60, 200)
    icalc = np.exp(-((x - 30) / 0.4) ** 2) + 0.6 * np.exp(-((x - 45) / 0.4) ** 2)
    iobs = icalc + np.random.default_rng(0).normal(0, 0.02, x.size)
    arr = np.column_stack([x, iobs, icalc])
    out = tmp_path / "rietveld.png"
    fig, _ = huitu.plot_rietveld(arr, save=out)
    fig.canvas.draw()
    # Find the diff axes (lower one)
    axes = fig.axes
    diff_ax = axes[-1] if len(axes) >= 2 else axes[0]
    ylabel_bbox = diff_ax.yaxis.label.get_window_extent()
    fig_bbox = fig.bbox
    ok = bbox_inside(ylabel_bbox, fig_bbox, pad_px=2.0)
    plt.close(fig)
    report(6, "Rietveld residual ylabel stays inside figure bbox",
           ok, "residual ylabel clipped past figure left edge")
    assert ok


# ── 7. archetype.schematic_led panel letter vs subtitle ───────────────────

def test_case_07_archetype_letter_no_overlap():
    """case_07: in archetype.schematic_led, the panel letter 'a' for the hero
    does not overlap the hero panel's title (if a title is set)."""
    import huitu

    fig, ax = huitu.archetype.schematic_led(journal="default", n_supports=3)
    ax["hero"].set_title("Hero panel title")
    fig.canvas.draw()
    title_bbox = ax["hero"].title.get_window_extent()
    # Find the annotation letter — schematic_led places it via ax.annotate
    annos = [c for c in ax["hero"].texts if c.get_text() in tuple("abcdefghij")]
    if not annos:
        # The label might be on a child annotation; pull from figure children
        annos = []
        for child in fig.findobj():
            if hasattr(child, "get_text") and child.get_text() in tuple("abcdefghij"):
                annos.append(child)
    overlap = False
    for a in annos:
        try:
            if bbox_overlaps(a.get_window_extent(), title_bbox):
                overlap = True
                break
        except Exception:
            continue
    plt.close(fig)
    ok = not overlap
    report(7, "archetype panel letter does not overlap panel title",
           ok, "hero panel letter overlaps suptitle/title")
    assert ok


# ── 8. plot_dqdv legend vs tall peak ──────────────────────────────────────

def test_case_08_dqdv_legend_no_peak_overlap():
    """case_08: dQ/dV legend doesn't overlap the tallest peak in the curve."""
    import huitu

    huitu.use_journal("default")
    v = np.linspace(2.5, 4.2, 400)
    # Sharp, tall peak near V=3.5 to force a clash with legend in upper region
    q = np.cumsum(np.exp(-((v - 3.5) ** 2) / 0.002))
    fig, ax = huitu.plot_dqdv((v, q), labels=["Ours"])
    fig.canvas.draw()
    legend = ax.get_legend()
    if legend is None:
        ok = True
        report(8, "dQ/dV legend exists or absent OK (no overlap to check)", ok, "")
        plt.close(fig)
        return
    leg_bbox = legend.get_window_extent()
    # Sample line bounding box
    line_bbox = ax.lines[0].get_window_extent()
    overlap = bbox_overlaps(leg_bbox, line_bbox)
    plt.close(fig)
    # Soft assertion — overlap is bad but acceptable if "outside" placement.
    ok = not overlap
    report(8, "dQ/dV legend does not overlap data trace",
           ok, "legend overlaps the tallest dQ/dV peak — readability hurt")
    assert ok


# ── 9. Twin-y axis labels don't collide ────────────────────────────────────

def test_case_09_twin_y_label_no_collision():
    """case_09: two y-axis labels on a twin-y plot do not overlap."""
    import huitu

    huitu.use_journal("default")
    fig, ax = plt.subplots()
    ax2 = ax.twinx()
    ax.plot([0, 1, 2], [0, 1, 2])
    ax2.plot([0, 1, 2], [10, 20, 30], color="red")
    ax.set_ylabel("primary axis label")
    ax2.set_ylabel("secondary axis label")
    fig.canvas.draw()
    b1 = ax.yaxis.label.get_window_extent()
    b2 = ax2.yaxis.label.get_window_extent()
    overlap = bbox_overlaps(b1, b2)
    plt.close(fig)
    ok = not overlap
    report(9, "twin-y axis labels do not overlap", ok,
           "primary + secondary ylabel bboxes overlap")
    assert ok


# ── 10. multi-panel figure with multiple colorbars (asymmetric_hero) ──────

def test_case_10_asymmetric_hero_no_axis_clip():
    """case_10: asymmetric_hero panel 'f' colorbar (if added) does not clip
    figure edge."""
    import huitu

    fig, ax = huitu.archetype.asymmetric_hero(journal="default")
    im = ax["e"].imshow(np.random.default_rng(0).random((5, 5)))
    cbar = fig.colorbar(im, ax=ax["e"])
    fig.canvas.draw()
    cb_bbox = cbar.ax.get_window_extent()
    fig_bbox = fig.bbox
    ok = bbox_inside(cb_bbox, fig_bbox, pad_px=2.0)
    plt.close(fig)
    report(10, "asymmetric_hero hero-panel colorbar fits inside figure",
           ok, "colorbar clipped past figure edge")
    assert ok


# ── 11. plot_xrd label overflow into next subplot ──────────────────────────

def test_case_11_xrd_xlabel_inside_axes():
    """case_11: xlabel ``"2θ (°)"`` rendered for plot_xrd stays within the
    axes' allocated rectangle (no overflow into adjacent subplot)."""
    import huitu

    huitu.use_journal("nature")
    fig, axes = huitu.make_subplots(1, 2, journal="nature")
    huitu.plot_xrd(sample("xrd.txt"), ax=axes[0])
    huitu.plot_xrd(sample("xrd.txt"), ax=axes[1])
    fig.canvas.draw()
    # Right edge of axes[0].xlabel vs left edge of axes[1].axes_bbox.
    xlab_bbox = axes[0].xaxis.label.get_window_extent()
    ax1_bbox = axes[1].get_window_extent()
    ok = xlab_bbox.x1 <= ax1_bbox.x0 + 5  # 5px tolerance
    plt.close(fig)
    report(11, "left subplot xlabel does not run into right subplot",
           ok, f"xlabel.x1={xlab_bbox.x1:.1f} > ax1.x0={ax1_bbox.x0:.1f}")
    assert ok


# ── 12. Pourbaix legend placement ─────────────────────────────────────────

def test_case_12_pourbaix_legend_not_over_region():
    """case_12: the H2/O2 legend doesn't sit on top of a region label."""
    import huitu

    regions = [
        {"label": "Wide region", "color": "tab:blue",
         "vertices": [(0, -1), (14, -1), (14, 2), (0, 2)]},
    ]
    huitu.use_journal("default")
    fig, ax = huitu.plot_pourbaix(regions)
    fig.canvas.draw()
    legend = ax.get_legend()
    if legend is None:
        ok = True
        report(12, "Pourbaix legend handled or absent", ok, "")
        plt.close(fig)
        return
    leg_bbox = legend.get_window_extent()
    region_texts = [t for t in ax.texts if t.get_text() == "Wide region"]
    overlap = any(bbox_overlaps(leg_bbox, t.get_window_extent())
                  for t in region_texts)
    plt.close(fig)
    ok = not overlap
    report(12, "Pourbaix legend does not overlap a region label",
           ok, "legend obscures region centroid label")
    assert ok


# ── 13. plot_operando_xrd_echem title does not overlap the colorbar ───────

def test_case_13_operando_title_no_cb_overlap():
    """case_13: a user-set ``fig.suptitle`` on operando_xrd_echem stays above
    the top-mounted colorbar."""
    import huitu

    huitu.use_journal("default")
    M, N = 20, 80
    Z = np.random.default_rng(0).random((M, N))
    x = np.linspace(10, 30, N)
    y = np.arange(M)
    echem = np.linspace(2.5, 4.2, M)
    fig, (ax_map, ax_ec) = huitu.plot_operando_xrd_echem(
        Z, x=x, y=y, echem=echem,
    )
    fig.suptitle("Operando XRD/echem")
    fig.canvas.draw()
    sup_bbox = fig._suptitle.get_window_extent()
    cb_axes = [a for a in fig.axes if a not in (ax_map, ax_ec)]
    overlap = False
    for cba in cb_axes:
        if bbox_overlaps(sup_bbox, cba.get_window_extent()):
            overlap = True
            break
    plt.close(fig)
    ok = not overlap
    report(13, "operando_xrd_echem suptitle does not overlap colorbar",
           ok, "suptitle sits on top of the colorbar axes")
    assert ok


# ── 14. plot_rietveld difference panel has its own y-axis label ───────────

def test_case_14_rietveld_diff_ylabel_present():
    """case_14: residual subplot has a non-empty ylabel."""
    import huitu

    x = np.linspace(20, 60, 200)
    icalc = np.exp(-((x - 30) / 0.4) ** 2)
    iobs = icalc + 0.02
    arr = np.column_stack([x, iobs, icalc])
    huitu.use_journal("default")
    fig, _ = huitu.plot_rietveld(arr)
    axes = fig.axes
    diff_ax = axes[-1]
    ylab = diff_ax.get_ylabel()
    plt.close(fig)
    ok = bool(ylab.strip())
    report(14, "Rietveld diff axes has a non-empty ylabel", ok,
           f"ylabel was {ylab!r}")
    assert ok


# ── 15. plot_eis: Nyquist square aspect not broken ─────────────────────────

def test_case_15_eis_nyquist_aspect():
    """case_15: Nyquist plot's data aspect is approximately 1:1 (semicircle
    must look like a circle, not an oval)."""
    import huitu

    huitu.use_journal("default")
    fig, ax = huitu.plot_eis(sample("eis.txt"))
    fig.canvas.draw()
    aspect = ax.get_aspect()
    plt.close(fig)
    # Either explicit 'equal' or a numeric float close to 1.0.
    ok = aspect in ("equal", 1.0) or (isinstance(aspect, (int, float))
                                       and 0.5 <= float(aspect) <= 2.0)
    report(15, "Nyquist plot data aspect is 1:1 (or 'equal')", ok,
           f"got aspect={aspect}")
    assert ok


# ── 16. supertitle Y position doesn't bleed off page ──────────────────────

def test_case_16_supertitle_inside_figure():
    """case_16: huitu.supertitle places the suptitle text inside the figure bbox."""
    import huitu

    fig, axes = huitu.make_subplots(2, 2, journal="default", figsize=(5, 4))
    huitu.supertitle(fig, "Big title across panels")
    fig.canvas.draw()
    sup_bbox = fig._suptitle.get_window_extent()
    ok = bbox_inside(sup_bbox, fig.bbox, pad_px=2.0)
    plt.close(fig)
    report(16, "supertitle stays inside figure", ok,
           "suptitle bbox clipped past figure top edge")
    assert ok


# ── 17. constrained_layout is on by default ────────────────────────────────

def test_case_17_constrained_layout_on():
    """case_17: ``figure.constrained_layout.use=True`` after use_journal."""
    import huitu

    huitu.use_journal("nature")
    ok = bool(mpl.rcParams.get("figure.constrained_layout.use", False))
    report(17, "constrained_layout enabled after use_journal", ok,
           f"got {mpl.rcParams.get('figure.constrained_layout.use')}")
    assert ok


# ── 18. plot_pourbaix water_stability=False removes lines completely ──────

def test_case_18_pourbaix_no_water_stability():
    """case_18: ``water_stability=False`` produces zero dashed lines and zero
    legend entry — letting users build a clean Pourbaix without the overlap."""
    import huitu

    huitu.use_journal("default")
    regions = [
        {"label": "A", "color": "tab:blue",
         "vertices": [(0, -1), (5, -1), (5, 0), (0, 0)]},
    ]
    fig, ax = huitu.plot_pourbaix(regions, water_stability=False)
    fig.canvas.draw()
    dashed = [l for l in ax.lines if l.get_linestyle() == "--"]
    plt.close(fig)
    ok = len(dashed) == 0
    report(18, "water_stability=False removes dashed lines",
           ok, f"still found {len(dashed)} dashed lines")
    assert ok
