import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"
SEPARATOR = "=" * 60

def log(msg, color="white"):
    # Simple color logging
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "white": "\033[0m",
        "cyan": "\033[96m"
    }
    timestamp = time.strftime("%H:%M:%S")
    print(f"{colors.get(color, '')}[{timestamp}] {msg}{colors['white']}")

def assert_status(resp, expected=200, step_name=""):
    if resp.status_code != expected:
        log(f"❌ {step_name} Failed! Status: {resp.status_code}", "red")
        log(f"Response: {resp.text}", "red")
        sys.exit(1)
    else:
        log(f"✅ {step_name} Success (200)", "green")

def run_e2e_test():
    print(SEPARATOR)
    log("🚀 Project_Mia Master E2E Test (Doomsday Judgment) Started", "cyan")
    print(SEPARATOR)

    # =================================================================
    # Step 1: System Init
    # =================================================================
    log("🔹 [Step 1] System Init: Fetching Exams List...", "yellow")
    try:
        resp = requests.get(f"{BASE_URL}/api/exams")
        assert_status(resp, 200, "Get Exams")
        exams = resp.json()
        if not isinstance(exams, list) or len(exams) == 0:
            log("❌ Exams list is empty or invalid!", "red")
            sys.exit(1)
        log(f"   Fetched {len(exams)} exams.", "white")
    except Exception as e:
        log(f"❌ Connection Failed: {e}", "red")
        sys.exit(1)

    # =================================================================
    # Step 2: RPG Load
    # =================================================================
    log("🔹 [Step 2] RPG Load: Loading User Status...", "yellow")
    resp = requests.get(f"{BASE_URL}/api/user/load")
    assert_status(resp, 200, "Load RPG Profile")
    profile = resp.json()
    log(f"   HP: {profile.get('hp')}/{profile.get('max_hp')}, Level: {profile.get('level')}", "white")
    
    initial_hp = profile.get("hp", 100)

    # =================================================================
    # Step 3: Objective Submit (Reading - Incorrect Answer to cause damage)
    # =================================================================
    log("🔹 [Step 3] Objective Submit: Submitting Wrong Answer...", "yellow")
    payload_obj = {
        "q_id": "2023-eng1-reading-text1-q21", # Assuming this ID exists or mocked
        "answer": "WRONG_OPTION",
        "section_type": "reading_a"
    }
    resp = requests.post(f"{BASE_URL}/api/exam/submit_objective", json=payload_obj)
    assert_status(resp, 200, "Submit Objective")
    res_obj = resp.json()
    
    damage = res_obj.get("hp_change", 0)
    current_hp = res_obj.get("hp")
    log(f"   Answer Correct: {res_obj.get('correct')}", "white")
    log(f"   HP Change: {damage}, Current HP: {current_hp}", "white")

    if damage >= 0:
        log("⚠️ Warning: No damage received for wrong answer. (Maybe full health or config?)", "yellow")

    # =================================================================
    # Step 4: RPG Save (Sync)
    # =================================================================
    log("🔹 [Step 4] RPG Save: Syncing State to DB...", "yellow")
    save_payload = {
        "slot_id": 0,
        "hp": current_hp,
        "max_hp": 100,
        "level": 1,
        "exp": 0,
        "current_paper_id": "2023-eng1",
        "mia_mood": "normal"
    }
    resp = requests.post(f"{BASE_URL}/api/user/save", json=save_payload)
    assert_status(resp, 200, "Save RPG Profile")
    log("   Save successful.", "green")

    # =================================================================
    # Step 5: Subjective Translation (The 500 Killer)
    # =================================================================
    log("🔹 [Step 5] Subjective Translation: Submitting...", "yellow")
    payload_trans = {
        "q_id": "2023-eng1-translation-q46",
        "answer": "The quick brown fox jumps over the lazy dog.",
        "section_type": "translation"
    }
    
    # 增加超时时间，LLM 可能较慢
    resp = requests.post(f"{BASE_URL}/api/exam/submit_subjective", json=payload_trans, timeout=60)
    assert_status(resp, 200, "Submit Translation")
    
    res_trans = resp.json()
    score_trans = res_trans.get("score")
    log(f"   Score: {score_trans} / {res_trans.get('max_score')}", "white")
    log(f"   Mia Feedback: {res_trans.get('mia_feedback')}", "white")

    # Deep Assertion: Score Range
    if not (0.0 <= score_trans <= 2.0):
        log(f"❌ Score out of range! Got {score_trans}, expected 0-2.0", "red")
        sys.exit(1)
    
    # Deep Assertion: JSON Structure (implicit in .json() success, but check fields)
    if "detailed_analysis" not in res_trans:
        log("❌ Missing 'detailed_analysis' field.", "red")
        sys.exit(1)

    # =================================================================
    # Step 6: Subjective Essay (Writing)
    # =================================================================
    log("🔹 [Step 6] Subjective Essay: Submitting...", "yellow")
    payload_essay = {
        "q_id": "2023-eng1-writing-a",
        "answer": "Dear Sir/Madam, I am writing to suggest improving the library service...",
        "section_type": "writing_a"
    }
    resp = requests.post(f"{BASE_URL}/api/exam/submit_subjective", json=payload_essay, timeout=60)
    assert_status(resp, 200, "Submit Essay")
    
    res_essay = resp.json()
    score_essay = res_essay.get("score")
    log(f"   Score: {score_essay} / {res_essay.get('max_score')}", "white")
    
    if not (0.0 <= score_essay <= 10.0): # Writing A is max 10
         log(f"❌ Score out of range! Got {score_essay}, expected 0-10.0", "red")
         sys.exit(1)

    # =================================================================
    # Step 7: Chat New (Stream)
    # =================================================================
    log("🔹 [Step 7] Chat New: Starting Conversation...", "yellow")
    chat_payload = {
        "messages": [{"role": "user", "content": "Hello Mia, what's my HP?"}],
        "q_id": "2023-eng1-translation-q46",
        "context_type": "translation",
        "stream": True
    }
    
    full_content = ""
    with requests.post(f"{BASE_URL}/api/mia/interact", json=chat_payload, stream=True, timeout=30) as r:
        assert_status(r, 200, "Chat Interact")
        for line in r.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                # SSE format: data: ...
                if decoded.startswith("data: "):
                    try:
                        data_str = decoded[6:]
                        if data_str == "[DONE]":
                            break
                        chunk_json = json.loads(data_str)
                        if "mia_reply" in chunk_json:
                            full_content += chunk_json["mia_reply"]
                        if "content" in chunk_json:
                            full_content += chunk_json["content"]
                    except:
                        pass
    
    if not full_content:
        log("❌ No content received from chat stream!", "red")
        # sys.exit(1) # Allow to proceed for now to test step 8 if possible, or fail?
        # Let's fail strict.
        sys.exit(1)
        
    log(f"   Mia replied: {full_content[:50]}...", "white")

    # =================================================================
    # Step 8: Chat Follow-up (Context Retention)
    # =================================================================
    log("🔹 [Step 8] Chat Follow-up: Asking detailed question...", "yellow")
    # For a real retention test, we'd need conversation_id. 
    # Current simplistic API might just rely on client sending history?
    # Checking backend agent.py... it receives `messages` list.
    # So "Retention" is client-side responsibility in this API design.
    # We will simulate sending history.
    
    chat_payload_2 = {
        "messages": [
             {"role": "user", "content": "Hello Mia, what's my HP?"},
             {"role": "assistant", "content": full_content},
             {"role": "user", "content": "Tell me more about it."}
        ],
        "q_id": "2023-eng1-translation-q46",
        "context_type": "translation",
        "stream": True
    }
    
    full_content_2 = ""
    with requests.post(f"{BASE_URL}/api/mia/interact", json=chat_payload_2, stream=True, timeout=30) as r:
        assert_status(r, 200, "Chat Follow-up")
        for line in r.iter_lines():
           if line:
                decoded = line.decode('utf-8')
                if decoded.startswith("data: "):
                     data_str = decoded[6:]
                     if data_str == "[DONE]": break
                     try:
                        chunk_json = json.loads(data_str)
                        if "mia_reply" in chunk_json:
                             full_content_2 += chunk_json["mia_reply"]
                        if "content" in chunk_json:
                             full_content_2 += chunk_json["content"]
                     except: pass

    if not full_content_2:
        log("❌ No content received from follow-up chat!", "red")
        sys.exit(1)
        
    log(f"   Mia follow-up: {full_content_2[:50]}...", "white")

    print(SEPARATOR)
    log("✨🎉 ALL SYSTEMS GO! DOOMSDAY JUDGMENT PASSED! 🎉✨", "green")
    print(SEPARATOR)

if __name__ == "__main__":
    run_e2e_test()
