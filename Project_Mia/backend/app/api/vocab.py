from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
import json

from app.db.helpers import get_profile_conn, get_static_conn, ensure_auto_save, update_user_hp

router = APIRouter()

# UTC+8 Timezone (硬编码，不依赖服务器本地时间)
UTC8 = timezone(timedelta(hours=8))

def parse_vocab_row(row: dict) -> dict:
    if not row:
        return {}
    return {
        "word": row.get("word", ""),
        "phonetic": row.get("phonetic", ""),
        "pos": row.get("pos", ""),
        "meanings": json.loads(row.get("meanings", "[]")) if row.get("meanings") else [],
        "sentences": json.loads(row.get("sentences", "[]")) if row.get("sentences") else []
    }

def get_logical_date(reset_time_str: str = "04:00") -> str:
    """
    [Stage 20.0] 根据 daily_reset_time 计算"逻辑日期"。
    强制使用 UTC+8 时区。
    如果当前时间早于 reset_time，则属于前一个逻辑日。
    """
    now_utc8 = datetime.now(UTC8)
    
    try:
        parts = reset_time_str.split(":")
        reset_hour = int(parts[0])
        reset_minute = int(parts[1]) if len(parts) > 1 else 0
    except (ValueError, IndexError):
        reset_hour, reset_minute = 4, 0  # Safe fallback

    reset_today = now_utc8.replace(hour=reset_hour, minute=reset_minute, second=0, microsecond=0)
    
    if now_utc8 < reset_today:
        # 当前时间早于刷新时间 → 归属前一个逻辑日
        logical_date = (now_utc8 - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        logical_date = now_utc8.strftime("%Y-%m-%d")
    
    return logical_date


@router.get("/today")
def get_todays_vocab(slot_id: int = 0):
    """
    [Stage 16.0 / 20.0] 获取今日单词任务 (SuperMemo 2 logic simplified)
    1. Pending Reviews: next_review_date <= logical_today
    2. New Words: if Pending count < limit
    
    [Stage 23.0] Completely moved to SQLite (static_content.db) for Vocab source of truth.
    """
    review_words = []
    new_words = []
    
    with get_profile_conn() as conn, get_static_conn() as static_conn:
        ensure_auto_save(conn)
        
        # Fetch slot settings for reset time and daily limit
        slot_row = conn.execute(
            "SELECT daily_new_words_limit, daily_reset_time FROM game_saves WHERE slot_id=?", (slot_id,)
        ).fetchone()
        
        daily_limit = 30
        reset_time = "04:00"
        if slot_row:
            daily_limit = slot_row.get("daily_new_words_limit") or 30
            reset_time = slot_row.get("daily_reset_time") or "04:00"
        
        # Calculate logical date using UTC+8 + reset_time
        today_str = get_logical_date(reset_time)
        
        # 1. Get Due Reviews
        rows = conn.execute("""
            SELECT word, easiness_factor, interval, repetitions 
            FROM user_vocab_memory
            WHERE slot_id = ? AND next_review_date <= ?
            ORDER BY next_review_date ASC
            LIMIT 20
        """, (slot_id, today_str)).fetchall()
        
        for r in rows:
            static_row = static_conn.execute("SELECT * FROM vocabulary WHERE word=?", (r["word"],)).fetchone()
            word_info = parse_vocab_row(static_row) if static_row else {"word": r["word"], "definition": "Unknown"}
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
        if len(review_words) < 50:  # Only fetch new words when not already overwhelmed
            existing = {r["word"] for r in conn.execute("SELECT word FROM user_vocab_memory WHERE slot_id=?", (slot_id,)).fetchall()}
            
            # Fetch all vocabulary words, prioritize ones with sentences
            all_static_words = static_conn.execute("SELECT word, sentences FROM vocabulary").fetchall()
            
            # Separate into words with sentences and without sentences
            words_with_sentences = [w["word"] for w in all_static_words if w["sentences"] != "[]" and w["sentences"]]
            words_without_sentences = [w["word"] for w in all_static_words if w["sentences"] == "[]" or not w["sentences"]]
            
            import random
            random.seed(f"slot_{slot_id}_{today_str}")
            
            # Shuffle both lists stably
            random.shuffle(words_with_sentences)
            random.shuffle(words_without_sentences)
            
            # Combine them, prioritizing those with sentences
            shuffled_keys = words_with_sentences + words_without_sentences
            
            random.seed() # reset seed
            
            count = 0
            for word in shuffled_keys:
                if word not in existing:
                    static_row = static_conn.execute("SELECT * FROM vocabulary WHERE word=?", (word,)).fetchone()
                    data = parse_vocab_row(static_row)
                    new_words.append({**data, "type": "new"})
                    count += 1
                    if count >= daily_limit: # Respect per-slot daily limit
                        break
    
    return {
        "date": today_str,
        "daily_limit": daily_limit,
        "tasks": review_words + new_words,
        "review_count": len(review_words),
        "new_count": len(new_words),
        "total_count": len(review_words) + len(new_words)
    }

@router.post("/review")
def submit_review(data: Dict[str, Any]):
    """
    [Stage 21.0] 深度复习与进度结算
    """
    slot_id = data.get("slot_id", 0)
    word = data.get("word")
    quality = data.get("quality", 0) # 0-5
    
    now_utc8 = datetime.now(UTC8)
    today = now_utc8.date()
    
    with get_profile_conn() as conn:
        ensure_auto_save(conn)
        
        row = conn.execute(
            "SELECT easiness_factor, interval, repetitions, mastery_level, success_streak, total_recall_count, total_error_count FROM user_vocab_memory WHERE slot_id=? AND word=?",
            (slot_id, word)
        ).fetchone()
        
        if row:
            ef = row["easiness_factor"]
            interval = row["interval"]
            reps = row["repetitions"]
            mastery_level = row["mastery_level"]
            success_streak = row["success_streak"]
            total_recall_count = row["total_recall_count"]
            total_error_count = row["total_error_count"]
        else:
            ef = 2.5
            interval = 0
            reps = 0
            mastery_level = 0
            success_streak = 0
            total_recall_count = 0
            total_error_count = 0
            
        reward = {"hp": 0, "exp": 0, "leveled_up": False}
        is_success = quality >= 3
            
        if is_success:
            if reps == 0:
                interval = 1
            elif reps == 1:
                interval = 6
            else:
                interval = int(interval * ef)
            
            reps += 1
            ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            if ef < 1.3: ef = 1.3
            
            # [Stage 21.0] Pro-level SRS Update
            success_streak += 1
            total_recall_count += 1
            
            # Update mastery_level (cap at 7)
            if success_streak >= 5 and interval >= 14:
                mastery_level = min(7, mastery_level + 1)
                
            # Reward: 2 EXP Base + Streak Bonus (max +5)
            streak_bonus = min(5, success_streak // 2)
            exp_gain = 2 + streak_bonus
            reward["exp"] = exp_gain
            
        else:
            reps = 0
            interval = 1
            # [Stage 21.0] Punishment logic
            success_streak = 0
            total_error_count += 1
            mastery_level = max(0, mastery_level - 1)
            
            # Damage HP
            reward["hp"] = -5 # Fixed damage for mistake
            
        next_date = today + timedelta(days=interval)
        next_date_str = next_date.strftime("%Y-%m-%d")
        
        # Save to user_vocab_memory
        conn.execute("""
            INSERT OR REPLACE INTO user_vocab_memory 
            (slot_id, word, easiness_factor, interval, repetitions, next_review_date, last_review_date, 
             mastery_level, success_streak, total_recall_count, total_error_count, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
        """, (slot_id, word, ef, interval, reps, next_date_str, today.strftime("%Y-%m-%d"), 
              mastery_level, success_streak, total_recall_count, total_error_count))
        
        # Apply HP / EXP to game_saves
        user_row = conn.execute("SELECT hp, max_hp, exp, level FROM game_saves WHERE slot_id=?", (slot_id,)).fetchone()
        if user_row:
            cur_hp = user_row["hp"]
            max_hp = user_row["max_hp"]
            cur_exp = user_row["exp"]
            cur_level = user_row["level"]
            
            new_hp = cur_hp
            new_exp = cur_exp
            leveled_up = False
            
            if reward["hp"] != 0:
                new_hp = min(float(max_hp), float(cur_hp) + reward["hp"])
                if new_hp < 0: new_hp = 0
                
            if reward["exp"] > 0:
                new_exp += reward["exp"]
                # Seamless Level Up Loop (EXP Overflow)
                while True:
                    needed_exp = cur_level * 100
                    if new_exp >= needed_exp:
                        new_exp -= needed_exp
                        cur_level += 1
                        new_hp = max_hp # Full heal on level up
                        leveled_up = True
                    else:
                        break
                        
                if leveled_up:
                    print(f"[vocab] Slot {slot_id} Leveled Up to {cur_level}!")
            
            conn.execute("""
                UPDATE game_saves SET hp=?, exp=?, level=? WHERE slot_id=?
            """, (new_hp, new_exp, cur_level, slot_id))
            
            reward["leveled_up"] = leveled_up
            reward["new_level"] = cur_level
            reward["new_hp"] = new_hp
            reward["new_exp"] = new_exp
        
        conn.commit()

    return {
        "success": True,
        "word": word,
        "next_review": next_date_str,
        "reward": reward,
        "srs": {
            "streak": success_streak,
            "mastery": mastery_level
        }
    }


@router.get("/list")
def get_vocab_list(slot_id: int = 0):
    """
    [Stage 21.0] 全局单词本视图
    [Stage 23.0] Switched to DB
    """
    with get_profile_conn() as conn, get_static_conn() as static_conn:
        ensure_auto_save(conn)
        rows = conn.execute("""
            SELECT word, mastery_level, success_streak, next_review_date
            FROM user_vocab_memory
            WHERE slot_id = ?
        """, (slot_id,)).fetchall()
        memory_map = {r["word"]: r for r in rows}
        
        static_words = static_conn.execute("SELECT * FROM vocabulary").fetchall()
        
    vocab_list = []
    learned_count = 0
    total_count = len(static_words)
    
    for row in static_words:
        word = row["word"]
        data = parse_vocab_row(row)
        mem = memory_map.get(word)
        if mem:
            learned_count += 1
            vocab_list.append({
                "word": word,
                "phonetic": data.get("phonetic", ""),
                "meanings": data.get("meanings", []),
                "mastery_level": mem["mastery_level"],
                "success_streak": mem["success_streak"],
                "next_review_date": mem["next_review_date"],
                "status": "learned"
            })
        else:
            vocab_list.append({
                "word": word,
                "phonetic": data.get("phonetic", ""),
                "meanings": data.get("meanings", []),
                "mastery_level": 0,
                "success_streak": 0,
                "next_review_date": None,
                "status": "unlearned"
            })
            
    return {
        "total": total_count,
        "learned": learned_count,
        "unlearned": total_count - learned_count,
        "items": vocab_list
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
