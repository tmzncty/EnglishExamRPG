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
def get_user_status(slot_id: int = 0):
    """
    返回玩家当前状态（从 femo_profile.db 读取）。
    前端启动时调用，获取真实 HP。
    """
    with get_profile_conn() as conn:
        ensure_auto_save(conn)
        # 统一从 game_saves 读取
        row = conn.execute(
            "SELECT hp, max_hp, level, exp, mia_mood FROM game_saves WHERE slot_id = ?",
            (slot_id,)
        ).fetchone()

    if not row:
         # 尝试初始化该 slot (fallback)
         try:
             conn.execute("INSERT OR IGNORE INTO game_saves (slot_id) VALUES (?)", (slot_id,))
             conn.commit()
         except:
             pass
         return {"hp": 100, "maxHp": 100, "level": 1, "mood": "focused", "exp": 0}

    return {
        "hp":     row["hp"],
        "maxHp":  row["max_hp"],
        "level":  row["level"],
        "mood":   row["mia_mood"] or "focused",
        "exp":    row["exp"],
    }


@router.get("/slots")
def get_user_slots():
    """
    [Stage 15.0] 获取所有可用存档
    """
    slots = []
    try:
        with get_profile_conn() as conn:
            ensure_auto_save(conn)
            rows = conn.execute("SELECT slot_id, hp, level, updated_at FROM game_saves ORDER BY slot_id ASC").fetchall()
            for r in rows:
                slots.append({
                    "slot_id": r["slot_id"],
                    "summary": f"Lv.{r['level']} HP:{r['hp']}",
                    "updated_at": r["updated_at"]
                })
    except Exception as e:
        print(f"[user] Get slots failed: {e}")
    
    # 确保至少有 Slot 0
    if not any(s["slot_id"] == 0 for s in slots):
        slots.insert(0, {"slot_id": 0, "summary": "New Game", "updated_at": ""})
        
    return slots


@router.post("/slots/new")
def create_new_slot():
    """
    [Stage 16.0] 创建新存档
    自动寻找当前最大 slot_id + 1，初始化状态
    """
    new_slot_id = 0
    try:
        with get_profile_conn() as conn:
            ensure_auto_save(conn)
            # Find max slot_id
            row = conn.execute("SELECT MAX(slot_id) as max_id FROM game_saves").fetchone()
            if row and row["max_id"] is not None:
                new_slot_id = row["max_id"] + 1
            
            # Create new slot
            conn.execute("""
                INSERT INTO game_saves (slot_id, hp, max_hp, level, exp, mia_mood)
                VALUES (?, 100, 100, 1, 0, 'normal')
            """, (new_slot_id,))
            conn.commit()
            print(f"[user] Created new slot: {new_slot_id}")
    except Exception as e:
        print(f"[user] Create slot failed: {e}")
        return {"success": False, "error": str(e)}

    return {"success": True, "slot_id": new_slot_id}


@router.post("/save")
def save_game_progress(data: Dict[str, Any]):
    """
    保存游戏进度 [Stage 16.0 Updated: Leveling System]
    Payload: { "slot_id": 0, "hp": 90, ... }
    """
    slot_id = data.get("slot_id", 0)
    current_hp = data.get("hp", 100) # Use different var name to avoid confusion
    max_hp = data.get("max_hp", 100)
    level = data.get("level", 1)
    exp = data.get("exp", 0)
    current_paper_id = data.get("current_paper_id", "")
    mia_mood = data.get("mia_mood", "normal")
    
    # [Stage 16.0] Level Up Logic
    # Next Level EXP = Level * 100
    # Loop to handle multiple level ups at once (if massive EXP gain)
    leveled_up = False
    while True:
        needed_exp = level * 100
        if exp >= needed_exp:
            exp -= needed_exp
            level += 1
            current_hp = max_hp # Heal on level up
            leveled_up = True
            print(f"[user] Slot {slot_id} Leveled Up! Lv.{level}, HP Restored.")
        else:
            break
            
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
            
            # 确保 Slot 存在
            conn.execute("INSERT OR IGNORE INTO game_saves (slot_id) VALUES (?)", (slot_id,))
            conn.commit()
            
            # Update
            conn.execute("""
                UPDATE game_saves 
                SET hp=?, max_hp=?, level=?, exp=?, mia_mood=?, current_paper_id=?, snapshot_json=?, updated_at=datetime('now', 'localtime')
                WHERE slot_id=?
            """, (current_hp, max_hp, level, exp, mia_mood, current_paper_id, snapshot_json, slot_id))
            conn.commit()
    except Exception as e:
        print(f"[user] Save failed: {e}")
        return {"success": False, "error": str(e)}

    return {
        "success": True, 
        "leveled_up": leveled_up, 
        "new_level": level, 
        "new_hp": current_hp,
        "new_exp": exp
    }


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
def load_game_progress(slot_id: int = 0):
    """
    读取游戏进度
    """
    with get_profile_conn() as conn:
        ensure_auto_save(conn)
        row = conn.execute("""
            SELECT hp, max_hp, level, exp, mia_mood, snapshot_json 
            FROM game_saves WHERE slot_id=?
        """, (slot_id,)).fetchone()
    
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
