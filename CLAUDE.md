# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository status

This repository holds standalone tools rather than a single application; there is
no shared build system across the repo. Each tool directory under `tools/`
documents its own setup and usage in its own README.

## tools/thesis_review

A three-stage `analyzer -> fixer -> recommender` pipeline for reviewing a `.docx`
document (built against a Master's thesis, but not thesis-specific in its
detection logic):

- `analyzer.py` finds duplicate paragraphs, broken heading numbering, in-text
  citations that don't resolve against the reference list, inconsistent
  numeric figures (e.g. a population size stated two different ways), and any
  corrections supplied via a JSON config. Writes `findings.json`.
- `fixer.py` applies every `auto_fixable` finding to a copy of the document.
- `recommender.py` turns everything left (`needs_review`) into a Markdown
  checklist for the author.

Setup: `pip install -r tools/thesis_review/requirements.txt` (needs
`python-docx`). Full usage and the `corrections.json` format are documented in
`tools/thesis_review/README.md`.

There is no automated test suite for this tool yet; validate changes by running
the three scripts against a sample `.docx` and inspecting `findings.json` /
the revised document.
