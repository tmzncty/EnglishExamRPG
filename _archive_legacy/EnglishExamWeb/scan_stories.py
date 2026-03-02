import sqlite3

def scan_2010_stories():
    try:
        conn = sqlite3.connect('story_content.db')
        c = conn.cursor()
        
        c.execute("PRAGMA table_info(stories)")
        cols = c.fetchall()
        print("Column Types:")
        for col in cols:
             print(f"  {col[1]}: {col[2]}") # Name, Type

        print("Scaning stories for Year 2010...")
        c.execute("SELECT q_id, section_type FROM stories WHERE year=2010")
        rows = c.fetchall()
        
        if not rows:
            print("No stories found for 2010!")
        else:
            print(f"Found {len(rows)} stories for 2010.")
            print("First 10 IDs:")
            for r in rows[:10]:
                print(f"  ID: {r[0]}, Type: {r[1]}")
                
            # Check specifically for ID 3
            ids = [r[0] for r in rows]
            if 3 in ids:
                print("\n✅ ID 3 exists!")
                # Print details for ID 3
                c.execute("SELECT * FROM stories WHERE year=2010 AND q_id=3")
                print(f"Details for ID 3: {c.fetchone()}")
            else:
                print("\n❌ ID 3 does NOT exist.")
                print(f"Available IDs (first 20): {sorted(ids)[:20]}")

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    scan_2010_stories()
