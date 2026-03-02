import sqlite3
import os

DB_FILE = 'webnav_rpg.db'

def upgrade_db():
    """Add missing tables to existing database without affecting existing data"""
    if not os.path.exists(DB_FILE):
        print(f"Database {DB_FILE} not found. Run init_db.py first.")
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Check existing tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in c.fetchall()]
    print(f"Existing tables: {', '.join(existing_tables)}")
    
    # Add drawings table if missing
    if 'drawings' not in existing_tables:
        print("Creating drawings table...")
        c.execute('''CREATE TABLE IF NOT EXISTS drawings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            paper_id TEXT NOT NULL,
            strokes_json TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, paper_id)
        )''')
        print("✓ drawings table created")
    else:
        print("✓ drawings table already exists")
    
    # Add game_saves table if missing
    if 'game_saves' not in existing_tables:
        print("Creating game_saves table...")
        c.execute('''CREATE TABLE IF NOT EXISTS game_saves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            slot_id INTEGER DEFAULT 0,
            data_json TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, slot_id)
        )''')
        print("✓ game_saves table created")
    else:
        print("✓ game_saves table already exists")
        # Check how many saves exist
        c.execute("SELECT COUNT(*) FROM game_saves WHERE user_id=1")
        count = c.fetchone()[0]
        print(f"  → Found {count} saved games")
    
    # Add ai_cache table if missing
    if 'ai_cache' not in existing_tables:
        print("Creating ai_cache table...")
        c.execute('''CREATE TABLE IF NOT EXISTS ai_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_hash TEXT UNIQUE NOT NULL,
            prompt_text TEXT,
            response TEXT,
            provider TEXT,
            model TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        print("✓ ai_cache table created")
    else:
        print("✓ ai_cache table already exists")
    
    # Add users table if missing
    if 'users' not in existing_tables:
        print("Creating users table...")
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        c.execute("INSERT OR IGNORE INTO users (id, username) VALUES (1, 'Commander')")
        print("✓ users table created")
    else:
        print("✓ users table already exists")
    
    conn.commit()
    conn.close()
    print(f"\n✅ Database upgraded successfully!")

if __name__ == '__main__':
    upgrade_db()
