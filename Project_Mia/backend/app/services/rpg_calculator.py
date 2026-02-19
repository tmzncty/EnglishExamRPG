"""
RPG数值计算引擎 - Project_Mia
负责计算精神力(HP)的损失和恢复

Author: Femo
Date: 2026-02-15
"""

from typing import Dict, Optional
from enum import Enum

class QuestionType(Enum):
    """题型枚举"""
    CLOZE = "cloze"              # 完形填空
    READING = "reading"          # 阅读理解
    TRANSLATION = "translation"  # 翻译
    WRITING = "writing"          # 写作


class DamageCalculator:
    """
    精神力损伤计算器
    公式: HP损失 = 基础伤害 × 题型权重(α) × 难度系数(β)
    """
    
    # 题型权重配置 (α系数)
    TYPE_WEIGHTS = {
        QuestionType.CLOZE: 0.5,        # 完形填空: 0.5倍
        QuestionType.READING: 1.0,      # 阅读理解: 1.0倍
        QuestionType.TRANSLATION: 1.5,  # 翻译: 1.5倍
        QuestionType.WRITING: 2.0,      # 写作: 2.0倍
    }
    
    # 难度系数映射 (β系数)
    DIFFICULTY_MULTIPLIERS = {
        1: 0.5,   # 简单: 0.5倍
        2: 0.75,  # 较简单: 0.75倍
        3: 1.0,   # 中等: 1.0倍
        4: 1.25,  # 较难: 1.25倍
        5: 1.5,   # 困难: 1.5倍
    }
    
    BASE_DAMAGE = 5  # 基础伤害值
    
    @classmethod
    def calculate(
        cls,
        q_type: str,
        difficulty: int = 3,
        is_correct: bool = False
    ) -> int:
        """
        计算HP损失
        
        Args:
            q_type: 题型 ('cloze', 'reading', 'translation', 'writing')
            difficulty: 难度 (1-5)
            is_correct: 是否答对
        
        Returns:
            HP损失值 (答对时返回0)
        """
        if is_correct:
            return 0
        
        # 转换题型枚举
        try:
            question_enum = QuestionType(q_type.lower())
        except ValueError:
            question_enum = QuestionType.READING  # 默认阅读理解
        
        # 获取权重
        alpha = cls.TYPE_WEIGHTS.get(question_enum, 1.0)
        beta = cls.DIFFICULTY_MULTIPLIERS.get(difficulty, 1.0)
        
        # 计算最终伤害
        damage = round(cls.BASE_DAMAGE * alpha * beta)
        
        return max(1, damage)  # 至少扣1滴血
    
    @classmethod
    def calculate_subjective(
        cls,
        q_type: str,
        score: float,
        max_score: float,
        difficulty: int = 3
    ) -> int:
        """
        计算主观题HP损失 (基于得分率)
        
        Args:
            q_type: 题型
            score: 实际得分
            max_score: 满分
            difficulty: 难度
        
        Returns:
            HP损失值
        """
        if score >= max_score:
            return 0
        
        # 计算得分率
        score_rate = score / max_score if max_score > 0 else 0
        
        # 转换题型
        try:
            question_enum = QuestionType(q_type.lower())
        except ValueError:
            question_enum = QuestionType.TRANSLATION
        
        alpha = cls.TYPE_WEIGHTS.get(question_enum, 1.5)
        beta = cls.DIFFICULTY_MULTIPLIERS.get(difficulty, 1.0)
        
        # 主观题伤害 = 基础伤害 × 权重 × 难度 × (1 - 得分率)
        damage = round(cls.BASE_DAMAGE * alpha * beta * (1 - score_rate))
        
        return max(1, damage)


class HealingCalculator:
    """
    精神力恢复计算器
    用于背单词连续答对的回血逻辑
    """
    
    BASE_HEAL = 2  # 基础回血量
    
    # 连击奖励 (Combo Bonus)
    COMBO_BONUS = {
        1: 0,     # 1次: 无奖励
        2: 1,     # 2连对: +1
        3: 2,     # 3连对: +2
        5: 3,     # 5连对: +3
        10: 5,    # 10连对: +5
    }
    
    @classmethod
    def calculate(
        cls,
        is_correct: bool,
        consecutive_correct: int = 0,
        quality: int = 4
    ) -> int:
        """
        计算回血量
        
        Args:
            is_correct: 是否答对
            consecutive_correct: 连续答对次数
            quality: 答题质量 (0-5, SM-2算法的quality参数)
        
        Returns:
            HP恢复值
        """
        if not is_correct:
            return 0
        
        # 基础回血
        heal = cls.BASE_HEAL
        
        # 质量加成 (quality >= 5时额外+1)
        if quality >= 5:
            heal += 1
        
        # 连击加成
        combo_bonus = 0
        for threshold, bonus in sorted(cls.COMBO_BONUS.items(), reverse=True):
            if consecutive_correct >= threshold:
                combo_bonus = bonus
                break
        
        heal += combo_bonus
        
        return heal
    
    @classmethod
    def calculate_review_bonus(cls, proficiency: int) -> int:
        """
        复习熟练词汇的额外回血
        
        Args:
            proficiency: 熟练度 (0-5)
        
        Returns:
            额外回血量
        """
        if proficiency >= 5:
            return 1  # 完美掌握的词,复习时额外+1
        return 0


class MoodStateEngine:
    """
    Mia情绪状态引擎
    根据HP百分比映射情绪状态
    """
    
    @staticmethod
    def get_mood(hp: int, max_hp: int) -> str:
        """
        根据HP计算Mia情绪
        
        Args:
            hp: 当前HP
            max_hp: 最大HP
        
        Returns:
            情绪状态字符串
        """
        if hp <= 0:
            return 'exhausted'  # 力竭: 锁定做题,强制休息
        
        hp_percentage = (hp / max_hp) * 100
        
        if hp_percentage >= 80:
            return 'energetic'  # 元气满满: 崇拜、开心
        elif hp_percentage >= 30:
            return 'focused'    # 专注状态: 专业、稳重
        else:
            return 'warning'    # 红血警告: 心疼、傲娇生气
    
    @staticmethod
    def get_prompt_prefix(mood: str) -> str:
        """
        获取Mia的Prompt前缀 (用于API调用)
        
        Args:
            mood: 情绪状态
        
        Returns:
            Prompt前缀文本
        """
        prefixes = {
            'energetic': "你现在精神饱满，请用崇拜和开心的语气",
            'focused': "你现在状态良好，请用专业稳重的语气",
            'warning': "绯墨的精神力已经很低了(红血状态)，请用心疼但略带傲娇的语气",
            'exhausted': "绯墨已经精疲力竭，请用非常心疼和关切的语气劝他休息"
        }
        return prefixes.get(mood, prefixes['focused'])


# 使用示例
if __name__ == '__main__':
    # 示例1: 客观题扣血
    damage = DamageCalculator.calculate(
        q_type='reading',
        difficulty=4,
        is_correct=False
    )
    print(f"阅读理解(难度4)答错扣血: {damage}HP")  # 预期: 5 * 1.0 * 1.25 = 6HP
    
    # 示例2: 主观题扣血
    damage = DamageCalculator.calculate_subjective(
        q_type='translation',
        score=6.5,
        max_score=10,
        difficulty=3
    )
    print(f"翻译题(得分6.5/10)扣血: {damage}HP")  # 预期: 5 * 1.5 * 1.0 * 0.35 = 3HP
    
    # 示例3: 背单词回血
    heal = HealingCalculator.calculate(
        is_correct=True,
        consecutive_correct=5,
        quality=5
    )
    print(f"背单词(5连对, quality=5)回血: {heal}HP")  # 预期: 2 + 1(quality) + 3(combo) = 6HP
    
    # 示例4: 情绪状态
    mood = MoodStateEngine.get_mood(hp=25, max_hp=100)
    print(f"HP 25/100 的情绪状态: {mood}")  # 预期: warning
    print(f"Prompt前缀: {MoodStateEngine.get_prompt_prefix(mood)}")
