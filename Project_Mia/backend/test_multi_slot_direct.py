import sys
import os
import json
from fastapi.testclient import TestClient

# Add current directory to sys.path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app

client = TestClient(app)

def test_multi_slot_isolation():
    print("\n--- Testing Multi-Slot Isolation ---")
    
    # 1. Reset Slot 0 and Slot 1 (optional, but good practice)
    
    # 2. Save progress to Slot 0
    print("Saving to Slot 0...")
    resp = client.post("/api/user/save", json={"slot_id": 0, "hp": 100, "level": 1})
    assert resp.status_code == 200
    
    # 3. Save progress to Slot 1
    print("Saving to Slot 1...")
    resp = client.post("/api/user/save", json={"slot_id": 1, "hp": 50, "level": 2})
    assert resp.status_code == 200
    
    # 4. Verify Load Isolation
    print("Verifying Load Isolation...")
    resp0 = client.get("/api/user/load", params={"slot_id": 0})
    data0 = resp0.json()
    print(f"Slot 0 Data: HP={data0['hp']}, Level={data0['level']}")
    assert data0['hp'] == 100
    assert data0['level'] == 1
    
    resp1 = client.get("/api/user/load", params={"slot_id": 1})
    data1 = resp1.json()
    print(f"Slot 1 Data: HP={data1['hp']}, Level={data1['level']}")
    assert data1['hp'] == 50
    assert data1['level'] == 2
    
    # 5. Verify Slots List
    print("Verifying Slots List...")
    resp_slots = client.get("/api/user/slots")
    slots = resp_slots.json()
    print(f"Available Slots: {slots}")
    assert len(slots) >= 2
    
    # 6. Submit Objective Answer to Slot 0 & 1
    print("Testing Answer Isolation...")
    
    # Get a valid QID
    resp_exams = client.get("/api/exams")
    exams = resp_exams.json()
    q_id = "test_q_1" # Fallback
    if exams:
        paper_id = exams[0]['paper_id']
        resp_paper = client.get(f"/api/exam/{paper_id}")
        paper_data = resp_paper.json()
        if paper_data['sections']['reading_a']:
             q_id = paper_data['sections']['reading_a'][0]['questions'][0]['q_id']
    
    print(f"Using QID: {q_id}")
    
    # Slot 0: Answer 'A'
    client.post("/api/exam/submit_objective", json={"q_id": q_id, "answer": "A", "slot_id": 0})
    
    # Slot 1: Answer 'B'
    client.post("/api/exam/submit_objective", json={"q_id": q_id, "answer": "B", "slot_id": 1})
    
    # Verify History Slot 0
    hist0 = client.get("/api/exam/history", params={"slot_id": 0}).json()
    print(f"Hist0: {hist0}")
    ans0 = hist0.get(q_id, {}).get("user_answer")
    print(f"Slot 0 Answer: {ans0}")
    assert ans0 == "A"
    
    # Verify History Slot 1
    hist1 = client.get("/api/exam/history", params={"slot_id": 1}).json()
    ans1 = hist1.get(q_id, {}).get("user_answer")
    print(f"Slot 1 Answer: {ans1}")
    assert ans1 == "B"
    
    print("Answer Isolation Verified!")

    # 7. Test Subjective Submission & Error Visibility
    print("\n--- Testing Subjective Submission Error Visibility ---")
    # Using a dummy translation question or existing one
    # If q_id is reading_a, submit_subjective might behave weirdly but logic should hold.
    # Better to use a translation q_id if possible.
    
    # Try to find translation q
    trans_q_id = q_id
    if exams:
        paper_id = exams[0]['paper_id']
        resp_paper = client.get(f"/api/exam/{paper_id}")
        pd = resp_paper.json()
        if pd['sections']['translation']:
            trans_q_id = pd['sections']['translation']['questions'][0]['q_id']
    
    print(f"Submitting Subjective to {trans_q_id}...")
    # This should trigger LLM. If LLM fails, we should see error in console.
    # User requested ~70 words.
    long_answer = (
        "This is a test answer for the translation section. "
        "It needs to be sufficiently long to mimic a real student response "
        "and potentially trigger any length-related processing in the LLM service. "
        "The quick brown fox jumps over the lazy dog repeatedly to ensure we have enough tokens. "
        "This checks if the system handles the request correctly or crashes with a traceback. "
        "We expect a JSON response with a score and feedback."
    )
    
    resp_sub = client.post("/api/exam/submit_subjective", json={
        "q_id": trans_q_id, 
        "answer": long_answer,
        "section_type": "translation",
        "slot_id": 0
    })
    print(f"Subjective Response: {resp_sub.json()}")
    if "[Mock]" in str(resp_sub.json()):
        print("Received Mock response as expected (if LLM failed). Check console for traceback!")

if __name__ == "__main__":
    test_multi_slot_isolation()
