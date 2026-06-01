"""T1: User API 测试 — 存档读写、等级系统"""
import pytest


@pytest.mark.asyncio
async def test_get_user_status_default(client):
    """GET /api/user/status 应返回默认状态"""
    response = await client.get("/api/user/status?slot_id=99")
    assert response.status_code == 200
    data = response.json()
    assert data["hp"] == 100
    assert data["maxHp"] == 100
    assert data["level"] == 1


@pytest.mark.asyncio
async def test_save_and_load(client):
    """POST /api/user/save + GET /api/user/load 完整存档流程"""
    # Save
    save_res = await client.post("/api/user/save", json={
        "slot_id": 1,
        "hp": 75,
        "max_hp": 120,
        "level": 3,
        "exp": 150,
        "mia_mood": "happy",
        "completed_questions": ["q1", "q2"]
    })
    assert save_res.status_code == 200
    assert save_res.json()["success"] is True

    # Load
    load_res = await client.get("/api/user/load?slot_id=1")
    assert load_res.status_code == 200
    data = load_res.json()
    assert data["hp"] == 75
    assert data["max_hp"] == 120
    assert data["level"] == 3
    assert data["exp"] == 150
    assert "q1" in data["completed_questions"]


@pytest.mark.asyncio
async def test_save_triggers_level_up(client):
    """POST /api/user/save 经验达标应触发升级 + 满血"""
    # level=1, 升级需 exp >= 1*100=100. 250 exp → Lv2 (need 200?), actual:
    # level=1, need 100. exp=250>=100 → exp-=100=150, level=2, hp restored
    # level=2, need 200. exp=150<200 → stop.
    res = await client.post("/api/user/save", json={
        "slot_id": 2,
        "hp": 60,
        "max_hp": 100,
        "level": 1,
        "exp": 250,
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["leveled_up"] is True

    # 升级后: Lv2, exp=150, hp=100 (满血)
    load = await client.get("/api/user/load?slot_id=2")
    ld = load.json()
    assert ld["level"] == 2
    assert ld["exp"] == 150
    assert ld["hp"] == 100  # 升级回满


@pytest.mark.asyncio
async def test_get_slots(client):
    """GET /api/user/slots 应返回存档列表"""
    response = await client.get("/api/user/slots")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(s["slot_id"] == 0 for s in data)


@pytest.mark.asyncio
async def test_load_nonexistent_slot(client):
    """GET /api/user/load 不存在的 slot → 返回默认值"""
    response = await client.get("/api/user/load?slot_id=999")
    assert response.status_code == 200
    data = response.json()
    assert data["hp"] == 100  # 默认
    assert data["level"] == 1
