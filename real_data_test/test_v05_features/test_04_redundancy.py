"""Test 4: Anti-redundancy helpers — ``check_redundancy`` / ``print_redundancy_report``.

Scenarios:

  * Clean figure (3 panels, 3 distinct questions, all 3 info levels): no
    issues should be reported.
  * Same-question redundancy (two panels answering "what is the
    composition?"): WARN with both ids.
  * Same-data-slice redundancy (stacked_bar + pie of 'composition'): a
    WARN AND the encoding-rule trap (pie + stacked).
  * Two ranked-bar panels: WARN.
  * Missing info-level (only overview panels): an INFO suggesting the
    missing levels.
  * Edge cases: empty list, single panel, panel without 'question',
    malformed dict (missing 'id' on a complaint path), case/whitespace
    insensitivity for question matching.
  * ``print_redundancy_report`` prints something — capture stdout and
    confirm it's non-empty / non-spammy on a clean plan.
"""

from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

import huitu

OUT = Path(__file__).resolve().parent / "output"
OUT.mkdir(exist_ok=True)


def _severities(issues) -> list[str]:
    return [i.severity for i in issues]


def _ids_per_issue(issues) -> list[tuple[str, ...]]:
    return [i.panels for i in issues]


def main() -> int:
    failures: list[str] = []
    log = OUT / "redundancy_log.txt"
    log_lines: list[str] = []

    def _log(s: str) -> None:
        print(s)
        log_lines.append(s)

    # 1. Clean plan: 3 panels, 3 distinct questions, 3 info levels.
    clean = [
        {"id": "a", "question": "What is the composition?",
         "encoding": "stacked_bar", "data": "composition", "level": "overview"},
        {"id": "b", "question": "Which features deviate from the mean?",
         "encoding": "z_score_heatmap", "data": "z_score",
         "level": "deviation"},
        {"id": "c", "question": "How does feature X co-vary with Y?",
         "encoding": "bubble_scatter", "data": "correlation",
         "level": "relationship"},
    ]
    issues = huitu.check_redundancy(clean)
    if issues:
        failures.append(
            f"clean plan reported {len(issues)} false positives: "
            + "; ".join(str(i) for i in issues)
        )
    else:
        _log("clean plan: 0 issues (good)")

    # 2. Same-question redundancy.
    same_q = [
        {"id": "a", "question": "What is the composition?",
         "encoding": "stacked_bar"},
        {"id": "b", "question": "what is the composition?",  # case differs
         "encoding": "single_bar"},
        {"id": "c", "question": "What is the composition?",
         "encoding": "donut"},
    ]
    issues = huitu.check_redundancy(same_q)
    sevs = _severities(issues)
    ids = _ids_per_issue(issues)
    same_q_warn = [i for i, s in zip(issues, sevs) if s == "warn" and
                   set(i.panels) == {"a", "b", "c"} and "same scientific question"
                   in i.message]
    if not same_q_warn:
        failures.append(
            "same-question redundancy not detected (expected warn over a/b/c)"
        )
    else:
        _log(f"same-question: warn raised: {same_q_warn[0]}")

    # 3. Same-data-slice + pie/stacked encoding trap.
    same_data = [
        {"id": "a", "question": "What is the composition by class?",
         "encoding": "stacked_bar", "data": "composition"},
        {"id": "b", "question": "How are class fractions distributed?",
         "encoding": "pie", "data": "composition"},
    ]
    issues = huitu.check_redundancy(same_data)
    if not any("data slice" in i.message for i in issues):
        failures.append("same-data-slice redundancy not detected")
    if not any("pie + stacked bar" in i.message for i in issues):
        failures.append("pie + stacked-bar trap not detected")
    if issues:
        _log(f"same-data-slice: {len(issues)} issues raised")
        for i in issues:
            _log(f"  {i}")

    # 4. Two ranked-bar panels.
    ranked_pair = [
        {"id": "a", "question": "Top genes by effect size?",
         "encoding": "ranked_bar"},
        {"id": "b", "question": "Top pathways by enrichment?",
         "encoding": "ranking_bar"},
    ]
    issues = huitu.check_redundancy(ranked_pair)
    if not any("ranked-bar" in i.message and i.severity == "warn"
               for i in issues):
        failures.append("two ranked-bar panels not flagged as warn")
    else:
        _log("ranked-bar pair: warn raised")

    # 5. Missing info-level (only overviews ⇒ deviation+relationship missing).
    only_overviews = [
        {"id": "a", "question": "Composition v1?", "encoding": "stacked_bar"},
        {"id": "b", "question": "Composition v2?", "encoding": "stacked_bar"},
        {"id": "c", "question": "Composition v3?", "encoding": "single_bar"},
    ]
    issues = huitu.check_redundancy(only_overviews)
    info_missing_levels = [
        i for i in issues
        if i.severity == "info" and "missing the information level" in i.message
    ]
    if not info_missing_levels:
        failures.append(
            "only-overviews plan did not raise INFO about missing info-levels"
        )
    else:
        _log(f"only-overviews: info raised: {info_missing_levels[0]}")
        msg = info_missing_levels[0].message
        if "deviation" not in msg or "relationship" not in msg:
            failures.append(
                f"missing-levels message lacks deviation/relationship: {msg!r}"
            )

    # 6. Edge: empty list — should be empty issues, not crash.
    if huitu.check_redundancy([]) != []:
        failures.append("empty list returned non-empty issues")

    # 7. Edge: single panel — at most 1 issue (missing question if any).
    one = huitu.check_redundancy([
        {"id": "a", "question": "Composition?", "encoding": "stacked_bar"},
    ])
    if len(one) > 0:
        failures.append(f"single clean panel produced {len(one)} issues")

    # 8. Edge: panel without 'question' raises an INFO complaint.
    miss_q = huitu.check_redundancy([
        {"id": "a", "encoding": "stacked_bar"},
    ])
    if not any(i.severity == "info" and "missing a 'question'" in i.message
               for i in miss_q):
        failures.append("missing-question panel did NOT yield INFO")
    else:
        _log(f"missing-question: info raised: {miss_q[0]}")

    # 9. Edge: malformed dict — no 'id' at all. The current implementation
    # uses p.get('id', '?') in the missing-question branch but p['id']
    # everywhere else, so a malformed dict that DOES have a question crashes.
    # This is the kind of rough edge the test must surface.
    malformed_with_q = [
        {"question": "What is the composition?", "encoding": "stacked_bar"},
    ]
    try:
        huitu.check_redundancy(malformed_with_q)
        _log("malformed (no 'id') with question: did NOT raise (good)")
    except KeyError as exc:
        # Treat as an issue — surface to reviewer.
        failures.append(
            f"check_redundancy raises KeyError on dict missing 'id': {exc}. "
            f"Should validate inputs gracefully (review.py:106 uses p['id'])."
        )
    except Exception as exc:  # noqa: BLE001
        failures.append(
            f"check_redundancy on malformed dict raised {type(exc).__name__}: {exc}"
        )

    # 10. print_redundancy_report — capture stdout on clean and noisy plans.
    buf_clean = io.StringIO()
    with redirect_stdout(buf_clean):
        huitu.print_redundancy_report(clean)
    out = buf_clean.getvalue()
    if "[OK]" not in out or "no redundancy issues" not in out:
        failures.append(
            f"print_redundancy_report on clean plan didn't say [OK]: {out!r}"
        )
    log_lines.append("=== print_redundancy_report (clean) ===")
    log_lines.append(out)

    buf_dirty = io.StringIO()
    with redirect_stdout(buf_dirty):
        huitu.print_redundancy_report(same_q + same_data + ranked_pair)
    out = buf_dirty.getvalue()
    if "[REVIEW]" not in out:
        failures.append(
            f"print_redundancy_report on dirty plan didn't say [REVIEW]: {out!r}"
        )
    log_lines.append("=== print_redundancy_report (dirty) ===")
    log_lines.append(out)

    # 11. Bug-hunting: false-positive whitespace insensitivity. The two
    # 'questions' below differ only by whitespace; they should collapse
    # into one bucket.
    ws = [
        {"id": "a", "question": "  What  is the   composition?",
         "encoding": "stacked_bar"},
        {"id": "b", "question": "What is the composition?",
         "encoding": "donut"},
    ]
    issues = huitu.check_redundancy(ws)
    if not any(i.severity == "warn" and set(i.panels) == {"a", "b"}
               for i in issues):
        failures.append(
            "whitespace-insensitive question match not working — a/b "
            "differ only by whitespace and should collide"
        )

    # Persist log for downstream review.
    log.write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    if failures:
        print("\nFAILED:")
        for f in failures:
            print(" -", f)
        return 1
    print("\nALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
