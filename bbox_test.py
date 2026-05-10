from backend.core.parser import parse_document, find_bbox_for_text
import json

md, doc = parse_document("sample_07_rain_injury.pdf")

# Test a known extraction
target = "Side-impact (failure to yield) / 2 vehicles"
bbox_info = find_bbox_for_text(doc, target)

print(f"Target: {target}")
print(f"BBox Info: {bbox_info}")
