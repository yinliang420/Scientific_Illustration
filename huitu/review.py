"""Pre-submission review helpers — anti-redundancy & reviewer-risk checklist.

Two utilities Nature-tier figures benefit from before submitting:

1. :func:`check_redundancy` — given a list of panel descriptors, surfaces
   redundant panels (two panels answering the same scientific question or
   showing the same data slice in a different visual form), and warns when
   the figure is missing one of the three information levels
   *Overview → Deviation → Relationship*.

2. :func:`reviewer_checklist` — given a metadata dict, prints / returns the
   pre-submission checklist that a skeptical reviewer or journal editor will
   apply: ``n`` definition, replicates, center / spread / test / correction,
   source-data file, scale bar, image-integrity log.

Neither helper opens a graphics device or modifies rcParams — both are safe
to call from a pytest fixture, a CI gate, or an interactive notebook cell.

Reference: ``Yuan1z0825/nature-skills`` / ``nature-figure`` →
``references/qa-contract.md`` and ``references/design-theory.md`` § 11.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


# ── Anti-redundancy ─────────────────────────────────────────────────────────

# The Nature-figure three-level information hierarchy.
#   overview     — "What is the landscape?"      e.g. stacked bar / composition
#   deviation    — "What is distinctive?"        e.g. z-score heatmap
#   relationship — "How do variables co-vary?"   e.g. bubble scatter
_INFO_LEVELS = ("overview", "deviation", "relationship")


@dataclass(frozen=True)
class PanelIssue:
    """One redundancy / hierarchy issue raised by :func:`check_redundancy`."""

    severity: str          # "warn" | "info"
    panels:   tuple[str, ...]   # affected panel ids, e.g. ("a", "b")
    message:  str          # one-sentence diagnosis

    def __str__(self) -> str:
        sev = self.severity.upper()
        pid = "/".join(self.panels) if self.panels else "—"
        return f"[{sev}] {pid}: {self.message}"


def check_redundancy(panels: Sequence[dict]) -> list[PanelIssue]:
    """Audit a multi-panel figure plan for redundancy.

    Each entry in ``panels`` is a dict describing one panel:

    ============= ==============================================================
    Key           Meaning
    ============= ==============================================================
    ``id``        Panel letter (e.g. ``"a"``).  Required.
    ``question``  One-sentence question this panel answers. Required.
    ``encoding``  Visual grammar: ``"stacked_bar"``, ``"z_score_heatmap"``,
                  ``"bubble_scatter"``, ``"line"``, ``"forest"``, …
                  Required.
    ``data``      Optional short tag for the data slice, e.g. ``"composition"``,
                  ``"z_score"``, ``"correlation"``. Used for *same data, two
                  encodings* detection.
    ``level``     Optional — one of ``"overview"``, ``"deviation"``,
                  ``"relationship"``. Auto-inferred from ``encoding`` when
                  omitted.
    ============= ==============================================================

    Returns
    -------
    issues : list[PanelIssue]
        Empty list ⇔ no problems detected. Each issue carries a severity
        (``"warn"`` blocks submission; ``"info"`` is a softer suggestion),
        the panel ids it references, and a one-sentence message.

    Examples
    --------
    >>> issues = check_redundancy([
    ...     {"id": "a", "question": "What is the composition?",
    ...      "encoding": "stacked_bar",  "level": "overview"},
    ...     {"id": "b", "question": "What is the composition?",
    ...      "encoding": "pie",          "level": "overview"},
    ... ])
    >>> [str(i) for i in issues]   # doctest: +ELLIPSIS
    ['[WARN] a/b: ... same scientific question ...']
    """
    issues: list[PanelIssue] = []
    if not panels:
        return issues

    # 1. Same scientific question (case- and whitespace-insensitive).
    by_question: dict[str, list[str]] = {}
    for p in panels:
        q = " ".join((p.get("question") or "").lower().split())
        if not q:
            issues.append(PanelIssue(
                "info", (p.get("id", "?"),),
                "panel is missing a 'question' — every Nature-style panel "
                "should answer one well-formed scientific question."
            ))
            continue
        by_question.setdefault(q, []).append(p.get("id", "?"))
    for q, ids in by_question.items():
        if len(ids) > 1:
            issues.append(PanelIssue(
                "warn", tuple(ids),
                "panels answer the same scientific question — keep only the "
                "clearest encoding, or split the question into two non-"
                "overlapping subquestions."
            ))

    # 2. Same data slice in two visual forms (e.g. stacked bar + pie of the
    #    same composition). Driven by the optional ``data`` tag.
    by_data: dict[str, list[tuple[str, str]]] = {}
    for p in panels:
        d = (p.get("data") or "").lower().strip()
        if not d:
            continue
        by_data.setdefault(d, []).append((p.get("id", "?"), p.get("encoding", "?")))
    for d, hits in by_data.items():
        if len(hits) > 1:
            ids = tuple(h[0] for h in hits)
            encs = ", ".join(f"{h[0]}={h[1]}" for h in hits)
            issues.append(PanelIssue(
                "warn", ids,
                f"panels share the same data slice '{d}' ({encs}). Replace "
                f"one with a deviation (z-score) or relationship (scatter / "
                f"bubble) view of the same numbers."
            ))

    # 3. Information hierarchy: overview → deviation → relationship.
    levels_present: set[str] = set()
    for p in panels:
        lvl = (p.get("level") or _infer_level(p.get("encoding", ""))).lower()
        if lvl in _INFO_LEVELS:
            levels_present.add(lvl)
    if len(panels) >= 3:
        missing = [lv for lv in _INFO_LEVELS if lv not in levels_present]
        if missing:
            issues.append(PanelIssue(
                "info", (),
                f"figure is missing the information level(s) "
                f"{', '.join(missing)} — Nature multi-panel figures usually "
                f"climb Overview → Deviation → Relationship so each panel "
                f"adds a dimension absent from the others."
            ))

    # 4. Common redundancy traps (heuristic).
    encodings = {p.get("id", "?"): (p.get("encoding") or "").lower() for p in panels}
    ranked = [pid for pid, e in encodings.items()
              if "ranked" in e or "ranking" in e]
    if len(ranked) >= 2:
        issues.append(PanelIssue(
            "warn", tuple(ranked),
            "two ranked-bar panels — replace one with a scatter/bubble plot "
            "showing co-variation between the two metrics."
        ))
    pies = [pid for pid, e in encodings.items() if "pie" in e]
    stacks = [pid for pid, e in encodings.items() if "stacked" in e]
    if pies and stacks:
        issues.append(PanelIssue(
            "warn", tuple(pies + stacks),
            "pie + stacked bar typically encode the same composition — drop "
            "the pie or replace it with a relationship view."
        ))

    return issues


def _infer_level(encoding: str) -> str:
    """Best-effort mapping of an encoding string to an info-hierarchy level."""
    e = (encoding or "").lower()
    if any(k in e for k in ("z_score", "z-score", "diverging", "deviation",
                            "rdbu", "log2fc", "volcano")):
        return "deviation"
    if any(k in e for k in ("scatter", "bubble", "relationship",
                            "correlation", "pair")):
        return "relationship"
    if any(k in e for k in ("stacked", "composition", "overview", "pie",
                            "single_bar", "stacked_bar", "stacked_area")):
        return "overview"
    return ""


def print_redundancy_report(panels: Sequence[dict]) -> None:
    """Print :func:`check_redundancy` results in a human-readable form."""
    issues = check_redundancy(panels)
    if not issues:
        print("[OK] no redundancy issues detected ({} panels).".format(
            len(panels)))
        return
    n_warn = sum(1 for i in issues if i.severity == "warn")
    n_info = sum(1 for i in issues if i.severity == "info")
    print(f"[REVIEW] {n_warn} warn / {n_info} info  ({len(panels)} panels)")
    for issue in issues:
        print("  " + str(issue))


# ── Reviewer-risk checklist ─────────────────────────────────────────────────

# Each row: (key, label, severity if missing, notes/hint shown when missing).
# severity ∈ {"required", "recommended"}.
_QUANT_FIELDS: list[tuple[str, str, str, str]] = [
    ("n",                    "n definition",
     "required",
     "Sample size, e.g. 'n=12 mice / group, 3 biological replicates'."),
    ("biological_replicates","biological replicates",
     "required",
     "Independent biological samples — not technical re-runs."),
    ("technical_replicates", "technical replicates",
     "recommended",
     "Within-sample re-measurements, e.g. 'qPCR run in triplicate'."),
    ("center",               "center statistic",
     "required",
     "Mean / median / geometric mean — must match the error-bar definition."),
    ("spread",               "spread / interval",
     "required",
     "SD / SEM / 95 % CI / IQR — be explicit; SEM and SD are not "
     "interchangeable."),
    ("test",                 "statistical test",
     "required",
     "e.g. 'two-sided Wilcoxon rank-sum'. Name and tail must be stated."),
    ("correction",           "multiple-comparison correction",
     "recommended",
     "Bonferroni / Holm / BH-FDR. Required for any panel with ≥3 tests."),
    ("p_value_format",       "p-value display",
     "recommended",
     "'exact', 'p<0.05', '*/**/***', or 'n.s.'. Pick one and stay consistent."),
    ("source_data",          "source-data file",
     "required",
     "Path to a clean CSV/TSV/XLSX that lets a reader regenerate the panel."),
]

_IMAGE_FIELDS: list[tuple[str, str, str, str]] = [
    ("scale_bar",            "scale bar",
     "required",
     "Calibrated bar with units, not a magnification factor (×40)."),
    ("raw_file",             "raw image file",
     "required",
     "Path / DOI of the unaltered raw acquisition."),
    ("crop",                 "crop record",
     "recommended",
     "Pixel ROI used. Avoid local selective crops without disclosure."),
    ("brightness_contrast",  "brightness/contrast/gamma",
     "recommended",
     "State global adjustments; flag any non-linear (γ ≠ 1) tone curves."),
    ("pseudo_color",         "pseudo-color mapping",
     "recommended",
     "Channel → display color mapping, e.g. 'GFP → cyan, mCherry → magenta'."),
    ("stitching",            "stitching record",
     "recommended",
     "If panels are stitched, name the algorithm and seam handling."),
    ("reuse",                "reuse declaration",
     "recommended",
     "Note when an image already appeared in another figure or paper."),
]

_ML_FIELDS: list[tuple[str, str, str, str]] = [
    ("split",                "train/val/test split",
     "required",
     "Sizes, leakage handling, patient/subject overlap policy."),
    ("seeds",                "seeds or folds",
     "required",
     "Number of seeds (e.g. 5 random restarts) or CV folds."),
    ("metric",               "metric definition",
     "required",
     "Exact metric formula — accuracy on what threshold, AUC of which curve."),
    ("ci",                   "confidence interval / variability",
     "recommended",
     "Bootstrap CI, ±SD across seeds, or per-fold spread."),
    ("baseline",             "baseline definition",
     "required",
     "Which exact comparison method, with version / hyper-parameters."),
]

_FIGURE_FIELDS: list[tuple[str, str, str, str]] = [
    ("core_conclusion",      "one-sentence core conclusion",
     "required",
     "A single declarative sentence the figure must defend."),
    ("archetype",            "figure archetype",
     "recommended",
     "quantitative-grid / schematic-led / image-plate / asymmetric-hero."),
    ("final_size",           "final printed size",
     "required",
     "Single column ≈ 89 mm or double ≈ 183 mm. Should match journal limit."),
    ("editable_text",        "editable SVG/PDF text",
     "recommended",
     "Verify text remains <text> nodes (not paths) at final export. "
     "huitu enforces svg.fonttype='none' + pdf.fonttype=42 by default."),
    ("color_grayscale_safe", "grayscale-print safe",
     "recommended",
     "Confirm the figure is interpretable when colour information is lost."),
]


def reviewer_checklist(
    *,
    figure: dict | None = None,
    quantitative: dict | None = None,
    image: dict | None = None,
    machine_learning: dict | None = None,
    print_report: bool = True,
) -> dict:
    """Pre-submission reviewer-risk checklist.

    Section semantics:

    * ``figure`` and ``quantitative`` are **core** — they always run.
      Pass ``None`` (the default) and the function still flags every
      required field as missing, so a bare ``reviewer_checklist()`` call
      surfaces the minimum scaffolding every figure must carry
      (core conclusion, final size, ``n``, center / spread / test, source
      data).
    * ``image`` and ``machine_learning`` are **modality-specific** opt-ins.
      Omit the parameter (leave as ``None``) and the section is skipped
      silently. Pass any dict — even ``{}`` — and the section runs and
      surfaces missing required fields. Use this when the figure has
      microscopy / blot panels or ML metrics; otherwise leave them off.

    Parameters
    ----------
    figure
        Top-level figure metadata. Recognised keys:
        ``core_conclusion``, ``archetype``, ``final_size``, ``editable_text``,
        ``color_grayscale_safe``.
    quantitative
        Per-panel statistics metadata. Recognised keys: ``n``,
        ``biological_replicates``, ``technical_replicates``, ``center``,
        ``spread``, ``test``, ``correction``, ``p_value_format``,
        ``source_data``.
    image
        Image-integrity metadata. Recognised keys: ``scale_bar``,
        ``raw_file``, ``crop``, ``brightness_contrast``, ``pseudo_color``,
        ``stitching``, ``reuse``.
    machine_learning
        ML-specific metadata. Recognised keys: ``split``, ``seeds``,
        ``metric``, ``ci``, ``baseline``.
    print_report
        If ``True`` (default), prints a formatted ✓/✗/⚠ table to stdout.

    Returns
    -------
    report : dict
        ``{'sections': [...], 'n_required_missing': int,
        'n_recommended_missing': int, 'pass': bool}``. ``'pass'`` is ``True``
        when no *required* fields are missing. Each section entry is a list
        of ``(key, label, status)`` tuples where ``status`` ∈ ``{'ok',
        'missing_required', 'missing_recommended'}``.

    Examples
    --------
    >>> rep = reviewer_checklist(
    ...     figure={"core_conclusion": "Treatment X reduces tumor by 60 %"},
    ...     quantitative={"n": 12, "center": "median", "spread": "IQR",
    ...                   "test": "two-sided Wilcoxon", "source_data":
    ...                   "fig3.csv"},
    ...     print_report=False,
    ... )
    >>> rep["pass"]
    False
    >>> rep["n_required_missing"] >= 1
    True
    """
    report: dict = {"sections": [], "n_required_missing": 0,
                    "n_recommended_missing": 0}
    # Section policy:
    #   * Figure / Quantitative are core — coerce ``None`` → ``{}`` so they
    #     always run; missing required fields then surface as failures.
    #   * Image / ML are modality opt-ins — skip when ``None``; run when the
    #     user passes any dict (even ``{}``). That way passing
    #     ``image={}`` flags every required image field as missing, but
    #     omitting ``image=`` keeps the report quiet for figures with no
    #     image panels.
    sections = [
        ("Figure",       {} if figure       is None else figure,       _FIGURE_FIELDS, True),
        ("Quantitative", {} if quantitative is None else quantitative, _QUANT_FIELDS,  True),
        ("Image",        image,                                        _IMAGE_FIELDS,  False),
        ("ML / model",   machine_learning,                             _ML_FIELDS,     False),
    ]
    for sec_name, payload, fields, always_run in sections:
        if payload is None and not always_run:
            # User did not pass an opt-in section — skip it silently.
            continue
        payload = payload or {}
        rows = []
        for key, label, severity, hint in fields:
            value = payload.get(key)
            if value in (None, "", []):
                if severity == "required":
                    rows.append((key, label, "missing_required", hint))
                    report["n_required_missing"] += 1
                else:
                    rows.append((key, label, "missing_recommended", hint))
                    report["n_recommended_missing"] += 1
            else:
                rows.append((key, label, "ok", str(value)))
        report["sections"].append({"name": sec_name, "rows": rows})
    report["pass"] = (report["n_required_missing"] == 0)

    if print_report:
        _print_checklist(report)
    return report


def _print_checklist(report: dict) -> None:
    """Pretty-print a reviewer-risk report."""
    sym = {"ok": "[OK] ",
           "missing_required":   "[!!] ",
           "missing_recommended":"[??] "}
    header = ("PASS" if report["pass"] else "FAIL")
    print(f"reviewer-risk checklist: {header}  "
          f"(required missing: {report['n_required_missing']}, "
          f"recommended missing: {report['n_recommended_missing']})")
    for sec in report["sections"]:
        if not sec["rows"]:
            continue
        print(f"\n  {sec['name']}")
        for key, label, status, value_or_hint in sec["rows"]:
            line = sym[status] + label
            if status == "ok":
                # Truncate very long values so the table stays readable.
                shown = value_or_hint
                if len(shown) > 60:
                    shown = shown[:57] + "..."
                line += f": {shown}"
            else:
                line += f"  — {value_or_hint}"
            print("    " + line)
    print()


# ── Public re-exports ──────────────────────────────────────────────────────

__all__ = [
    "PanelIssue",
    "check_redundancy",
    "print_redundancy_report",
    "reviewer_checklist",
]
