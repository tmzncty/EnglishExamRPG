"""
GameMechanicsService - 英语一 (English I) 特化的 RPG 数值引擎
废弃通用公式，为每个题型定义精确的伤害/消耗规则。

题型枚举 (section_type):
  - use_of_english  完形填空   20题 × 0.5分
  - reading_a       传统阅读   20题 × 2分
  - reading_b       新题型7选5  5题 × 2分
  - translation     长难句翻译  5题 × 2分 (主观)
  - writing_a       小作文      满分10分 (主观)
  - writing_b       大作文      满分20分 (主观)

Author: Femo
Date: 2026-02-18
"""

from typing import Dict


# ============================================================================
#  英语一专用伤害计算器
# ============================================================================

class EnglishOneDamageCalculator:
    """
    针对考研英语一的精细化 HP 伤害系统。

    设计理念:
        - 完形填空分值低(0.5)但惩罚重(2HP)，逼你认真做
        - 阅读理解是核心分(2分)，错一题痛5HP
        - 翻译按 AI 评分差值扣血
        - 写作引入"基础消耗" + 低分追加惩罚
    """

    # ---- 客观题: 固定伤害 ----

    @staticmethod
    def use_of_english_damage() -> int:
        """
        完形填空错一题: 固定扣 2 HP
        (痛点: 分值低易忽视，高惩罚逼你认真)
        """
        return 2

    @staticmethod
    def reading_damage() -> int:
        """
        阅读理解 (A 传统 / B 新题型) 错一题: 固定扣 5 HP
        (核心得分点, 错了就是真的心痛)
        """
        return 5

    # ---- 主观题: 动态伤害 ----

    @staticmethod
    def translation_damage(ai_score: float) -> int:
        """
        翻译题(长难句)伤害计算。

        公式: Damage = (2.0 - ai_score) × 2.5
        满分2分: AI打2分 → 扣0HP; AI打1分 → 扣2.5→3HP; AI打0分 → 扣5HP

        Args:
            ai_score: AI 评分 (0.0 - 2.0, 步长 0.5)

        Returns:
            HP 损失值 (>= 0)
        """
        ai_score = max(0.0, min(2.0, ai_score))
        raw = (2.0 - ai_score) * 2.5
        return max(0, round(raw))

    @staticmethod
    def writing_damage(question_type: str, ai_score: float) -> Dict[str, int]:
        """
        写作题伤害计算 (基础消耗 + 追加惩罚)。

        机制:
            1. 基础消耗 (Base Cost): 提交即扣 5 HP (脑力消耗)
            2. 追加惩罚: AI 评分低于及格线时额外扣血
               - writing_a (小作文, 满分10): 及格线 6分, 追加 = (6 - score) × 1.0
               - writing_b (大作文, 满分20): 及格线 12分, 追加 = (12 - score) × 1.0

        Args:
            question_type: 'writing_a' 或 'writing_b'
            ai_score:      AI 评分

        Returns:
            {"base_cost": 5, "penalty": int, "total": int}
        """
        BASE_COST = 5

        if question_type == "writing_a":
            threshold = 6.0
        else:  # writing_b
            threshold = 12.0

        # 追加惩罚: 低于及格线才扣
        penalty = 0
        if ai_score < threshold:
            penalty = max(0, round((threshold - ai_score) * 1.0))

        return {
            "base_cost": BASE_COST,
            "penalty": penalty,
            "total": BASE_COST + penalty,
        }

    # ---- 统一入口 ----

    @classmethod
    def calculate(
        cls,
        section_type: str,
        ai_score: float = 0.0,
        is_correct: bool = False,
    ) -> int:
        """
        统一的 HP 损失计算入口。

        Args:
            section_type: 题型 (use_of_english / reading_a / reading_b /
                           translation / writing_a / writing_b)
            ai_score:     AI 评分 (仅主观题需要)
            is_correct:   是否答对 (仅客观题需要)

        Returns:
            总 HP 损失值
        """
        st = section_type.lower()

        # --- 客观题 ---
        if st == "use_of_english":
            return 0 if is_correct else cls.use_of_english_damage()

        if st in ("reading_a", "reading_b"):
            return 0 if is_correct else cls.reading_damage()

        # --- 主观题 ---
        if st == "translation":
            return cls.translation_damage(ai_score)

        if st in ("writing_a", "writing_b"):
            result = cls.writing_damage(st, ai_score)
            return result["total"]

        # 未知题型: fallback 扣 3 HP
        return 0 if is_correct else 3


# ============================================================================
#  回血机制 (保持不变)
# ============================================================================

class HealingCalculator:
    """精神力恢复计算"""

    @staticmethod
    def heal_from_vocab_review(quality: int) -> int:
        """背单词回血: quality >= 4 → +1 HP"""
        return 1 if quality >= 4 else 0

    @staticmethod
    def heal_from_context_lookup() -> int:
        """上下文查词共鸣: 固定 +2 HP"""
        return 2


# ============================================================================
#  Mia 情绪状态机 (保持不变)
# ============================================================================

class MoodStateMachine:
    """根据 HP 百分比映射 Mia 的情绪状态和 Prompt 前缀"""

    @staticmethod
    def get_mia_mood(current_hp: int, max_hp: int) -> Dict[str, str]:
        if max_hp <= 0:
            max_hp = 1

        ratio = current_hp / max_hp

        if current_hp <= 0:
            return {
                "mood": "exhausted",
                "prompt_prefix": (
                    "绯墨已经彻底力竭了，禁止他继续做题，"
                    "强制要求他去休息喵！"
                ),
            }
        if ratio < 0.30:
            return {
                "mood": "worried",
                "prompt_prefix": (
                    "绯墨的精神力已经见底了，请用非常心疼、"
                    "甚至带点生气的傲娇语气，强烈建议他去休息"
                    "或背几个单词回回血。"
                ),
            }
        if ratio < 0.80:
            return {
                "mood": "focused",
                "prompt_prefix": (
                    "绯墨正在稳步推进，请用专业且带有一点小俏皮"
                    "的语气给他分析题目。"
                ),
            }
        return {
            "mood": "happy",
            "prompt_prefix": (
                "绯墨现在状态极佳，请用崇拜、开心的语气夸奖他。"
            ),
        }


# ============================================================================
#  兼容层: 保留旧的 game_mechanics 单例接口
# ============================================================================

class GameMechanicsService:
    """向后兼容的统一入口"""

    damage = EnglishOneDamageCalculator
    healing = HealingCalculator
    mood = MoodStateMachine

    # 旧接口兼容
    @classmethod
    def calculate_hp_loss(cls, q_type: str, max_score: float = 0,
                          actual_score: float = 0, difficulty: float = 1.0) -> int:
        """兼容旧调用: 自动映射到新的 EnglishOneDamageCalculator"""
        section_map = {
            "cloze": "use_of_english",
            "reading": "reading_a",
        }
        section = section_map.get(q_type.lower(), q_type.lower())
        is_correct = (actual_score >= max_score) if max_score > 0 else False
        return cls.damage.calculate(section, ai_score=actual_score, is_correct=is_correct)

    @classmethod
    def heal_from_vocab_review(cls, quality: int) -> int:
        return cls.healing.heal_from_vocab_review(quality)

    @classmethod
    def heal_from_context_lookup(cls) -> int:
        return cls.healing.heal_from_context_lookup()

    @classmethod
    def get_mia_mood(cls, current_hp: int, max_hp: int) -> Dict[str, str]:
        return cls.mood.get_mia_mood(current_hp, max_hp)


# 模块级单例
game_mechanics = GameMechanicsService()
