import re

def flatten_markdown_tables(text: str) -> str:
    import re
    flattened_lines = []
    lines = text.split('\n')
    in_table = False
    headers = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('|') and line.endswith('|'):
            if re.match(r'^\|[\s\-\|]+\|$', line):
                in_table = True
                continue
                
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            
            # Check for Key-Value alternating row
            is_kv_row = False
            if len(cells) % 2 == 0 and len(cells) > 0:
                keys = [c for c in cells[0::2] if c]
                if keys and all(c.isupper() or c.endswith(':') for c in keys):
                    is_kv_row = True
                    for i in range(0, len(cells), 2):
                        if cells[i] and i+1 < len(cells):
                            flattened_lines.append(f"{cells[i]}: {cells[i+1]}")
                            
            if is_kv_row:
                continue
            
            if not in_table:
                headers = cells
            else:
                if len(headers) == 2 and headers[0].lower() in ['field', 'key', 'name', 'item', ''] and headers[1].lower() in ['value', 'data', 'detail', 'details', '']:
                    if len(cells) == 2 and cells[0] and cells[1]:
                        flattened_lines.append(f"{cells[0]}: {cells[1]}")
                else:
                    for i, cell in enumerate(cells):
                        if i < len(headers) and headers[i] and cell:
                            flattened_lines.append(f"{headers[i]}: {cell}")
        else:
            in_table = False
            headers = []
            
    return "\n".join(flattened_lines)

test_md = """
| CASE NUMBER      | NAPD-26-09-22-3308                                                  | WEATHER                      | Rain (moderate)                             |
|------------------|---------------------------------------------------------------------|------------------------------|---------------------------------------------|
| DATE OF INCIDENT | September 22, 2026                                                  | LIGHT CONDITIONS             | Daylight                                    |
| TIME OF INCIDENT | 07:46 hrs                                                           | ROADWAY SURFACE              | Wet                                         |
| LOCATION         | Sutton Street & Park Street (intersection), North Andover, MA 01845 | TYPE OF COLLISION / VEHICLES | Side-impact (failure to yield) / 2 vehicles |
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from modules.police_extractor import extract_police_report

flattened = flatten_markdown_tables(test_md)
print(flattened)
print("\n--- EXTRACTION RESULT ---")
import json
print(json.dumps(extract_police_report(flattened), indent=2))
