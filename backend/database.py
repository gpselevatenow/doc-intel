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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS custom_fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id TEXT NOT NULL,
            field_name TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            UNIQUE(doc_id, field_name)
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

def add_custom_field(doc_id: str, field_name: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    try:
        cursor.execute('INSERT INTO custom_fields (doc_id, field_name, timestamp) VALUES (?, ?, ?)', (doc_id, field_name, timestamp))
        conn.commit()
    except sqlite3.IntegrityError:
        pass # Ignore duplicates
    finally:
        conn.close()

def get_custom_fields(doc_id: str) -> list:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT field_name FROM custom_fields WHERE doc_id = ?', (doc_id,))
    fields = [row[0] for row in cursor.fetchall()]
    conn.close()
    return fields

def delete_custom_field(doc_id: str, field_name: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM custom_fields WHERE doc_id = ? AND field_name = ?', (doc_id, field_name))
    conn.commit()
    conn.close()
