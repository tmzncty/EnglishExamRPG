import sqlite3
import os
from pathlib import Path

BASE_DIR = Path("f:/sanity_check_avg/Project_Mia/backend").resolve()
DATA_DIR = BASE_DIR / "data"
PROFILE_DB = DATA_DIR / "femo_profile.db"
STATIC_DB = DATA_DIR / "static_content.db"

def seed_db():
    print("🌱 Seeding DB for Testing...")
    
    # 1. Create exam_history table if missing
    conn = sqlite3.connect(PROFILE_DB, timeout=20.0)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS exam_history (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        q_id TEXT NOT NULL,
        user_answer TEXT,
        is_correct BOOLEAN,
        score REAL,
        max_score REAL,
        time_spent INTEGER,
        attempt_count INTEGER DEFAULT 1,
        ai_feedback TEXT,
        weak_words_detected TEXT,  -- JSON
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Check if we have data for our test q_id
    q_id = "2023-eng1-writing-partB"
    row = conn.execute("SELECT log_id FROM exam_history WHERE q_id = ?", (q_id,)).fetchone()
    if not row:
        print(f"Adding mock exam history for {q_id}...")
        conn.execute("""
            INSERT INTO exam_history (q_id, user_answer, is_correct, score, max_score, ai_feedback)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (q_id, "这是我的测试作文，写的很烂但我想知道怎么改。", False, 5.5, 20.0, "作文跑题，词汇贫乏，建议重写喵！"))
        conn.commit()
    else:
        print(f"Exam history for {q_id} already exists.")
    conn.close()

    # 2. Add image to static db question (mocking it)
    conn = sqlite3.connect(STATIC_DB, timeout=20.0)
    # Ensure correct question exists or update it
    # First check if q_id exists
    row = conn.execute("SELECT q_id FROM questions WHERE q_id = ?", (q_id,)).fetchone()
    mock_img = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    
    if not row:
        print(f"Adding mock question {q_id}...")
        conn.execute("""
            INSERT INTO questions (q_id, paper_id, q_type, content, image_base64)
            VALUES (?, ?, ?, ?, ?)
        """, (q_id, "2023-eng1", "writing", "Write an essay based on the chart.", mock_img))
    else:
        print(f"Updating image for {q_id}...")
        conn.execute("UPDATE questions SET image_base64 = ? WHERE q_id = ?", (mock_img, q_id))
    
    conn.commit()
    conn.close()
    
    print("✅ Seeding Complete.")

if __name__ == "__main__":
    seed_db()
