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
            snapshot_json TEXT,  -- JSON
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
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
