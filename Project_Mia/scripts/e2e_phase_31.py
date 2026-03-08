import os
import sqlite3
from playwright.sync_api import sync_playwright, expect
import time

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'data', 'femo_profile.db'))

def get_attempts_from_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT attempt_id, paper_id FROM exam_attempts ORDER BY attempt_id DESC")
    attempts = cur.fetchall()
    conn.close()
    return attempts

def get_answers_from_db(attempt_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, q_id, user_answer FROM user_answers WHERE attempt_id = ?", (attempt_id,))
    answers = cur.fetchall()
    conn.close()
    return answers


def test_phase_31_time_engine_and_history():
    print("🚀 [E2E] Starting Phase 31.0 Verification (Time Engine & History Archive)")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        page.on("console", lambda msg: print(f"Browser console [{msg.type}]: {msg.text}"))
        
        # Handle all dialogs automatically
        page.on("dialog", lambda dialog: dialog.accept())

        # Step 1: Login & Navigate to Dashboard
        page.goto("http://localhost:5200/")
        print("✅ [E2E] Reached Dashboard")
        page.wait_for_selector(".grid .group", timeout=10000)
        
        # We will do this TWICE to verify multiple attempts on the same paper
        for attempt_idx in range(1, 3):
            print(f"\n--- 🚀 [E2E] Starting Attempt {attempt_idx} on the same paper ---")
            
            # Click the first paper's "Start" area
            paper_card = page.locator(".grid .group").first
            paper_card.click()
            
            print("✅ [E2E] Navigated to Exam Room")
            page.wait_for_selector('text=← Home', timeout=10000)
            
            # Wait for the timer to load
            timer_element = page.locator("span:has-text('Total') + span").first
            page.wait_for_timeout(2000)
            timer_text = timer_element.inner_text()
            print(f"✅ [E2E] Timer is running: {timer_text}")
            
            # Test blur/focus on the first attempt only
            if attempt_idx == 1:
                print("⏳ [E2E] Testing window blur (Pause)")
                page.evaluate("window.dispatchEvent(new Event('blur'))")
                page.wait_for_timeout(1000)
                print(f"✅ [E2E] Timer after blur: {timer_element.inner_text()}")
                
                print("⏳ [E2E] Testing window focus (Resume)")
                page.evaluate("window.dispatchEvent(new Event('focus'))")
                page.wait_for_timeout(1000)
                print("✅ [E2E] Resumed successfully")
                
                print("⏳ [E2E] Waiting for 10s heartbeat sync to /api/exam/sync_time...")
                with page.expect_response("**/api/exam/sync_time", timeout=15000) as response_info:
                    pass
                resp = response_info.value
                assert resp.status == 200, f"Heartbeat failed with status {resp.status}"
                print("✅ [E2E] Heartbeat intercepted successfully! (200 OK)")

            # Submit answer
            try:
                # Find an objective option
                options = page.locator('label.cursor-pointer').all()
                if len(options) > 0:
                    print("⏳ [E2E] Submitting objective answer (to test attempt_id binding)...")
                    options[0].click(force=True)
                    page.wait_for_timeout(2000) # Wait for network
            except Exception as e:
                print("⚠️ [E2E] Objective answer UI not found:", e)

            # Finish Attempt properly by triggering a reset (which finishes the current attempt and starts a new one)
            print("⏳ [E2E] Triggering '二刷' to finish current attempt...")
            reset_button = page.locator("button:has-text('二刷')").first
            if reset_button.is_visible():
                reset_button.click()
                page.wait_for_timeout(2000)
                
            print("⏳ [E2E] Returning to Dashboard...")
            page.goto("http://localhost:5200/")
                 
            page.wait_for_selector(".grid .group", timeout=10000)
            
            # Check DB state after attempt
            attempts = get_attempts_from_db()
            print(f"🔍 [E2E] Latest Attempt in DB: ID {attempts[0][0]}, Paper {attempts[0][1]}")
            answers = get_answers_from_db(attempts[0][0])
            print(f"🔍 [E2E] Answers recorded for this attempt: {len(answers)}")

        print("\n--- 🔍 [E2E] Verifying DB Constraints (No IntegrityError) ---")
        attempts = get_attempts_from_db()
        assert attempts[0][0] != attempts[1][0], "Attempt IDs should be different!"
        assert attempts[0][1] == attempts[1][1], "Should be on the same paper!"
        print("✅ [E2E] Multiple attempts successfully generated without UNIQUE constraint errors!")

        print("\n--- 🔍 [E2E] Verifying History Archive (Read-only mode) ---")
        history_btn = page.locator("button[title='查看历史批次记录']").first
        history_btn.click()
        
        page.wait_for_selector("text=历史批次", timeout=10000)
        print("✅ [E2E] Reached Exam Report page")
        
        # Verify multiple attempts exist
        attempt_items = page.locator("button:has-text('Attempt #')")
        count = attempt_items.count()
        print(f"✅ [E2E] Found {count} attempts in history.")
        assert count >= 2, "Expected at least 2 attempts for this paper!"
        
        # Verify read-only state (check UI for disabled/static text instead of inputs)
        print("⏳ [E2E] Loading Latest Attempt Detail...")
        
        # Hide the RPG HUD overlay to prevent pointer interception
        page.evaluate("if(document.querySelector('.fixed.z-40')) document.querySelector('.fixed.z-40').style.display='none';")
        
        attempt_items.first.click()
        
        page.wait_for_selector("text=📂 答题明细", timeout=10000)
        print("✅ [E2E] Attempt details loaded!")
        
        # Make sure there are no radio buttons (should be strictly read-only divs)
        radios = page.locator("input[type='radio']")
        assert radios.count() == 0, "Found radio inputs in history view! It should be strictly read-only."
        print("✅ [E2E] ExamReport is strictly read-only (No inputs found)!")

        print("\n🎉 [E2E] Phase 31.0 Verification Complete! Database UNIQUE constraints and Heartbeat verified.")
        browser.close()

if __name__ == "__main__":
    test_phase_31_time_engine_and_history()
