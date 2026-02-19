"""
User 状态接口
GET  /api/user/status  — 从 femo_profile.db 读取当前 HP/等级
POST /api/user/status  — 前端手动同步状态（备用）
"""

from fastapi import APIRouter
from typing import Dict, Any

from app.db.helpers import get_profile_conn, get_user_hp, get_user_max_hp, ensure_auto_save
from contextlib import closing
import json

router = APIRouter()


@router.get("/status", response_model=Dict[str, Any])
def get_user_status():
    """
    返回玩家当前状态（从 femo_profile.db 读取）。
    前端启动时调用，获取真实 HP。
    """
    with get_profile_conn() as conn:
        ensure_auto_save(conn)
        # 统一从 game_saves 读取
        row = conn.execute(
            "SELECT hp, max_hp, level, exp, mia_mood FROM game_saves WHERE slot_id = 0"
        ).fetchone()

    if not row:
         return {"hp": 100, "maxHp": 100, "level": 1, "mood": "focused", "exp": 0}

    return {
        "hp":     row["hp"],
        "maxHp":  row["max_hp"],
        "level":  row["level"],
        "mood":   row["mia_mood"] or "focused",
        "exp":    row["exp"],
    }


@router.post("/save")
def save_game_progress(data: Dict[str, Any]):
    """
    保存游戏进度
    Payload: { "hp": 90, "max_hp": 100, "level": 2, "exp": 150, "completed_questions": ["q1", "q2"] }
    """
    hp = data.get("hp", 100)
    max_hp = data.get("max_hp", 100)
    level = data.get("level", 1)
    exp = data.get("exp", 0)
    current_paper_id = data.get("current_paper_id", "")
    mia_mood = data.get("mia_mood", "normal")
    
    # 将复杂结构存入 snapshot_json
    completed = data.get("completed_questions", [])
    snapshot = {
        "completed_questions": completed,
        "timestamp": 0 # TODO: add timestamp if needed
    }
    snapshot_json = json.dumps(snapshot)

    try:
        with get_profile_conn() as conn:
            ensure_auto_save(conn)
            # Update slot 0
            conn.execute("""
                UPDATE game_saves 
                SET hp=?, max_hp=?, level=?, exp=?, mia_mood=?, current_paper_id=?, snapshot_json=?, updated_at=datetime('now', 'localtime')
                WHERE slot_id=0
            """, (hp, max_hp, level, exp, mia_mood, current_paper_id, snapshot_json))
            conn.commit()
    except Exception as e:
        print(f"[user] Save failed: {e}")
        return {"success": False, "error": str(e)}

    return {"success": True}


@router.post("/load")  # 注意：前端可能用 POST /api/user/load ? 
# 之前的 E2E 脚本里写的是 GET /api/user/load，但任务描述里写 GET。
# 可是刚才的 e2e 脚本报错是 500。
# 检查一下 routes。Main.py 里 include user.router prefix /api/user
# e2e script step 2 sent GET /api/user/load.
# 但这里原来的 definition 是 @router.get("/load"). 
# Wait, let me check the original code I replaced. 
# It was @router.get("/load"). 
# So I should keep it as GET or change E2E? 
# Task says GET /api/user/load. So I stick to GET.

@router.get("/load", response_model=Dict[str, Any])
def load_game_progress():
    """
    读取游戏进度
    """
    with get_profile_conn() as conn:
        ensure_auto_save(conn)
        row = conn.execute("""
            SELECT hp, max_hp, level, exp, mia_mood, snapshot_json 
            FROM game_saves WHERE slot_id=0
        """).fetchone()
    
    if not row:
        return {
            "hp": 100, "max_hp": 100, "level": 1, "exp": 0, 
            "completed_questions": [], "user_id": "femo",
            "mia_mood": "normal"
        }

    completed = []
    if row["snapshot_json"]:
        try:
            snap = json.loads(row["snapshot_json"])
            completed = snap.get("completed_questions", [])
        except:
            pass

    return {
        "hp": row["hp"],
        "max_hp": row["max_hp"],
        "level": row["level"],
        "exp": row["exp"],
        "completed_questions": completed,
        "user_id": "femo",
        "mia_mood": row["mia_mood"]
    }
