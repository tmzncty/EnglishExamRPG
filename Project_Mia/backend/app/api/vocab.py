from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
import json
import math

from app.db.helpers import get_profile_conn, get_static_conn, ensure_auto_save, update_user_hp
from app.services.sm2 import sm2_service

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
            "SELECT daily_new_words_limit, daily_reset_time, last_reset_day, daily_streak, last_goal_met_date, today_focus_time FROM game_saves WHERE slot_id=?", (slot_id,)
        ).fetchone()
        
        daily_limit = 30
        reset_time = "04:00"
        last_reset_day = ""
        daily_streak = 0
        last_goal_met_date = ""
        today_focus_time = 0
        
        if slot_row:
            daily_limit = slot_row.get("daily_new_words_limit") or 30
            reset_time = slot_row.get("daily_reset_time") or "04:00"
            last_reset_day = slot_row.get("last_reset_day") or ""
            daily_streak = slot_row.get("daily_streak") or 0
            last_goal_met_date = slot_row.get("last_goal_met_date") or ""
            today_focus_time = slot_row.get("today_focus_time") or 0
        
        # Calculate logical date using UTC+8 + reset_time
        today_str = get_logical_date(reset_time)
        
        if last_reset_day != today_str:
            conn.execute("""
                UPDATE game_saves 
                SET today_learned_count=0, today_reviewed_count=0, today_focus_time=0, last_reset_day=? 
                WHERE slot_id=?
            """, (today_str, slot_id))
            conn.commit()
            today_focus_time = 0
            
        # ── [Stage 35.5] Emergency Debt Restructuring ──────────
        # Heal words that have a good streak but a bugged short interval
        conn.execute("""
            UPDATE user_vocab_memory
            SET next_review_date = date(?, '+4 days'),
                interval = 4
            WHERE slot_id = ? AND success_streak >= 1 AND interval < 3 AND next_review_date <= ?
        """, (today_str, slot_id, today_str))
        conn.commit()
        
        # ── [Stage 35.4] True SRS Engine: Dynamic Quota Algorithm ──────────
        # 1. Get ALL Due Reviews — NO LIMIT! SRS debt must be repaid.
        rows = conn.execute("""
            SELECT word, easiness_factor, interval, repetitions 
            FROM user_vocab_memory
            WHERE slot_id = ? AND next_review_date <= ?
            ORDER BY next_review_date ASC
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
        
        # 2. Dynamic Quota Calculation
        #    daily_limit = user's slider value = TOTAL daily learning budget
        #    Scenario A: DueReviews < DailyLimit → new_word_quota = DailyLimit - DueReviews
        #    Scenario B: DueReviews >= DailyLimit → new_word_quota = 0 (clear debt first!)
        due_review_count = len(review_words)
        new_word_quota = max(0, daily_limit - due_review_count)
        
        # 3. Get New Words (only if quota > 0)
        if new_word_quota > 0:
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
                    if count >= new_word_quota:
                        break
    
    # [Stage 35.3 / 35.4] 终极混排：新旧词汇无缝穿插 (Mix New & Review)
    tasks = review_words + new_words
    import random
    random.seed(f"slot_{slot_id}_{today_str}_mix")
    random.shuffle(tasks)
    random.seed() # Reset to system entropy

    return {
        "date": today_str,
        "daily_limit": daily_limit,
        "daily_streak": daily_streak,
        "last_goal_met_date": last_goal_met_date,
        "today_focus_time": today_focus_time,
        "tasks": tasks,
        "review_count": len(review_words),
        "new_count": len(new_words),
        "total_count": len(review_words) + len(new_words),
        "today_learned_count": slot_row.get("today_learned_count", 0) if slot_row else 0,
        "today_reviewed_count": slot_row.get("today_reviewed_count", 0) if slot_row else 0
    }

# Constant for Mastery Level Threshold
MASTERY_THRESHOLD = 4

@router.get("/global_stats")
def get_global_stats(slot_id: int = 0):
    with get_profile_conn() as pconn, get_static_conn() as sconn:
        # Total static words
        total_words_row = sconn.execute("SELECT COUNT(1) as cnt FROM vocabulary").fetchone()
        total_words = total_words_row["cnt"] if total_words_row else 5500
        
        # Mastered words
        mastered_row = pconn.execute(
            "SELECT COUNT(1) as cnt FROM user_vocab_memory WHERE slot_id = ? AND mastery_level >= ?", 
            (slot_id, MASTERY_THRESHOLD)
        ).fetchone()
        mastered_words = mastered_row["cnt"] if mastered_row else 0
        
        return {
            "total_words": total_words,
            "mastered_words": mastered_words
        }

@router.post("/review")
def submit_review(data: Dict[str, Any]):
    """
    [Stage 21.0] 深度复习与进度结算
    """
    slot_id = data.get("slot_id", 0)
    word = data.get("word")
    quality = max(0, min(5, int(data.get("quality", 0))))  # 0-5 边界校验
    
    with get_profile_conn() as conn:
        ensure_auto_save(conn)
        
        slot_info = conn.execute("SELECT daily_reset_time FROM game_saves WHERE slot_id=?", (slot_id,)).fetchone()
        reset_time = slot_info["daily_reset_time"] if slot_info and slot_info["daily_reset_time"] else "04:00"
        logical_today_str = get_logical_date(reset_time)
        logical_today_dt = datetime.strptime(logical_today_str, "%Y-%m-%d").date()
        
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
            # Call unified SM-2 service (aggressive mode)
            sm2_result = sm2_service.calculate(
                quality=quality,
                repetition=reps,
                easiness_factor=ef,
                interval=interval,
                aggressive=True,
                success_streak=success_streak,
            )
            ef = sm2_result["easiness_factor"]
            interval = sm2_result["interval"]
            reps = sm2_result["repetition"]
            
            # Pro-level SRS Update
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
            # Call unified SM-2 service (failure reset)
            sm2_result = sm2_service.calculate(
                quality=quality,
                repetition=reps,
                easiness_factor=ef,
                interval=interval,
                aggressive=True,
                success_streak=success_streak,
            )
            ef = sm2_result["easiness_factor"]
            interval = sm2_result["interval"]
            reps = sm2_result["repetition"]
            
            success_streak = 0
            total_error_count += 1
            mastery_level = max(0, mastery_level - 1)
            
            # Damage HP
            reward["hp"] = -5 # Fixed damage for mistake
            
        # Calculate next_date based on *Logical Today*, not actual time!
        next_date = logical_today_dt + timedelta(days=interval)
        next_date_str = next_date.strftime("%Y-%m-%d")
        
        # Save to user_vocab_memory
        conn.execute("""
            INSERT OR REPLACE INTO user_vocab_memory 
            (slot_id, word, easiness_factor, interval, repetitions, next_review_date, last_review_date, 
             mastery_level, success_streak, total_recall_count, total_error_count, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
        """, (slot_id, word, ef, interval, reps, next_date_str, logical_today_str, 
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
            
    mastered_count = sum(1 for item in vocab_list if item["mastery_level"] >= MASTERY_THRESHOLD)
            
    return {
        "total": total_count,
        "learned": learned_count,
        "mastered": mastered_count,
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

@router.post("/sync_progress")
def sync_progress(data: Dict[str, Any]):
    """
    [Stage 30.0] 同步专注时间和打卡进度
    """
    slot_id = data.get("slot_id", 0)
    focus_time = data.get("focus_time", 0)
    goal_met = data.get("goal_met", False)
    
    with get_profile_conn() as conn:
        ensure_auto_save(conn)
        
        row = conn.execute(
            "SELECT daily_reset_time, daily_streak, last_goal_met_date, today_focus_time FROM game_saves WHERE slot_id=?", 
            (slot_id,)
        ).fetchone()
        
        if not row:
            return {"success": False, "error": "Slot not found"}
            
        reset_time = row["daily_reset_time"] or "04:00"
        daily_streak = row["daily_streak"] or 0
        last_goal_met_date = row["last_goal_met_date"] or ""
        today_focus_time = row["today_focus_time"] or 0
        
        today_logical = get_logical_date(reset_time)
        
        from datetime import datetime, timedelta
        yesterday_dt = datetime.strptime(today_logical, "%Y-%m-%d") - timedelta(days=1)
        yesterday_logical = yesterday_dt.strftime("%Y-%m-%d")
        
        is_new_streak = False
        
        # Streak Update Logic
        if goal_met and last_goal_met_date != today_logical:
            if last_goal_met_date == yesterday_logical:
                daily_streak += 1
            else:
                daily_streak = 1 # Streak broken or brand new
            last_goal_met_date = today_logical
            is_new_streak = True
            
        # Update focus time 
        new_focus_time = max(today_focus_time, focus_time)
        
        conn.execute("""
            UPDATE game_saves 
            SET daily_streak = ?, last_goal_met_date = ?, today_focus_time = ?, updated_at = datetime('now', 'localtime')
            WHERE slot_id = ?
        """, (daily_streak, last_goal_met_date, new_focus_time, slot_id))
        conn.commit()
        
    return {
        "success": True,
        "daily_streak": daily_streak,
        "last_goal_met_date": last_goal_met_date,
        "today_focus_time": new_focus_time,
        "is_new_streak": is_new_streak
    }


# ── [Stage 31.0] Vocab Session Lifecycle APIs ──────────────────────────

@router.post("/start_session")
def start_vocab_session(data: Dict[str, Any]):
    """
    [Stage 31.0] 开启一个新的背词会话
    """
    slot_id = data.get("slot_id", 0)
    try:
        with get_profile_conn() as pconn:
            ensure_auto_save(pconn)
            cursor = pconn.execute("""
                INSERT INTO vocab_sessions (slot_id, started_at) 
                VALUES (?, datetime('now', 'localtime'))
            """, (slot_id,))
            session_id = cursor.lastrowid
            pconn.commit()
            return {"success": True, "session_id": session_id}
    except Exception as e:
        print(f"[vocab] start_session error: {e}")
        return {"success": False, "error": str(e)}

@router.post("/log_word")
def log_vocab_word(data: Dict[str, Any]):
    """
    [Stage 31.0] 记录会话中的单个单词作答
    """
    session_id = data.get("session_id")
    word = data.get("word")
    action = data.get("action", "learn") # learn/review
    time_spent = data.get("time_spent", 0)
    result = data.get("result", "") # correct/forgot
    
    if not session_id or not word:
        return {"success": False, "error": "session_id and word required"}
        
    try:
        with get_profile_conn() as pconn:
            pconn.execute("""
                INSERT INTO vocab_session_words (session_id, word, action, time_spent, result)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, word, action, time_spent, result))
            pconn.commit()
            return {"success": True}
    except Exception as e:
        print(f"[vocab] log_word error: {e}")
        return {"success": False, "error": str(e)}

@router.post("/finish_session")
def finish_vocab_session(data: Dict[str, Any]):
    """
    [Stage 31.0] 结束且结算会话
    """
    session_id = data.get("session_id")
    total_time = data.get("total_time", 0)
    words_learned = data.get("words_learned", 0)
    words_reviewed = data.get("words_reviewed", 0)
    
    if not session_id:
        return {"success": False, "error": "session_id required"}
        
    try:
        with get_profile_conn() as pconn:
            pconn.execute("""
                UPDATE vocab_sessions
                SET finished_at = datetime('now', 'localtime'),
                    total_time = ?, words_learned = ?, words_reviewed = ?
                WHERE session_id = ?
            """, (total_time, words_learned, words_reviewed, session_id))
            pconn.commit()
            return {"success": True}
    except Exception as e:
        print(f"[vocab] finish_session error: {e}")
        return {"success": False, "error": str(e)}

@router.get("/vocab/sessions")
def get_vocab_sessions(slot_id: int = 0):
    try:
        with get_profile_conn() as pconn:
            ensure_auto_save(pconn)
            sessions = pconn.execute("""
                SELECT * FROM vocab_sessions 
                WHERE slot_id = ? AND finished_at IS NOT NULL
                ORDER BY started_at DESC
            """, (slot_id,)).fetchall()
            
            return [dict(s) for s in sessions]
    except Exception as e:
        print(f"[vocab] get_vocab_sessions error: {e}")
        return []


# ══════════════════════════════════════════════════════════════
#  进度统计 / 筛选 / 批量标记
# ══════════════════════════════════════════════════════════════

EXAM_DATE = "2026-12-20"


@router.get("/progress_stats")
def get_progress_stats(slot_id: int = 0):
    """返回背单词进度统计"""
    with get_profile_conn() as pconn, get_static_conn() as sconn:
        total_words = sconn.execute("SELECT COUNT(1) as cnt FROM vocabulary").fetchone()["cnt"]

        learned = pconn.execute(
            "SELECT COUNT(1) as cnt FROM user_vocab_memory WHERE slot_id=?", (slot_id,)
        ).fetchone()["cnt"]

        mastered = pconn.execute(
            "SELECT COUNT(1) as cnt FROM user_vocab_memory WHERE slot_id=? AND mastery_level >= 4",
            (slot_id,)
        ).fetchone()["cnt"]

        graduated = pconn.execute(
            "SELECT COUNT(1) as cnt FROM user_vocab_memory WHERE slot_id=? AND mastery_level >= 4 AND interval > 90",
            (slot_id,)
        ).fetchone()["cnt"]

        mistake_book = pconn.execute(
            "SELECT COUNT(1) as cnt FROM user_vocab_memory WHERE slot_id=? AND easiness_factor < 1.8",
            (slot_id,)
        ).fetchone()["cnt"]

        unseen = max(0, total_words - learned)

        # UTC+8 今天 vs 考研日期
        today_utc8 = datetime.now(UTC8).date()
        exam_date = datetime.strptime(EXAM_DATE, "%Y-%m-%d").date()
        days_until_exam = max(1, (exam_date - today_utc8).days)

        daily_needed = math.ceil(unseen / days_until_exam) if unseen > 0 else 0

        return {
            "total_words": total_words,
            "learned": learned,
            "mastered": mastered,
            "graduated": graduated,
            "mistake_book": mistake_book,
            "unseen": unseen,
            "days_until_exam": days_until_exam,
            "daily_needed": daily_needed,
        }


@router.get("/screening")
def get_screening(slot_id: int = 0, limit: int = 50):
    """返回未学新词列表（优先有例句、高频词）"""
    with get_profile_conn() as pconn, get_static_conn() as sconn:
        learned_words = {
            r["word"] for r in
            pconn.execute("SELECT word FROM user_vocab_memory WHERE slot_id=?", (slot_id,)).fetchall()
        }

        # 优先有例句的，按 ROWID 作为自然顺序（高频靠前）
        all_words = sconn.execute(
            "SELECT * FROM vocabulary ORDER BY (sentences != '[]' AND sentences IS NOT NULL) DESC, ROWID ASC"
        ).fetchall()

        words = []
        for row in all_words:
            if row["word"] not in learned_words:
                parsed = parse_vocab_row(row)
                words.append({**parsed, "type": "new"})
                if len(words) >= limit:
                    break

        return {"words": words}


@router.post("/batch_mark")
def batch_mark(data: Dict[str, Any]):
    """
    批量标记单词。
    action=skip: 标记为已掌握（mastery_level=4, interval=365 天）
    action=reset: 从记忆中移除，回退到未学状态
    """
    slot_id = data.get("slot_id", 0)
    words = data.get("words", [])
    action = data.get("action", "skip")

    if not words or action not in ("skip", "reset"):
        return {"ok": False, "count": 0, "error": "invalid params"}

    count = 0
    review_date = (datetime.now(UTC8) + timedelta(days=365)).strftime("%Y-%m-%d")

    with get_profile_conn() as conn:
        ensure_auto_save(conn)

        if action == "skip":
            for word in words:
                conn.execute("""
                    INSERT OR REPLACE INTO user_vocab_memory
                    (slot_id, word, easiness_factor, interval, repetitions, mastery_level,
                     success_streak, total_recall_count, total_error_count,
                     next_review_date, last_review_date, updated_at)
                    VALUES (?, ?, 2.5, 365, 5, 4, 5, 5, 0, ?, ?, datetime('now', 'localtime'))
                """, (slot_id, word, review_date, datetime.now(UTC8).strftime("%Y-%m-%d")))
                count += 1
        elif action == "reset":
            for word in words:
                cur = conn.execute(
                    "DELETE FROM user_vocab_memory WHERE slot_id=? AND word=?",
                    (slot_id, word)
                )
                count += cur.rowcount

        conn.commit()

    return {"ok": True, "count": count}
