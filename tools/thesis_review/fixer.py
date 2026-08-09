#!/usr/bin/env python3
"""Stage 2 of the analyzer -> fixer -> recommender pipeline.

Applies every `auto_fixable` finding from analyzer.py's findings.json to the
source .docx and writes a revised copy. Two kinds of fixes are applied:

  - duplicate_paragraph: deletes the later, redundant paragraph outright.
  - text_correction: rewrites a short, unambiguous span (spelling fix,
    heading renumber, grammar fix) as supplied by a corrections config.

Findings that are not auto_fixable (citation mismatches, numbering *design*
questions, anything needing a judgement call) are left untouched here --
recommender.py turns those into a report for the author instead.

Usage:
    python3 fixer.py <input.docx> findings.json -o revised.docx
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from docx_utils import load_paragraphs, delete_paragraph, replace_text_in_paragraph


def apply_fixes(docx_path: str, findings: list[dict], corrections: list[dict]) -> tuple[object, list[dict]]:
    document, paras = load_paragraphs(docx_path)
    by_index = {p.index: p for p in paras}
    corrections_by_find = {c["find"]: c for c in corrections}

    applied = []
    to_delete = []

    for f in findings:
        if not f.get("auto_fixable"):
            continue

        if f["type"] == "duplicate_paragraph":
            para = by_index.get(f["paragraph_index"])
            if para is not None:
                to_delete.append((f, para))

        elif f["type"] == "text_correction":
            para = by_index.get(f["paragraph_index"])
            if para is None:
                continue
            ok = replace_text_in_paragraph(para.paragraph, f["find"], f["replace"])
            if ok:
                applied.append(f)

    # Delete duplicate paragraphs last, and skip any paragraph a text_correction
    # already touched -- editing a paragraph object after it's removed from the
    # tree would raise.
    for f, para in to_delete:
        delete_paragraph(para.paragraph)
        applied.append(f)

    return document, applied


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("docx_path")
    ap.add_argument("findings_json")
    ap.add_argument("--corrections", help="JSON file of known text corrections (same one passed to analyzer.py)")
    ap.add_argument("-o", "--output", default="revised.docx")
    args = ap.parse_args()

    findings = json.loads(Path(args.findings_json).read_text())["findings"]
    corrections = []
    if args.corrections and Path(args.corrections).exists():
        corrections = json.loads(Path(args.corrections).read_text())

    document, applied = apply_fixes(args.docx_path, findings, corrections)
    document.save(args.output)

    print(f"Applied {len(applied)} fix(es). Wrote {args.output}.")
    for f in applied:
        print(f"  - [{f['type']}] {f['description']}")


if __name__ == "__main__":
    main()
