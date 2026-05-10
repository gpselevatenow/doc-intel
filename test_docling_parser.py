import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from core.parser import parse_document, flatten_markdown_tables

pdf_path = "sample_07_rain_injury.pdf"

print(f"Parsing {pdf_path}...")
markdown_text, _ = parse_document(pdf_path)

with open("docling_output.md", "w", encoding="utf-8") as f:
    f.write(markdown_text)

print("Flattening tables...")
flattened = flatten_markdown_tables(markdown_text)

with open("docling_flattened.txt", "w", encoding="utf-8") as f:
    f.write(flattened)

print("Done. Check docling_output.md and docling_flattened.txt")
