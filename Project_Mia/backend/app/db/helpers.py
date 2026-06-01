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
    
    # ── [Stage 31.0] exam_attempts 表 ──────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS exam_attempts (
            attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id INTEGER DEFAULT 0,
            paper_id TEXT NOT NULL,
            attempt_number INTEGER DEFAULT 1,
            status TEXT DEFAULT 'in_progress',
            total_time INTEGER DEFAULT 0,
            total_score REAL DEFAULT 0,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            finished_at TIMESTAMP
        )
    """)

    # ── [Stage 31.0] user_answers 表 (带 attempt_id) ─────────────────────
    # 新表定义 — 允许同一 slot+q_id 有多条记录（不同 attempt）
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id INTEGER,
            slot_id INTEGER DEFAULT 0,
            q_id TEXT NOT NULL,
            section_type TEXT,
            user_answer TEXT,
            score REAL,
            is_correct BOOLEAN,
            ai_feedback TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── [Stage 31.0] user_answers 表重建迁移 ────────────────────────────
    # 如果旧表还带有 UNIQUE(slot_id, q_id) 约束，必须重建去掉它
    try:
        cursor = conn.execute("PRAGMA table_info(user_answers)")
        columns = [col["name"] for col in cursor.fetchall()]

        needs_rebuild = "attempt_id" not in columns
        if not needs_rebuild:
            # 检查是否还残留旧的 UNIQUE(slot_id, q_id) 约束
            idx_cursor = conn.execute("PRAGMA index_list(user_answers)")
            for idx in idx_cursor.fetchall():
                idx_info = conn.execute(f"PRAGMA index_info({idx['name']})").fetchall()
                col_names = [c["name"] for c in idx_info]
                if "slot_id" in col_names and "q_id" in col_names and "attempt_id" not in col_names:
                    needs_rebuild = True
                    break

        if needs_rebuild:
            print("[helpers] [Stage 31.0] Rebuilding user_answers table (adding attempt_id, removing old UNIQUE)...")
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_answers_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        attempt_id INTEGER,
                        slot_id INTEGER DEFAULT 0,
                        q_id TEXT NOT NULL,
                        section_type TEXT,
                        user_answer TEXT,
                        score REAL,
                        is_correct BOOLEAN,
                        ai_feedback TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 迁移旧数据 — 动态构建列映射
                if "attempt_id" in columns:
                    conn.execute("INSERT OR IGNORE INTO user_answers_new SELECT * FROM user_answers")
                else:
                    # 旧表无 attempt_id，填 NULL
                    old_cols = "id, slot_id, q_id, section_type, user_answer, score, is_correct, ai_feedback, updated_at"
                    conn.execute(f"""
                        INSERT OR IGNORE INTO user_answers_new
                        (id, attempt_id, slot_id, q_id, section_type, user_answer, score, is_correct, ai_feedback, updated_at)
                        SELECT id, NULL, slot_id, q_id, section_type, user_answer, score, is_correct, ai_feedback, updated_at
                        FROM user_answers
                    """)

                conn.execute("DROP TABLE user_answers")
                conn.execute("ALTER TABLE user_answers_new RENAME TO user_answers")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_user_answers_attempt_q ON user_answers(attempt_id, q_id)")
                conn.commit()
                print("[helpers] [Stage 31.0] user_answers rebuild complete!")
            except Exception as e:
                print(f"[helpers] [Stage 31.0] user_answers rebuild failed: {e}")
                import traceback; traceback.print_exc()
        else:
            # 确保索引存在
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_answers_attempt_q ON user_answers(attempt_id, q_id)")
            conn.commit()
    except Exception as e:
        print(f"[helpers] [Stage 31.0] user_answers migration check failed: {e}")

    # ── [Stage 31.0] attempt_question_times 表 ──────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS attempt_question_times (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id INTEGER NOT NULL,
            q_id TEXT NOT NULL,
            time_spent INTEGER DEFAULT 0,
            UNIQUE(attempt_id, q_id)
        )
    """)

    # ── [Stage 31.0] vocab_sessions 表 ──────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vocab_sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id INTEGER DEFAULT 0,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            finished_at TIMESTAMP,
            total_time INTEGER DEFAULT 0,
            words_learned INTEGER DEFAULT 0,
            words_reviewed INTEGER DEFAULT 0
        )
    """)

    # ── [Stage 31.0] vocab_session_words 表 ─────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vocab_session_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            word TEXT NOT NULL,
            action TEXT DEFAULT 'learn',
            time_spent INTEGER DEFAULT 0,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── [Stage 31.0] conversations 表迁移: 添加 attempt_id + word_id ────
    try:
        cursor = conn.execute("PRAGMA table_info(conversations)")
        conv_columns = [col["name"] for col in cursor.fetchall()]
        if conv_columns:  # 表存在才迁移
            if "attempt_id" not in conv_columns:
                print("[helpers] [Stage 31.0] Migrating conversations: Adding attempt_id...")
                conn.execute("ALTER TABLE conversations ADD COLUMN attempt_id INTEGER")
                conn.commit()
            if "word_id" not in conv_columns:
                print("[helpers] [Stage 31.0] Migrating conversations: Adding word_id...")
                conn.execute("ALTER TABLE conversations ADD COLUMN word_id TEXT")
                conn.commit()
    except Exception as e:
        print(f"[helpers] [Stage 31.0] conversations migration failed: {e}")

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

    # [Stage 30.0] Migrations for Check-in & Time Engine
    try:
        cursor = conn.execute("PRAGMA table_info(game_saves)")
        columns = [col["name"] for col in cursor.fetchall()]

        if "daily_streak" not in columns:
            try:
                conn.execute("ALTER TABLE game_saves ADD COLUMN daily_streak INTEGER DEFAULT 0")
                conn.commit()
            except Exception as e:
                print(f"[helpers] Migration failed for daily_streak: {e}")
                
        if "last_goal_met_date" not in columns:
            try:
                conn.execute("ALTER TABLE game_saves ADD COLUMN last_goal_met_date TEXT DEFAULT ''")
                conn.commit()
            except Exception as e:
                print(f"[helpers] Migration failed for last_goal_met_date: {e}")

        if "today_focus_time" not in columns:
            try:
                conn.execute("ALTER TABLE game_saves ADD COLUMN today_focus_time INTEGER DEFAULT 0")
                conn.commit()
            except Exception as e:
                print(f"[helpers] Migration failed for today_focus_time: {e}")

    except Exception as e:
        print(f"[helpers] Schema check failed for game_saves 30.0 columns: {e}")

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
