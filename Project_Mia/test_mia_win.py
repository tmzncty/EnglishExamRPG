"""
test_mia_win.py v2.5 — 英语一特化微缩版引擎
纯内存数据库 + 英语一精确伤害 + AI 阅卷 Mock

启动: python test_mia_win.py
测试: http://127.0.0.1:8000/docs

Author: Femo
Date: 2026-02-18
"""

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import sqlite3
import json
import re

app = FastAPI(title="Project_Mia v2.5 — 英语一特化引擎 🐾")

# ============================================================================
# 1. 内存数据库
# ============================================================================
conn = sqlite3.connect(":memory:", check_same_thread=False)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 题目表 (含 section_type)
cur.execute("""
    CREATE TABLE questions (
        q_id TEXT PRIMARY KEY,
        section_type TEXT,
        max_score REAL,
        correct_answer TEXT,
        passage_text TEXT
    )
""")

# 测试数据 — 全6种英语一题型
cur.executemany(
    "INSERT INTO questions VALUES (?, ?, ?, ?, ?)",
    [
        # 完形填空 (use_of_english)
        ("2023-cloze-1",  "use_of_english", 0.5, "A", "The author argues that ___"),
        ("2023-cloze-2",  "use_of_english", 0.5, "C", "However, the ___"),
        # 阅读A (reading_a)
        ("2023-read-a-1", "reading_a",      2.0, "B", "Passage about economics…"),
        ("2023-read-a-2", "reading_a",      2.0, "D", "Passage about AI ethics…"),
        # 阅读B 7选5 (reading_b)
        ("2023-read-b-1", "reading_b",      2.0, "F", "Passage with 7 options…"),
        # 翻译 (translation)
        ("2010-trans-46", "translation",    2.0, "科学家们认为,影响人们判断的不仅是信息本身,还有信息呈现的方式。",
         "Scientists believe that it is not just the information itself, but how it is presented that influences people's thinking."),
        # 小作文 (writing_a)
        ("2023-writ-a",   "writing_a",     10.0, None,
         "Write a letter to a foreign friend inviting him/her to attend a cultural event."),
        # 大作文 (writing_b)
        ("2023-writ-b",   "writing_b",     20.0, None,
         "The picture shows a young man at a crossroads, with signs pointing to different directions."),
    ],
)

# 用户状态
cur.execute("CREATE TABLE user_stats (hp INTEGER, max_hp INTEGER, exp INTEGER, level INTEGER)")
cur.execute("INSERT INTO user_stats VALUES (100, 100, 0, 1)")

# 答题历史
cur.execute("""
    CREATE TABLE exam_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        q_id TEXT, section_type TEXT, user_answer TEXT,
        is_correct BOOLEAN, score REAL, damage INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()


# ============================================================================
# 2. 英语一特化伤害计算器
# ============================================================================

def english1_damage(section_type: str, is_correct: bool = False, ai_score: float = 0) -> dict:
    """英语一精确伤害计算"""
    st = section_type.lower()

    if st == "use_of_english":
        dmg = 0 if is_correct else 2
        return {"type": "完形填空", "damage": dmg, "detail": "固定 2HP/错"}

    if st in ("reading_a", "reading_b"):
        dmg = 0 if is_correct else 5
        label = "传统阅读" if st == "reading_a" else "新题型7选5"
        return {"type": label, "damage": dmg, "detail": "固定 5HP/错"}

    if st == "translation":
        dmg = max(0, round((2.0 - ai_score) * 2.5))
        return {"type": "长难句翻译", "damage": dmg, "detail": f"(2.0-{ai_score})×2.5"}

    if st == "writing_a":
        base = 5
        penalty = max(0, round((6.0 - ai_score) * 1.0)) if ai_score < 6.0 else 0
        return {"type": "小作文", "damage": base + penalty,
                "detail": f"基础消耗5 + 追加{penalty}", "base_cost": base, "penalty": penalty}

    if st == "writing_b":
        base = 5
        penalty = max(0, round((12.0 - ai_score) * 1.0)) if ai_score < 12.0 else 0
        return {"type": "大作文", "damage": base + penalty,
                "detail": f"基础消耗5 + 追加{penalty}", "base_cost": base, "penalty": penalty}

    return {"type": "未知", "damage": 3, "detail": "fallback"}


def get_mia_mood(hp: int, max_hp: int) -> dict:
    if max_hp <= 0: max_hp = 1
    ratio = hp / max_hp
    if hp <= 0:
        return {"mood": "exhausted",  "emoji": "😵",  "line": "绯墨已力竭！禁止做题，马上休息喵！(╬ Ò ‸ Ó)"}
    if ratio < 0.30:
        return {"mood": "worried",    "emoji": "😟",  "line": "绯墨...精神力快见底了...去背几个单词回血？(´;ω;`)"}
    if ratio < 0.80:
        return {"mood": "focused",    "emoji": "🧐",  "line": "继续加油，Mia 在旁边帮你分析~ 📖"}
    return {"mood": "happy",      "emoji": "😊",  "line": "绯墨状态超好喵！✨(≧▽≦)"}


def mock_ai_grade(section_type: str, user_text: str) -> dict:
    """Mock AI 阅卷 (模拟 Gemini 返回)"""
    text_len = len(user_text.strip())
    if section_type == "translation":
        score = min(2.0, max(0.0, text_len / 20.0))  # 大致按字数给分
        score = round(score * 2) / 2  # 步长 0.5
        return {
            "score": score,
            "feedback": f"翻译 {text_len} 字，Mia 评 {score} 分喵~ {'结构还行~' if score >= 1.0 else '关键语法翻错了！'}",
            "key_points_missed": ["定语从句处理"] if score < 2.0 else [],
        }
    elif section_type == "writing_a":
        score = min(10.0, max(2.0, text_len / 15.0))
        return {
            "score": round(score, 1),
            "feedback": f"小作文 {text_len} 字，Mia 评 {round(score,1)} 分喵~",
            "suggestions": ["注意格式规范"] if score < 7 else ["继续保持！"],
        }
    else:  # writing_b
        score = min(20.0, max(4.0, text_len / 10.0))
        return {
            "score": round(score, 1),
            "feedback": f"大作文 {text_len} 字，Mia 评 {round(score,1)} 分喵~",
            "suggestions": ["论点可以更丰富"],
        }


# 辅助: 扣血并写历史
def apply_damage(q_id, section_type, user_answer, is_correct, score, damage):
    row = conn.execute("SELECT hp, max_hp FROM user_stats").fetchone()
    hp = max(0, row["hp"] - damage)
    conn.execute("UPDATE user_stats SET hp = ?", (hp,))
    conn.execute(
        "INSERT INTO exam_history (q_id, section_type, user_answer, is_correct, score, damage) VALUES (?,?,?,?,?,?)",
        (q_id, section_type, user_answer, is_correct, score, damage)
    )
    conn.commit()
    return hp, row["max_hp"]


# ============================================================================
# 3. Pydantic Models
# ============================================================================

class ObjectiveInput(BaseModel):
    q_id: str
    user_answer: str

class SubjectiveInput(BaseModel):
    q_id: str
    user_text: str = Field(..., min_length=1)


# ============================================================================
# 4. API 路由
# ============================================================================

@app.post("/api/exam/submit_objective")
async def submit_objective(body: ObjectiveInput):
    """客观题提交 (完形 / 阅读) — 英语一精确伤害"""
    q = conn.execute("SELECT * FROM questions WHERE q_id = ?", (body.q_id,)).fetchone()
    if not q:
        return {"error": f"题目 {body.q_id} 不存在"}

    correct = q["correct_answer"] or ""
    is_correct = body.user_answer.strip().upper() == correct.strip().upper()

    info = english1_damage(q["section_type"], is_correct=is_correct)
    hp, max_hp = apply_damage(body.q_id, q["section_type"], body.user_answer, is_correct, q["max_score"] if is_correct else 0, info["damage"])

    mood = get_mia_mood(hp, max_hp)
    return {
        "is_correct": is_correct,
        "correct_answer": correct,
        "section_type": q["section_type"],
        "damage_info": info,
        "hp_change": -info["damage"],
        "current_hp": hp,
        "max_hp": max_hp,
        "mia_mood": mood["mood"],
        "mia_reply": (
            f"全对喵！{mood['line']}" if is_correct
            else f"答案是 **{correct}**！扣除 **{info['damage']}** 点精神力！({info['type']}惩罚) {mood['line']}"
        ),
    }


@app.post("/api/exam/submit_subjective")
async def submit_subjective(body: SubjectiveInput):
    """主观题提交 (翻译 / 写作) — AI 阅卷 + 基础消耗 + 追加惩罚"""
    q = conn.execute("SELECT * FROM questions WHERE q_id = ?", (body.q_id,)).fetchone()
    if not q:
        return {"error": f"题目 {body.q_id} 不存在"}

    section_type = q["section_type"]

    # AI 阅卷 (Mock)
    grade = mock_ai_grade(section_type, body.user_text)
    ai_score = grade["score"]

    # 计算伤害
    info = english1_damage(section_type, ai_score=ai_score)

    hp, max_hp = apply_damage(body.q_id, section_type, body.user_text[:100], False, ai_score, info["damage"])

    mood = get_mia_mood(hp, max_hp)
    return {
        "section_type": section_type,
        "ai_score": ai_score,
        "max_score": q["max_score"],
        "damage_info": info,
        "hp_change": -info["damage"],
        "current_hp": hp,
        "max_hp": max_hp,
        "mia_mood": mood["mood"],
        "mia_feedback": grade["feedback"],
        "details": {k: v for k, v in grade.items() if k not in ("score", "feedback")},
    }


@app.get("/api/status")
async def get_status():
    """当前状态"""
    row = conn.execute("SELECT * FROM user_stats").fetchone()
    history = conn.execute("SELECT * FROM exam_history ORDER BY id DESC LIMIT 5").fetchall()
    return {
        "hp": row["hp"], "max_hp": row["max_hp"],
        "mood": get_mia_mood(row["hp"], row["max_hp"]),
        "recent_history": [dict(h) for h in history],
    }


@app.post("/api/reset")
async def reset():
    """重置"""
    conn.execute("UPDATE user_stats SET hp=100, max_hp=100, exp=0, level=1")
    conn.execute("DELETE FROM exam_history")
    conn.commit()
    return {"message": "重置完成! HP: 100/100 ✨"}


@app.get("/api/damage_table")
async def damage_table():
    """英语一伤害速查表"""
    return {
        "english_one_damage_system": {
            "use_of_english": {"per_wrong": "2 HP", "total_questions": 20, "max_damage": "40 HP"},
            "reading_a":      {"per_wrong": "5 HP", "total_questions": 20, "max_damage": "100 HP"},
            "reading_b":      {"per_wrong": "5 HP", "total_questions": 5,  "max_damage": "25 HP"},
            "translation":    {"formula": "(2.0 - ai_score) × 2.5", "max_damage": "5 HP/句"},
            "writing_a":      {"base_cost": "5 HP", "penalty": "(6.0 - score) × 1.0", "max_total": "11 HP"},
            "writing_b":      {"base_cost": "5 HP", "penalty": "(12.0 - score) × 1.0", "max_total": "17 HP"},
        }
    }


# ============================================================================
# 5. 启动
# ============================================================================
if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("🐾 Project_Mia v2.5 — 英语一特化引擎启动中...")
    print("=" * 60)
    print()
    print("📋 Swagger UI:  http://127.0.0.1:8000/docs")
    print()
    print("🧪 快速测试:")
    print('  [客观] POST /api/exam/submit_objective')
    print('    完形: {"q_id":"2023-cloze-1", "user_answer":"B"}  → 扣2HP')
    print('    阅读: {"q_id":"2023-read-a-1", "user_answer":"A"} → 扣5HP')
    print()
    print('  [主观] POST /api/exam/submit_subjective')
    print('    翻译: {"q_id":"2010-trans-46", "user_text":"科学家认为..."}')
    print('    大作文: {"q_id":"2023-writ-b", "user_text":"In the picture..."}')
    print()
    print('  GET /api/damage_table  → 英语一伤害速查表')
    print('  GET /api/status       → 当前状态')
    print('  POST /api/reset       → 重置满血')
    print()
    print("=" * 60)

    uvicorn.run(app, host="127.0.0.1", port=8000)
