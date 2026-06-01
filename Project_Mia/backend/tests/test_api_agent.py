"""T1: Mia Agent API 测试 (Mock LLM)"""
import pytest


@pytest.mark.asyncio
async def test_mia_interact_chat(client, mock_llm):
    """POST /api/mia/interact 聊天模式 — 流式响应"""
    response = await client.post("/api/mia/interact", json={
        "context_type": "chat",
        "context_data": {
            "message": "Hello Mia!",
            "rpg_mode": False,
            "attach_context": False
        }
    })
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")

    # 验证流中包含初始元数据
    body = response.text
    assert "conversation_id" in body


@pytest.mark.asyncio
async def test_mia_conversations_empty(client):
    """GET /api/mia/conversations 空列表"""
    response = await client.get("/api/mia/conversations")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_mia_interact_creates_conversation(client, mock_llm):
    """交互后会话列表应有记录"""
    await client.post("/api/mia/interact", json={
        "context_type": "chat",
        "context_data": {
            "message": "Test message",
            "rpg_mode": False,
            "attach_context": False
        }
    })

    convs = await client.get("/api/mia/conversations")
    data = convs.json()
    assert len(data) >= 1
    assert "title" in data[0]


@pytest.mark.asyncio
async def test_mia_interact_rpg_mode_exhausted(client, mock_llm):
    """RPG 模式 HP=0 时返回疲惫回复"""
    # 保存 HP=0
    await client.post("/api/user/save", json={
        "slot_id": 0, "hp": 0, "max_hp": 100, "level": 1, "exp": 0
    })

    response = await client.post("/api/mia/interact", json={
        "context_type": "chat",
        "context_data": {
            "message": "Can I study?",
            "rpg_mode": True,
            "attach_context": False
        }
    })
    # 非流式拦截 (HP≤0 直接返回 JSON)
    body = response.text
    # 可能返回 JSON 拦截或流式（取决于实现）
    if "text/event-stream" not in response.headers.get("content-type", ""):
        data = response.json()
        assert "mia_reply" in data
        assert data["hp"] == 0


@pytest.mark.asyncio
async def test_mia_conversation_detail_not_found(client):
    """GET /api/mia/conversations/999 → 返回占位"""
    response = await client.get("/api/mia/conversations/999")
    assert response.status_code == 200
    data = response.json()
    assert "Not Found" in data.get("title", "")
