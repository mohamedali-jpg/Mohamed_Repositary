# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository status

This repository has no application source code, build system, or test suite. It currently holds Claude Code configuration only.

## Structure

- `.claude/agents/` — custom Claude Code subagent definitions.
  - `docs-writer` — generates/updates documentation from the current state of the codebase.
  - Thesis review pipeline (run in order):
    1. `thesis-analyzer` — reviews thesis/dissertation writing and produces a findings report (argumentation, structure, clarity, citations).
    2. `thesis-analysis-fixer` — verifies that report against the source text, fixing/removing/merging inaccurate findings.
    3. `thesis-edit-recommender` — turns the verified findings into concrete "change X to Y" edit recommendations.

When application code is added to this repository, update this file with:
- Build, lint, and test commands (including how to run a single test)
- The high-level architecture and structure of the codebase
