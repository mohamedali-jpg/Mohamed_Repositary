# Thesis review pipeline: analyzer -> fixer -> recommender

Three small, composable scripts for reviewing a `.docx` document (built
against a Master's thesis, but not thesis-specific in its detection logic):

1. **`analyzer.py`** reads the document and reports findings: near-duplicate
   paragraphs, broken heading numbering, in-text citations that don't match
   the reference list, inconsistent population/sample figures, and any
   corrections supplied via a JSON config. Each finding is tagged
   `auto_fixable: true` (safe to apply mechanically) or `false` (needs a
   human decision).
2. **`fixer.py`** applies every `auto_fixable` finding to a copy of the
   document: deletes duplicate paragraphs, and rewrites short spans for
   spelling/grammar/renumbering fixes.
3. **`recommender.py`** turns everything that was *not* auto-fixed into a
   Markdown checklist for the author, grouped by issue type.

## Usage

```bash
pip install -r requirements.txt

python3 analyzer.py mythesis.docx --corrections corrections.json -o findings.json
python3 fixer.py mythesis.docx findings.json --corrections corrections.json -o mythesis.revised.docx
python3 recommender.py findings.json -o recommendations.md
```

`corrections.json` is a list of specific, pre-confirmed text fixes:

```json
[
  {"find": "teh", "replace": "the", "reason": "typo"},
  {"find": "Old Heading", "replace": "1.2 Old Heading", "reason": "missing section number", "match": "exact"}
]
```

`"match": "exact"` requires the *entire* paragraph text to equal `find`
(used for headings, where the same word can legitimately appear as a
substring elsewhere in the document). Omit it for an ordinary substring
replacement.

The `corrections.json` checked into this directory is specific to
`MAM_THESIS_3.docx` -- delete or replace it when running the pipeline
against a different document.
