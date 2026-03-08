"""
Phase 33.0 — True Human Simulation E2E Script
Simulates random human behavior with mandatory screenshots for Vision QA.
"""
import os
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:5200"
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def screenshot(page, name):
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=True)
    print(f"📸 Screenshot saved: {name}.png")
    return path

def test_human_simulation():
    print("🧬 [Human Sim] Starting True Human Simulation E2E")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        page.on("console", lambda msg: print(f"  [{msg.type}] {msg.text}") if msg.type in ["error", "warning"] else None)
        page.on("dialog", lambda dialog: dialog.accept())

        # =============================================
        # STEP 1: Dashboard — Overview screenshot
        # =============================================
        print("\n" + "="*60)
        print("STEP 1: Dashboard")
        print("="*60)
        page.goto(f"{BASE_URL}/")
        page.wait_for_timeout(2000)
        screenshot(page, "01_dashboard")

        # =============================================
        # STEP 2: Enter an exam, answer ONLY 1 question, then leave
        # =============================================
        print("\n" + "="*60)
        print("STEP 2: Quick Exam (1 question only)")
        print("="*60)
        
        # Find and click the first exam paper
        exam_link = page.locator("a[href*='/exam/']").first
        if exam_link.count() > 0:
            exam_link.click()
            page.wait_for_timeout(2000)
            screenshot(page, "02_exam_room_entry")
            
            # Answer the first question — just click ANY radio button
            radio = page.locator("input[type='radio']").first
            if radio.count() > 0:
                radio.click(force=True)
                page.wait_for_timeout(500)
                screenshot(page, "03_exam_answered_one")
            else:
                # Try clicking option button if radio not found
                option_btn = page.locator("button:has-text('A')").first
                if option_btn.count() > 0:
                    option_btn.click()
                    page.wait_for_timeout(500)

            # Try to submit / navigate to report
            screenshot(page, "04_exam_before_leave")
        else:
            print("⚠️ No exam links found on dashboard, skipping exam test")

        # =============================================
        # STEP 3: Go to ExamReport for this paper
        # =============================================
        print("\n" + "="*60)
        print("STEP 3: Exam Report (sparse data)")
        print("="*60)
        
        # Navigate to report for test_paper_2026 (has data from Phase 31 tests)
        page.goto(f"{BASE_URL}/report/test_paper_2026")
        page.wait_for_timeout(3000)
        screenshot(page, "05_exam_report_overview")
        
        # Hide GameHUD overlay
        page.evaluate("document.querySelectorAll('.fixed.z-40').forEach(el => el.style.display = 'none')")
        
        # Click first attempt if available
        attempt_btn = page.locator("button:has-text('Attempt')").first
        if attempt_btn.count() > 0:
            attempt_btn.click()
            page.wait_for_timeout(3000)
            screenshot(page, "06_exam_report_detail")
        else:
            print("⚠️ No attempt buttons found")

        # =============================================
        # STEP 4: Vocab Garden — Learn a few words
        # =============================================
        print("\n" + "="*60)
        print("STEP 4: Vocab Garden")
        print("="*60)
        
        page.goto(f"{BASE_URL}/garden")
        page.wait_for_timeout(3000)
        screenshot(page, "07_vocab_garden_initial")
        
        # Learn 3 words
        for i in range(3):
            show_btn = page.locator("#btn-show-answer")
            if show_btn.count() > 0 and show_btn.is_visible():
                show_btn.click()
                page.wait_for_timeout(500)
                screenshot(page, f"08_vocab_card_back_{i+1}") if i == 0 else None
                
                correct_btn = page.locator("#btn-correct")
                if correct_btn.count() > 0 and correct_btn.is_visible():
                    correct_btn.click()
                    page.wait_for_timeout(600)
            else:
                break
        
        screenshot(page, "09_vocab_after_learning")

        # =============================================
        # STEP 5: Speed through remaining to reach Tended
        # =============================================
        print("\n" + "="*60)
        print("STEP 5: Speed to Tended Screen")
        print("="*60)
        
        for i in range(50):
            show_btn = page.locator("#btn-show-answer")
            if show_btn.count() > 0 and show_btn.is_visible():
                show_btn.click()
                page.wait_for_timeout(200)
                correct_btn = page.locator("#btn-correct")
                if correct_btn.count() > 0 and correct_btn.is_visible():
                    correct_btn.click()
                    page.wait_for_timeout(200)
            else:
                break
        
        page.wait_for_timeout(1000)
        tended = page.locator("text=Garden Tended!")
        if tended.count() > 0:
            screenshot(page, "10_vocab_garden_tended")
            
            # STEP 6: Click Endless Mode
            print("\n" + "="*60)
            print("STEP 6: Endless Mode (+10)")
            print("="*60)
            
            endless_btn = page.locator("button:has-text('状态极佳：再背 10 个！')")
            if endless_btn.count() > 0:
                endless_btn.click()
                page.wait_for_timeout(3000)
                screenshot(page, "11_vocab_endless_mode")
                
                # Do 2 more words in endless mode
                for i in range(2):
                    show_btn = page.locator("#btn-show-answer")
                    if show_btn.count() > 0 and show_btn.is_visible():
                        show_btn.click()
                        page.wait_for_timeout(300)
                        correct_btn = page.locator("#btn-correct")
                        if correct_btn.count() > 0:
                            correct_btn.click()
                            page.wait_for_timeout(300)
                
                screenshot(page, "12_vocab_endless_learning")
        else:
            print("⚠️ Could not reach Tended screen")
            screenshot(page, "10_vocab_not_tended")

        print("\n" + "="*60)
        print("🎉 [Human Sim] Simulation Complete!")
        print(f"📁 Screenshots saved to: {SCREENSHOT_DIR}")
        print("="*60)
        
        # List screenshots
        for f in sorted(os.listdir(SCREENSHOT_DIR)):
            if f.endswith(".png"):
                full_path = os.path.join(SCREENSHOT_DIR, f)
                size_kb = os.path.getsize(full_path) / 1024
                print(f"  📸 {f} ({size_kb:.0f} KB)")
        
        browser.close()

if __name__ == "__main__":
    test_human_simulation()
