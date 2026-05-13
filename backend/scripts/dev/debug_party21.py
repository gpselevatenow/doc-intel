import re, pdfplumber, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from core.orchestrator_integration import _normalize_compound_lines

base = r"C:\Users\ridea\OneDrive\Desktop\VS Projects\doc-intel\sample documents"
fname = "sample_21_fog_5veh_houston.pdf"
path = f"{base}\\{fname}"
parts = []
with pdfplumber.open(path) as pdf:
    for pg in pdf.pages:
        parts.append(pg.extract_text() or "")
text = "\n".join(parts)
text = _normalize_compound_lines(text)
lines = text.splitlines()

party_pattern = re.compile(
    r'(?i)(Party\s*[#]?\s*\d*\s*:?|Person\s*[#]?\s*\d+\s*:?|Veh\s*:\s*V\d+|'
    r'Operator(?=\s*(?:[^A-Za-z\s)]|$))\s*[#]?\s*\d*\s*(?:\(V\d+\))?\s*:?|'
    r'Driver(?!\s+(?:Name|Information)\b)(?=[#\s]*\d|[#\s]*\(V|[#\s]*:)|'
    r'Passenger\b\s*[#]?\s*\d*\s*(?:\(V\d+\))?\s*:?|Pedestrian\b\s*[#]?\s*\d*\s*:?|'
    r'Bicyclist\b\s*[#]?\s*\d*\s*:?|VICTIM[\s/]*COMPLAINANT\b|VICTIM\b|COMPLAINANT\b|'
    r'SUSPECT[\s/]*OFFENDER\b|SUSPECT\b|OFFENDER\b)'
)
section_pattern = re.compile(r'(?i)^SECTION\s+(?:[6-9]|\d{2,})\b|^(?:NARRATIVE|SUPPLEMENTAL|SUPPLEMENT|ADDENDUM)\b')
table_header = re.compile(r'(?i)^Party\s+Name\s+DOB\s+(?:License|DL)\b')
table_row = re.compile(
    r'(?i)^(Driver|Operator)\s+(?:V\d+\s+)?'
    r'([A-Z][A-Za-z\s,\.\']{3,40}?)\s+'
    r'(\d{1,2}/\d{1,2}/\d{2,4})\s+'
    r'([A-Z][A-Z0-9\-]{3,20})'
)

print(f"Total lines: {len(lines)}")
for i, ln in enumerate(lines):
    ln = re.sub(r'\(cid:\d+\)', '', ln).strip()
    if not ln:
        continue
    if section_pattern.match(ln):
        print(f"[{i}] SECTION BOUNDARY: {repr(ln)}")
        continue
    if table_header.match(ln):
        print(f"[{i}] TABLE HEADER: {repr(ln)}")
        continue
    if table_row.match(ln):
        print(f"[{i}] TABLE ROW: {repr(ln)}")
        continue
    pm = party_pattern.match(ln)
    if pm:
        print(f"[{i}] PARTY MATCH ({pm.group(0)!r}): {repr(ln[:80])}")
