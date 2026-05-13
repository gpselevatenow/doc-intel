import sqlite3
from datetime import datetime
import os

DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "feedback.db")

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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS raw_documents (
            doc_id TEXT PRIMARY KEY,
            markdown_text TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS table_aliases (
            canonical_field TEXT NOT NULL,
            alias_header TEXT NOT NULL,
            UNIQUE(canonical_field, alias_header)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id TEXT NOT NULL,
            score INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS learned_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_name TEXT NOT NULL,
            pattern TEXT NOT NULL,
            example TEXT,
            source_doc TEXT,
            UNIQUE(field_name, pattern)
        )
    ''')
    conn.commit()
    conn.close()


def get_learned_patterns(field_name: str) -> list:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT pattern FROM learned_patterns WHERE field_name = ?', (field_name,))
        return [row[0] for row in cursor.fetchall()]
    except Exception:
        return []
    finally:
        conn.close()


def save_learned_pattern(field_name: str, pattern: str, example: str = '', source_doc: str = '') -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT OR IGNORE INTO learned_patterns (field_name, pattern, example, source_doc) VALUES (?, ?, ?, ?)',
            (field_name, pattern, example, source_doc)
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception:
        return False
    finally:
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
    # Fetch globally to apply continuous learning across all documents
    cursor.execute('SELECT DISTINCT field_name FROM custom_fields')
    fields = [row[0] for row in cursor.fetchall()]
    conn.close()
    return fields

def delete_custom_field(doc_id: str, field_name: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM custom_fields WHERE doc_id = ? AND field_name = ?', (doc_id, field_name))
    conn.commit()
    conn.close()

def save_raw_document(doc_id: str, markdown_text: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT OR REPLACE INTO raw_documents (doc_id, markdown_text) VALUES (?, ?)', (doc_id, markdown_text))
        conn.commit()
    except Exception as e:
        print(f"Failed to save raw doc: {e}")
    finally:
        conn.close()

def get_aliases_for(canonical_field: str) -> list[str]:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT alias_header FROM table_aliases WHERE canonical_field = ?', (canonical_field,))
        aliases = [row[0] for row in cursor.fetchall()]
        return aliases
    except Exception:
        return []
    finally:
        conn.close()

def log_user_feedback(doc_id: str, score: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO user_feedback (doc_id, score, timestamp)
        VALUES (?, ?, ?)
    ''', (doc_id, score, timestamp))
    conn.commit()
    conn.close()

