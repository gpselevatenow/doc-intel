import sys, os, pdfplumber

base = r"C:\Users\ridea\OneDrive\Desktop\VS Projects\doc-intel\sample documents"

for fname in ["sample_full_report.pdf", "sample_21_fog_5veh_houston.pdf", "Police_Report_High_Complexity.pdf"]:
    path = os.path.join(base, fname)
    parts = []
    with pdfplumber.open(path) as pdf:
        for pg in pdf.pages:
            parts.append(pg.extract_text() or "")
    text = "\n".join(parts)

    print(f"\n{'='*60}")
    print(f"FILE: {fname}")
    print(f"{'='*60}")

    lines = text.splitlines()
    # Find the first vehicle header and print 60 lines around it
    for i, line in enumerate(lines):
        if any(kw in line.upper() for kw in ["VEHICLE", "UNIT", "OPERATOR", "DRIVER", "PARTY", "PERSON"]):
            start = max(0, i-2)
            end = min(len(lines), i+5)
            # Print a window around it (just first match)
            print(f"\n--- First vehicle/party keyword at line {i} ---")
            for j in range(start, end):
                print(f"  [{j}] {repr(lines[j])}")
            break

    # Find party section
    for i, line in enumerate(lines):
        if "OPERATOR" in line.upper() or ("DRIVER" in line.upper() and "LICENSE" not in line.upper()):
            start = max(0, i-1)
            end = min(len(lines), i+15)
            print(f"\n--- First operator/driver at line {i} ---")
            for j in range(start, end):
                print(f"  [{j}] {repr(lines[j])}")
            break

    # Print last 80 lines to see structure
    print(f"\n--- Last 80 lines ---")
    for j, ln in enumerate(lines[-80:]):
        print(f"  [{len(lines)-80+j}] {repr(ln)}")
