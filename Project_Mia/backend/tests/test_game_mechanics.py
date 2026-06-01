"""T2: Game Mechanics 单元测试 — 伤害计算、回血、情绪"""
import pytest
from app.services.game_mechanics import (
    EnglishOneDamageCalculator,
    HealingCalculator,
    MoodStateMachine,
    GameMechanicsService,
)


class TestEnglishOneDamageCalculator:
    """英语一伤害计算器"""

    # ── 完形填空 ──

    def test_cloze_correct_no_damage(self):
        assert EnglishOneDamageCalculator.calculate("use_of_english", is_correct=True) == 0

    def test_cloze_wrong_2_damage(self):
        assert EnglishOneDamageCalculator.use_of_english_damage() == 2
        assert EnglishOneDamageCalculator.calculate("use_of_english", is_correct=False) == 2

    # ── 阅读理解 ──

    def test_reading_correct_no_damage(self):
        assert EnglishOneDamageCalculator.calculate("reading_a", is_correct=True) == 0
        assert EnglishOneDamageCalculator.calculate("reading_b", is_correct=True) == 0

    def test_reading_wrong_5_damage(self):
        assert EnglishOneDamageCalculator.reading_damage() == 5
        assert EnglishOneDamageCalculator.calculate("reading_a", is_correct=False) == 5
        assert EnglishOneDamageCalculator.calculate("reading_b", is_correct=False) == 5

    # ── 翻译题 ──

    def test_translation_perfect_score_zero_damage(self):
        assert EnglishOneDamageCalculator.translation_damage(2.0) == 0

    def test_translation_half_score(self):
        """score=1.0: (2.0-1.0)*2.5=2.5 → round → 2"""
        dmg = EnglishOneDamageCalculator.translation_damage(1.0)
        # Python banker's rounding: round(2.5)=2, round(3.5)=4
        assert dmg == 2  # round(2.5) → 2

    def test_translation_zero_score_max_damage(self):
        dmg = EnglishOneDamageCalculator.translation_damage(0.0)
        assert dmg == 5  # (2.0-0.0)*2.5=5.0 → round → 5

    def test_translation_clamped_score(self):
        """score 超出 0-2 范围自动 clamp"""
        dmg_low = EnglishOneDamageCalculator.translation_damage(-1.0)
        dmg_high = EnglishOneDamageCalculator.translation_damage(3.0)
        assert dmg_low == 5  # clamp to 0 → max damage
        assert dmg_high == 0  # clamp to 2 → no damage

    # ── 写作题 ──

    def test_writing_a_perfect_no_penalty(self):
        result = EnglishOneDamageCalculator.writing_damage("writing_a", 10.0)
        assert result["base_cost"] == 5
        assert result["penalty"] == 0
        assert result["total"] == 5

    def test_writing_a_low_score(self):
        """小作文 3分: penalty=(6-3)*1=3, total=8"""
        result = EnglishOneDamageCalculator.writing_damage("writing_a", 3.0)
        assert result["base_cost"] == 5
        assert result["penalty"] == 3
        assert result["total"] == 8

    def test_writing_a_at_threshold(self):
        """小作文刚好及格线 6分: 无追加惩罚"""
        result = EnglishOneDamageCalculator.writing_damage("writing_a", 6.0)
        assert result["penalty"] == 0

    def test_writing_b_high_score(self):
        result = EnglishOneDamageCalculator.writing_damage("writing_b", 18.0)
        assert result["base_cost"] == 5
        assert result["penalty"] == 0

    def test_writing_b_below_threshold(self):
        """大作文 8分: penalty=(12-8)*1=4, total=9"""
        result = EnglishOneDamageCalculator.writing_damage("writing_b", 8.0)
        assert result["penalty"] == 4
        assert result["total"] == 9

    def test_writing_b_zero(self):
        """大作文 0分: penalty=12, total=17"""
        result = EnglishOneDamageCalculator.writing_damage("writing_b", 0.0)
        assert result["penalty"] == 12
        assert result["total"] == 17

    # ── 统入口 + 边界 ──

    def test_calculate_writing_a(self):
        dmg = EnglishOneDamageCalculator.calculate("writing_a", ai_score=3.0)
        assert dmg == 8

    def test_calculate_writing_b(self):
        dmg = EnglishOneDamageCalculator.calculate("writing_b", ai_score=15.0)
        assert dmg == 5  # base_cost only

    def test_calculate_translation_via_calculate(self):
        dmg = EnglishOneDamageCalculator.calculate("translation", ai_score=1.0)
        assert dmg == 2

    def test_unknown_type_fallback(self):
        assert EnglishOneDamageCalculator.calculate("unknown_type", is_correct=False) == 3
        assert EnglishOneDamageCalculator.calculate("unknown_type", is_correct=True) == 0


class TestHealingCalculator:
    """回血机制"""

    def test_quality_4_heals(self):
        assert HealingCalculator.heal_from_vocab_review(4) == 1

    def test_quality_5_heals(self):
        assert HealingCalculator.heal_from_vocab_review(5) == 1

    def test_quality_below_4_no_heal(self):
        for q in [0, 1, 2, 3]:
            assert HealingCalculator.heal_from_vocab_review(q) == 0, f"quality={q} should not heal"

    def test_context_lookup_heal(self):
        assert HealingCalculator.heal_from_context_lookup() == 2


class TestMoodStateMachine:
    """情绪状态机"""

    def test_zero_hp_exhausted(self):
        mood = MoodStateMachine.get_mia_mood(0, 100)
        assert mood["mood"] == "exhausted"

    def test_negative_hp_exhausted(self):
        mood = MoodStateMachine.get_mia_mood(-5, 100)
        assert mood["mood"] == "exhausted"

    def test_worried_at_20_percent(self):
        mood = MoodStateMachine.get_mia_mood(20, 100)
        assert mood["mood"] == "worried"

    def test_focused_at_50_percent(self):
        mood = MoodStateMachine.get_mia_mood(50, 100)
        assert mood["mood"] == "focused"

    def test_happy_at_90_percent(self):
        mood = MoodStateMachine.get_mia_mood(90, 100)
        assert mood["mood"] == "happy"

    def test_boundary_30_percent(self):
        """ratio < 0.30 → worried, ratio >= 0.30 → focused"""
        mood = MoodStateMachine.get_mia_mood(29, 100)  # 0.29
        assert mood["mood"] == "worried"
        mood = MoodStateMachine.get_mia_mood(30, 100)  # 0.30
        assert mood["mood"] == "focused"

    def test_boundary_80_percent(self):
        """ratio < 0.80 → focused, ratio >= 0.80 → happy"""
        mood = MoodStateMachine.get_mia_mood(79, 100)  # 0.79
        assert mood["mood"] == "focused"
        mood = MoodStateMachine.get_mia_mood(80, 100)  # 0.80
        assert mood["mood"] == "happy"

    def test_zero_max_hp_handled(self):
        """max_hp=0 时不除零崩溃"""
        mood = MoodStateMachine.get_mia_mood(0, 0)
        assert mood["mood"] == "exhausted"


class TestGameMechanicsService:
    """向后兼容接口"""

    def test_calculate_hp_loss_compat(self):
        gm = GameMechanicsService()
        dmg = gm.calculate_hp_loss("cloze", max_score=0.5, actual_score=0.0)
        assert dmg == 2

    def test_heal_compat(self):
        gm = GameMechanicsService()
        assert gm.heal_from_vocab_review(4) == 1
        assert gm.heal_from_vocab_review(2) == 0
        assert gm.heal_from_context_lookup() == 2
