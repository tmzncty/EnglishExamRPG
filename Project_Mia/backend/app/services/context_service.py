"""
MiaContextService — 记忆雷达
扫描题目文本匹配用户背词进度，获取 RPG 状态快照。

Author: Femo
Date: 2026-02-18
"""

import re
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.db.helpers import get_profile_conn, get_static_conn, get_user_hp, get_user_max_hp, ensure_auto_save


# ---- 英语停用词（高频无意义词，不纳入记忆扫描）----
STOP_WORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "must", "can", "could", "to", "of", "in",
    "for", "on", "with", "at", "by", "from", "as", "into", "through",
    "during", "before", "after", "above", "below", "between", "out",
    "off", "over", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "each", "every",
    "both", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "just",
    "because", "but", "and", "or", "if", "while", "about", "up", "down",
    "he", "she", "it", "they", "we", "you", "i", "me", "him", "her",
    "us", "them", "my", "your", "his", "its", "our", "their", "this",
    "that", "these", "those", "what", "which", "who", "whom", "whose",
    "also", "still", "even", "much", "many", "well", "back", "new",
})


def _tokenize(text: str) -> set:
    """分词：转小写，去标点，去停用词，返回去重词集"""
    words = re.findall(r"[a-zA-Z]+", text.lower())
    return {w for w in words if len(w) >= 3 and w not in STOP_WORDS}


class MiaContextService:
    """记忆雷达 — 实时读取用户学习状态，构建上下文"""

    @staticmethod
    def get_vocab_resonance(text_content: str) -> List[Dict[str, Any]]:
        """
        扫描文本中出现的单词，匹配 vocab_progress 表，返回有学习记录的词汇列表。

        返回格式:
        [
          {"word": "inexorable", "status": "weak", "ef": 1.3, "reps": 2,
           "mistakes": 3, "meaning": "不可遏制的", "history": "错过3次, EF=1.3"},
          {"word": "prone", "status": "due", "ef": 2.5, ...},
        ]
        """
        tokens = _tokenize(text_content)
        if not tokens:
            return []

        results = []
        now = datetime.utcnow()

        with get_profile_conn() as pconn:
            # 批量查: 只查有学习记录的词
            placeholders = ",".join("?" for _ in tokens)
            rows = pconn.execute(
                f"""SELECT word, repetition, easiness_factor, interval,
                           next_review, mistake_count, consecutive_correct
                    FROM vocab_progress
                    WHERE word IN ({placeholders})""",
                list(tokens),
            ).fetchall()

        if not rows:
            return []

        # 查释义(从 static 库)
        found_words = [r["word"] for r in rows]
        meanings_map = {}
        with get_static_conn() as sconn:
            ph2 = ",".join("?" for _ in found_words)
            mrows = sconn.execute(
                f"SELECT word, meaning FROM dictionary WHERE word IN ({ph2})",
                found_words,
            ).fetchall()
            for mr in mrows:
                meanings_map[mr["word"]] = mr["meaning"]

        for row in rows:
            word = row["word"]
            ef = row["easiness_factor"] or 2.5
            reps = row["repetition"] or 0
            mistakes = row["mistake_count"] or 0
            consec = row["consecutive_correct"] or 0
            next_rev = row["next_review"]

            # 状态判定
            is_due = False
            if next_rev:
                try:
                    next_dt = datetime.fromisoformat(next_rev.replace("Z", "+00:00"))
                    is_due = next_dt <= now
                except (ValueError, TypeError):
                    pass

            if ef < 2.0 or mistakes >= 2:
                status = "weak"       # 死对头
                history = f"错过{mistakes}次, EF={ef:.1f}"
            elif reps >= 5 and consec >= 3:
                status = "mastered"   # 老朋友
                history = f"已复习{reps}次, 连对{consec}次"
            elif is_due:
                status = "due"        # 急需复习
                history = f"已过期, 上次复习距今较久"
            else:
                status = "learning"   # 正在学
                history = f"复习{reps}次, EF={ef:.1f}"

            meaning_short = meanings_map.get(word, "")
            if meaning_short:
                # 取第一行释义
                meaning_short = meaning_short.split("\n")[0][:40]

            results.append({
                "word": word,
                "status": status,
                "ef": ef,
                "reps": reps,
                "mistakes": mistakes,
                "meaning": meaning_short,
                "history": history,
            })

        # 按优先级排序: weak > due > learning > mastered
        priority = {"weak": 0, "due": 1, "learning": 2, "mastered": 3}
        results.sort(key=lambda x: priority.get(x["status"], 9))

        return results

    @staticmethod
    def get_user_status_snapshot() -> Dict[str, Any]:
        """
        获取用户当前 RPG 状态快照。

        返回:
        {
          "hp": 65, "max_hp": 100, "hp_pct": 65.0,
          "recent_accuracy": 0.6,   # 近5题正确率
          "recent_history": [...],   # 近5条答题记录
          "total_vocab_learned": 61, # 已背词数
          "weak_vocab_count": 3,     # 死对头数
        }
        """
        snapshot = {
            "hp": 100, "max_hp": 100, "hp_pct": 100.0,
            "recent_accuracy": 1.0, "recent_history": [],
            "total_vocab_learned": 0, "weak_vocab_count": 0,
        }

        with get_profile_conn() as pconn:
            ensure_auto_save(pconn)
            hp = get_user_hp(pconn)
            max_hp = get_user_max_hp(pconn)
            snapshot["hp"] = hp
            snapshot["max_hp"] = max_hp
            snapshot["hp_pct"] = round(hp / max(max_hp, 1) * 100, 1)

            # 近5次答题记录
            try:
                history = pconn.execute(
                    """SELECT q_id, user_answer, is_correct, created_at
                       FROM exam_history
                       ORDER BY created_at DESC LIMIT 5"""
                ).fetchall()
                snapshot["recent_history"] = history
                if history:
                    correct_count = sum(1 for h in history if h.get("is_correct"))
                    snapshot["recent_accuracy"] = round(correct_count / len(history), 2)
            except Exception:
                pass  # 表可能不存在

            # 词汇统计
            try:
                vocab_stats = pconn.execute(
                    """SELECT COUNT(*) as total,
                              SUM(CASE WHEN easiness_factor < 2.0 OR mistake_count >= 2 THEN 1 ELSE 0 END) as weak
                       FROM vocab_progress"""
                ).fetchone()
                if vocab_stats:
                    snapshot["total_vocab_learned"] = vocab_stats["total"] or 0
                    snapshot["weak_vocab_count"] = vocab_stats["weak"] or 0
            except Exception:
                pass

        return snapshot


# 单例
context_service = MiaContextService()
