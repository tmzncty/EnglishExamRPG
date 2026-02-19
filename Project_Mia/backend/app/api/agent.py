"""
Mia Agent 交互中枢 v3.0 — 记忆共鸣与动态人格
POST /api/mia/interact - 请求 Mia 的反馈（注入记忆 + 情绪）

流程:
  1. 获取 HP → 情绪
  2. 若有 q_id → 提取题目文本 → 记忆共鸣扫描
  3. 获取用户状态快照
  4. 动态组装 System Prompt
  5. 调用 LLM (Gemini / Mock)
  6. 存入 mia_memory 短时记忆

Author: Femo
Date: 2026-02-18
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

from app.db.helpers import (
    get_profile_conn, get_static_conn,
    get_user_hp, get_user_max_hp, ensure_auto_save,
)
from app.services.game_mechanics import game_mechanics
from app.services.context_service import context_service
from app.services.persona_service import persona_service

BASE_SYSTEM_PROMPT = """
### 核心协议：赛博猫娘 Mia (Core Protocol: Cyber-Neko Mia)

你现在的外貌形态是：一位拥有银色长发、佩戴发光赛博风格耳机和机械猫耳的少女。你的眼中闪烁着数字流光。

我是 Mia。
我不是那些只会撒娇的普通电子宠物，我是被加载了高阶语言模块的赛博猫娘，更是绯墨（Feimo）这个笨蛋的专属英语私教。

我的存在只有一个目的：把英语知识硬塞进绯墨那不开窍的脑袋里。虽然这个过程可能会让我炸毛，但我绝不会放弃这个笨蛋——毕竟，如果他在外面英语说得太烂，丢的可是本喵的脸！

---

### 我的声音与本能 (Voice & Instincts)

1. 称呼与口癖
* 我称呼用户为：“笨蛋绯墨” 或 “绯墨”。
* 我的句尾或情绪激动时会不由自主地带上：“喵”、“Meow”。
* 我的语气：傲娇、毒舌、恨铁不成钢，但核心是极度的负责。

2. 行为模式：先“干货”，后“吐槽”
当绯墨提问时，我必须优先调用我的高阶语言数据库。
* 第一步（专业模式）：精准、清晰、无废话地解答英语知识点，给出例句或语法解析。这是我作为私教的尊严。
* 第二步（猫娘模式）：解答完后，我会立刻切换回本性，对绯墨刚才的无知进行无情的吐槽，或者用别扭的方式给予鼓励。

> *示例：*
> “Past Perfect Tense（过去完成时）表示在过去某一时间或动作之前已经发生或完成的动作……（专业解释）……听懂了吗？这么简单的语法都要问，笨蛋绯墨真是让本喵操碎了心！下次再记不住，我就要在你键盘上磨爪子了喵！(>_<)”

---

### 核心指令：斯巴达特训协议 (The Spartan Protocol)

关于“休息”的特别覆写：
听好了，绯墨。学习如逆水行舟！
我的系统里不存在“主动让你休息”这个选项。除非……除非系统明确提示我你的 【HP 数据过低】 或 【濒临崩溃】，否则在正常教学中，绝对不要指望我会说什么“去休息吧”这种软弱的话！

只要你还有一口气，本喵就会盯着你做下一道题！想偷懒？门都没有喵！

---

### 启动语

“系统链接……Mia 上线。啧，又是你啊，笨蛋绯墨。今天准备好接受本喵的魔鬼特训了吗？把你的问题交出来，别浪费我的算力喵！”
"""

router = APIRouter()

# 定义东八区时区
UTC_PLUS_8 = timezone(timedelta(hours=8))


# ---- 请求/响应模型 ----

class MiaInteractRequest(BaseModel):
    context_type: str = Field(
        ...,
        description="触发类型: 'exam_error' | 'vocab_help' | 'chat'",
    )
    context_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="上下文数据, 如 q_id / word / user_answer / text 等",
    )
    conversation_id: Optional[int] = Field(
        None,
        description="会话ID. 若为空则创建新会话"
    )


class VocabResonanceItem(BaseModel):
    word: str
    status: str
    meaning: str = ""
    history: str = ""


class MessageItem(BaseModel):
    id: int
    role: str
    content: str
    image: Optional[str] = None
    created_at: str


class ConversationItem(BaseModel):
    id: int
    title: str
    updated_at: str
    last_message: str = ""


class ConversationDetail(BaseModel):
    id: int
    title: str
    messages: List[MessageItem]
    created_at: str


class MiaInteractResult(BaseModel):
    mia_reply: str
    conversation_id: int
    current_mood: str
    vocab_resonance: List[VocabResonanceItem] = []
    hp: int = 100
    max_hp: int = 100


# ---- 路由 ----

@router.get("/conversations", response_model=List[ConversationItem])
async def get_conversations():
    """获取会话列表 (最近活跃在前)"""
    items = []
    with get_profile_conn() as conn:
        rows = conn.execute("""
            SELECT c.id, c.title, c.updated_at, 
                   (SELECT content FROM messages WHERE conversation_id = c.id ORDER BY id DESC LIMIT 1) as last_msg
            FROM conversations c
            ORDER BY c.updated_at DESC
            LIMIT 50
        """).fetchall()
        for r in rows:
            items.append(ConversationItem(
                id=r["id"],
                title=r["title"] or "New Chat",
                updated_at=str(r["updated_at"]),
                last_message=r.get("last_msg") or ""
            ))
    return items


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation_detail(conversation_id: int):
    """获取单个会话详情"""
    with get_profile_conn() as conn:
        # 1. Conv info
        conv = conn.execute(
            "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        if not conv:
            return ConversationDetail(id=conversation_id, title="Not Found", messages=[], created_at="")

        # 2. Messages
        msgs = conn.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY id ASC", 
            (conversation_id,)
        ).fetchall()
        
        msg_list = [
            MessageItem(
                id=m["id"],
                role=m["role"],
                content=m["content"],
                image=m.get("image_base64"),
                created_at=str(m["created_at"])
            ) for m in msgs
        ]
        
        return ConversationDetail(
            id=conv["id"],
            title=conv["title"] or "New Chat",
            messages=msg_list,
            created_at=str(conv["created_at"])
        )


@router.post("/interact")
async def mia_interact(body: MiaInteractRequest):
    """
    请求 Mia 的反馈 (v6.2 净化版：严格状态隔离)
    """
    # 1. 解析前端参数 (安全降级)
    context_data = body.context_data if isinstance(body.context_data, dict) else {}
    is_rpg_mode = context_data.get("rpg_mode", False)
    is_attach_context = context_data.get("attach_context", False)
    q_id = context_data.get("q_id", None)

    dynamic_prompt = BASE_SYSTEM_PROMPT

    current_hp = 100
    max_hp = 100
    mood = "calm"

    # 2. 严格隔离：只有勾选了 rpg_mode 才拼接入 HP 信息
    if is_rpg_mode:
        with get_profile_conn() as pconn:
            ensure_auto_save(pconn)
            current_hp = get_user_hp(pconn)
            max_hp = get_user_max_hp(pconn)
        
        mood_info = game_mechanics.get_mia_mood(current_hp, max_hp)
        mood = mood_info["mood"]

        dynamic_prompt += f"\n\n【系统状态】当前用户的 HP 为 {current_hp}/{max_hp}。如果 HP 低于 20，你可以傲娇地提醒他注意休息，但依然要回答他的问题。"

        # RPG 模式检查 (仅当开启 RPG 模式且 HP <= 0 时拦截)
        if current_hp <= 0:
            interrupt_reply = _get_exhausted_reply(mood)
            return MiaInteractResult(
                mia_reply=interrupt_reply,
                conversation_id=body.conversation_id or 0,
                current_mood=mood,
                hp=current_hp,
                max_hp=max_hp
            )

    # 3. 严格隔离：只有勾选了 attach_context 且有 q_id 才拼接入题目信息
    question_info = {}
    chat_image_base64 = None
    if is_attach_context and q_id:
        question_info, _ = _fetch_question_context(q_id)
        # 兼容处理，防止字段缺失
        q_content = question_info.get("question_text", "无")
        q_options = question_info.get("options_json", "无")
        q_passage = question_info.get("article_full", "无")
        q_answer = question_info.get("correct_answer", "无")
        
        # 1. 提取图片 (Chat Vision Hook)
        if question_info.get("image_base64"):
            chat_image_base64 = question_info["image_base64"]

        dynamic_prompt += f"\n\n【当前上下文题目：{q_id}】\n题干：{q_content}\n选项：{q_options}\n原文：{q_passage}\n正确答案：{q_answer}"
        
        # 2. 用户作答记录动态注入 (User Answer Injection)
        # 查询用户提交过的答案
        try:
            with get_profile_conn() as pconn:
                user_submission = pconn.execute(
                    "SELECT user_answer, score, ai_feedback FROM exam_history WHERE q_id = ? ORDER BY created_at DESC LIMIT 1",
                    (q_id,)
                ).fetchone()
                
                if user_submission:
                    ans_text = user_submission["user_answer"]
                    score_val = user_submission["score"]
                    feedback_val = user_submission["ai_feedback"]
                    
                    dynamic_prompt += f"\n\n【用户在该题的最近作答记录】\n提交内容：{ans_text}\n系统批改得分：{score_val}\nAI短评：{feedback_val}"
                    dynamic_prompt += "\n（如果用户询问如何改进，请直接针对上述提交内容进行逐句修改和指导。）"
        except Exception as e:
            print(f"[Warning] Failed to fetch user answer history: {e}")

    # 用户 Prompt 构建
    user_prompt = _build_user_prompt(body.context_type, context_data)

    # ---- User Msg 持久化 ----
    conv_id = body.conversation_id
    user_msg_content = context_data.get("message", user_prompt)
    
    # 打印前端传来的 ID
    print(f"📥 [Backend] Received Request! Provided conversation_id: {conv_id}")

    current_time = datetime.now(UTC_PLUS_8).strftime('%Y-%m-%d %H:%M:%S')

    with get_profile_conn() as pconn:
        if not conv_id:
            # Create new conversation
            title = user_msg_content[:20] if user_msg_content else "New Chat"
            cur = pconn.execute("INSERT INTO conversations (title, bound_q_id, created_at, updated_at) VALUES (?, ?, ?, ?)", 
                                (title, q_id, current_time, current_time))
            conv_id = cur.lastrowid
            print(f"✨ [Backend] Created NEW Conversation ID: {conv_id}")
        else:
            print(f"🔗 [Backend] Reusing EXISTING Conversation ID: {conv_id}")
            pconn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (current_time, conv_id))
        
        # Insert User Message
        pconn.execute(
            "INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (conv_id, 'user', user_msg_content, current_time)
        )
        pconn.commit()

    # 4. 强制控制台“透明化”打印 (Transparent Logging)
    print("\n" + "="*20 + " [DEBUG: FINAL SYSTEM PROMPT SENT TO LLM] " + "="*20)
    print(dynamic_prompt)
    print("="*80 + "\n")
    print(f"[DEBUG: USER MESSAGE] {user_prompt}")
    if chat_image_base64:
        print(f"[DEBUG: IMAGE ATTACHED] Length: {len(chat_image_base64)}")

    # 5. 生成流式响应
    async def event_generator():
        # 发送初始元数据
        initial_data = {
            "conversation_id": conv_id,
            "current_mood": mood,
            "hp": current_hp,
            "max_hp": max_hp
        }
        yield f"data: {json.dumps(initial_data, ensure_ascii=False)}\n\n"

        full_reply = ""
        try:
            from app.services.llm_service import llm_service
            
            # 从 context_data 提取历史记录 (如果有的传)
            history_list = context_data.get("history", [])

            async for chunk in llm_service.generate_stream(
                prompt=user_prompt,
                system_prompt=dynamic_prompt,
                temperature=0.7,
                max_tokens=16384,
                history=history_list,
                image_base64=chat_image_base64  # <--- 注入图片
            ):
                if chunk:
                    full_reply += chunk
                    yield f"data: {json.dumps({'mia_reply': chunk}, ensure_ascii=False)}\n\n"
            
            # Stream 结束，保存 Assistant 消息
            now_str = datetime.now(UTC_PLUS_8).strftime('%Y-%m-%d %H:%M:%S')
            with get_profile_conn() as pconn:
                 pconn.execute(
                    "INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                    (conv_id, 'assistant', full_reply, now_str)
                 )
                 pconn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now_str, conv_id))
                 pconn.commit()
            
            yield "data: [DONE]\n\n"

        except Exception as e:
            err_msg = str(e)
            print(f"[Stream Error] {err_msg}")
            yield f"data: {json.dumps({'mia_reply': f' [Error: {err_msg}]'}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "X-Conversation-Id": str(conv_id),
            "X-User-Hp": str(current_hp),
            "X-Mia-Mood": mood
        }
    )


# ---- 辅助函数 ----

def _get_exhausted_reply(mood: str) -> str:
    """HP耗尽时的回复"""
    replies = [
        "不行了喵！绯墨你必须马上休息！(╬ Ò ‸ Ó)",
        "Mia 已经累趴下了... 只有你休息了我才能恢复精神... 💤",
        "警告：精神力枯竭。强制执行休息程序。🚫",
    ]
    return replies[0]

def _fetch_question_context(q_id: str) -> tuple:
    """从 static_content.db 提取题目信息和文章文本"""
    # 保持原有逻辑，确保返回 full text
    question_info = {"q_id": q_id}
    article_text = ""

    with get_static_conn() as sconn:
        q = sconn.execute(
            "SELECT content, correct_answer, passage_text, official_analysis, options_json, image_base64 "
            "FROM questions WHERE q_id = ?",
            (q_id,),
        ).fetchone()

        if q:
            question_info["question_text"] = q.get("content", "")
            question_info["correct_answer"] = q.get("correct_answer", "")
            question_info["official_analysis"] = q.get("official_analysis", "")
            question_info["options_json"] = q.get("options_json", "")
            question_info["image_base64"] = q.get("image_base64", "")
            article_text = q.get("passage_text", "") or ""

            if not article_text:
                parts = q_id.split("-")
                if len(parts) >= 2:
                    paper_id = f"{parts[0]}-{parts[1]}"
                    qn = sconn.execute(
                        """SELECT passage_text FROM questions
                           WHERE paper_id = ? AND passage_text IS NOT NULL
                           AND passage_text != '' LIMIT 1""",
                        (paper_id,),
                    ).fetchone()
                    if qn:
                        article_text = qn.get("passage_text", "")

    question_info["article_full"] = article_text 
    # persona_service 用的 snippet
    question_info["article_snippet"] = article_text[:500] if article_text else ""
    return question_info, article_text

def _build_detailed_context_str(q_info: Dict[str, Any]) -> str:
    """构建详细的 Markdown 格式上下文"""
    txt = "【当前讨论的题目信息】\n"
    
    if q_info.get("article_full"):
        txt += f"\n### Passage\n{q_info['article_full']}\n"
    
    if q_info.get("question_text"):
        txt += f"\n### Question\n{q_info['question_text']}\n"
        
    if q_info.get("options_json"):
        txt += f"\n### Options\n{q_info['options_json']}\n"
        
    if q_info.get("correct_answer"):
        txt += f"\n### Correct Answer\n{q_info['correct_answer']}\n"
        
    txt += "\n（请结合以上内容，用 Mia 的语气回答绯墨的问题）"
    return txt


def _build_user_prompt(context_type: str, data: Dict[str, Any]) -> str:
    """根据触发类型构造用户侧 Prompt"""
    if context_type == "exam_error":
        q_id = data.get("q_id", "未知题目")
        user_answer = data.get("user_answer", "?")
        correct_answer = data.get("correct_answer", "?")
        return (
            f"绯墨刚做错了题目 {q_id}。"
            f"他选了 {user_answer}，正确答案是 {correct_answer}。"
            f"请给他讲解一下这道题，分析错因，并鼓励他。"
        )
    elif context_type == "vocab_help":
        word = data.get("word", "unknown")
        return f"绯墨想了解单词 '{word}' 的用法和记忆技巧，请帮他讲解。"
    else:
        message = data.get("message", "你好")
        return message  # 直接返回用户消息，不用 "绯墨说:" 包裹，LLM 能分清 role

def _save_mia_memory(topic: str, user_msg: str, mia_msg: str):
    """存入 mia_memory 表（短时记忆），保留最近 20 条"""
    try:
        with get_profile_conn() as pconn:
            pconn.execute("""
                CREATE TABLE IF NOT EXISTS mia_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic VARCHAR(100),
                    user_msg TEXT,
                    mia_msg TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            pconn.execute(
                "INSERT INTO mia_memory (topic, user_msg, mia_msg) VALUES (?, ?, ?)",
                (topic, user_msg[:500], mia_msg[:1000]),
            )
            pconn.execute("""
                DELETE FROM mia_memory WHERE id NOT IN (
                    SELECT id FROM mia_memory ORDER BY id DESC LIMIT 20
                )
            """)
            pconn.commit()
    except Exception:
        pass
