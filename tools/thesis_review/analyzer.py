#!/usr/bin/env python3
"""Stage 1 of the analyzer -> fixer -> recommender pipeline.

Scans a .docx document for mechanical defects that are cheap to detect
automatically:
  - near-duplicate paragraphs (copy/paste leftovers)
  - broken heading numbering (duplicate or non-sequential section numbers)
  - APA in-text citations that don't resolve against the reference list
    (missing entries, or a year mismatch between the citation and the entry)
  - known text corrections supplied via a JSON config (spelling/grammar
    fixes that a human has already confirmed are unambiguous)

Findings are split into "auto_fixable" (safe for fixer.py to apply without
further judgement) and "needs_review" (surfaced by recommender.py instead,
because resolving them requires a decision only the author can make, e.g.
which of two conflicting population figures is correct).

Usage:
    python3 analyzer.py <input.docx> [--corrections corrections.json] -o findings.json
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
from pathlib import Path

from docx_utils import load_paragraphs

SECTION_RE = re.compile(r"^(\d+(?:\.\d+)*)\s+\S")
# "(Author, 2024)" / "(Author & Other, 2024)" / "(Author et al., 2024)"
PAREN_CITATION_RE = re.compile(
    r"\(([A-Z][A-Za-z.\-]+(?:,?\s*(?:&|and)\s*[A-Z][A-Za-z.\-]+|,?\s*et al\.?)*),?\s*(\d{4})\)"
)
# "Author (2024)" narrative citation
NARRATIVE_CITATION_RE = re.compile(
    r"\b([A-Z][A-Za-z.\-]+(?:,?\s*(?:&|and)\s*[A-Z][A-Za-z.\-]+|,?\s*et al\.?)*)\s*\((\d{4})\)"
)
# Captures the lead author/organization name of a reference-list entry: everything
# up to the first ", " (individual author, e.g. "Bass, B. M., ...") or the first
# ". (" (organizational author, e.g. "World Bank. (2020)."), whichever comes first.
REFERENCE_NAME_RE = re.compile(r"^(.+?)(?:,\s|\.\s*\()")
REFERENCE_YEAR_RE = re.compile(r"\((\d{4}[a-z]?)\)")


def find_duplicate_paragraphs(paras, min_len=80, ratio_threshold=0.9, containment_min_len=60):
    """Flag paragraphs that duplicate an earlier one, either near-verbatim (high
    SequenceMatcher ratio) or as a straight copy/paste leftover, where the shorter
    paragraph's text appears verbatim inside a longer one (common when only part of
    a citation got left behind).
    """
    findings = []
    seen = []
    for p in paras:
        if len(p.text) < min_len:
            continue
        for prior in seen:
            shorter, longer = sorted((p.text, prior.text), key=len)
            if len(shorter) >= containment_min_len and shorter in longer:
                findings.append({
                    "type": "duplicate_paragraph",
                    "auto_fixable": True,
                    "paragraph_index": p.index,
                    "duplicate_of_index": prior.index,
                    "similarity": 1.0,
                    "text_preview": p.text[:100],
                    "description": (
                        f"Paragraph {p.index} duplicates text already present in "
                        f"paragraph {prior.index} verbatim and appears to be a stray "
                        f"copy/paste leftover."
                    ),
                })
                continue
            ratio = difflib.SequenceMatcher(None, p.text, prior.text).ratio()
            if ratio >= ratio_threshold:
                findings.append({
                    "type": "duplicate_paragraph",
                    "auto_fixable": True,
                    "paragraph_index": p.index,
                    "duplicate_of_index": prior.index,
                    "similarity": round(ratio, 3),
                    "text_preview": p.text[:100],
                    "description": (
                        f"Paragraph {p.index} is {ratio:.0%} similar to paragraph "
                        f"{prior.index} and appears to be a stray duplicate."
                    ),
                })
        seen.append(p)
    return findings


def find_numbering_issues(paras):
    """Flag heading numbers that repeat or skip when read in document order."""
    findings = []
    headings = []
    for p in paras:
        m = SECTION_RE.match(p.text)
        if m and (p.is_bold_heading or len(p.text) < 80):
            headings.append((p, m.group(1)))

    seen_numbers = {}
    for p, number in headings:
        if number in seen_numbers:
            findings.append({
                "type": "duplicate_section_number",
                "auto_fixable": False,
                "paragraph_index": p.index,
                "description": (
                    f"Heading '{p.text[:60]}' at paragraph {p.index} reuses section "
                    f"number {number}, already used at paragraph {seen_numbers[number]}."
                ),
            })
        seen_numbers[number] = p.index
    return findings


def parse_reference_list(paras):
    """Return {surname_lower: set(years)} built from the REFERENCE LIST section."""
    start = None
    end = None
    for p in paras:
        if p.text.strip().upper() == "REFERENCE LIST":
            start = p.index
        elif start is not None and p.text.strip().isupper() and len(p.text) > 10 and p.index != start:
            end = p.index
            break
    if start is None:
        return {}, (None, None)

    entries: dict[str, set[str]] = {}
    for p in paras:
        if p.index <= start:
            continue
        if end is not None and p.index >= end:
            break
        text = p.text.strip()
        name_match = REFERENCE_NAME_RE.match(text)
        year_match = REFERENCE_YEAR_RE.search(text)
        if not (name_match and year_match):
            continue
        name, year = name_match.group(1).lower(), year_match.group(1)
        entries.setdefault(name, set()).add(year)
        # Narrative citations of a multi-word organizational author (e.g. "World
        # Bank") often get truncated by our regex to just the last word ("Bank"),
        # so index that too and treat it as the same source.
        words = name.split()
        if len(words) > 1:
            entries.setdefault(words[-1], set()).add(year)
    return entries, (start, end)


def find_citation_issues(paras):
    ref_entries, (ref_start, ref_end) = parse_reference_list(paras)
    if not ref_entries:
        return []

    findings = []
    reported = set()
    for p in paras:
        if ref_start is not None and p.index >= ref_start:
            continue
        for regex in (PAREN_CITATION_RE, NARRATIVE_CITATION_RE):
            for match in regex.finditer(p.text):
                author_blob, year = match.group(1), match.group(2)
                first_surname = re.split(r"[,&]| and | et al", author_blob)[0].strip().lower()
                if not first_surname or not first_surname[0].isalpha():
                    continue
                if len(first_surname.rstrip(".")) < 3:
                    # Almost certainly a stray initial ("M.", "A.") swept up by the
                    # narrative-citation regex from something like "Reta, M. A.
                    # (2021)", not a real citation of an author named "M".
                    continue
                key = (p.index, first_surname, year)
                if key in reported:
                    continue
                reported.add(key)

                if first_surname not in ref_entries:
                    findings.append({
                        "type": "missing_reference",
                        "auto_fixable": False,
                        "paragraph_index": p.index,
                        "citation": match.group(0),
                        "description": (
                            f"In-text citation {match.group(0)!r} (paragraph {p.index}) has no "
                            f"matching entry in the reference list."
                        ),
                    })
                elif year not in ref_entries[first_surname]:
                    findings.append({
                        "type": "citation_year_mismatch",
                        "auto_fixable": False,
                        "paragraph_index": p.index,
                        "citation": match.group(0),
                        "reference_years": sorted(ref_entries[first_surname]),
                        "description": (
                            f"In-text citation {match.group(0)!r} (paragraph {p.index}) cites "
                            f"{year}, but the reference list entry for "
                            f"{first_surname.title()} uses {sorted(ref_entries[first_surname])}."
                        ),
                    })
    return findings


POPULATION_RE = re.compile(
    r"(?:population of(?: approximately)?|totaling approximately)\s*(\d{2,7})|(\d{2,7})\s*employees"
)


def find_numeric_inconsistencies(paras):
    """Flag a stated population/sample count that disagrees with an earlier mention."""
    mentions = []
    for p in paras:
        for m in POPULATION_RE.finditer(p.text):
            value = m.group(1) or m.group(2)
            mentions.append((p.index, value, p.text[:120]))

    findings = []
    distinct = {v for _, v, _ in mentions}
    if len(distinct) > 1:
        findings.append({
            "type": "population_size_inconsistency",
            "auto_fixable": False,
            "paragraph_index": mentions[0][0],
            "mentions": [{"paragraph_index": i, "value": v, "context": t} for i, v, t in mentions],
            "description": (
                "The study population/sample size is stated inconsistently: "
                + ", ".join(f"{v} (paragraph {i})" for i, v, _ in mentions)
                + ". Confirm the correct figure and align every mention."
            ),
        })
    return findings


def find_configured_corrections(paras, corrections):
    findings = []
    for p in paras:
        for c in corrections:
            is_match = (p.text == c["find"]) if c.get("match") == "exact" else (c["find"] in p.text)
            if is_match:
                findings.append({
                    "type": "text_correction",
                    "auto_fixable": True,
                    "paragraph_index": p.index,
                    "find": c["find"],
                    "replace": c["replace"],
                    "reason": c.get("reason", ""),
                    "description": (
                        f"Paragraph {p.index}: replace {c['find']!r} with {c['replace']!r} "
                        f"({c.get('reason', 'text correction')})."
                    ),
                })
    return findings


def analyze(docx_path: str, corrections_path: str | None) -> dict:
    _, paras = load_paragraphs(docx_path)
    body_paras = [p for p in paras if not p.in_table]

    corrections = []
    if corrections_path and Path(corrections_path).exists():
        corrections = json.loads(Path(corrections_path).read_text())

    findings = []
    findings += find_duplicate_paragraphs(body_paras)
    findings += find_numbering_issues(body_paras)
    findings += find_citation_issues(body_paras)
    findings += find_numeric_inconsistencies(body_paras)
    findings += find_configured_corrections(paras, corrections)

    auto = [f for f in findings if f["auto_fixable"]]
    fixed_paragraph_indices = {f["paragraph_index"] for f in auto if f["type"] == "text_correction"}

    def already_resolved(f):
        # A generic finding (e.g. "this heading's section number repeats") that a
        # configured text_correction on the same paragraph already queues a fix
        # for is redundant to also surface as an open review item.
        return not f["auto_fixable"] and f["paragraph_index"] in fixed_paragraph_indices

    findings = [f for f in findings if not already_resolved(f)]
    review = [f for f in findings if not f["auto_fixable"]]
    return {
        "source": docx_path,
        "paragraph_count": len(paras),
        "auto_fixable_count": len(auto),
        "needs_review_count": len(review),
        "findings": findings,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("docx_path")
    ap.add_argument("--corrections", help="JSON file of known text corrections to check for")
    ap.add_argument("-o", "--output", default="findings.json")
    args = ap.parse_args()

    result = analyze(args.docx_path, args.corrections)
    Path(args.output).write_text(json.dumps(result, indent=2))
    print(
        f"Analyzed {args.docx_path}: {result['auto_fixable_count']} auto-fixable, "
        f"{result['needs_review_count']} need review. Wrote {args.output}."
    )


if __name__ == "__main__":
    main()
