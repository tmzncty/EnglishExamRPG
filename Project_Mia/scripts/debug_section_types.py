import sqlite3
import os

# Adjust path as needed
DB_PATH = r"f:\sanity_check_avg\Project_Mia\backend\data\static_content.db"

def check_section_types():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print(f"--- DISTINCT section_type in 'questions' table ---")
        cursor.execute("SELECT DISTINCT section_type FROM questions")
        rows = cursor.fetchall()
        for row in rows:
            print(f"Found: {row[0]}")
            
        conn.close()
    except Exception as e:
        print(f"Error querying database: {e}")

if __name__ == "__main__":
    check_section_types()
