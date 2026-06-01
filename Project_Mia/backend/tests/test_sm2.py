"""T2: SM-2 算法单元测试 — 已知正确值验证 + quality 0-5 全梯度"""
import pytest
from app.services.sm2 import SM2Service


class TestSM2KnownValues:
    """参考 SM-2 官方规范验证"""

    def test_first_review_correct(self):
        """第1次正确复习 (rep=0→1, interval=1)"""
        result = SM2Service.calculate(quality=4, repetition=0, easiness_factor=2.5, interval=0)
        assert result["repetition"] == 1
        assert result["interval"] == 1

    def test_second_review_correct(self):
        """第2次正确复习 (rep=1→2, interval=6)"""
        result = SM2Service.calculate(quality=4, repetition=1, easiness_factor=2.5, interval=1)
        assert result["repetition"] == 2
        assert result["interval"] == 6

    def test_third_review_correct(self):
        """第3次正确复习: interval = round(6 * EF)"""
        # q=4: delta_ef = 0.1 - 1*(0.08+0.02) = 0.1-0.1 = 0, EF stays 2.5
        result = SM2Service.calculate(quality=4, repetition=2, easiness_factor=2.5, interval=6)
        assert result["repetition"] == 3
        assert result["interval"] == 15  # round(6 * 2.5) = 15

    def test_fourth_review_correct(self):
        """第4次: EF=2.5, prev=15 → interval=round(15*2.5)=38"""
        result = SM2Service.calculate(quality=4, repetition=3, easiness_factor=2.5, interval=15)
        assert result["repetition"] == 4
        assert result["interval"] == 38  # round(15 * 2.5) = round(37.5) = 38

    def test_wrong_answer_resets(self):
        """答错 (quality=1 < 3): 重置 rep=0, interval=0"""
        result = SM2Service.calculate(quality=1, repetition=5, easiness_factor=2.5, interval=30)
        assert result["repetition"] == 0
        assert result["interval"] == 0

    def test_quality_2_resets(self):
        """quality=2: 仍在 reset 边界"""
        result = SM2Service.calculate(quality=2, repetition=3, easiness_factor=2.5, interval=10)
        assert result["repetition"] == 0

    def test_quality_3_does_not_reset(self):
        """quality=3 (及格线): 不重置"""
        result = SM2Service.calculate(quality=3, repetition=3, easiness_factor=2.5, interval=10)
        assert result["repetition"] == 4

    def test_ef_clamped_minimum(self):
        """EF 不低于 1.3"""
        # 多次 q=0 降低 EF
        ef = 2.5
        for _ in range(20):
            result = SM2Service.calculate(quality=0, repetition=0, easiness_factor=ef, interval=0)
            ef = result["easiness_factor"]
        assert ef == 1.3  # Clamped

    def test_quality_out_of_bounds_high(self):
        """quality=10 被 clamp 到 5"""
        result = SM2Service.calculate(quality=10, repetition=0, easiness_factor=2.5, interval=0)
        # quality=5: rep→1 (success)
        assert result["repetition"] == 1

    def test_quality_out_of_bounds_low(self):
        """quality=-5 被 clamp 到 0 → 重置"""
        result = SM2Service.calculate(quality=-5, repetition=5, easiness_factor=2.5, interval=30)
        assert result["repetition"] == 0

    def test_next_review_is_future(self):
        """next_review 应为未来日期"""
        from datetime import datetime
        result = SM2Service.calculate(quality=4, repetition=0, easiness_factor=2.5, interval=0)
        next_review = datetime.fromisoformat(result["next_review"])
        assert next_review > datetime.utcnow()


class TestSM2QualityGradient:
    """quality=0-5 各值的 SM-2 EF 输出验证"""

    def test_quality_5_best(self):
        """q=5: EF 增加 0.1"""
        result = SM2Service.calculate(quality=5, repetition=0, easiness_factor=2.5, interval=0)
        assert result["easiness_factor"] == pytest.approx(2.6, rel=1e-3)
        assert result["repetition"] == 1

    def test_quality_4_neutral(self):
        """q=4: delta_ef = 0.1-1*(0.08+0.02) = 0"""
        result = SM2Service.calculate(quality=4, repetition=0, easiness_factor=2.5, interval=0)
        assert result["easiness_factor"] == pytest.approx(2.5, rel=1e-3)

    def test_quality_3_slight_decrease(self):
        """q=3: delta_ef = 0.1 - 2*(0.08+2*0.02) = 0.1 - 0.24 = -0.14, EF=2.36"""
        result = SM2Service.calculate(quality=3, repetition=0, easiness_factor=2.5, interval=0)
        assert result["easiness_factor"] == pytest.approx(2.36, rel=1e-3)

    def test_quality_2_resets_and_decreases(self):
        """q=2: delta_ef = 0.1-3*(0.08+3*0.02) = 0.1-0.42 = -0.32, EF=2.18"""
        result = SM2Service.calculate(quality=2, repetition=5, easiness_factor=2.5, interval=30)
        assert result["easiness_factor"] == pytest.approx(2.18, rel=1e-3)
        assert result["repetition"] == 0

    def test_quality_1(self):
        """q=1: delta_ef = 0.1-4*(0.08+4*0.02) = 0.1-4*0.16 = -0.54, EF=1.96"""
        result = SM2Service.calculate(quality=1, repetition=0, easiness_factor=2.5, interval=0)
        assert result["easiness_factor"] == pytest.approx(1.96, rel=1e-3)

    def test_quality_0_max_decrease(self):
        """q=0: delta_ef = 0.1-5*(0.08+5*0.02) = 0.1-5*0.18 = -0.8, EF=1.7"""
        result = SM2Service.calculate(quality=0, repetition=0, easiness_factor=2.5, interval=0)
        assert result["easiness_factor"] == pytest.approx(1.7, rel=1e-3)
        assert result["repetition"] == 0

    def test_ef_nearest_precision(self):
        """EF 保留4位小数"""
        result = SM2Service.calculate(quality=5, repetition=0, easiness_factor=2.5, interval=0)
        ef_str = str(result["easiness_factor"])
        # 2.6 精确表示
        assert result["easiness_factor"] == 2.6
