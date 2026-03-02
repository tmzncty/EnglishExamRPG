from playwright.sync_api import sync_playwright, expect
import sys
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 414, 'height': 896})  # Mobile layout
        page = context.new_page()

        print("🚀 [Phase 24 E2E] Starting Test: Sentence Debug & Contextual AI")
        
        # Setup request interception to verify prompt
        interacted_prompt = []
        
        def handle_request(request):
            if "api/mia/interact" in request.url and request.method == "POST":
                data = request.post_data_json
                if data and "context_data" in data and "message" in data["context_data"]:
                    msg = data["context_data"]["message"]
                    interacted_prompt.append(msg)
                    print(f"📡 Intercepted Mia Prompt: {msg[:50]}...")

        page.on("request", handle_request)
        
        try:
            # 1. Enter Garden
            print("🔹 Navigate to /garden...")
            page.goto("http://localhost:5200/garden")
            page.wait_for_load_state("networkidle")
            
            # Wait for word card to appear
            expect(page.locator("h1.text-5xl.font-black").first).to_be_visible(timeout=10000)
            
            # 2. Find a word with an exam sentence
            print("🔹 Searching for a word with an exam sentence...")
            exam_sentence_locator = page.locator(".exam-sentence").first
            sentence_text = None
            found = False
            
            for _ in range(3):
                try:
                    expect(exam_sentence_locator).to_be_visible(timeout=2000)
                    sentence_text = exam_sentence_locator.inner_text()
                    found = True
                    break
                except Exception:
                    print("   ...No sentence on this word, skipping...")
                    page.locator("button:has-text('Know')").first.click(force=True)
                    page.wait_for_timeout(300)
                    page.locator("button:has-text('Next Word')").first.click(force=True)
                    page.wait_for_timeout(500)
            
            if not found:
                raise Exception("Could not find a sentence after 3 tries. API prioritization might have failed.")
            
            print(f"✅ Found Exam Sentence on Front: {sentence_text.strip()}")
            
            # 3. Flip the card (click Know)
            print("🔹 Flipping the card...")
            page.locator("button:has-text('Know')").first.click(force=True)
            
            # Wait for flip animation
            page.wait_for_timeout(500)
            
            # Assert .exam-sentence is visible on back
            print("🔹 Asserting .exam-sentence is visible on the Back Card...")
            back_sentence_locator = page.locator(".rotate-y-180 .exam-sentence").first
            expect(back_sentence_locator).to_be_visible(timeout=5000)
            print("✅ Found Exam Sentence on Back.")
            
            # 4. Click Call Mia
            print("🔹 Clicking [💡 呼叫 Mia 详细讲解]...")
            page.locator("text=呼叫 Mia 详细讲解").click(force=True)
            
            # Wait for the network request to fire
            page.wait_for_timeout(2000)
            
            # 5. Assert global chat opens and context is passed
            print("🔹 Verifying Mia prompt contains the sentence...")
            
            clean_sentence = sentence_text.strip().strip('"')
            
            if not interacted_prompt:
                raise Exception("Did not intercept any request to /api/mia/interact")
                
            actual_prompt = interacted_prompt[0]
            if clean_sentence not in actual_prompt:
                raise Exception(f"Intercepted prompt did not contain the sentence. Prompt: {actual_prompt}")
                
            print("✅ Successfully verified contextual prompt includes the sentence!")
            
        except Exception as e:
            print(f"❌ Test Failed: {e}")
            browser.close()
            sys.exit(1)
            
        browser.close()
        print("✅ End of E2E verification.")

if __name__ == "__main__":
    run()
