import sqlite3
import os
import json

LOG_FILE = 'db_check.log'

def log(msg):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(str(msg) + '\n')

def check_story_db():
    db_path = 'story_content.db'
    if not os.path.exists(db_path):
        log(f"Error: {db_path} does not exist.")
        return

    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Check tables
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = c.fetchall()
        log(f"Tables in {db_path}: {tables}")
        
        # Check stories table
        if ('stories',) in tables:
            c.execute("SELECT count(*) FROM stories")
            count = c.fetchone()[0]
            log(f"Total stories: {count}")
            
            c.execute("SELECT * FROM stories LIMIT 1")
            first = c.fetchone()
            log(f"First story sample: {first}")
            
            # Check column names
            c.execute("PRAGMA table_info(stories)")
            cols = c.fetchall()
            log(f"Columns: {[col[1] for col in cols]}")

        conn.close()
    except Exception as e:
        log(f"Database error: {e}")

if __name__ == '__main__':
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    log("Checking story_content.db...")
    check_story_db()
