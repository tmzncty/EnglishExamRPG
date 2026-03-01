import requests
import sqlite3
import os
import time

BASE_URL = "http://127.0.0.1:8000"
DB_PATH = r"f:\sanity_check_avg\Project_Mia\backend\data\static_content.db"

def setup_test_data():
    """Injects temporary test data directly into the database."""
    print("🛠️ Injecting test data...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Insert Dummy Paper
        cursor.execute("INSERT OR IGNORE INTO papers (paper_id, year, exam_type, title) VALUES (?, ?, ?, ?)", 
                       ("test_paper_2026", 2026, "Test", "HP Penalty Logic Test"))

        # 2. Insert Dummy Questions
        # - Cloze (Use 'use_of_english')
        cursor.execute("""
            INSERT OR REPACE INTO questions 
            (q_id, paper_id, question_number, q_type, section_type, content, options_json, correct_answer, score) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("test_cloze_1", "test_paper_2026", 1, "objective", "use_of_english", "Cloze Test Q1", '{"A":"OptA"}', "A", 0.5))

        # - Reading A (Section 'reading_a')
        cursor.execute("""
            INSERT OR REPACE INTO questions 
            (q_id, paper_id, question_number, q_type, section_type, content, options_json, correct_answer, score) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("test_reading_1", "test_paper_2026", 21, "objective", "reading_a", "Reading A Q21", '{"A":"OptA"}', "A", 2.0))
        
        # - Writing B (Subjective) - Note: Subjective needs careful handling w/o mocking LLM, but we test the math logic mainly
        cursor.execute("""
            INSERT OR REPACE INTO questions 
            (q_id, paper_id, question_number, q_type, section_type, content, score) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("test_essay_1", "test_paper_2026", 52, "subjective", "writing_b", "Write an essay about testing.", 20.0))

        conn.commit()
        conn.close()
        print("✅ Test data injected successfully.")
    except Exception as e:
        print(f"❌ Failed to inject test data: {e}")
        # Improve robustness: if column mismatch, we might need adjustments, but assuming schema is standard
        # If 'REPACE' is typo, it should be 'REPLACE'.
        if "REPACE" in str(e): # typo fix self check
             pass # Logic error in my string above? Yes REPLACE
        raise e

def test_hp_penalty():
    print("🧪 Starting Strict HP Penalty Test...")
    
    # --- 1. Use of English (0.5 HP) ---
    print("\n[Scenario 1] Wrong Cloze Question (Expected: -0.5 HP)")
    try:
        # Submit WRONG answer for our injected question
        payload = {
            "q_id": "test_cloze_1",
            "answer": "B" # Correct is A
        }
        res = requests.post(f"{BASE_URL}/api/exam/submit_objective", json=payload).json()
        print(f"  -> HP Change: {res.get('hp_change')}")
        assert res.get('hp_change') == -0.5, f"Expected -0.5, got {res.get('hp_change')}"
        print("  ✅ PASS")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        raise e # Fail checks!

    # --- 2. Reading A (2.0 HP) ---
    print("\n[Scenario 2] Wrong Reading A Question (Expected: -2.0 HP)")
    try:
        payload = {
            "q_id": "test_reading_1",
            "answer": "B" # Correct is A
        }
        res = requests.post(f"{BASE_URL}/api/exam/submit_objective", json=payload).json()
        print(f"  -> HP Change: {res.get('hp_change')}")
        assert res.get('hp_change') == -2.0, f"Expected -2.0, got {res.get('hp_change')}"
        print("  ✅ PASS")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        raise e

    # --- 3. Subjective Essay (Math Check) ---
    print("\n[Scenario 3] Subjective Essay Logic (Simulated Score)")
    try:
        # We can't easily force specific score from LLM without mocking.
        # But we can check if the RETURN packet respects the math: hp_change = -(max_score - score)
        payload = {
            "q_id": "test_essay_1",
            "answer": "This is a test essay submission.",
            "section_type": "writing_b"
        }
        
        # Note: If LLM fails/mock runs, it might return 0 score. Max is 20.
        # This is fine, we just verify the math consistency.
        
        res = requests.post(f"{BASE_URL}/api/exam/submit_subjective", json=payload).json()
        
        score = res['score']
        max_score = res['max_score']
        hp_change = res['hp_change']
        
        print(f"  -> Score: {score}, Max: {max_score}, HP Change: {hp_change}")
        
        expected_penalty = -(max_score - score)
        
        # Float math check
        if abs(hp_change - expected_penalty) > 0.01:
             raise AssertionError(f"Math Mismatch! Expected {expected_penalty}, got {hp_change}")
        
        # We ideally want to see NON-ZERO penalty to prove it works, but 0 penalty implies perfect score.
        # If score is 0, penalty must be -20.
        
        print("  ✅ PASS")

    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        raise e

if __name__ == "__main__":
    # Fix typo in my injection script string before running logic
    # Actually I'll correct it in the file writing content below.
    # Re-defining setup here safely.
    
    # Correction for "REPACE" -> "REPLACE"
    def setup_test_data_corrected():
        print("🛠️ Injecting test data...")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO papers (paper_id, year, exam_type, title) VALUES (?, ?, ?, ?)", 
                       ("test_paper_2026", 2026, "Test", "HP Penalty Logic Test"))

        # Cloze
        cursor.execute("""
            INSERT OR REPLACE INTO questions 
            (q_id, paper_id, question_number, q_type, section_type, content, options_json, correct_answer, score) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("test_cloze_1", "test_paper_2026", 1, "objective", "use_of_english", "Cloze Test Q1", '{"A":"OptA"}', "A", 0.5))

        # Reading
        cursor.execute("""
            INSERT OR REPLACE INTO questions 
            (q_id, paper_id, question_number, q_type, section_type, content, options_json, correct_answer, score) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("test_reading_1", "test_paper_2026", 21, "objective", "reading_a", "Reading A Q21", '{"A":"OptA"}', "A", 2.0))
        
        # Writing
        cursor.execute("""
            INSERT OR REPLACE INTO questions 
            (q_id, paper_id, question_number, q_type, section_type, content, score) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("test_essay_1", "test_paper_2026", 52, "subjective", "writing_b", "Write an essay.", 20.0))

        conn.commit()
        conn.close()
        print("✅ Test data injected successfully.")

    try:
        setup_test_data_corrected()
        test_hp_penalty()
    except Exception as e:
        print(f"\n❌ SCRIPT FAILED: {e}")
        exit(1)
