"""One-shot script: add inline officer pattern to all state templates."""
import json, os, glob

INLINE_PATTERN = (
    r"(?im)(?:Investig\w*|Reporting|Responding)\s+Officer\s+"
    r"(?P<value>[A-Za-z][A-Za-z\s,.\'\-]{2,50}?)"
    r"(?=\s+Badge|\s+Agency|\s+#\s*\d|\s*$)"
)

templates_dir = os.path.join(os.path.dirname(__file__), "templates")
skip = {"police_report.json", "tx_cr3.json", "ia_report.json", "acord_report.json"}

for path in sorted(glob.glob(os.path.join(templates_dir, "*.json"))):
    if os.path.basename(path) in skip:
        continue
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    changed = False
    for field in data.get("fields", []):
        if field.get("field_id") != "officer":
            continue
        for strat in field.get("strategies", []):
            patterns = strat.get("config", {}).get("patterns", [])
            if patterns and patterns[0] != INLINE_PATTERN:
                patterns.insert(0, INLINE_PATTERN)
                changed = True
    if changed:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Updated: {os.path.basename(path)}")

print("Done.")
