import sys
import os
import time
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.main import app

client = TestClient(app)

def print_pass(msg):
    print(f"✅ PASS: {msg}")

def print_fail(msg):
    print(f"❌ FAIL: {msg}")
    sys.exit(1)

def test_peaceful_garden():
    print("\n🌸 Entering Peaceful Garden Automated Test 🌸\n")

    # 1. Test Free Save Slots
    print("--- Task 1: Free Save Slots ---")
    
    # Get initial slots
    resp = client.get("/api/user/slots")
    initial_slots = resp.json()
    print(f"Initial Slots: {len(initial_slots)}")
    
    # Create new slot
    print("Creating new slot...")
    resp = client.post("/api/user/slots/new")
    assert resp.status_code == 200
    new_slot_id = resp.json()["slot_id"]
    print(f"Created Slot ID: {new_slot_id}")
    
    # Verify slot exists
    resp = client.get("/api/user/slots")
    current_slots = resp.json()
    found = any(s["slot_id"] == new_slot_id for s in current_slots)
    
    if found:
        print_pass(f"New slot {new_slot_id} created and verified.")
    else:
        print_fail(f"New slot {new_slot_id} not found in listing.")

    # 2. Test Gentle Leveling System
    print("\n--- Task 2: Gentle Leveling System ---")
    # Initial state: Lv 1, EXP 0, HP 100
    
    # Force add EXP to trigger level up (Need 100 EXP for Lv 2)
    # We will save EXP = 150
    print(f"Simulating massive EXP gain (150 EXP) on Slot {new_slot_id}...")
    
    # First, drain HP a bit to test heal
    client.post("/api/user/save", json={"slot_id": new_slot_id, "hp": 50, "max_hp": 100, "level": 1, "exp": 0})
    
    # Now Save with EXP 150
    resp = client.post("/api/user/save", json={
        "slot_id": new_slot_id, 
        "hp": 50, 
        "max_hp": 100, 
        "level": 1, 
        "exp": 150
    })
    
    data = resp.json()
    print(f"Save Response: {data}")
    
    if data.get("leveled_up") and data.get("new_level") == 2 and data.get("new_hp") == 100:
        print_pass("Level Up triggered correctly! Lv 1 -> 2, HP restored to 100.")
    else:
        print_fail(f"Level up failed. Expected Lv 2 & HP 100. Got: {data}")
        
    # Check if EXP carried over (Should be 50)
    if data.get("new_exp") == 50:
        print_pass("EXP carried over correctly (150 - 100 = 50).")
    else:
        print_fail(f"EXP calculation wrong. Expected 50, got {data.get('new_exp')}")


    # 3. Test Vocab Engine
    print("\n--- Task 3: Vocab Engine (The Garden) ---")
    
    # Get Today's tasks
    print("Fetching today's vocab tasks...")
    resp = client.get("/api/vocab/today", params={"slot_id": new_slot_id})
    tasks = resp.json().get("tasks", [])
    print(f"Tasks received: {len(tasks)}")
    
    if len(tasks) > 0:
        print_pass("Vocab tasks fetched successfully.")
        
        # Test Review
        word_to_review = tasks[0]["word"]
        print(f"Reviewing word: '{word_to_review}' (Perfect Score 5)...")
        
        # Current state check
        # Slot is now Lv 2, EXP 50, HP 100 (Full) from previous step
        # Let's drain HP again to verify +0.5 HP reward
        client.post("/api/user/save", json={"slot_id": new_slot_id, "hp": 90, "max_hp": 100, "level": 2, "exp": 50})
        
        resp = client.post("/api/vocab/review", json={
            "slot_id": new_slot_id,
            "word": word_to_review,
            "quality": 5
        })
        review_res = resp.json()
        print(f"Review Result: {review_res}")
        
        reward = review_res.get("reward", {})
        if reward.get("hp") == 0.5 and reward.get("exp") == 2:
            print_pass("Review reward logic returns correct values (+0.5 HP, +2 EXP).")
            
            # Verify DB state
            status = client.get("/api/user/status", params={"slot_id": new_slot_id}).json()
            print(f"User Status after review: {status}")
            
            # Expected: HP 90->90.5 (or 90.5 stored), EXP 50->52
            if status["exp"] == 52:
                print_pass("EXP updated in DB correctly (50 -> 52).")
            else:
                print_fail(f"EXP update failed. Expected 52, got {status['exp']}")
                
            if status["hp"] > 90:
                print_pass("HP updated in DB correctly (> 90).")
            else:
                print_fail(f"HP update failed. Expected > 90, got {status['hp']}")
                
        else:
            print_fail(f"Reward logic incorrect. Got: {reward}")
            
    else:
        print_fail("No vocab tasks returned. Is exam_vocabulary.json loaded?")

    print("\n🎉 Peaceful Garden Verification Completed Successfully! 🎉")

if __name__ == "__main__":
    test_peaceful_garden()
