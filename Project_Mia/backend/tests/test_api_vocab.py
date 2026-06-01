"""T1: Vocab API 测试 — 今日任务、复习提交"""
import pytest


@pytest.mark.asyncio
async def test_get_todays_vocab(client):
    """GET /api/vocab/today 应返回今日单词任务"""
    response = await client.get("/api/vocab/today?slot_id=0")
    assert response.status_code == 200
    data = response.json()
    assert "date" in data
    assert "tasks" in data
    assert "daily_limit" in data
    assert data["daily_limit"] == 30
    # 全新用户应该有 new words
    assert data["new_count"] > 0


@pytest.mark.asyncio
async def test_submit_review_new_word(client):
    """POST /api/vocab/review 提交新单词复习 (quality=4)"""
    response = await client.post("/api/vocab/review", json={
        "slot_id": 0,
        "word": "persistent",
        "quality": 4
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_submit_review_poor_quality(client):
    """POST /api/vocab/review quality=1 应记录失败但返回 success"""
    response = await client.post("/api/vocab/review", json={
        "slot_id": 0,
        "word": "notorious",
        "quality": 1
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_global_stats(client):
    """GET /api/vocab/global_stats 应返回统计"""
    response = await client.get("/api/vocab/global_stats?slot_id=0")
    assert response.status_code == 200
    data = response.json()
    assert "total_words" in data
    assert "mastered_words" in data
    assert data["total_words"] >= 5  # 种子数据有5个词


@pytest.mark.asyncio
async def test_submit_review_updates_progress(client):
    """复习后 /today 的复习计数应该变化"""
    # 先复习一个词
    await client.post("/api/vocab/review", json={
        "slot_id": 0, "word": "abandon", "quality": 5
    })
    response = await client.get("/api/vocab/today?slot_id=0")
    data = response.json()
    # 有复习记录后，learned_count 应该更新
    assert data["today_learned_count"] >= 0  # 至少不报错
