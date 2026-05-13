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

    # Print lines 218 onwards
    for i, ln in enumerate(lines[218:], start=218):
        s = ln.strip()
        print(f"[{i}] {repr(s)}")
        if i > 320:
            break
