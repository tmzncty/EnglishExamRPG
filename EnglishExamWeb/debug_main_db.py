import sqlite3
import os

def check_main_db():
    db_path = 'webnav_rpg.db'
    print(f"Checking {db_path}...")
    
    try:
        conn = sqlite3.connect(db_path, timeout=10)
        c = conn.cursor()
        
        # Check tables
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = c.fetchall()
        print(f"Tables: {tables}")
        
        # Try a write
        print("Attempting to write dummy data...")
        try:
            c.execute("INSERT OR IGNORE INTO users (id, username) VALUES (999, 'TestUser')")
            conn.commit()
            print("Write successful!")
        except Exception as e:
            print(f"Write failed: {e}")
            
        conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == '__main__':
    check_main_db()
