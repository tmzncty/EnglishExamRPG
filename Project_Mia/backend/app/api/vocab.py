from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json
from pathlib import Path

from app.db.helpers import get_profile_conn, ensure_auto_save, update_user_hp

router = APIRouter()

# Load Vocab Data (One-time load or Lazy load)
VOCAB_DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "exam_vocabulary.json"
VOCAB_DB = {}

def load_vocab_data():
    global VOCAB_DB
    if not VOCAB_DB and VOCAB_DATA_PATH.exists():
        try:
            with open(VOCAB_DATA_PATH, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                # Convert list to dict keyed by word if necessary
                if isinstance(raw_data, list):
                    for item in raw_data:
                        if "word" in item:
                            VOCAB_DB[item["word"]] = item
                elif isinstance(raw_data, dict):
                    VOCAB_DB = raw_data
                    
            print(f"[vocab] Loaded {len(VOCAB_DB)} words from {VOCAB_DATA_PATH}")
        except Exception as e:
            print(f"[vocab] Failed to load data: {e}")

load_vocab_data()

@router.get("/today")
def get_todays_vocab(slot_id: int = 0):
    """
    [Stage 16.0] 获取今日单词任务 (SuperMemo 2 logic simplified)
    1. Pending Reviews: next_review_date <= today
    2. New Words: if Pending count < limit
    """
    load_vocab_data() # Ensure loaded
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    review_words = []
    new_words = []
    
    with get_profile_conn() as conn:
        ensure_auto_save(conn)
        
        # 1. Get Due Reviews
        rows = conn.execute("""
            SELECT word, easiness_factor, interval, repetitions 
            FROM user_vocab_memory
            WHERE slot_id = ? AND next_review_date <= ?
            ORDER BY next_review_date ASC
            LIMIT 20
        """, (slot_id, today_str)).fetchall()
        
        for r in rows:
            word_info = VOCAB_DB.get(r["word"], {"word": r["word"], "definition": "Unknown"})
            review_words.append({
                **word_info, 
                "type": "review",
                "memory": {
                    "ef": r["easiness_factor"],
                    "interval": r["interval"],
                    "reps": r["repetitions"]
                }
            })
            
        # 2. Get New Words — respect per-slot daily_new_words_limit
        # Fetch limit from DB (default 30)
        limit_row = conn.execute(
            "SELECT daily_new_words_limit FROM game_saves WHERE slot_id=?", (slot_id,)
        ).fetchone()
        daily_limit = limit_row["daily_new_words_limit"] if limit_row and limit_row["daily_new_words_limit"] else 30
        
        if len(review_words) < 50:  # Only fetch new words when not already overwhelmed
            existing = {r["word"] for r in conn.execute("SELECT word FROM user_vocab_memory WHERE slot_id=?", (slot_id,)).fetchall()}
            
            count = 0
            for word, data in VOCAB_DB.items():
                if word not in existing:
                    new_words.append({**data, "type": "new"})
                    count += 1
                    if count >= daily_limit: # Respect per-slot daily limit
                        break
    
    return {
        "date": today_str,
        "tasks": review_words + new_words,
        "total_count": len(review_words) + len(new_words)
    }

@router.post("/review")
def submit_review(data: Dict[str, Any]):
    """
    提交单词复习结果
    Payload: { "slot_id": 0, "word": "apple", "quality": 0-5 }
    Returns: { "next_review": "YYYY-MM-DD", "hp_reward": 0.5, "exp_reward": 2 }
    """
    slot_id = data.get("slot_id", 0)
    word = data.get("word")
    quality = data.get("quality", 0) # 0-5
    
    # SM2 Algorithm
    # Ref: https://super-memory.com/english/ol/sm2.htm
    
    today = datetime.now().date()
    
    with get_profile_conn() as conn:
        ensure_auto_save(conn)
        
        # Get existing state
        row = conn.execute(
            "SELECT easiness_factor, interval, repetitions FROM user_vocab_memory WHERE slot_id=? AND word=?",
            (slot_id, word)
        ).fetchone()
        
        if row:
            ef = row["easiness_factor"]
            interval = row["interval"]
            reps = row["repetitions"]
        else:
            # First time logic
            ef = 2.5
            interval = 0
            reps = 0
            
        # Update Logic
        if quality >= 3:
            if reps == 0:
                interval = 1
            elif reps == 1:
                interval = 6
            else:
                interval = int(interval * ef)
            
            reps += 1
            # EF update
            ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            if ef < 1.3: ef = 1.3
        else:
            reps = 0
            interval = 1
        
        next_date = today + timedelta(days=interval)
        next_date_str = next_date.strftime("%Y-%m-%d")
        
        # Save to DB
        conn.execute("""
            INSERT OR REPLACE INTO user_vocab_memory 
            (slot_id, word, easiness_factor, interval, repetitions, next_review_date, last_review_date, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
        """, (slot_id, word, ef, interval, reps, next_date_str, today.strftime("%Y-%m-%d")))
        
        # Reward Logic
        # > 3 means "remembered", give reward
        reward = {"hp": 0, "exp": 0}
        if quality >= 3:
            # +0.5 HP, +2 EXP
            # Update HP directly? Or just return? 
            # The prompt says: "Automatically give slot_id +0.5 HP and +2 EXP"
            
            # Fetch current stats
            user_row = conn.execute("SELECT hp, max_hp, exp, level FROM game_saves WHERE slot_id=?", (slot_id,)).fetchone()
            if user_row:
                cur_hp = user_row["hp"]
                max_hp = user_row["max_hp"]
                cur_exp = user_row["exp"]
                cur_level = user_row["level"]
                
                new_hp = min(float(max_hp), float(cur_hp) + 0.5) 
                
                new_exp = cur_exp + 2
                
                # Check level up (Gentle logic again)
                needed_exp = cur_level * 100
                leveled_up = False
                if new_exp >= needed_exp:
                    new_exp -= needed_exp
                    cur_level += 1
                    new_hp = max_hp
                    leveled_up = True
                    print(f"[vocab] Slot {slot_id} Level Up via Vocab!")
                
                conn.execute("""
                    UPDATE game_saves SET hp=?, exp=?, level=? WHERE slot_id=?
                """, (new_hp, new_exp, cur_level, slot_id))
                
                reward = {"hp": 0.5, "exp": 2, "leveled_up": leveled_up}
        
        conn.commit()

    return {
        "success": True,
        "word": word,
        "next_review": next_date_str,
        "reward": reward
    }


@router.post("/explain")
async def explain_word(data: Dict[str, Any]):
    """
    [Stage 17.0] Mia AI 单词讲解（带 DB 缓存）
    Payload: { "word": "ability" }
    First checks vocab_ai_cache; calls LLM on miss and persists result.
    """
    word = data.get("word", "").strip()
    if not word:
        return {"success": False, "error": "word is required"}

    # 1. Cache Hit Check
    with get_profile_conn() as conn:
        ensure_auto_save(conn)
        row = conn.execute(
            "SELECT ai_explanation FROM vocab_ai_cache WHERE word=?", (word,)
        ).fetchone()
        if row:
            print(f"[vocab] Cache HIT for '{word}'")
            return {"success": True, "word": word, "explanation": row["ai_explanation"], "cached": True}

    # 2. Cache Miss — call LLM
    print(f"[vocab] Cache MISS for '{word}' — calling LLM...")
    from app.services.llm_service import llm_service
    explanation = await llm_service.explain_vocab_word(word)

    # 3. Persist to Cache
    try:
        with get_profile_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO vocab_ai_cache (word, ai_explanation, updated_at) VALUES (?, ?, datetime('now', 'localtime'))",
                (word, explanation)
            )
            conn.commit()
            print(f"[vocab] Cached explanation for '{word}'")
    except Exception as e:
        print(f"[vocab] Cache write failed: {e}")

    return {"success": True, "word": word, "explanation": explanation, "cached": False}
