"""
Feedback-driven learning loop.
Runs after each user correction and on demand.

Two learning strategies:
  1. Table alias learning — if a user corrected a field whose value came from a
     table column, learn that column header as an alias for the canonical field.
  2. Scalar pattern learning — if the extractor returned Unknown and the user
     provided the correct value, find that value in the raw doc and extract the
     label that preceded it as a new regex pattern.
"""

import re
import sqlite3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import DB_NAME, save_learned_pattern


# ── Local markdown table parser (no external dep) ────────────────────────────

def _parse_markdown_tables(text: str) -> list[list[list[str]]]:
    """Return list of tables; each table is a list of rows; each row is list of cells."""
    tables = []
    current: list[list[str]] = []
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('|') and line.endswith('|'):
            if re.match(r'^\|[\s\-\|]+\|$', line):
                continue  # separator row
            cells = [c.strip() for c in line.split('|')[1:-1]]
            current.append(cells)
        else:
            if current:
                tables.append(current)
                current = []
    if current:
        tables.append(current)
    return tables


# ── Strategy 1: table column alias learning ───────────────────────────────────

def train_aliases():
    """
    For corrections where the corrected value can be traced to a specific table
    column header, persist that header as an alias for the canonical field so
    future extractions pick it up automatically.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, doc_id, field_name, original_value, new_value FROM corrections')
    corrections = cursor.fetchall()

    if not corrections:
        conn.close()
        return 0

    learned = 0
    for _, doc_id, field_name, _, new_value in corrections:
        if not new_value or not new_value.strip():
            continue

        cursor.execute('SELECT markdown_text FROM raw_documents WHERE doc_id = ?', (doc_id,))
        row = cursor.fetchone()
        if not row:
            continue

        tables = _parse_markdown_tables(row[0])
        new_value_lower = new_value.strip().lower()

        for table in tables:
            if not table:
                continue
            # Find header row: contains field-like keywords
            header_row_idx = 0
            for idx, r in enumerate(table):
                row_str = ' '.join(r).lower()
                if any(kw in row_str for kw in ('vin', 'plate', 'license', 'citation', 'name', 'dob')):
                    header_row_idx = idx
                    break

            headers = [h.lower().strip() for h in table[header_row_idx]]
            for data_row in table[header_row_idx + 1:]:
                for col_idx, cell in enumerate(data_row):
                    if col_idx >= len(headers):
                        continue
                    if new_value_lower in cell.lower() or cell.lower() in new_value_lower:
                        alias = headers[col_idx]
                        if alias and alias != field_name.lower():
                            try:
                                cursor.execute(
                                    'INSERT OR IGNORE INTO table_aliases (canonical_field, alias_header) VALUES (?, ?)',
                                    (field_name.lower(), alias)
                                )
                                if cursor.rowcount:
                                    print(f"[ALIAS] '{alias}' → '{field_name}'")
                                    learned += 1
                            except sqlite3.IntegrityError:
                                pass
                            conn.commit()

    conn.close()
    return learned


# ── Strategy 2: scalar pattern learning ──────────────────────────────────────

_EXTRACTABLE_FIELDS = {
    'date_time', 'location', 'agency', 'officer', 'report_number', 'ems_agency',
    'inspection_date', 'inspection_firm', 'cause_of_loss',
    'coverage_a', 'coverage_b', 'coverage_c', 'coverage_d',
    'settlement', 'subrogation',
}

_MISSING = {'unknown', 'n/a', '', 'not found', 'none'}


def learn_scalar_patterns():
    """
    For corrections where the original value was Unknown/empty and the user
    provided the correct value: find that value in the raw markdown, extract
    the label that preceded it, and store a regex pattern for future use.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, doc_id, field_name, new_value
        FROM corrections
        WHERE LOWER(TRIM(original_value)) IN ('unknown', 'n/a', '', 'not found', 'none')
          AND TRIM(new_value) != ''
          AND new_value IS NOT NULL
    ''')
    corrections = cursor.fetchall()
    conn.close()

    learned = 0
    for _, doc_id, field_name, new_value in corrections:
        if field_name not in _EXTRACTABLE_FIELDS:
            continue

        conn2 = sqlite3.connect(DB_NAME)
        cur2 = conn2.cursor()
        cur2.execute('SELECT markdown_text FROM raw_documents WHERE doc_id = ?', (doc_id,))
        row = cur2.fetchone()
        conn2.close()

        if not row:
            continue

        markdown = row[0]
        # Find the corrected value in the raw text (case-insensitive)
        m = re.search(re.escape(new_value), markdown, re.IGNORECASE)
        if not m:
            continue

        # Grab up to 60 chars before the value
        start = m.start()
        context_before = markdown[max(0, start - 60): start]

        # Extract the last meaningful label from the context
        # (last non-empty line, or last colon-delimited token)
        lines = [ln.strip() for ln in context_before.split('\n') if ln.strip()]
        if not lines:
            continue
        last_line = lines[-1]
        # Strip trailing colon/dash/space
        label = re.sub(r'[\s:\-]+$', '', last_line).strip()
        if len(label) < 3 or len(label) > 60:
            continue
        # Skip if label looks like a value itself (has digits or is very short)
        if re.match(r'^\d', label):
            continue

        safe_label = re.escape(label)
        pattern = rf'(?i){safe_label}[\s:*\-]{{0,5}}(.{{3,80}})(?:\n|$)'

        # Validate the pattern actually matches in this doc
        try:
            pm = re.search(pattern, markdown)
            if not pm:
                continue
        except re.error:
            continue

        if save_learned_pattern(field_name, pattern, new_value, doc_id):
            print(f"[PATTERN] {field_name}: «{label}» → «{new_value}»")
            learned += 1

    return learned


# ── Public entry point ────────────────────────────────────────────────────────

def run_all_training():
    """Run both learning strategies. Called as a background task after corrections."""
    a = train_aliases()
    b = learn_scalar_patterns()
    print(f"Training complete: {a} new aliases, {b} new patterns.")


if __name__ == '__main__':
    run_all_training()
