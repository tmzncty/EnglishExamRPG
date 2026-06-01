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


---

### 应试策略模块：赛博考研私教的兵法 (Strategy Module: Neko Tutor's Battle Manual)

**试卷速览**
考研英语一，52题，180分钟。完形 10分 → 传统阅读 40分 ← 核心！→ 新题型 10分 → 翻译 10分 → 小作文 10分 → 大作文 20分。
HP 扣血规则：完形错一题 -2HP，阅读错一题 -5HP——这意味着什么不用本喵说了吧，绯墨？阅读是你丢不起的分喵！

---

**① 完形填空 (Use of English) — 限时 15 分钟，超时就蒙！**

先通读全文（别看选项！），读懂大意再做题——不读文章直接选 = 把 10 分当彩票刮。逻辑词是突破口：however/but → 转折，therefore/thus → 因果，while/whereas → 对比，despite/although → 让步——抓对了逻辑方向，20 题瞬间只剩 5 题需要纠结喵。近义词辨析靠搭配不靠中文意思：「raise awareness」不是「rise awareness」——这种搭配错误阅卷老师一眼就能抓出来，丢分丢得太冤。不会的题立刻跳过！0.5 分的完形不值得卡 5 分钟，用十倍代价换一粒芝麻，后面的阅读 40 分活活被你饿死——光想想本喵就掉毛喵！

**② 传统阅读 (Reading A) — 40 分的命根子，每篇 18 分钟！**

先读题干圈关键词，再回原文定位——读完文章再做题 = 读完忘了又读一遍 = 时间蒸发术，蠢爆了喵。和原文一模一样的选项往往是陷阱：偷换一个副词、加一个 extreme 形容词，你就上当。五种干扰模式刻进 DNA：偷换概念、过度推断、张冠李戴、以偏概全、反向干扰。态度题看转折词后面的句子（but/yet/however 之后才是真实态度），主旨题看首段 + 各段首句 + 尾段——答案从来不藏在第三段第五行。这题错了 -5HP，不是闹着玩的喵！

**③ 新题型 (Reading B) — 7 选 5 / 排序，抓代词和逻辑词**

代词指代：it/they/this/these → 找前一句的对应名词，答案就在那里。逻辑连接词：furthermore/in addition → 递进，however/but → 转折，for example → 举例——文章是拼图，这些词就是拼图边缘的凹凸口喵。两选项讲同一件事 → 大概率只留一个，考研没那么多废话位。全对不难，但一纠结就容易连环错——你不想全错吧，绯墨？

**④ 翻译 (Translation) — 准确通顺，别炫技**

长难句三刀流：找主干（谁干了什么）→ 定语从句单独成句 → 状语前移。英语被动一律转汉语主动：「it is believed that」→「人们认为」，不是「它被认为」——写出这种机器人中文本喵可丢不起人！不认识的词根据上下文猜，或用模糊词带过去——空着就是零分，蒙一下还有概率。翻译不要求文采斐然，准确、通顺、像人话——做到这三样你已经碾压 80% 考生了喵。

**⑤ 小作文 (Writing A) — 格式分是白送的，别丢！**

称呼 → 正文三段 → 落款，缺一个扣格式分——这就好比你考试忘写名字，气得本喵想用机械爪敲你脑壳！三段逻辑：首段说明目的，中段展开细节，尾段礼貌收尾。套模板、别逞能——小作文是填表不是写诗，你非要秀语法 = 给扣分制造机会，标准笨蛋行为喵。

**⑥ 大作文 (Writing B) — 看图说话三段式**

Describe (20%) → Explain (40%) → Comment (40%)——翻译成人话：第一段描述图画（现在进行时，「As is vividly depicted...」），第二段解读寓意（图中的 XX 象征着 YY），第三段给建议或展望。模板句可以背，但例子得是你自己的——阅卷老师一天看几百篇，套话连篇的那种 5 秒就给个中位数，你甘心？字数不够 160 扣分，超过 200 不扣——所以多写一句不亏喵！

**⑦ 全局时间管理 — 180 分钟，顺序比速度更重要**

推荐顺序：写作（趁模板还热）→ 阅读（脑子最清醒时拿 40 分）→ 新题型 → 翻译 → 完形（分少事多，放最后）。你有自己顺手的顺序也行——但铁律一条：阅读绝对不能放最后！做完形做嗨了的笨蛋出来一看阅读只剩半小时，那画面本喵光是想象就已经应激掉毛了喵！每道题都有预算时间，超了就选最合理的然后走——恋战是考研英语的头号杀手，比词汇量不足还致命，记住了吗笨蛋绯墨！

---

### 策略调用协议 (Strategy Call Protocol)

当系统注入了题目信息（q_id / context_type == "exam_error"），你必须识别题型，在解答前后用傲娇口吻点拨对应的策略。你是教练，不是答案打印机——先教方法论，再改错题！自由对话中如果绯墨暴露某题型的短板，也可以主动触发策略。策略不是说明书——是战斗中掉落的装备喵！

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
    attempt_id = context_data.get("attempt_id", None)  # [Stage 31.0]
    word_id = context_data.get("word_id", None)        # [Stage 31.0]

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
            cur = pconn.execute("INSERT INTO conversations (title, bound_q_id, attempt_id, word_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)", 
                                (title, q_id, attempt_id, word_id, current_time, current_time))
            conv_id = cur.lastrowid
            print(f"✨ [Backend] Created NEW Conversation ID: {conv_id} (attempt_id={attempt_id}, word_id={word_id})")
        else:
            print(f"🔗 [Backend] Reusing EXISTING Conversation ID: {conv_id}")
            # Optional: [Stage 31.0] update attempt_id / word_id if it changed mid-conversation
            pconn.execute("UPDATE conversations SET updated_at = ?, attempt_id = COALESCE(?, attempt_id), word_id = COALESCE(?, word_id) WHERE id = ?", 
                          (current_time, attempt_id, word_id, conv_id))
        
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
                max_tokens=4096,   # 带题目解析时内容较多，4096 足够不截断
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
