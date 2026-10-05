"""Legacy manual seed helper for local testing.

Important: test rows live under a dedicated `exam_type=Test` paper and must never be
inserted into an official English I paper.
"""

from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROFILE_DB = DATA_DIR / "femo_profile.db"
STATIC_DB = DATA_DIR / "static_content.db"
TEST_PAPER_ID = "test_paper_2026"
TEST_Q_ID = "test_essay_1"


def seed_db() -> None:
    print("🌱 Seeding DB for testing...")

    conn = sqlite3.connect(PROFILE_DB, timeout=20.0)
    conn.execute(
        """
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
            weak_words_detected TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    if not conn.execute("SELECT 1 FROM exam_history WHERE q_id=?", (TEST_Q_ID,)).fetchone():
        conn.execute(
            """
            INSERT INTO exam_history (q_id, user_answer, is_correct, score, max_score, ai_feedback)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (TEST_Q_ID, "这是测试作文。", False, 5.5, 20.0, "测试反馈"),
        )
    conn.commit()
    conn.close()

    conn = sqlite3.connect(STATIC_DB, timeout=20.0)
    conn.execute(
        """
        INSERT OR REPLACE INTO papers (paper_id, year, exam_type, title, total_score, time_limit)
        VALUES (?, 2026, 'Test', 'Local Test Fixture', 20, 30)
        """,
        (TEST_PAPER_ID,),
    )
    mock_img = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    conn.execute(
        """
        INSERT OR REPLACE INTO questions
        (q_id, paper_id, q_type, section_type, section_name, question_number, content, image_base64, score)
        VALUES (?, ?, 'writing', 'writing_b', 'Test Writing', 52, 'Write a test essay.', ?, 20)
        """,
        (TEST_Q_ID, TEST_PAPER_ID, mock_img),
    )
    conn.commit()
    conn.close()

    print("✅ Test seed complete; official exam papers were not modified.")


if __name__ == "__main__":
    seed_db()
