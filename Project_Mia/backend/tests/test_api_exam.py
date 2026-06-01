"""T1: Exam API 测试 — 试卷列表、attempt 生命周期"""
import pytest


@pytest.mark.asyncio
async def test_get_exams_returns_list(client):
    """GET /api/exams 应返回试卷列表"""
    response = await client.get("/api/exams")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    paper = data[0]
    assert "paper_id" in paper
    assert "year" in paper
    assert "title" in paper
    assert paper["paper_id"] == "2023-eng1"


@pytest.mark.asyncio
async def test_get_exam_history_empty(client):
    """GET /api/exam/history 无记录时应返回空对象"""
    response = await client.get("/api/exam/history")
    assert response.status_code == 200
    assert response.json() == {}


@pytest.mark.asyncio
async def test_start_attempt_creates_new(client):
    """POST /api/exam/start_attempt 应创建新 attempt"""
    response = await client.post("/api/exam/start_attempt", json={
        "paper_id": "2023-eng1",
        "slot_id": 0
    })
    assert response.status_code == 200
    data = response.json()
    assert "attempt_id" in data
    assert data["attempt_number"] == 1
    assert data["restored_time"]["total_time"] == 0


@pytest.mark.asyncio
async def test_start_attempt_resumes_in_progress(client):
    """POST /api/exam/start_attempt 应恢复未完成的 attempt"""
    r1 = await client.post("/api/exam/start_attempt", json={"paper_id": "2023-eng1"})
    aid = r1.json()["attempt_id"]
    r2 = await client.post("/api/exam/start_attempt", json={"paper_id": "2023-eng1"})
    assert r2.json()["attempt_id"] == aid
    assert r2.json()["attempt_number"] == 1


@pytest.mark.asyncio
async def test_start_attempt_missing_paper_id(client):
    """POST /api/exam/start_attempt 缺少 paper_id → 400"""
    response = await client.post("/api/exam/start_attempt", json={})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_sync_time(client):
    """POST /api/exam/sync_time 应成功同步"""
    r = await client.post("/api/exam/start_attempt", json={"paper_id": "2023-eng1"})
    aid = r.json()["attempt_id"]
    response = await client.post("/api/exam/sync_time", json={
        "attempt_id": aid,
        "total_time": 120,
        "question_times": {"2023-eng1-cloze-q1": 30}
    })
    assert response.json()["ok"] is True


@pytest.mark.asyncio
async def test_sync_time_missing_attempt_id(client):
    """POST /api/exam/sync_time 缺少 attempt_id → ok=False"""
    response = await client.post("/api/exam/sync_time", json={})
    assert response.json()["ok"] is False


@pytest.mark.asyncio
async def test_finish_attempt(client):
    """POST /api/exam/finish_attempt 应结束 attempt"""
    r = await client.post("/api/exam/start_attempt", json={"paper_id": "2023-eng1"})
    aid = r.json()["attempt_id"]
    response = await client.post("/api/exam/finish_attempt", json={"attempt_id": aid})
    assert response.json()["ok"] is True


@pytest.mark.asyncio
async def test_finish_attempt_missing_id(client):
    """POST /api/exam/finish_attempt 缺少 attempt_id → ok=False"""
    response = await client.post("/api/exam/finish_attempt", json={})
    assert response.json()["ok"] is False


@pytest.mark.asyncio
async def test_get_paper_attempts(client):
    """GET /api/exam/attempts/{paper_id} 应返回 attempt 列表"""
    # 先创建一个 attempt
    r = await client.post("/api/exam/start_attempt", json={"paper_id": "2023-eng1"})
    r.json()["attempt_id"]
    await client.post("/api/exam/finish_attempt", json={"attempt_id": r.json()["attempt_id"]})

    response = await client.get("/api/exam/attempts/2023-eng1")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["attempt_id"] is not None
    assert data[0]["status"] == "finished"
