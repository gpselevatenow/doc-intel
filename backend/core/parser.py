import os
import re
from docling.document_converter import DocumentConverter
from core.docling_service import load_canonical_document

# Known field labels in police/IA form PDFs rendered by Docling without colons
_KNOWN_LABEL_RE = re.compile(
    r'^(?:name(?:\s*\([^)]*\))?|date\s+of\s+birth|dob|address|addr|phone|'
    r'tel(?:ephone)?|cell|year|make|manufacturer|model|color|'
    r'vin(?:\s+number)?|vehicle\s+identification(?:\s+number)?|'
    r'plate|license\s+plate|tag|'
    r'statute\s*/\s*charge|offense(?:\s*/\s*classification)?|crime\s+type|'
    r'reporting\s+officer|badge(?:\s+number)?|case\s+status|'
    r'owner(?:\s+name|\s+address)?|insurance(?:\s+company)?|carrier|'
    r'policy(?:\s+number)?|tow(?:ed|ing)?(?:\s+company)?|'
    r'dl(?:\s+[#]|\s+number)?|driver.?s?\s+licens\w*|'
    r'transported\s+to|hospital|taken\s+to|'
    r'citation|charge|infraction|injur(?:y|ies)|condition|'
    r'witness(?:\s+statement)?|statement)$',
    re.IGNORECASE
)

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

_PARTY_VEHICLE_DELIMITER_RE = re.compile(
    r'^(?:DRIVER|OPERATOR|PASSENGER|VEHICLE|PARTY|WITNESS|VICTIM|SUSPECT|OFFENDER|'
    r'V\d+\s*:|W\d+\s*:)',
    re.IGNORECASE
)


def normalize_label_value_blocks(text: str) -> str:
    """
    Handles Docling's form-PDF rendering where labels and values appear on
    separate lines (LABEL\\n\\nVALUE instead of LABEL: VALUE). Converts to
    LABEL: VALUE. Also strips ## heading markers that Docling applies to
    some field values (e.g. ## 2HGFC2F63LH521047 for a VIN).
    """
    lines = text.split('\n')

    # Strip heading markers from every line
    lines = [re.sub(r'^#{1,6}\s+', '', ln) for ln in lines]

    result = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if not line:
            result.append('')
            i += 1
            continue

        # Find the next non-empty line
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1

        if j < len(lines) and (j - i) > 1:
            next_line = lines[j].strip()

            ends_colon = line.endswith(':')
            no_lower = not re.search(r'[a-z]', line)
            is_known = bool(_KNOWN_LABEL_RE.match(line))
            is_label = ends_colon or no_lower or is_known

            # Never merge a label into a party/vehicle delimiter line —
            # that would hide the delimiter from the table extractor.
            next_is_delimiter = bool(_PARTY_VEHICLE_DELIMITER_RE.match(next_line))

            if is_known:
                # Known field label: accept any non-empty value regardless of case
                is_value = bool(next_line)
            else:
                is_value = (
                    bool(re.search(r'[a-z]', next_line)) or
                    bool(re.match(r'^\d', next_line)) or
                    bool(re.match(r'^[A-Z]{1,4}[-\d]', next_line))
                )

            if is_label and is_value and not next_is_delimiter:
                sep = ' ' if ends_colon else ': '
                result.append(f"{line}{sep}{next_line}")
                i = j + 1
                continue

        result.append(line)
        i += 1

    return _merge_date_time_lines('\n'.join(result))


def _merge_date_time_lines(text: str) -> str:
    """
    Merge adjacent 'Date: MM/DD/YYYY' + 'Time: HH:MM' lines into
    'Date/Time: MM/DD/YYYY HH:MM' so a single regex can capture both.
    """
    return re.sub(
        r'(?im)^(Date:\s*\d{1,2}/\d{1,2}/\d{2,4}(?:\s+\d{1,2}:\d{2}(?:\s*hrs?)?)?)\s*\n\s*(Time:\s*\d{1,2}:\d{2}(?:\s*hrs?)?)',
        lambda m: 'Date/Time: ' + m.group(1).split(':', 1)[1].strip() + ' ' + m.group(2).split(':', 1)[1].strip(),
        text
    )


def split_narrative_section(text: str) -> tuple[str, str]:
    """
    Split document text at the NARRATIVE section header.
    Returns (pre_narrative, narrative). If no NARRATIVE marker found, returns (full_text, "").
    Handles: 'NARRATIVE', 'OFFICER NARRATIVE', 'SECTION N - NARRATIVE',
             'SECTION N - OFFICER NARRATIVE' (Docling inline format).
    """
    m = re.search(
        r'(?im)^(?:SECTION\s*\d+\s*[-–]\s*)?(?:OFFICER\s+)?NARRATIVE\b',
        text
    )
    if not m:
        return text, ""
    return text[: m.start()], text[m.start():]


def flatten_markdown_tables(text: str) -> str:
    flattened_lines = []
    lines = text.split('\n')
    in_table = False
    headers = []
    is_kv_table = False  # True for 2-col key:value tables (Section 1 style)

    for line in lines:
        line = line.strip()

        # Docling inline format: "SECTION X - LABEL: | col1 | col2 | ..."
        # Strip the section prefix so the pipe portion is processed normally
        if '|' in line and not line.startswith('|'):
            pipe_idx = line.index('|')
            table_part = line[pipe_idx:].strip()
            if table_part.startswith('|') and table_part.endswith('|'):
                line = table_part

        if line.startswith('|') and line.endswith('|'):
            # Separator row (---|---|---) — marks start of table body
            if re.match(r'^\|[\s\-\|]+\|$', line):
                in_table = True
                continue

            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            if not cells:
                continue

            # KV-alternating row: | ALL_CAPS_KEY | val | ALL_CAPS_KEY | val |
            if len(cells) % 2 == 0:
                keys = [c for c in cells[0::2] if c]
                if keys and all(c.isupper() or c.endswith(':') for c in keys):
                    for i in range(0, len(cells), 2):
                        if cells[i] and i + 1 < len(cells):
                            flattened_lines.append(f"{cells[i]}: {cells[i+1]}")
                    continue

            if not in_table:
                # First non-separator row: decide table type
                if len(cells) == 2 and cells[0] and cells[1]:
                    # 2-column with data in both cells — emit as key:value directly
                    flattened_lines.append(f"{cells[0]}: {cells[1]}")
                    is_kv_table = True
                    headers = []
                else:
                    # Multi-column — treat as column header row
                    headers = cells
                    is_kv_table = False
            else:
                if is_kv_table:
                    if len(cells) >= 2 and cells[0] and cells[1]:
                        flattened_lines.append(f"{cells[0]}: {cells[1]}")
                elif headers:
                    for i, cell in enumerate(cells):
                        if i < len(headers) and headers[i] and cell:
                            flattened_lines.append(f"{headers[i]}: {cell}")
        else:
            in_table = False
            headers = []
            is_kv_table = False

    return "\n".join(flattened_lines)

