#!/usr/bin/env python3
"""Stage 3 of the analyzer -> fixer -> recommender pipeline.

Turns findings.json's `needs_review` items -- the ones fixer.py deliberately
left alone because resolving them takes a judgement call -- into a Markdown
report the author can work through, grouped by finding type. Also lists what
fixer.py already changed, so the report is a complete record of the run.

Usage:
    python3 recommender.py findings.json -o recommendations.md
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

TYPE_LABELS = {
    "duplicate_section_number": "Section numbering",
    "missing_reference": "Citations missing from the reference list",
    "citation_year_mismatch": "Citation / reference-list year mismatches",
    "population_size_inconsistency": "Inconsistent population or sample figures",
}


def build_report(findings: list[dict]) -> str:
    auto = [f for f in findings if f["auto_fixable"]]
    review = [f for f in findings if not f["auto_fixable"]]

    by_type = defaultdict(list)
    for f in review:
        by_type[f["type"]].append(f)

    lines = ["# Thesis Review Recommendations", ""]

    lines.append("## Already fixed automatically")
    if auto:
        for f in auto:
            lines.append(f"- {f['description']}")
    else:
        lines.append("- (none)")
    lines.append("")

    lines.append("## Needs your review")
    if not review:
        lines.append("- No open issues detected by the automated checks.")
    for ftype, items in by_type.items():
        lines.append(f"\n### {TYPE_LABELS.get(ftype, ftype)}")
        for f in items:
            lines.append(f"- {f['description']}")

    lines.append("\n## Additional editorial notes")
    lines.append(
        "These fall outside what the analyzer checks mechanically, but came up "
        "while reviewing the document and are worth the author's attention:"
    )
    lines += [
        "- Several Empirical Review paragraphs (e.g. the Gichuki et al. 2024, "
        "Sood & Tarah 2024, Zahari et al. 2024, Abdi et al. 2024, Sheikh Ali 2025, "
        "and Kulmie et al. 2025 discussions) open with a full reference-list-style "
        "citation (all authors spelled out) instead of an APA in-text citation "
        "(Author et al., Year). Recommend converting these to standard in-text form.",
        "- Two in-text citations use a 2026 publication year (Andarini, 2026; "
        "Transparency International, 2026), which is unusual for sources otherwise "
        "cited from 2019-2024 in the reference list. Confirm these dates are correct.",
        "- The document is explicitly framed as \"This Proposal\" (title page) but is "
        "titled and submitted as a completed \"THESIS\", and only contains Chapters "
        "1-3 (no Results, Discussion, or Conclusion chapters). Confirm this matches "
        "the intended submission stage.",
        "- In-text abbreviation \"FGS\" is used once (Section 1.2) alongside the fully "
        "spelled-out \"Federal Government of Somalia\" used elsewhere; consider "
        "defining the abbreviation on first use or using one form consistently.",
    ]

    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("findings_json")
    ap.add_argument("-o", "--output", default="recommendations.md")
    args = ap.parse_args()

    findings = json.loads(Path(args.findings_json).read_text())["findings"]
    report = build_report(findings)
    Path(args.output).write_text(report)
    print(f"Wrote {args.output}.")


if __name__ == "__main__":
    main()
