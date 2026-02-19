"""
SuperMemo 2 (SM-2) 间隔重复算法

核心公式:
  EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
  Interval(1) = 1
  Interval(2) = 6
  Interval(n) = Interval(n-1) * EF

Author: Femo
Date: 2026-02-18
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
    ) -> Dict:
        """
        计算下次复习参数。

        Args:
            quality:         答题质量 (0-5)
            repetition:      已复习次数
            easiness_factor: 当前 EF
            interval:        当前间隔天数

        Returns:
            {
                "repetition": int,
                "easiness_factor": float,
                "interval": int,
                "next_review": str (ISO 格式)
            }
        """
        quality = max(0, min(5, quality))

        # 更新 EF
        new_ef = easiness_factor + (
            0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        )
        new_ef = max(cls.EF_MIN, new_ef)

        if quality < 3:
            # 答错: 重置进度
            new_rep = 0
            new_interval = 0
        else:
            new_rep = repetition + 1
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
