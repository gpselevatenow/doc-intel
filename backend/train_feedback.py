import sqlite3
import os
import sys

# Ensure backend modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from modules.police_extractor import parse_markdown_tables
from database import DB_NAME

def train_aliases():
    """
    Analyzes all corrections in feedback.db.
    If an adjuster corrected a field, it re-parses the original document's
    markdown tables, finds the cell containing the correction,
    traces it up to the column header, and permanently learns that header
    as an alias for the canonical field!
    """
    print(f"Connecting to {DB_NAME} for training loop...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Get all corrections where original value was empty/unknown
    cursor.execute('''
        SELECT id, doc_id, field_name, original_value, new_value 
        FROM corrections
    ''')
    corrections = cursor.fetchall()
    
    if not corrections:
        print("No corrections found in database. Exiting.")
        conn.close()
        return

    new_aliases_learned = 0

    for row in corrections:
        c_id, doc_id, field_name, original_value, new_value = row
        
        if not new_value or new_value.strip() == "":
            continue
            
        new_value_clean = new_value.strip().lower()
            
        # 2. Get the original raw markdown for this document
        cursor.execute('SELECT markdown_text FROM raw_documents WHERE doc_id = ?', (doc_id,))
        doc_row = cursor.fetchone()
        if not doc_row:
            continue
            
        markdown_text = doc_row[0]
        
        # 3. Parse tables into 2D arrays
        tables = parse_markdown_tables(markdown_text)
        
        learned_header = None
        
        # 4. Search the tables for the human's correction
        for table in tables:
            if not table: continue
            
            # For simplicity, assume row 0 is the true header for this naive search
            # We will scan all rows below it.
            # A more robust system uses the dynamic header discovery from police_extractor
            
            # Let's find the true header row exactly as police_extractor does
            header_row_idx = -1
            for idx, r in enumerate(table):
                row_str = " ".join(r).lower()
                # If this row looks like a header row
                if "vin" in row_str or "plate" in row_str or "license" in row_str or "citation" in row_str or "name" in row_str:
                    header_row_idx = idx
                    break
                    
            if header_row_idx == -1:
                # Fallback to row 0
                header_row_idx = 0
                
            headers = [h.lower().strip() for h in table[header_row_idx]]
            data_rows = table[header_row_idx+1:]
            
            for row in data_rows:
                for col_idx, cell in enumerate(row):
                    if col_idx < len(headers):
                        if new_value_clean in cell.lower().strip() or cell.lower().strip() in new_value_clean:
                            # WE FOUND IT! Trace back up to the header
                            learned_header = headers[col_idx]
                            break
                if learned_header: break
            if learned_header: break
            
        # 5. Save the learned mapping!
        if learned_header and learned_header != field_name.lower():
            try:
                cursor.execute(
                    'INSERT INTO table_aliases (canonical_field, alias_header) VALUES (?, ?)',
                    (field_name.lower(), learned_header)
                )
                conn.commit()
                print(f"[LEARNED] Mapped column '{learned_header}' to canonical field '{field_name}'!")
                new_aliases_learned += 1
            except sqlite3.IntegrityError:
                # Already learned this alias
                pass

    conn.close()
    print(f"Training complete. Learned {new_aliases_learned} new column mappings.")

if __name__ == "__main__":
    train_aliases()
