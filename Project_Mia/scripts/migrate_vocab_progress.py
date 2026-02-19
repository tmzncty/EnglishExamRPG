"""
migrate_vocab_progress.py — 阶段 2.9 任务 4: 旧进度迁移
==========================================================
将 VocabWeb/user_vocab.db 中的 learning_records (SM-2 数据)
迁移到 Project_Mia/backend/data/femo_profile.db 的 vocab_progress 表。

旧表结构 (learning_records):
  id, word_id, sentence_id, is_correct, repetition,
  easiness_factor, interval, next_review, last_review,
  consecutive_correct, mistake_count

需要通过 word_id → vocabulary.word 解析出实际单词。

Usage:
    python scripts/migrate_vocab_progress.py
"""

import sqlite3
from pathlib import Path
from datetime import datetime

# --- 路径 ---
OLD_DB = Path(r"F:\sanity_check_avg\VocabWeb\user_vocab.db")
NEW_DB = Path(__file__).resolve().parent.parent / "backend" / "data" / "femo_profile.db"

# --- 颜色 ---
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def main():
    print(f"\n{BOLD}{CYAN}{'='*60}")
    print(f"  🔄 Project_Mia — Vocab Progress Migration")
    print(f"{'='*60}{RESET}\n")

    if not OLD_DB.exists():
        print(f"  {YELLOW}[SKIP] Old database not found: {OLD_DB}{RESET}")
        print(f"  Starting fresh with no prior progress.\n")
        return

    # --- 读取旧数据 ---
    old_conn = sqlite3.connect(str(OLD_DB))
    old_cur = old_conn.cursor()

    # 获取 word_id → word 映射
    old_cur.execute("SELECT id, word FROM vocabulary")
    word_map = {row[0]: row[1] for row in old_cur.fetchall()}

    # 获取学习记录
    old_cur.execute("""
        SELECT word_id, repetition, easiness_factor, interval,
               next_review, last_review, consecutive_correct, is_mistake
        FROM learning_records
    """)
    records = old_cur.fetchall()
    old_conn.close()

    print(f"  Old records found: {len(records)}")
    print(f"  Word mapping size: {len(word_map)}")

    if not records:
        print(f"  {YELLOW}No records to migrate.{RESET}\n")
        return

    # --- 写入新数据库 ---
    new_conn = sqlite3.connect(str(NEW_DB))
    new_cur = new_conn.cursor()

    # 确保表存在
    new_cur.execute("""
        CREATE TABLE IF NOT EXISTS vocab_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word VARCHAR(50) UNIQUE NOT NULL,
            repetition INTEGER DEFAULT 0,
            easiness_factor REAL DEFAULT 2.5,
            interval INTEGER DEFAULT 0,
            next_review TIMESTAMP,
            last_review TIMESTAMP,
            mistake_count INTEGER DEFAULT 0,
            consecutive_correct INTEGER DEFAULT 0,
            is_in_mistake_book BOOLEAN DEFAULT 0,
            total_reviews INTEGER DEFAULT 0,
            correct_reviews INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    new_cur.execute("CREATE INDEX IF NOT EXISTS ix_vocab_progress_word ON vocab_progress(word)")

    migrated = 0
    skipped = 0
    errors = 0

    for word_id, rep, ef, interval, next_rev, last_rev, consec_correct, is_mistake in records:
        word = word_map.get(word_id)
        if not word:
            skipped += 1
            continue

        try:
            # 计算 total_reviews 和 correct_reviews (近似)
            total_reviews = rep if rep else 0
            correct_reviews = consec_correct if consec_correct else 0
            is_mistake_val = 1 if is_mistake else 0

            new_cur.execute("""
                INSERT INTO vocab_progress
                    (word, repetition, easiness_factor, interval,
                     next_review, last_review, mistake_count,
                     consecutive_correct, is_in_mistake_book,
                     total_reviews, correct_reviews)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(word) DO UPDATE SET
                    repetition = excluded.repetition,
                    easiness_factor = excluded.easiness_factor,
                    interval = excluded.interval,
                    next_review = excluded.next_review,
                    last_review = excluded.last_review,
                    mistake_count = excluded.mistake_count,
                    consecutive_correct = excluded.consecutive_correct,
                    is_in_mistake_book = excluded.is_in_mistake_book,
                    total_reviews = excluded.total_reviews,
                    correct_reviews = excluded.correct_reviews,
                    updated_at = CURRENT_TIMESTAMP
            """, (word, rep, ef, interval, next_rev, last_rev,
                  0, consec_correct or 0, is_mistake_val,
                  total_reviews, correct_reviews))
            migrated += 1
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"  {RED}[ERROR] {word}: {e}{RESET}")

    new_conn.commit()
    new_conn.close()

    # --- 报告 ---
    print(f"\n{BOLD}  📊 Migration Summary{RESET}")
    print(f"  {'─'*40}")
    print(f"  Migrated:  {GREEN}{migrated}{RESET}")
    print(f"  Skipped:   {skipped}")
    print(f"  Errors:    {RED if errors else GREEN}{errors}{RESET}")

    if errors == 0:
        print(f"\n  {GREEN}{BOLD}✅ Progress migration complete!{RESET}\n")
    else:
        print(f"\n  {YELLOW}⚠ Migration completed with {errors} errors.{RESET}\n")


if __name__ == "__main__":
    main()
