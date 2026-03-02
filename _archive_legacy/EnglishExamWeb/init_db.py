import sqlite3
import os

DB_FILE = 'webnav_rpg.db'

def init_db():
    if os.path.exists(DB_FILE):
        print(f"Database {DB_FILE} already exists.")
        # Optional: Backup or ask to overwrite? For now, we assume upgrades are additive or manual.
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Users table (future proofing)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Game Saves
    c.execute('''CREATE TABLE IF NOT EXISTS game_saves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        slot_id INTEGER DEFAULT 0,
        data_json TEXT, -- Complete JSON dump of localStorage or specific state
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, slot_id)
    )''')

    # AI Response Cache (Token saving)
    c.execute('''CREATE TABLE IF NOT EXISTS ai_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prompt_hash TEXT UNIQUE NOT NULL, -- MD5 or SHA256 of the prompt
        prompt_text TEXT,
        response TEXT,
        provider TEXT,
        model TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Drawing paths
    c.execute('''CREATE TABLE IF NOT EXISTS drawings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        paper_id TEXT NOT NULL, -- e.g., '2020-text1'
        strokes_json TEXT, -- JSON array of paths
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, paper_id)
    )''')

    # Insert default user
    c.execute("INSERT OR IGNORE INTO users (id, username) VALUES (1, 'Commander')")

    conn.commit()
    conn.close()
    print(f"Database {DB_FILE} initialized successfully.")

if __name__ == '__main__':
    init_db()
