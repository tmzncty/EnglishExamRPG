import os
import sys
import re
from playwright.sync_api import sync_playwright

def main():
    print("🚀 Starting Phase 26 E2E Test: Honest Review & Deferred Grading")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            print("1️⃣ Navigating to Vocab Garden...")
            page.goto("http://localhost:5200/garden")
            page.wait_for_selector(".perspective-1000", timeout=10000)
            
            # Wait for HP to be visible
            print("2️⃣ Fetching current HP...")
            hp_locator = page.locator("span", has_text=re.compile(r"HP \d+ / \d+"))
            hp_locator.wait_for(state="visible", timeout=5000)
            hp_text = hp_locator.text_content()
            
            # Parse initial HP. Format: HP 85 / 100
            try:
                initial_hp = int(re.search(r"HP\s+(\d+)", hp_text).group(1))
                print(f"   ➤ Initial HP: {initial_hp}")
            except Exception as e:
                print(f"   ❌ Failed to parse initial HP from: {hp_text}")
                raise e

            print("3️⃣ Clicking front card to reveal answer...")
            # Locator for Show Answer button.
            show_answer_btn = page.locator("button", has_text="点击查看释义 (Show Answer)")
            show_answer_btn.wait_for(state="visible", timeout=5000)
            show_answer_btn.click()
            
            print("4️⃣ Asserting absence of legacy 'Next Word' button...")
            page.wait_for_selector(".rotate-y-180", timeout=5000) # Wait for back side
            next_word_btn = page.locator("button", has_text="Next Word")
            # The button might be hidden or completely removed. We check its visibility.
            if next_word_btn.count() > 0:
                if next_word_btn.is_visible():
                    raise AssertionError("Legacy 'Next Word' button still exists on the back card!")
            print("   ✅ Legacy 'Next Word' button correctly removed.")

            print("5️⃣ Clicking '记错了' (Forgot) on the back card...")
            forgot_btn = page.locator("button", has_text="记错了 (Forgot)")
            forgot_btn.wait_for(state="visible", timeout=5000)
            forgot_btn.click()
            
            # Wait for the next word to load, which should flip the card back to front
            # The HP should change. Let's wait a bit and fetch it again.
            print("6️⃣ Waiting for HP damage to apply (API call and state update)...")
            page.wait_for_timeout(3000)
            
            new_hp_text = hp_locator.text_content()
            new_hp = int(re.search(r"HP\s+(\d+)", new_hp_text).group(1))
            print(f"   ➤ New HP: {new_hp}")
            
            if new_hp >= initial_hp:
                print(f"   ⚠️ HP did not decrease! initial: {initial_hp}, new: {new_hp}")
                if initial_hp > 0:
                    raise AssertionError("HP did not decrease after marking a word as forgotten!")
            else:
                print(f"   ✅ HP successfully decreased! (Damage registered)")

            print("🎉 All assertions passed for Phase 26.0 Deferred Grading!")
            
        except AssertionError as e:
           print(f"❌ Assertion Error: {e}")
           sys.exit(1)
        except Exception as e:
            print(f"❌ Test Failed: {e}")
            sys.exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    main()
