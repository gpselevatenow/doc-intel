"""Canonical Document model — Layer 1.

Normalizes Docling's output into an internal representation that all
extractors operate on. Extractors NEVER touch raw Docling JSON.

Hierarchy (per page unless noted):
    Document
      → pages
          → tokens   (word-level text items with bbox + ocr conf)
          → lines    (visual lines)
          → blocks   (paragraph-like groupings; Docling's `texts[]` items map here)
          → tables   (rows × cells)
      → sections     (logical heading + body, doc-wide)

Coordinates: BOTTOMLEFT origin in PDF points (Docling default).

The conversion from Docling JSON → Document lives in
`services/docling_service.py`. This file declares the shape only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


BBox = list[float]    # [l, t, r, b] in points, BOTTOMLEFT origin


# ── Atomic text elements ─────────────────────────────────────────────

@dataclass
class Token:
    """A word-level text item."""
    text:           str
    bbox:           BBox
    page:           int
    block_id:       str | None = None
    line_id:        str | None = None
    reading_order:  int        = 0
    ocr_confidence: float | None = None


@dataclass
class Line:
    """A visual line of text."""
    line_id:       str
    text:          str
    bbox:          BBox
    page:          int
    block_id:      str | None  = None
    reading_order: int         = 0
    tokens:        list[Token] = field(default_factory=list)


@dataclass
class Block:
    """A paragraph-like grouping. Docling `texts[]` items map to a Block."""
    block_id:      str
    text:          str
    bbox:          BBox
    page:          int
    label:         str | None = None    # docling label: text/list_item/page_header/...
    reading_order: int        = 0
    lines:         list[Line] = field(default_factory=list)


@dataclass
class TableCell:
    text:    str
    bbox:    BBox
    page:    int
    row:     int
    col:     int
    rowspan: int = 1
    colspan: int = 1


@dataclass
class Table:
    table_id:      str
    page:          int
    bbox:          BBox
    n_rows:        int
    n_cols:        int
    cells:         list[TableCell] = field(default_factory=list)
    reading_order: int             = 0


@dataclass
class Section:
    """A logical section — anchored by a heading, contains the body until the next heading."""
    section_id: str
    heading:    str | None
    page_start: int
    page_end:   int
    text:       str
    block_ids:  list[str] = field(default_factory=list)


@dataclass
class Page:
    page_no:    int
    width_pt:   float
    height_pt:  float
    tokens:     list[Token] = field(default_factory=list)
    lines:      list[Line]  = field(default_factory=list)
    blocks:     list[Block] = field(default_factory=list)
    tables:     list[Table] = field(default_factory=list)


# ── Top-level Document ───────────────────────────────────────────────

@dataclass
class Document:
    """Canonical, parser-agnostic document model."""

    document_id: str
    source_path: str
    n_pages:     int
    markdown:    str
    pages:       list[Page]    = field(default_factory=list)
    sections:    list[Section] = field(default_factory=list)
    metadata:    dict[str, Any] = field(default_factory=dict)

    # ── Convenience accessors ────────────────────────────────────────

    def page(self, page_no: int) -> Page | None:
        for p in self.pages:
            if p.page_no == page_no:
                return p
        return None

    def all_blocks(self) -> list[Block]:
        return [b for p in self.pages for b in p.blocks]

    def all_lines(self) -> list[Line]:
        return [ln for p in self.pages for ln in p.lines]

    def all_tokens(self) -> list[Token]:
        return [t for p in self.pages for t in p.tokens]

    def all_tables(self) -> list[Table]:
        return [t for p in self.pages for t in p.tables]
