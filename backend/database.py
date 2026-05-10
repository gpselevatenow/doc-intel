import sqlite3
from datetime import datetime

DB_NAME = "feedback.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS corrections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id TEXT NOT NULL,
            field_name TEXT NOT NULL,
            original_value TEXT NOT NULL,
            new_value TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def log_correction(doc_id: str, field_name: str, original_value: str, new_value: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO corrections (doc_id, field_name, original_value, new_value, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (doc_id, field_name, original_value, new_value, timestamp))
    conn.commit()
    conn.close()
