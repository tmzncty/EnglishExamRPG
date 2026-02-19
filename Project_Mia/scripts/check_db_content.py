import sqlite3
import os
from pathlib import Path

# Replicate logic from helpers.py
BASE_DIR = Path("f:/sanity_check_avg/Project_Mia/backend").resolve()
DATA_DIR = BASE_DIR / "data"

STATIC_DB = DATA_DIR / "static_content.db"
PROFILE_DB = DATA_DIR / "femo_profile.db"

Q_ID = "2023-eng1-writing-partB" 

def check_db():
    print(f"Checking DBs for Q_ID: {Q_ID}")
    print(f"Static DB Path: {STATIC_DB}")
    print(f"Profile DB Path: {PROFILE_DB}")
    
    if not STATIC_DB.exists():
        print(f"❌ Static DB not found at {STATIC_DB}")
        return

    try:
        conn = sqlite3.connect(STATIC_DB)
        cursor = conn.cursor()
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questions'")
        if not cursor.fetchone():
             print("❌ Table 'questions' does not exist in Static DB.")
        else:
            row = cursor.execute("SELECT image_base64 FROM questions WHERE q_id = ?", (Q_ID,)).fetchone()
            if row:
                img = row[0]
                if img:
                    print(f"✅ Found Image in Static DB! Length: {len(img)}")
                else:
                    print(f"⚠️ Question found, but image_base64 is NULL/Empty.")
            else:
                print(f"❌ Question ID not found in Static DB.")
        conn.close()
    except Exception as e:
        print(f"❌ Error reading Static DB: {e}")

    if not PROFILE_DB.exists():
        print(f"❌ Profile DB not found: {PROFILE_DB}")
        return

    try:
        conn = sqlite3.connect(PROFILE_DB)
        cursor = conn.cursor()
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='exam_history'")
        if not cursor.fetchone():
             print("❌ Table 'exam_history' does not exist in Profile DB.")
        else:
            row = cursor.execute("SELECT user_answer FROM exam_history WHERE q_id = ? ORDER BY created_at DESC LIMIT 1", (Q_ID,)).fetchone()
            if row:
                print(f"✅ Found User History! Answer: {row[0][:50]}...")
            else:
                 print(f"⚠️ No user history found for this Q_ID.")
        
        # List all tables to be sure
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables in Profile DB: {[t[0] for t in tables]}")

        conn.close()
    except Exception as e:
        print(f"❌ Error reading Profile DB: {e}")

if __name__ == "__main__":
    check_db()
