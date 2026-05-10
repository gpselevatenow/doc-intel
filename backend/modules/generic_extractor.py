import re
from database import get_custom_fields

def extract_generic_fields(text: str, doc_id: str) -> dict:
    """
    Parses a flattened markdown document to extract a dynamic dictionary of all
    Key-Value pairs found, and specifically looks for user-defined custom fields.
    """
    dynamic_fields = {}
    
    # 1. Pull user-defined custom fields from database
    try:
        custom_fields = get_custom_fields(doc_id)
    except Exception:
        custom_fields = []
        
    # 2. Extract standard Key: Value lines (from flattened tables or formatted text)
    lines = text.split('\n')
    for line in lines:
        if ':' in line:
            parts = line.split(':', 1)
            key = parts[0].strip()
            val = parts[1].strip()
            
            # Basic validation to ensure it's actually a field and not a random sentence
            if key and val and len(key) < 50 and len(val) < 200:
                # Clean up key name for UI display
                clean_key = re.sub(r'[^a-zA-Z0-9\s/]', '', key).strip()
                if clean_key:
                    dynamic_fields[clean_key] = val

    # 3. Fuzzy search for User's Custom Fields if they weren't caught perfectly by the table flattener
    for custom_field in custom_fields:
        # Check if we already found an exact or close match
        already_found = any(custom_field.lower() in k.lower() for k in dynamic_fields.keys())
        if not already_found:
            # Try to regex hunt for it in the raw text
            # E.g. "Weather Conditions: Sunny" or "Weather Conditions Sunny"
            escaped_field = re.escape(custom_field)
            match = re.search(fr'(?i){escaped_field}(?:[:\s\-]+)?([A-Za-z0-9\s,\.]+)(?=\n|$)', text)
            if match:
                val = match.group(1).strip()
                if len(val) < 100:
                    dynamic_fields[custom_field] = val
            else:
                # If we absolutely cannot find it, add it as missing so the UI still displays it for the user to edit
                dynamic_fields[custom_field] = "Not Found"

    return dynamic_fields
