import sqlite3
import os

def debug_query():
    db_path = 'story_content.db'
    if not os.path.exists(db_path):
        print("DB not found")
        return

    q_id = 3
    year = 2010
    is_correct = False
    
    # Logic from server.py
    field_cn = 'correct_cn' if is_correct else 'wrong_cn'
    field_en = 'correct_en' if is_correct else 'wrong_en'
    
    print(f"Querying: SELECT {field_cn}, {field_en} FROM stories WHERE q_id={q_id} AND year={year}")
    
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Exact query
        c.execute(f'SELECT {field_cn}, {field_en} FROM stories WHERE q_id=? AND year=?', (q_id, year))
        row = c.fetchone()
        
        if row:
            print("Row found!")
            print(f"CN: {row[0][:20]}...")
            print(f"EN: {row[1][:20]}...")
        else:
            print("Row NOT found (None returned)")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    debug_query()
