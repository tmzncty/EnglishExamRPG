"""
SuperMemo 2 (SM-2) 间隔重复算法

标准 SM-2 公式:
  EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
  Interval(1) = 1
  Interval(2) = 6
  Interval(n) = Interval(n-1) * EF

激进模式 (aggressive=True):
  用于 Project Mia 的词汇学习场景，采用更快的间隔增长策略：
  - Interval = previous_interval * 2.5 (常规)
  - Interval = previous_interval * 3.5 (连续成功 ≥ 3 次)
  - 答错时 interval 重置为 1 (而非 0)，保留一定记忆痕迹

Author: Femo / Saihi
Date: 2026-02-18 / 2026-05-30
"""

from datetime import datetime, timedelta
from typing import Dict


class SM2Service:
    """SuperMemo 2 算法服务"""

    EF_MIN = 1.3
    EF_DEFAULT = 2.5

    @classmethod
    def calculate(
        cls,
        quality: int,
        repetition: int = 0,
        easiness_factor: float = 2.5,
        interval: int = 0,
        aggressive: bool = False,
        success_streak: int = 0,
    ) -> Dict:
        """
        计算下次复习参数。

        Args:
            quality:         答题质量 (0-5)
            repetition:      已复习次数
            easiness_factor: 当前 EF
            interval:        当前间隔天数
            aggressive:      是否启用激进模式（Project Mia 词汇场景）
            success_streak:  连续成功次数（激进模式下用于判断加速档位）

        Returns:
            {
                "repetition": int,
                "easiness_factor": float,
                "interval": int,
                "next_review": str (ISO 格式)
            }
        """
        quality = max(0, min(5, quality))

        # 更新 EF (两种模式共用)
        new_ef = easiness_factor + (
            0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        )
        new_ef = max(cls.EF_MIN, new_ef)

        if quality < 3:
            # 答错: 重置进度
            new_rep = 0
            if aggressive:
                # 激进模式保留 interval=1，不完全归零
                new_interval = 1
            else:
                # 标准 SM-2: interval 归零
                new_interval = 0
        else:
            new_rep = repetition + 1

            if aggressive:
                # ── 激进模式：指数增长 ──
                if interval == 0:
                    new_interval = 1
                elif success_streak >= 3:
                    new_interval = int(interval * 3.5)
                else:
                    new_interval = int(interval * 2.5)
            else:
                # ── 标准 SM-2 ──
                if new_rep == 1:
                    new_interval = 1
                elif new_rep == 2:
                    new_interval = 6
                else:
                    new_interval = round(interval * new_ef)

        next_review = datetime.utcnow() + timedelta(days=new_interval)

        return {
            "repetition": new_rep,
            "easiness_factor": round(new_ef, 4),
            "interval": new_interval,
            "next_review": next_review.isoformat(),
        }


# 模块级单例
sm2_service = SM2Service()
