"""Docling JSON + Markdown → canonical Document.

Single conversion entry point. Strategies operate on the canonical
Document only; they never touch raw Docling JSON.

Phase-A2 scope:
  - Pages with size in points (BOTTOMLEFT origin)
  - Blocks (one per Docling `texts[]` entry, with bbox/page/label/reading order)
  - Tables (cells with row/col/spans + bboxes)
  - Markdown body (read from sibling .md file if provided)

Tokens (word-level) and Sections (logical) are not populated yet.
Strategies that need them can derive on demand.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.core.document_model import (
    Block,
    Document,
    Page,
    Table,
    TableCell,
)


# ── Bbox helpers ─────────────────────────────────────────────────────

def _bbox_from_prov_entry(prov_entry: dict | None) -> list[float] | None:
    if not prov_entry:
        return None
    bb = prov_entry.get("bbox") or {}
    if all(k in bb for k in ("l", "t", "r", "b")):
        return [float(bb["l"]), float(bb["t"]), float(bb["r"]), float(bb["b"])]
    return None


# ── Public API ───────────────────────────────────────────────────────

def load_canonical_document(
    raw: dict[str, Any],
    document_id: str | None = None,
) -> Document:
    """Build a canonical Document from a Docling-export JSON dictionary."""

    # Pages (Docling exports a `pages` dict keyed by page-number-as-string).
    pages_dict = raw.get("pages") or {}
    pages: list[Page] = []
    for k, pinfo in pages_dict.items():
        try:
            pno = int(k)
        except (TypeError, ValueError):
            continue
        size = (pinfo or {}).get("size", {}) or {}
        pages.append(Page(
            page_no=pno,
            width_pt=float(size.get("width", 0.0)),
            height_pt=float(size.get("height", 0.0)),
        ))
    pages_by_no: dict[int, Page] = {p.page_no: p for p in pages}

    # Texts → Blocks
    texts = raw.get("texts") or []
    for idx, item in enumerate(texts):
        prov = item.get("prov") or []
        if not prov:
            continue
        bbox = _bbox_from_prov_entry(prov[0])
        if bbox is None:
            continue
        page_no = int(prov[0].get("page_no") or 1)
        text = (item.get("text") or "").strip()
        if not text:
            continue
        block = Block(
            block_id=f"text-{idx}",
            text=text,
            bbox=bbox,
            page=page_no,
            label=item.get("label"),
            reading_order=idx,
        )
        if page_no not in pages_by_no:
            page = Page(page_no=page_no, width_pt=0.0, height_pt=0.0)
            pages.append(page)
            pages_by_no[page_no] = page
        pages_by_no[page_no].blocks.append(block)

    # Tables → Table + TableCell
    tables = raw.get("tables") or []
    for tidx, t in enumerate(tables):
        prov = t.get("prov") or []
        if not prov:
            continue
        bbox = _bbox_from_prov_entry(prov[0]) or [0.0, 0.0, 0.0, 0.0]
        page_no = int(prov[0].get("page_no") or 1)
        data = t.get("data", {}) or {}
        n_rows = int(data.get("num_rows") or 0)
        n_cols = int(data.get("num_cols") or 0)

        # Cell bboxes: prefer Docling's per-cell prov. When missing (common
        # for many PDFs), synthesize from grid position so spatial pairing
        # works. BOTTOMLEFT origin: t > b, larger y is higher on the page.
        # Row 0 sits at the top of the table band; row N-1 sits at the bottom.
        table_l, table_t, table_r, table_b = bbox
        cell_w = ((table_r - table_l) / n_cols) if n_cols > 0 else (table_r - table_l)
        cell_h = ((table_t - table_b) / n_rows) if n_rows > 0 else (table_t - table_b)

        cells: list[TableCell] = []
        for cell in (data.get("table_cells") or []):
            cprov = (cell.get("prov") or [None])[0]
            cbbox = _bbox_from_prov_entry(cprov)
            row     = int(cell.get("start_row_offset_idx") or 0)
            col     = int(cell.get("start_col_offset_idx") or 0)
            rowspan = int(cell.get("row_span") or 1)
            colspan = int(cell.get("col_span") or 1)
            if cbbox is None:
                # Synthetic bbox from row/col grid position
                cell_left   = table_l + col * cell_w
                cell_right  = cell_left + cell_w * colspan
                cell_top    = table_t - row * cell_h
                cell_bottom = cell_top - cell_h * rowspan
                cbbox = [cell_left, cell_top, cell_right, cell_bottom]
            cells.append(TableCell(
                text=(cell.get("text") or "").strip(),
                bbox=cbbox,
                page=page_no,
                row=row,
                col=col,
                rowspan=rowspan,
                colspan=colspan,
            ))
        table = Table(
            table_id=f"table-{tidx}",
            page=page_no,
            bbox=bbox,
            n_rows=n_rows,
            n_cols=n_cols,
            cells=cells,
            reading_order=tidx,
        )
        if page_no in pages_by_no:
            pages_by_no[page_no].tables.append(table)
            # Also expose every cell as a Block so spatial matchers find
            # them. Cells in police/IA reports carry the actual field
            # labels and values; without this they're invisible to the
            # block-walking matchers.
            for cell in cells:
                if not cell.text.strip():
                    continue
                pages_by_no[page_no].blocks.append(Block(
                    block_id      = f"cell-{tidx}-{cell.row}-{cell.col}",
                    text          = cell.text,
                    bbox          = cell.bbox,
                    page          = cell.page,
                    label         = "table_cell",
                    reading_order = tidx * 1000 + cell.row * 100 + cell.col,
                ))

    pages.sort(key=lambda p: p.page_no)

    return Document(
        document_id = document_id or "doc",
        source_path = "",
        n_pages     = len(pages),
        markdown    = "",
        pages       = pages,
        metadata    = {"docling_export_version": raw.get("version")},
    )
