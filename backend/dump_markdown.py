import sqlite3

conn = sqlite3.connect("feedback.db")
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", cur.fetchall())
cur.execute("SELECT doc_id, LENGTH(markdown_text) FROM raw_documents ORDER BY rowid DESC LIMIT 5")
rows = cur.fetchall()
print("Recent docs:", rows)
if rows:
    cur.execute("SELECT markdown_text FROM raw_documents ORDER BY rowid DESC LIMIT 1")
    text = cur.fetchone()[0]
    print("\n=== LAST DOCUMENT MARKDOWN (first 4000 chars) ===")
    print(text[:4000])
