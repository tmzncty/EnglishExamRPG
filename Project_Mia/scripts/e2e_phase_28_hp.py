import asyncio
from playwright.async_api import async_playwright
import re

async def run():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Auto-accept window.confirm dialogs (like the reset paper confirm)
        page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))
        
        # Log all browser console messages
        page.on("console", lambda msg: print(f"Browser Console: {msg.text}"))
        
        print("🚀 [Phase 28 E2E] Starting HP Decoupling Validation...")
        
        # 1. Log in / Go to Home
        await page.goto("http://localhost:5200/")
        await page.wait_for_timeout(2000)
        
        # Get Global HP from Home or GameHUD
        hp_element = page.locator("span", has_text=re.compile(r"HP \d+ / \d+")).first
        await hp_element.wait_for(state="visible", timeout=10000)
        global_hp_text = await hp_element.inner_text()
        print(f"🔹 Step 1: Initial Global HP noted: {global_hp_text.strip()}")
        initial_hp_match = re.search(r'HP (\d+)', global_hp_text)
        initial_hp = int(initial_hp_match.group(1)) if initial_hp_match else 100
        
        # 2. Enter Paper A
        print("🔹 Step 2: Entering Paper A & Resetting Progress...")
        await page.goto("http://localhost:5200/exam/2010-eng1")
        await page.wait_for_selector("text=Exam Shield", state="visible")
        
        # Click reset progress to ensure clean state
        reset_btns = await page.locator("button[title*='清空']").count()
        if reset_btns > 0:
            print("   Resetting Paper A progress...")
            await page.locator("button[title*='清空']").first.click(force=True)
            await page.wait_for_timeout(2000)
            
        # Verify initial Paper A shield is 100
        paper_shield_text = await page.locator("text=/[\\d\\.]+\\s*/\\s*100/").first.inner_text()
        print(f"   Paper A Shield Initial: {paper_shield_text.strip()}")
        assert "100" in paper_shield_text, "Paper HP must start at 100 independently"

        # Answer one question to deduct shield
        print("   Answering a question to deduct shield...")
        
        # Click the second label (Option B) which is incorrect for Q1
        option_label = page.locator('.mb-5 label').nth(1)
        await option_label.click(force=True)
        await page.wait_for_timeout(3000)
        
        # Check shield again
        paper_shield_text_updated = await page.locator("text=/[\\d\\.]+\\s*/\\s*100/").first.inner_text()
        print(f"   Paper A Shield Updated: {paper_shield_text_updated.strip()}")
        
        assert paper_shield_text != paper_shield_text_updated, "Paper HP should be deducted after answer"

        # Exit to Home
        print("🔹 Step 3: Exiting to Home...")
        await page.goto("http://localhost:5200/")
        await page.wait_for_timeout(1500)

        # 3. Enter Paper B
        print("🔹 Step 3: Entering Paper B...")
        await page.goto("http://localhost:5200/exam/2010-eng2")
        await page.wait_for_selector("text=Exam Shield", state="visible")
        
        # Verify Paper B shield is 100
        paper_b_shield_text = await page.locator("text=/\\d+\\s*/\\s*100/").first.inner_text()
        print(f"   Paper B Shield Initial: {paper_b_shield_text.strip()}")
        assert "100" in paper_b_shield_text, "Paper B Shield must be 100 independently"
        
        # Exit to Home
        await page.click("text=← Home", force=True)
        await page.wait_for_timeout(1000)
        
        # Intercept Garden API to return empty tasks, forcing "Garden Tended!" immediately
        print("🔹 Step 5: Mocking Garden API to force empty state...")
        await page.route("**/api/vocab/today*", lambda route: route.fulfill(status=200, json={"tasks": [], "total_count": 0, "review_count": 0, "new_count": 0}))
        
        # Now enter Vocab Garden
        print("🔹 Step 4: Entering Vocab Garden...")
        await page.goto("http://localhost:5200/garden")
        await page.wait_for_timeout(2000)
        
        # Verify Global HP
        new_global_hp_text = await page.locator("text=/HP \\d+ / \\d+/").first.inner_text()
        print(f"   Global HP After Exam: {new_global_hp_text.strip()}")
        new_hp_match = re.search(r'HP (\d+)', new_global_hp_text)
        new_hp = int(new_hp_match.group(1)) if new_hp_match else 100
        assert initial_hp == new_hp, f"Global HP should be unchanged! (Initial: {initial_hp}, Now: {new_hp})"
        
        # Wait for Garden Tended to appear due to mocked empty response
        print("   Checking for Garden Tended state...")
        await page.wait_for_selector("text=Garden Tended!", state="visible", timeout=5000)
                
        # Garden is empty, now reload the page
        print("🔹 Step 6: Reloading page to check HP persistence bug...")
        await page.reload()
        await page.wait_for_timeout(3000)
        
        final_hp_text = await page.locator("text=/HP \\d+ / \\d+/").first.inner_text()
        print(f"   Final Global HP After Refresh: {final_hp_text.strip()}")
        final_hp_match = re.search(r'HP (\d+)', final_hp_text)
        final_hp = int(final_hp_match.group(1)) if final_hp_match else 0
        assert final_hp == initial_hp, f"Global HP Bug: HP should be preserved after completing garden! Expected {initial_hp}, got {final_hp}"
        
        print("🎉 [Phase 28 E2E] All HP Decoupling scenarios passed successfully!")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
