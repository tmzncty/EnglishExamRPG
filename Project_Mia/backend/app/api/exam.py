"""
Exam 路由 — 试卷列表、详情、客观题提交
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import traceback

from app.db.session import get_static_db
from app.db.models import Paper, Question
from app.db.helpers import (
    get_profile_conn, ensure_auto_save,
    get_user_hp, get_user_max_hp, update_user_hp,
)
from contextlib import closing
from app.services.game_mechanics import game_mechanics

router = APIRouter()


@router.get("/exams", response_model=List[Dict[str, Any]])
def get_exams(db: Session = Depends(get_static_db)):
    """获取所有试卷列表"""
    papers = db.query(Paper).order_by(Paper.year.desc()).all()
    return [
        {
            "paper_id": p.paper_id,
            "year": p.year,
            "title": p.title or f"{p.year}年考研英语{p.exam_type}",
            "exam_type": p.exam_type,
        }
        for p in papers
    ]


@router.get("/exam/history")
def get_exam_history(slot_id: int = 0):
    """
    [Stage 14.0] 获取用户的答题记录
    前端用于页面刷新后的状态恢复
    """
    history = {}
    try:
        with get_profile_conn() as conn:
            ensure_auto_save(conn)
            rows = conn.execute("""
                SELECT q_id, section_type, user_answer, score, is_correct, ai_feedback
                FROM user_answers
                WHERE slot_id = ?
            """, (slot_id,)).fetchall()
            
            for r in rows:
                history[r["q_id"]] = {
                    "user_answer": r["user_answer"],
                    "score":       r["score"],
                    "is_correct":  bool(r["is_correct"]),
                    "ai_feedback": r["ai_feedback"],
                    "section_type": r["section_type"]
                }
    except Exception as e:
        print(f"[exam] Fetch history failed: {e}")
        # Return empty dict on error, don't crash
        return {}

    return history


@router.get("/exam/{paper_id}", response_model=Dict[str, Any])
def get_exam_detail(paper_id: str, db: Session = Depends(get_static_db)):
    """获取试卷详情，聚合为前端可用结构"""
    paper = db.query(Paper).filter(Paper.paper_id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    questions = db.query(Question).filter(Question.paper_id == paper_id).all()

    sections = {
        "use_of_english": None,
        "reading_a": [],
        "reading_b": [],
        "translation": None,
        "writing_a": None,
        "writing_b": None,
    }

    grouped_reading = {}

    # reading_b 默认 A-G 选项 (7选5题型)
    READING_B_DEFAULT_OPTIONS = {k: k for k in "ABCDEFG"}

    for q in questions:
        # 解析选项；reading_b 如果 DB 中无选项则兜底 A-G
        raw_options = q.options_json
        if isinstance(raw_options, str):
            try:
                raw_options = json.loads(raw_options)
            except:
                raw_options = None
        
        if raw_options is None and q.section_type == "reading_b":
            raw_options = READING_B_DEFAULT_OPTIONS

        q_data = {
            "q_id": q.q_id,
            "question_number": q.question_number,
            "content": q.content,
            "options": raw_options,
            "q_type": q.q_type,
            "score": q.score,
        }

        st = q.section_type

        if st == "use_of_english":
            if not sections["use_of_english"]:
                sections["use_of_english"] = {"passage": q.passage_text, "questions": []}
            sections["use_of_english"]["questions"].append(q_data)

        elif st in ["reading_a", "reading_b"]:
            gn = q.group_name or "Text 1"
            if st not in grouped_reading:
                grouped_reading[st] = {}
            if gn not in grouped_reading[st]:
                grouped_reading[st][gn] = {"group_name": gn, "passage": q.passage_text, "questions": []}
            grouped_reading[st][gn]["questions"].append(q_data)

        elif st == "translation":
            if not sections["translation"]:
                sections["translation"] = {"passage": q.passage_text, "questions": []}
            sections["translation"]["questions"].append(q_data)

        elif st in ["writing_a", "writing_b"]:
            if not sections[st]:
                sections[st] = {
                    "q_id": q.q_id,
                    "prompt": q.content,
                    "image":  None,   # 收齐后填充
                    "passage": q.passage_text,
                    "questions": [],
                }
            # 优先提取图片：只要找到第一张有效图就定下
            if not sections[st]["image"] and q.image_base64 and len(q.image_base64) > 100:
                sections[st]["image"] = q.image_base64
            # prompt 也优先取非空的
            if not sections[st]["prompt"] and q.content:
                sections[st]["prompt"] = q.content
            # questions 列表（主观题可能有多行）
            sections[st]["questions"].append(q_data)

    if sections["use_of_english"]:
        sections["use_of_english"]["questions"].sort(key=lambda x: x["question_number"] or 0)
    if sections["translation"]:
        sections["translation"]["questions"].sort(key=lambda x: x["question_number"] or 0)

    for st in ["reading_a", "reading_b"]:
        if st in grouped_reading:
            groups = list(grouped_reading[st].values())
            for g in groups:
                g["questions"].sort(key=lambda x: x["question_number"] or 0)
            groups.sort(key=lambda g: g["questions"][0]["question_number"] if g["questions"] else 0)
            sections[st] = groups

    return {
        "id": paper.paper_id,
        "title": paper.title,
        "year": paper.year,
        "sections": sections,
    }


@router.post("/exam/submit_objective")
def submit_objective(data: Dict[str, Any], db: Session = Depends(get_static_db)):
    """
    提交客观题答案。
    - 判断正误
    - 计算伤害（按题型）
    - 写入 femo_profile.db (HP 持久化)
    - 返回判题结果 + 最新 HP
    """
    q_id     = data.get("q_id")
    user_ans = data.get("answer")
    slot_id  = data.get("slot_id", 0) # [Stage 15.0]
    
    print(f"[DEBUG] submit_objective: q_id={q_id}, ans={user_ans}, slot={slot_id}")

    q = db.query(Question).filter(Question.q_id == q_id).first()
    if not q:
        print(f"[DEBUG] Question not found: {q_id}")
        return {"correct": False, "correct_answer": None, "hp_change": 0, "hp": 100}

    is_correct  = (user_ans == q.correct_answer)
    section_type = q.section_type or "reading_a"

    # ── 计算题型伤害 (1:1 等价扣血) ──────────────────────────────────────────
    if is_correct:
        hp_change = 0
    else:
        # 完形填空 0.5 分，阅读 2.0 分
        weight_map = {
            "use_of_english": 0.5,
            "cloze": 0.5,
            "reading_a": 2.0,
            "reading_b": 2.0,
            "reading_c": 2.0,
            "translation": 2.0  # 客观题误判兜底
        }
        # 默认为 2.0 (Reading A/B)
        damage = weight_map.get(section_type, 2.0)
        hp_change = -damage

    # ── 写入数据库 HP ─────────────────────────────────────────
    new_hp = 100  # fallback
    try:
        with get_profile_conn() as pconn:
            ensure_auto_save(pconn)
            
            # Ensure slot exists if not 0? 
            # Ideally slot should exist if user selected it. 
            # But let's be safe: (though helper might not support arbitrary slot creation easily without full schema check)
            # helper ensure_auto_save only checks slot 0.
            # So we might fail if slot doesn't exist.
            # Let's try insert ignore for slot first?
            pconn.execute("INSERT OR IGNORE INTO game_saves (slot_id) VALUES (?)", (slot_id,))
            
            # Read current HP from specific slot
            row = pconn.execute("SELECT hp, max_hp FROM game_saves WHERE slot_id = ?", (slot_id,)).fetchone()
            if row:
                current_hp = row["hp"]
                max_hp     = row["max_hp"]
            else:
                current_hp = 100
                max_hp     = 100
                
            new_hp = max(0, min(max_hp, current_hp + hp_change))
            
            if hp_change != 0:
                pconn.execute("UPDATE game_saves SET hp=?, updated_at=datetime('now', 'localtime') WHERE slot_id=?", (new_hp, slot_id))
                pconn.commit()
            
            # ── [Stage 14.0] 答题记录持久化 ──
            try:
                pconn.execute("""
                    INSERT OR REPLACE INTO user_answers 
                    (slot_id, q_id, section_type, user_answer, is_correct, score, ai_feedback, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
                """, (
                    slot_id,
                    q_id,
                    section_type,
                    str(user_ans),
                    is_correct,
                    q.score if is_correct else 0, # objective score
                    None, # No AI feedback for objective
                ))
                pconn.commit()
            except Exception as e:
                print(f"[exam] Objective save answer failed: {e}")

            # ── [Stage 17.0] 答题轨迹日志 (Append-only, never deleted) ──
            try:
                pconn.execute("""
                    INSERT INTO answer_history_logs
                    (slot_id, q_id, user_answer, score, updated_at)
                    VALUES (?, ?, ?, ?, datetime('now', 'localtime'))
                """, (slot_id, q_id, str(user_ans), q.score if is_correct else 0))
                pconn.commit()
            except Exception as e:
                print(f"[exam] History log insert failed: {e}")

    except Exception as e:
        print(f"[exam] HP 写库失败: {e}")

    # ── 通知 Mia 情绪 ─────────────────────────────────────────
    mood_info = game_mechanics.get_mia_mood(new_hp, max_hp)

    return {
        "correct":        is_correct,
        "correct_answer": q.correct_answer,
        "hp_change":      hp_change,
        "hp":             new_hp,
        "max_hp":         max_hp,
        "mood":           mood_info["mood"],
    }


@router.post("/exam/submit_subjective")
async def submit_subjective(data: Dict[str, Any]):
    """
    提交主观题（翻译 / 作文）。
    - 尝试调用 LLM 批改
    - 失败则 Mock 评分
    - 更新 HP
    """
    q_id         = data.get("q_id", "")
    answer       = data.get("answer", "")
    section_type = data.get("section_type", "translation")
    slot_id      = data.get("slot_id", 0) # [Stage 15.0]

    # ── 按题型决定满分和 HP 消耗 ──
    type_cfg = {
        "translation": {"max_score": 10,  "hp_base": -3},
        "writing_a":   {"max_score": 10,  "hp_base": -4},
        "writing_b":   {"max_score": 20,  "hp_base": -5},
    }
    cfg = type_cfg.get(section_type, {"max_score": 10, "hp_base": -3})
    max_score = cfg["max_score"]

    # ── 3. 尝试 AI 批改 (调用封装好的 Robust Service) ──
    score      = 0.0
    feedback   = ""
    detailed_analysis = ""

    try:
        from app.services.llm_service import llm_service
        
        # 准备上下文
        context_info = {"section_type": section_type}
        
        # 尝试获取题目 context (图、文、参考答案)
        q_image = None
        standard_ans = "略"
        
        from app.db.session import StaticSessionLocal
        sdb = StaticSessionLocal()
        try:
            q_obj = sdb.query(Question).filter(Question.q_id == q_id).first()
            if q_obj:
                # 补充 context_info
                context_info["source_text"] = q_obj.content or q_obj.passage_text or ""
                context_info["topic"] = q_obj.content or ""
                context_info["image_base64"] = q_obj.image_base64  # <--- FIXED: 传递图片
                standard_ans = q_obj.official_analysis or q_obj.correct_answer or "略"
        except Exception:
            pass
        finally:
            sdb.close()

        # 调用 Service
        result = await llm_service.grade_subjective_question(
            question_type=section_type,
            user_text=answer,
            standard_answer=standard_ans,
            context_info=context_info
        )
        
        # 提取结果
        score = float(result.get("score", 0.0))
        feedback = result.get("feedback") or result.get("mia_comment") or "本喵累了，暂时没评语喵。"
        detailed_analysis = str(result.get("detailed_analysis") or result.get("suggestions") or result.get("key_points_missed") or "暂无详细分析。")

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"\n[🔥 FATAL ERROR in submit_subjective]\n{error_trace}\n")
        # 降级处理，不再抛出 500
        score = 0
        feedback = f"评分系统暂时故障: {str(e)}"
        detailed_analysis = "Error in AI Service."

    # 4. Score Clamping (强制熔断)
    final_score = max(0.0, min(score, max_score))
    score = round(final_score, 1)

    # ── 5. HP 更新 (1:1 等价扣血) ──
    # 丢多少分，扣多少血
    lost_score = max_score - score
    hp_change  = -lost_score
    new_hp    = 100
    max_hp    = 100
    try:
        with get_profile_conn() as pconn:
            ensure_auto_save(pconn)
            
            # Ensure slot exists
            pconn.execute("INSERT OR IGNORE INTO game_saves (slot_id) VALUES (?)", (slot_id,))
            
            # Read HP
            row = pconn.execute("SELECT hp, max_hp FROM game_saves WHERE slot_id = ?", (slot_id,)).fetchone()
            if row:
                current_hp = row["hp"]
                max_hp     = row["max_hp"]
            else:
                current_hp = 100
                max_hp     = 100
            
            new_hp     = max(0, min(max_hp, current_hp + hp_change)) # 允许扣为0
            
            pconn.execute("UPDATE game_saves SET hp=?, updated_at=datetime('now', 'localtime') WHERE slot_id=?", (new_hp, slot_id))
            pconn.commit()

            # ── [Stage 14.0] 答题记录持久化 ──
            try:
                pconn.execute("""
                    INSERT OR REPLACE INTO user_answers 
                    (slot_id, q_id, section_type, user_answer, is_correct, score, ai_feedback, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
                """, (
                    slot_id,
                    q_id,
                    section_type,
                    answer,
                    (score >= max_score * 0.6), # Pass/Fail heuristic
                    score,
                    feedback,
                ))
                pconn.commit()
            except Exception as e:
                print(f"[exam] Subjective save answer failed: {e}")

            # ── [Stage 17.0] 答题轨迹日志 (Append-only) ──
            try:
                pconn.execute("""
                    INSERT INTO answer_history_logs
                    (slot_id, q_id, user_answer, score, updated_at)
                    VALUES (?, ?, ?, ?, datetime('now', 'localtime'))
                """, (slot_id, q_id, answer, score))
                pconn.commit()
            except Exception as e:
                print(f"[exam] History log insert (subjective) failed: {e}")

    except Exception as e:
        print(f"[exam] subjective HP 写库失败: {e}")

    return {
        "score":        score,
        "max_score":    max_score,
        "mia_feedback": feedback,
        "detailed_analysis": detailed_analysis,
        "hp_change":    hp_change,
        "hp":           new_hp,
        "max_hp":       max_hp,
    }


@router.get("/exam/{paper_id}/progress")
def get_exam_progress(paper_id: str, slot_id: int = 0, db: Session = Depends(get_static_db)):
    """
    [Stage 17.0] 获取试卷作答进度
    Returns: { answered, total, percentage }
    """
    # Get total questions from static DB
    total = db.query(Question).filter(Question.paper_id == paper_id).count()

    answered = 0
    try:
        with get_profile_conn() as pconn:
            ensure_auto_save(pconn)
            # Get q_ids for this paper
            q_ids = [q.q_id for q in db.query(Question).filter(Question.paper_id == paper_id).all()]
            if q_ids:
                placeholders = ",".join(["?"] * len(q_ids))
                row = pconn.execute(
                    f"SELECT COUNT(*) as cnt FROM user_answers WHERE slot_id=? AND q_id IN ({placeholders})",
                    (slot_id, *q_ids)
                ).fetchone()
                answered = row["cnt"] if row else 0
    except Exception as e:
        print(f"[exam] Progress calc failed: {e}")

    pct = round((answered / total * 100), 1) if total > 0 else 0.0
    return {"answered": answered, "total": total, "percentage": pct}


@router.delete("/exam/{paper_id}/reset")
def reset_paper_progress(paper_id: str, slot_id: int = 0, db: Session = Depends(get_static_db)):
    """
    [Stage 17.0] 重置试卷当前面板 (保留 answer_history_logs)
    Deletes all user_answers for slot+paper. Historical logs survive.
    """
    deleted = 0
    try:
        with get_profile_conn() as pconn:
            ensure_auto_save(pconn)
            q_ids = [q.q_id for q in db.query(Question).filter(Question.paper_id == paper_id).all()]
            if q_ids:
                placeholders = ",".join(["?"] * len(q_ids))
                cursor = pconn.execute(
                    f"DELETE FROM user_answers WHERE slot_id=? AND q_id IN ({placeholders})",
                    (slot_id, *q_ids)
                )
                pconn.commit()
                deleted = cursor.rowcount
                print(f"[exam] Reset paper {paper_id} slot {slot_id}: deleted {deleted} rows")
    except Exception as e:
        print(f"[exam] Reset failed: {e}")
        return {"success": False, "error": str(e)}

    return {"success": True, "deleted": deleted}
