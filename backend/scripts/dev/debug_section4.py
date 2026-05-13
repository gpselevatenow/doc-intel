import re, pdfplumber

base = r"C:\Users\ridea\OneDrive\Desktop\VS Projects\doc-intel\sample documents"
for fname in ["sample_full_report.pdf"]:
    path = f"{base}\\{fname}"
    parts = []
    with pdfplumber.open(path) as pdf:
        for pg in pdf.pages:
            parts.append(pg.extract_text() or "")
    text = "\n".join(parts)
    lines = text.splitlines()

    # Find SECTION 4 and print until SECTION 6
    in_range = False
    for i, ln in enumerate(lines):
        s = ln.strip()
        if re.match(r'(?i)^SECTION\s+4\b', s):
            in_range = True
        if re.match(r'(?i)^SECTION\s+6\b', s):
            in_range = False
        if in_range:
            print(f"[{i}] {repr(s)}")
