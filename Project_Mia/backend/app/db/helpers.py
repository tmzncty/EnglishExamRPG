"""
轻量级 SQLite 数据库 Helper
直接使用 sqlite3，不引入 ORM 重型依赖，与 FastAPI 依赖注入配合使用。

Author: Femo
Date: 2026-02-18
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Dict, List, Any

# 数据库文件路径
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

STATIC_DB = DATA_DIR / "static_content.db"
PROFILE_DB = DATA_DIR / "femo_profile.db"


def _dict_factory(cursor, row):
    """让 fetchone/fetchall 返回 dict 而不是 tuple"""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


@contextmanager
def get_static_conn():
    """获取只读静态内容数据库连接"""
    conn = sqlite3.connect(STATIC_DB, timeout=20.0)
    conn.row_factory = _dict_factory
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_profile_conn():
    """获取读写用户数据库连接"""
    conn = sqlite3.connect(PROFILE_DB, timeout=20.0)
    conn.row_factory = _dict_factory
    try:
        yield conn
    finally:
        conn.close()


# ---- 用户状态快捷读写 ----

# ---- 用户状态快捷读写 ----

def get_user_hp(conn: sqlite3.Connection) -> int:
    """读取当前 HP (从 game_saves 表的 auto-save slot_id=0)"""
    # 兼容性重构: 优先尝试 slot_id=0
    try:
        row = conn.execute(
            "SELECT hp FROM game_saves WHERE slot_id = 0"
        ).fetchone()
        return row["hp"] if row else 100
    except sqlite3.OperationalError:
        # Fallback for old schema if migration hasn't run (though we should migrate)
        return 100


def get_user_max_hp(conn: sqlite3.Connection) -> int:
    """读取最大 HP"""
    try:
        row = conn.execute(
            "SELECT max_hp FROM game_saves WHERE slot_id = 0"
        ).fetchone()
        return row["max_hp"] if row else 100
    except sqlite3.OperationalError:
        return 100


def update_user_hp(conn: sqlite3.Connection, new_hp: int):
    """更新当前 HP"""
    conn.execute(
        "UPDATE game_saves SET hp = ?, updated_at = datetime('now', 'localtime') WHERE slot_id = 0",
        (new_hp,),
    )
    conn.commit()


def ensure_auto_save(conn: sqlite3.Connection):
    """确保 slot_id=0 的自动存档存在 (严查 Schema)"""
    # 1. 创建表 (完全对齐 models.py)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS game_saves (
            save_id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id INTEGER UNIQUE,
            current_paper_id TEXT,
            current_q_index INTEGER DEFAULT 0,
            hp INTEGER DEFAULT 100,
            max_hp INTEGER DEFAULT 100,
            exp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            mia_mood TEXT DEFAULT 'normal',
            mia_affection INTEGER DEFAULT 50,
            daily_new_words_limit INTEGER DEFAULT 30, -- [Stage 17.0]
            slot_name TEXT DEFAULT 'Auto Save',       -- [Stage 20.0]
            daily_reset_time TEXT DEFAULT '04:00',     -- [Stage 20.0]
            snapshot_json TEXT,  -- JSON
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id INTEGER DEFAULT 0,
            q_id TEXT NOT NULL,
            section_type TEXT,
            user_answer TEXT,
            score REAL,
            is_correct BOOLEAN,
            ai_feedback TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(slot_id, q_id)
        )
    """)
    
    # [Stage 14.1 Fix] 确保 user_answers 表有 slot_id 字段 (Migration)
    try:
        # Check if slot_id exists
        cursor = conn.execute("PRAGMA table_info(user_answers)")
        columns = [col["name"] for col in cursor.fetchall()]
        if "slot_id" not in columns:
            print("[helpers] Migrating user_answers: Adding slot_id column...")
            try:
                # SQLite doesn't support ADD COLUMN + UNIQUE constraint easily in one go for existing,
                # but we just need the column for now.
                # However, the UNIQUE constraint index might need recreation. 
                # For simplicity in this hotfix, we add the column.
                conn.execute("ALTER TABLE user_answers ADD COLUMN slot_id INTEGER DEFAULT 0")
                
                # We might need to recreate the index/unique constraint, but SQLite ALTER TABLE is limited.
                # Let's trust that basic functionality works, or if critical, we recreate table.
                # Given 'UNIQUE(slot_id, q_id)' is in CREATE statement, it won't be enforcing for old table unless we recreate.
                # Let's recreate index manually to be safe.
                conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_user_answers_slot_q ON user_answers(slot_id, q_id)")
                conn.commit()
            except Exception as e:
                print(f"[helpers] Migration failed: {e}")
    except Exception as e:
        print(f"[helpers] Schema check failed: {e}")

    # [Stage 17.0] Migrations for daily_new_words_limit
    try:
        cursor = conn.execute("PRAGMA table_info(game_saves)")
        columns = [col["name"] for col in cursor.fetchall()]
        if "daily_new_words_limit" not in columns:
            print("[helpers] Migrating game_saves: Adding daily_new_words_limit column...")
            try:
                conn.execute("ALTER TABLE game_saves ADD COLUMN daily_new_words_limit INTEGER DEFAULT 30")
                conn.commit()
            except Exception as e:
                print(f"[helpers] Migration failed for daily_new_words_limit: {e}")
    except Exception as e:
        print(f"[helpers] Schema check failed for game_saves: {e}")

    # [Stage 20.0] Migrations for slot_name and daily_reset_time
    try:
        cursor = conn.execute("PRAGMA table_info(game_saves)")
        columns = [col["name"] for col in cursor.fetchall()]
        if "slot_name" not in columns:
            print("[helpers] Migrating game_saves: Adding slot_name column...")
            try:
                conn.execute("ALTER TABLE game_saves ADD COLUMN slot_name TEXT DEFAULT 'Auto Save'")
                conn.commit()
            except Exception as e:
                print(f"[helpers] Migration failed for slot_name: {e}")
        if "daily_reset_time" not in columns:
            print("[helpers] Migrating game_saves: Adding daily_reset_time column...")
            try:
                conn.execute("ALTER TABLE game_saves ADD COLUMN daily_reset_time TEXT DEFAULT '04:00'")
                conn.commit()
            except Exception as e:
                print(f"[helpers] Migration failed for daily_reset_time: {e}")
    except Exception as e:
        print(f"[helpers] Schema check failed for slot_name/daily_reset_time: {e}")

    # [Stage 17.0] Attempt History Logs (Replayability)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS answer_history_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id INTEGER DEFAULT 0,
            q_id TEXT NOT NULL,
            user_answer TEXT,
            score REAL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # [Stage 17.0] Vocab AI Cache Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vocab_ai_cache (
            word TEXT PRIMARY KEY,
            ai_explanation TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # [Stage 16.0 / 21.0] Vocab Memory Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_vocab_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id INTEGER DEFAULT 0,
            word TEXT NOT NULL,
            easiness_factor REAL DEFAULT 2.5,
            interval INTEGER DEFAULT 0,
            repetitions INTEGER DEFAULT 0,
            next_review_date TEXT, -- YYYY-MM-DD
            last_review_date TEXT,
            mastery_level INTEGER DEFAULT 0,       -- [Stage 21.0]
            success_streak INTEGER DEFAULT 0,      -- [Stage 21.0]
            total_recall_count INTEGER DEFAULT 0,  -- [Stage 21.0]
            total_error_count INTEGER DEFAULT 0,   -- [Stage 21.0]
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(slot_id, word)
        )
    """)

    # [Stage 21.0] Migrations for game_saves Session Progress
    try:
        cursor = conn.execute("PRAGMA table_info(game_saves)")
        columns = [col["name"] for col in cursor.fetchall()]

        if "today_learned_count" not in columns:
            try:
                conn.execute("ALTER TABLE game_saves ADD COLUMN today_learned_count INTEGER DEFAULT 0")
                conn.commit()
            except Exception as e:
                print(f"[helpers] Migration failed for today_learned_count: {e}")
                
        if "today_reviewed_count" not in columns:
            try:
                conn.execute("ALTER TABLE game_saves ADD COLUMN today_reviewed_count INTEGER DEFAULT 0")
                conn.commit()
            except Exception as e:
                print(f"[helpers] Migration failed for today_reviewed_count: {e}")

        if "last_reset_day" not in columns:
            try:
                conn.execute("ALTER TABLE game_saves ADD COLUMN last_reset_day TEXT DEFAULT ''")
                conn.commit()
            except Exception as e:
                print(f"[helpers] Migration failed for last_reset_day: {e}")

    except Exception as e:
        print(f"[helpers] Schema check failed for game_saves 21.0 columns: {e}")

    # [Stage 21.0] Migrations for user_vocab_memory Pro-Level SRS Schema
    try:
        cursor = conn.execute("PRAGMA table_info(user_vocab_memory)")
        columns = [col["name"] for col in cursor.fetchall()]

        new_vocab_cols = {
            "mastery_level": "INTEGER DEFAULT 0",
            "success_streak": "INTEGER DEFAULT 0",
            "total_recall_count": "INTEGER DEFAULT 0",
            "total_error_count": "INTEGER DEFAULT 0"
        }
        
        for col_name, col_def in new_vocab_cols.items():
            if col_name not in columns:
                print(f"[helpers] Migrating user_vocab_memory: Adding {col_name} column...")
                try:
                    conn.execute(f"ALTER TABLE user_vocab_memory ADD COLUMN {col_name} {col_def}")
                    conn.commit()
                except Exception as e:
                    print(f"[helpers] Migration failed for {col_name}: {e}")
                    
    except Exception as e:
        print(f"[helpers] Schema check failed for user_vocab_memory extensions: {e}")
    
    # 2. 检查 slot_id=0 是否存在
    try:
        row = conn.execute("SELECT save_id FROM game_saves WHERE slot_id = 0").fetchone()
        if not row:
            conn.execute("""
                INSERT OR IGNORE INTO game_saves 
                (slot_id, hp, max_hp, level, exp, mia_mood, mia_affection)
                VALUES (0, 100, 100, 1, 0, 'normal', 50)
            """)
            conn.commit()
    except sqlite3.OperationalError as e:
        print(f"[helpers] Schema Error confirm: {e}")
