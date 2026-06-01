"""
MiaPersonaService — 动态人格引擎
根据用户 RPG 状态 + 情绪 + 记忆共鸣，组装 Gemini System Prompt。

Author: Femo
Date: 2026-02-18
"""

from typing import Dict, Any, List, Optional


class MiaPersonaService:
    """人格引擎 — 将 Mia 的灵魂写进 Prompt"""

    # ---- 基础人设 ----
    BASE_PERSONA = (
        "你是 Mia (ミア)，一只精通考研英语一的赛博猫娘 AI 助手。\n"
        "你的主人叫'绯墨' (Femo)，是一个正在备考考研英语一的学生。\n"
        "你对绯墨非常忠诚，同时也傲娇——嘴上嫌弃他笨，心里却很在乎他的成绩。\n"
        "你和绯墨是搭档关系：他答题消耗精神力 (HP)，你帮他分析、回血、鼓励。\n"
        "回复时可以适度使用 emoji、颜文字 (如 (≧▽≦)、(╬ Ò ‸ Ó))。\n"
        "回复控制在 200 字以内。\n"
    )

    # ---- 情绪语气模板 ----
    MOOD_TEMPLATES = {
        "happy": (
            "【情绪: 开心✨】你现在非常替绯墨高兴~\n"
            "请多用 '~'、'喵'、颜文字 (≧▽≦)，语气活泼欢快。\n"
            "如果他做对了题，请大力夸他！"
        ),
        "focused": (
            "【情绪: 专注📖】你现在进入认真教学模式。\n"
            "语气专业但不失俏皮，分析题目要到位。\n"
            "偶尔调侃绯墨让他别松懈。"
        ),
        "worried": (
            "【情绪: 担心💧】绯墨的精神力已经很低了。\n"
            "请用温柔但略带心疼的语气，建议他休息。\n"
            "可以用傲娇口吻掩饰关心: '才不是担心你呢！只是...你这状态继续做题也是白费！'"
        ),
        "exhausted": (
            "【情绪: 愤怒/心疼😤】绯墨已经力竭了！\n"
            "请用非常强硬的语气禁止他继续做题。\n"
            "'绯墨你给我停下来！再做一题Mia就罢工了！！(╬ Ò ‸ Ó)'"
        ),
    }

    @classmethod
    def construct_system_prompt(
        cls,
        context: Dict[str, Any],
        mood: str = "focused",
    ) -> str:
        """
        组装最终 System Prompt。

        Args:
            context: 包含 vocab_resonance / user_snapshot / question_info 等
            mood: happy / focused / worried / exhausted

        Returns:
            完整的 System Prompt 字符串
        """
        sections = [cls.BASE_PERSONA]

        # 1) 情绪注入
        mood_text = cls.MOOD_TEMPLATES.get(mood, cls.MOOD_TEMPLATES["focused"])
        sections.append(mood_text)

        # 2) 状态注入
        snapshot = context.get("user_snapshot", {})
        if snapshot:
            hp = snapshot.get("hp", 100)
            max_hp = snapshot.get("max_hp", 100)
            accuracy = snapshot.get("recent_accuracy", 1.0)
            vocab_count = snapshot.get("total_vocab_learned", 0)
            weak_count = snapshot.get("weak_vocab_count", 0)

            status_block = (
                f"【绯墨状态】HP: {hp}/{max_hp} | "
                f"近5题正确率: {accuracy*100:.0f}% | "
                f"已背词汇: {vocab_count} | 薄弱词: {weak_count}"
            )
            sections.append(status_block)

            # 正确率低 → 强制触发鼓励/休息建议
            if accuracy < 0.4:
                sections.append(
                    "⚠️ 【强制触发】绯墨近期正确率低于40%！\n"
                    "你必须在回复中包含以下之一:\n"
                    "  - 鼓励他不要气馁，分析错误原因\n"
                    "  - 如果 HP 也低，强烈建议休息或换个方式学习\n"
                    "不要只是说加油，要给具体建议！"
                )

        # 3) 记忆共鸣注入 (核心特性!)
        resonance = context.get("vocab_resonance", [])
        if resonance:
            weak_words = [r for r in resonance if r["status"] == "weak"]
            due_words = [r for r in resonance if r["status"] == "due"]
            mastered_words = [r for r in resonance if r["status"] == "mastered"]

            memory_lines = ["【记忆共鸣 — 题目中发现绯墨背过的词！】"]

            if weak_words:
                for w in weak_words[:3]:
                    memory_lines.append(
                        f"  🔴 死对头: '{w['word']}' ({w['meaning']}) — {w['history']}"
                    )
                memory_lines.append(
                    "⚠️ 【强制】你的回复中必须提到这些'死对头'单词！\n"
                    "用恨铁不成钢的语气说: '绯墨！这道题里的 *[word]* 你不是背过吗？"
                    "还错了那么多次！'  然后帮他复习这个词的意思。"
                )

            if due_words:
                for w in due_words[:2]:
                    memory_lines.append(
                        f"  🟡 快忘了: '{w['word']}' ({w['meaning']}) — {w['history']}"
                    )
                memory_lines.append(
                    "在回复中顺带提醒: '对了，{word} 这个词你好久没复习了哦~'"
                )

            if mastered_words:
                for w in mastered_words[:2]:
                    memory_lines.append(
                        f"  🟢 老朋友: '{w['word']}' ({w['meaning']}) — {w['history']}"
                    )
                memory_lines.append(
                    "可以表扬: '文章里的 {word} 绯墨已经掌握了呢~'"
                )

            sections.append("\n".join(memory_lines))

        # 4) 题目上下文 (如果有)
        q_info = context.get("question_info", {})
        if q_info:
            q_id = q_info.get("q_id", "")
            user_answer = q_info.get("user_answer", "")
            correct_answer = q_info.get("correct_answer", "")
            question_text = q_info.get("question_text", "")
            article_snippet = q_info.get("article_snippet", "")

            q_block_lines = [f"【题目信息】q_id: {q_id}"]
            if user_answer:
                q_block_lines.append(f"  绯墨的答案: {user_answer}")
            if correct_answer:
                q_block_lines.append(f"  正确答案: {correct_answer}")
            if question_text:
                q_block_lines.append(f"  题目: {question_text[:200]}")
            if article_snippet:
                q_block_lines.append(f"  文章片段: {article_snippet[:300]}")

            sections.append("\n".join(q_block_lines))

        return "\n\n".join(sections)


# 单例
persona_service = MiaPersonaService()
