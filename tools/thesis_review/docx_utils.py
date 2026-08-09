"""Shared helpers for reading and editing .docx paragraphs with python-docx."""
from __future__ import annotations

from dataclasses import dataclass

import docx
from docx.text.paragraph import Paragraph


@dataclass
class Para:
    index: int
    text: str
    is_bold_heading: bool
    paragraph: Paragraph
    in_table: bool = False


def _iter_all_paragraphs(document: docx.Document):
    """Yield body paragraphs followed by every table cell's paragraphs.

    python-docx's `document.paragraphs` skips table contents entirely, but this
    thesis keeps its entire questionnaire in a table, so callers that only want
    body text should filter on `Para.in_table`.
    """
    for p in document.paragraphs:
        yield p, False
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    yield p, True


def load_paragraphs(path: str) -> tuple[docx.Document, list[Para]]:
    """Return the Document plus a flat list of non-empty paragraphs with metadata."""
    document = docx.Document(path)
    paras: list[Para] = []
    for i, (p, in_table) in enumerate(_iter_all_paragraphs(document)):
        text = p.text.strip()
        if not text:
            continue
        is_bold = bool(p.runs) and all(r.bold for r in p.runs if r.text.strip())
        paras.append(Para(index=i, text=text, is_bold_heading=is_bold, paragraph=p, in_table=in_table))
    return document, paras


def delete_paragraph(paragraph: Paragraph) -> None:
    """Remove a paragraph element entirely from the document body."""
    element = paragraph._element
    element.getparent().remove(element)
    paragraph._p = paragraph._element = None


def replace_text_in_paragraph(paragraph: Paragraph, old: str, new: str) -> bool:
    """Replace `old` with `new` across a paragraph's runs, preserving formatting.

    Word frequently splits a single visible phrase across multiple runs (spell-check
    markers, revision boundaries), so a naive per-run string replace often misses the
    match. This rewrites the paragraph's full text and re-applies it through the first
    run, which is safe because we only use it for short, unambiguous corrections.
    """
    full_text = "".join(r.text for r in paragraph.runs)
    if old not in full_text:
        return False
    new_text = full_text.replace(old, new)
    if not paragraph.runs:
        return False
    paragraph.runs[0].text = new_text
    for r in paragraph.runs[1:]:
        r.text = ""
    return True
