import sqlite3
import json
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
STATIC_DB = DATA_DIR / "static_content.db"
JSON_FILE = DATA_DIR / "exam_vocabulary.json"

def migrate():
    if not JSON_FILE.exists():
        print(f"JSON file not found: {JSON_FILE}")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # raw_data is a list of dicts based on previous context
    # if it's a list, process it
    if isinstance(raw_data, list):
        items = raw_data
    elif isinstance(raw_data, dict):
        items = list(raw_data.values())
    else:
        print("Invalid JSON format.")
        return

    conn = sqlite3.connect(STATIC_DB)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vocabulary (
            word TEXT PRIMARY KEY,
            phonetic TEXT,
            pos TEXT,
            meanings TEXT,
            sentences TEXT
        )
    """)

    added = 0
    for item in items:
        word = item.get("word")
        if not word:
            continue
        
        phonetic = item.get("phonetic", "")
        pos = item.get("pos", "")
        meanings = json.dumps(item.get("meanings", []), ensure_ascii=False)
        sentences = json.dumps(item.get("sentences", []), ensure_ascii=False)

        cursor.execute("""
            INSERT OR REPLACE INTO vocabulary (word, phonetic, pos, meanings, sentences)
            VALUES (?, ?, ?, ?, ?)
        """, (word, phonetic, pos, meanings, sentences))
        added += 1

    conn.commit()
    conn.close()
    print(f"Migrated {added} words into static_content.db -> vocabulary table.")

if __name__ == "__main__":
    migrate()
