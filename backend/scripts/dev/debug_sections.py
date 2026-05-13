import sys, os, re, pdfplumber

base = r"C:\Users\ridea\OneDrive\Desktop\VS Projects\doc-intel\sample documents"

for fname in ["sample_full_report.pdf", "sample_21_fog_5veh_houston.pdf", "Police_Report_High_Complexity.pdf"]:
    path = os.path.join(base, fname)
    parts = []
    with pdfplumber.open(path) as pdf:
        for pg in pdf.pages:
            parts.append(pg.extract_text() or "")
    text = "\n".join(parts)
    lines = text.splitlines()

    print(f"\n{'='*60}")
    print(f"FILE: {fname}")
    print(f"{'='*60}")

    # Find V3 section lines
    in_v3 = False
    print("\n-- V3 section context --")
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.search(r'(?i)(Vehicle\s+V3|Unit.*?#\s*3|SECTION\s+3|V3\s*[\:—–�])', stripped):
            in_v3 = True
        if in_v3:
            print(f"  [{i}] {repr(stripped)}")
            if i > 0 and re.search(r'(?i)^SECTION\s+[4-9]', stripped):
                in_v3 = False
                print("  -- section end --")
                break
        if i > 300:
            break

    # Find first operator/party line
    print("\n-- First operator/party context --")
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.search(r'(?i)(^Operator\b|^Driver\b|SECTION\s+3\b|PERSONS\s+INVOLVED|PARTY\s+INVOLVED|UNIT\s*/\s*VEH)', stripped):
            start = max(0, i-1)
            end = min(len(lines), i+30)
            print(f"\n  Match at line {i}: {repr(stripped)}")
            for j in range(start, end):
                print(f"  [{j}] {repr(lines[j].strip())}")
            break
