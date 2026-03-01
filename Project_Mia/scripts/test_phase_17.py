"""
Phase 17.0 Self-Validation Test Script
Tests:
1. answer_history_logs records multiple submissions for same q_id
2. /api/vocab/explain caching speed (2nd call dramatically faster)
3. /api/exam/{paper_id}/progress returns correct format
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def p(msg):   print(f"  {msg}")
def ok(msg):  print(f"✅ PASS: {msg}")
def err(msg): print(f"❌ FAIL: {msg}"); sys.exit(1)

TARGET_SLOT = 99   # use an isolated test slot
TARGET_PAPER = None  # will pick first paper found

# ─────────────────────────────────────────────────────────────────────────────
# Helper: pick a real paper and q_id from static DB
# ─────────────────────────────────────────────────────────────────────────────
def pick_paper_and_question():
    papers = client.get("/api/exams").json()
    if not papers:
        err("No papers found. Seed data first.")
    paper = papers[0]
    detail = client.get(f"/api/exam/{paper['paper_id']}").json()
    # Find first objective question
    for section_name, section_data in detail.get("sections", {}).items():
        if isinstance(section_data, dict) and "questions" in section_data:
            qs = section_data["questions"]
            if qs:
                return paper["paper_id"], qs[0]["q_id"], qs[0].get("options", {})
        if isinstance(section_data, list):
            for group in section_data:
                if "questions" in group and group["questions"]:
                    return paper["paper_id"], group["questions"][0]["q_id"], group["questions"][0].get("options", {})
    err("No objective question found to test with.")

# ─────────────────────────────────────────────────────────────────────────────
# Test 1: answer_history_logs — two submissions → two rows
# ─────────────────────────────────────────────────────────────────────────────
def test_history_logs():
    p("=== Task 1: Attempt History Logs ===")
    paper_id, q_id, options = pick_paper_and_question()
    p(f"Using paper_id={paper_id}, q_id={q_id}")
    
    first_answer  = list(options.keys())[0] if options else "A"
    second_answer = list(options.keys())[1] if len(options) > 1 else "B"

    # Submission 1
    r1 = client.post("/api/exam/submit_objective", json={
        "q_id": q_id, "answer": first_answer, "slot_id": TARGET_SLOT
    })
    assert r1.status_code == 200, f"Submit 1 failed: {r1.text}"
    p(f"Submission 1 OK (answer={first_answer})")

    # Submission 2 (different answer — simulates 2nd-attempt)
    r2 = client.post("/api/exam/submit_objective", json={
        "q_id": q_id, "answer": second_answer, "slot_id": TARGET_SLOT
    })
    assert r2.status_code == 200, f"Submit 2 failed: {r2.text}"
    p(f"Submission 2 OK (answer={second_answer})")

    # Directly inspect DB
    import sqlite3
    DB = os.path.join(os.path.dirname(__file__), '..', 'backend', 'data', 'femo_profile.db')
    conn = sqlite3.connect(DB)
    rows = conn.execute(
        "SELECT * FROM answer_history_logs WHERE slot_id=? AND q_id=?",
        (TARGET_SLOT, q_id)
    ).fetchall()
    conn.close()

    count = len(rows)
    p(f"Rows found in answer_history_logs: {count}")
    if count >= 2:
        ok(f"answer_history_logs has {count} rows for same q_id — replayability confirmed!")
    else:
        err(f"Expected >= 2 rows, got {count}. Logs not appending correctly.")

    return paper_id

# ─────────────────────────────────────────────────────────────────────────────
# Test 2: Vocab /explain — cache miss vs cache hit latency
# ─────────────────────────────────────────────────────────────────────────────
def test_explain_cache():
    p("=== Task 2: Vocab AI Explain Cache ===")
    TEST_WORD = "ephemeral"   # unlikely to already be cached

    # First call — LLM (may be slow)
    p(f"Call 1 for '{TEST_WORD}' (cache miss expected)...")
    t0 = time.perf_counter()
    r1 = client.post("/api/vocab/explain", json={"word": TEST_WORD})
    t1 = time.perf_counter()
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1.get("success"), f"Explain failed: {data1}"
    elapsed1 = round(t1 - t0, 3)
    cached_flag1 = data1.get("cached", False)
    p(f"  Elapsed: {elapsed1}s  cached={cached_flag1}  len={len(data1.get('explanation',''))}")

    # Second call — DB cache hit (should be near-instant)
    p(f"Call 2 for '{TEST_WORD}' (cache HIT expected)...")
    t2 = time.perf_counter()
    r2 = client.post("/api/vocab/explain", json={"word": TEST_WORD})
    t3 = time.perf_counter()
    assert r2.status_code == 200
    data2 = r2.json()
    elapsed2 = round(t3 - t2, 3)
    cached_flag2 = data2.get("cached", False)
    p(f"  Elapsed: {elapsed2}s  cached={cached_flag2}")

    if cached_flag2:
        ok(f"Cache HIT verified! 2nd call returned cached=True ({elapsed2}s vs {elapsed1}s)")
    else:
        err(f"Cache MISS on 2nd call — cache not saving. data={data2}")

# ─────────────────────────────────────────────────────────────────────────────
# Test 3: Progress API format
# ─────────────────────────────────────────────────────────────────────────────
def test_progress_api(paper_id):
    p("=== Task 3: Progress API ===")
    r = client.get(f"/api/exam/{paper_id}/progress", params={"slot_id": TARGET_SLOT})
    assert r.status_code == 200, f"Progress API failed: {r.text}"
    data = r.json()
    p(f"Progress response: {data}")

    assert "answered" in data, "Missing 'answered'"
    assert "total"    in data, "Missing 'total'"
    assert "percentage" in data, "Missing 'percentage'"
    assert data["total"] > 0, "total should be > 0"
    assert data["answered"] >= 1, f"Expected answered >= 1 (we submitted), got {data['answered']}"

    ok(f"Progress API format OK: {data['answered']}/{data['total']} = {data['percentage']}%")

# ─────────────────────────────────────────────────────────────────────────────
# Test 4: Reset API — answered drops to 0
# ─────────────────────────────────────────────────────────────────────────────
def test_reset_api(paper_id):
    p("=== Task 4 (Bonus): Reset API ===")
    r = client.delete(f"/api/exam/{paper_id}/reset", params={"slot_id": TARGET_SLOT})
    assert r.status_code == 200
    data = r.json()
    p(f"Reset response: {data}")
    assert data.get("success"), f"Reset returned failure: {data}"

    # Check progress is now 0
    r2 = client.get(f"/api/exam/{paper_id}/progress", params={"slot_id": TARGET_SLOT})
    progress = r2.json()
    p(f"Progress after reset: {progress}")

    if progress["answered"] == 0:
        ok("Reset confirmed! answered=0 after reset.")
    else:
        err(f"Reset failed — answered={progress['answered']} (expected 0)")

if __name__ == "__main__":
    print("\n🔄 Phase 17.0 Self-Validation Test\n" + "="*45)
    paper_id = test_history_logs()
    test_explain_cache()
    test_progress_api(paper_id)
    test_reset_api(paper_id)
    print("\n🎉 All Phase 17.0 Tests PASSED!\n")
