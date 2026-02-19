"""
词汇 API 路由
POST /api/vocab/review - 提交背词结果 (SM-2 + 回血)

Author: Femo
Date: 2026-02-18
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.db.helpers import get_profile_conn, get_user_hp, get_user_max_hp, update_user_hp, ensure_auto_save
from app.services.sm2 import sm2_service
from app.services.game_mechanics import game_mechanics

router = APIRouter()


# ---- 请求/响应模型 ----

class VocabReviewRequest(BaseModel):
    word: str
    quality: int = Field(..., ge=0, le=5, description="SM-2 评分 (0-5)")


class VocabReviewResult(BaseModel):
    success: bool
    hp_healed: int
    current_hp: int
    next_review: str
    new_ef: float
    new_interval: int


# ---- 路由 ----

@router.post("/review", response_model=VocabReviewResult)
async def review_vocab(body: VocabReviewRequest):
    """
    提交背词结果

    1. 查 vocab_progress 获取当前 SM-2 参数
    2. 调用 SM-2 算法计算新的 EF/interval/next_review
    3. 调用 heal_from_vocab_review 判断是否回血
    4. 更新数据库
    """
    with get_profile_conn() as pconn:
        ensure_auto_save(pconn)

        # 1) 读取当前进度 (不存在则初始化)
        row = pconn.execute(
            "SELECT repetition, easiness_factor, interval FROM vocab_progress WHERE word = ?",
            (body.word,),
        ).fetchone()

        if row:
            rep = row["repetition"]
            ef = row["easiness_factor"]
            interval = row["interval"]
        else:
            rep, ef, interval = 0, 2.5, 0

        # 2) SM-2 计算
        result = sm2_service.calculate(
            quality=body.quality,
            repetition=rep,
            easiness_factor=ef,
            interval=interval,
        )

        # 3) 回血判定
        hp_healed = game_mechanics.heal_from_vocab_review(body.quality)

        current_hp = get_user_hp(pconn)
        max_hp = get_user_max_hp(pconn)
        if hp_healed > 0:
            new_hp = min(max_hp, current_hp + hp_healed)
            update_user_hp(pconn, new_hp)
            current_hp = new_hp

        # 4) 写入/更新 vocab_progress
        pconn.execute(
            """INSERT INTO vocab_progress (word, repetition, easiness_factor, interval, next_review, last_review, updated_at)
               VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
               ON CONFLICT(word) DO UPDATE SET
                   repetition = excluded.repetition,
                   easiness_factor = excluded.easiness_factor,
                   interval = excluded.interval,
                   next_review = excluded.next_review,
                   last_review = CURRENT_TIMESTAMP,
                   total_reviews = total_reviews + 1,
                   correct_reviews = correct_reviews + CASE WHEN ? >= 3 THEN 1 ELSE 0 END,
                   updated_at = CURRENT_TIMESTAMP
            """,
            (
                body.word,
                result["repetition"],
                result["easiness_factor"],
                result["interval"],
                result["next_review"],
                body.quality,
            ),
        )
        pconn.commit()

    return VocabReviewResult(
        success=True,
        hp_healed=hp_healed,
        current_hp=current_hp,
        next_review=result["next_review"],
        new_ef=result["easiness_factor"],
        new_interval=result["interval"],
    )
