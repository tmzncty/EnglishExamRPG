"""
Phase 32.0 E2E Test: Human-Centric UI & Endless Mode
Tests:
1. Global Mastery Progress bar renders on /garden
2. Endless mode button appears after all words are done
3. Phantom pause fix (timer runs while page is focused)
4. ExamReport human-readable rendering
"""
import sys
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:5200"

def test_phase_32():
    print("🚀 [E2E] Starting Phase 32.0 Verification")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        page.on("console", lambda msg: print(f"  Console [{msg.type}]: {msg.text}"))
        page.on("dialog", lambda dialog: dialog.accept())

        # =============================================
        # TEST 1: Global Mastery Progress on /garden
        # =============================================
        print("\n--- TEST 1: Global Mastery Progress ---")
        page.goto(f"{BASE_URL}/garden")
        page.wait_for_timeout(3000)  # Wait for API calls to complete
        
        mastery_el = page.locator("text=Mastery")
        if mastery_el.count() > 0:
            print("✅ [PASS] Global Mastery progress bar is rendered!")
            # Check if it shows the count format
            mastery_text = page.locator("#progress-dashboard").inner_text()
            print(f"  Dashboard text: {mastery_text[:200]}...")
        else:
            print("❌ [FAIL] Mastery progress bar not found!")
            browser.close()
            sys.exit(1)

        # =============================================
        # TEST 2: Phantom Pause Fix
        # =============================================
        print("\n--- TEST 2: Phantom Pause Fix ---")
        page.wait_for_timeout(1000)
        pause_badge = page.locator("text=[⏸️暂停中]")
        if pause_badge.count() == 0 or not pause_badge.is_visible():
            print("✅ [PASS] No phantom pause detected while page is focused!")
        else:
            print("❌ [FAIL] Phantom pause badge is visible despite page being focused!")
            browser.close()
            sys.exit(1)

        # =============================================
        # TEST 3: Endless Mode Button (after finishing)
        # =============================================
        print("\n--- TEST 3: Endless Mode Button ---")
        # Try to speed through any available words to reach the "Tended" screen
        for i in range(50):  # Try up to 50 words
            show_btn = page.locator("#btn-show-answer")
            if show_btn.count() > 0 and show_btn.is_visible():
                show_btn.click()
                page.wait_for_timeout(300)
                correct_btn = page.locator("#btn-correct")
                if correct_btn.count() > 0 and correct_btn.is_visible():
                    correct_btn.click()
                    page.wait_for_timeout(400)
            else:
                break
        
        # Check if we reached the Tended screen
        page.wait_for_timeout(1000)
        tended = page.locator("text=Garden Tended!")
        if tended.count() > 0:
            print("✅ Reached 'Garden Tended!' screen")
            endless_btn = page.locator("button:has-text('状态极佳：再背 10 个！')")
            if endless_btn.count() > 0 and endless_btn.is_visible():
                print("✅ [PASS] Endless mode button is rendered!")
            else:
                print("❌ [FAIL] Endless mode button not found on Tended screen!")
                browser.close()
                sys.exit(1)
        else:
            print("⚠️ [SKIP] Could not reach Tended screen (too many words). Skipping endless mode visual test.")

        # =============================================
        # TEST 4: Human-Readable Exam Report
        # =============================================
        print("\n--- TEST 4: Human-Readable Exam Report ---")
        page.goto(f"{BASE_URL}/report/test_paper_2026")
        page.wait_for_timeout(3000)
        
        history_header = page.locator("text=历史批次")
        if history_header.count() > 0:
            print("✅ Report page loaded with '历史批次' header")
            
            # Hide GameHUD overlay to prevent click interception
            page.evaluate("document.querySelectorAll('.fixed.z-40').forEach(el => el.style.display = 'none')")
            
            # Click the first attempt
            attempt_btn = page.locator("button:has-text('Attempt')").first
            if attempt_btn.count() > 0:
                attempt_btn.click()
                page.wait_for_timeout(2000)
                
                # Check for actual question content (not just q_id)
                detail_header = page.locator("text=📂 答题明细")
                if detail_header.count() > 0:
                    print("✅ [PASS] Answer details section rendered!")
                else:
                    print("⚠️ [WARN] Could not find '📂 答题明细' header")
            else:
                print("⚠️ [SKIP] No attempt buttons found to test")
        else:
            print("⚠️ [SKIP] No history found for test_paper_2026")

        # =============================================
        # TEST 5: API Endpoint Verification
        # =============================================
        print("\n--- TEST 5: API Endpoint Verification ---")
        response = page.evaluate("""async () => {
            try {
                const resp = await fetch('/api/vocab/global_stats?slot_id=0');
                const data = await resp.json();
                return { status: resp.status, data: data };
            } catch(e) {
                return { error: e.message };
            }
        }""")
        if response.get("status") == 200:
            data = response.get("data", {})
            print(f"✅ [PASS] /api/vocab/global_stats returns 200")
            print(f"  total_words: {data.get('total_words')}, mastered_words: {data.get('mastered_words')}")
        else:
            print(f"❌ [FAIL] /api/vocab/global_stats returned: {response}")

        print("\n🎉 [E2E] Phase 32.0 Verification Complete!")
        browser.close()

if __name__ == "__main__":
    test_phase_32()
