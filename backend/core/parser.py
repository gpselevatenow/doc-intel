import os
from docling.document_converter import DocumentConverter
from core.docling_service import load_canonical_document

def parse_document(file_path: str):
    """
    Wrapper around Docling to parse uploaded PDFs into Markdown,
    preserving table structures. Also returns a canonical Document for bbox tracking.
    """
    converter = DocumentConverter()
    result = converter.convert(file_path)
    markdown_text = result.document.export_to_markdown()
    
    raw_dict = result.document.export_to_dict()
    canonical_doc = load_canonical_document(raw_dict)
    canonical_doc.markdown = markdown_text
    
    return markdown_text, canonical_doc

def find_bbox_for_text(canonical_doc, search_text: str):
    """
    Scans the canonical document blocks for a string and returns its exact
    bounding box coordinates [left, top, right, bottom] and page number.
    """
    if not search_text or len(search_text) < 3:
        return None

    def norm(t): return str(t).lower().replace('\n', ' ').strip()
    target = norm(search_text)

    for block in canonical_doc.all_blocks():
        if target in norm(block.text):
            return {
                "bbox": block.bbox,
                "page": block.page
            }
    return None

def flatten_markdown_tables(text: str) -> str:
    import re
    flattened_lines = []
    lines = text.split('\n')
    in_table = False
    headers = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('|') and line.endswith('|'):
            if re.match(r'^\|[\s\-\|]+\|$', line):
                in_table = True
                continue
                
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            
            # Check for Key-Value alternating row
            is_kv_row = False
            if len(cells) % 2 == 0 and len(cells) > 0:
                keys = [c for c in cells[0::2] if c]
                if keys and all(c.isupper() or c.endswith(':') for c in keys):
                    is_kv_row = True
                    for i in range(0, len(cells), 2):
                        if cells[i] and i+1 < len(cells):
                            flattened_lines.append(f"{cells[i]}: {cells[i+1]}")
                            
            if is_kv_row:
                continue
            
            if not in_table:
                headers = cells
            else:
                if len(headers) == 2 and headers[0].lower() in ['field', 'key', 'name', 'item', ''] and headers[1].lower() in ['value', 'data', 'detail', 'details', '']:
                    if len(cells) == 2 and cells[0] and cells[1]:
                        flattened_lines.append(f"{cells[0]}: {cells[1]}")
                else:
                    for i, cell in enumerate(cells):
                        if i < len(headers) and headers[i] and cell:
                            flattened_lines.append(f"{headers[i]}: {cell}")
        else:
            in_table = False
            headers = []
            
    return "\n".join(flattened_lines)

