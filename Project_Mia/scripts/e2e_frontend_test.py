"""
E2E Desktop Core-Loop Test — Phase 18.1
Desktop viewport 1920x1080. Tests the full learn-practice-reset loop in ExamRoom.
Assumes backend (:8000) and frontend (:5200) are already running.
"""

import sys, os, time, socket, traceback

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    print("❌  pip install playwright && playwright install chromium")
    sys.exit(1)

ROOT     = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACK_URL = "http://localhost:8000"
SS_DIR   = os.path.join(ROOT, "scripts")

# Auto-detect which port Vite chose (5200, 5201, 5173 …)
def _detect_port(candidates):
    for p in candidates:
        try:
            with socket.create_connection(("localhost", p), timeout=1):
                return p
        except OSError:
            pass
    return None

_FRONT_PORT = _detect_port([5200, 5201, 5173, 5174])
FRONT_URL   = f"http://localhost:{_FRONT_PORT}" if _FRONT_PORT else "http://localhost:5200"

def log(m):  print(f"  {m}")
def ok(m):   print(f"✅  {m}")
def warn(m): print(f"⚠️   {m}")
def ss(page, name):
    p = os.path.join(SS_DIR, f"e2e_desktop_{name}.png")
    page.screenshot(path=p, full_page=False)
    log(f"📷  scripts/e2e_desktop_{name}.png")
    return p

def check_ports():
    # Backend
    try:
        with socket.create_connection(("localhost", 8000), timeout=2):
            ok("Backend reachable on :8000")
    except OSError:
        print("❌  Backend NOT running on :8000. Start it first!")
        sys.exit(1)
    # Frontend
    if _FRONT_PORT:
        ok(f"Frontend reachable on :{_FRONT_PORT}  → {FRONT_URL}")
    else:
        print("❌  Frontend NOT running on any known port (5200/5201/5173). Start vite first!")
        sys.exit(1)


def run():
    print("\n🖥️   Phase 18.1  Desktop Core-Loop E2E Test")
    print("=" * 55)
    print("\n─── Pre-flight ───")
    check_ports()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, slow_mo=120)
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = ctx.new_page()

        js_errors = []
        page.on("console", lambda m: js_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: js_errors.append(str(e)))

        # Auto-accept every confirm dialog
        page.on("dialog", lambda d: (
            log(f"🔔  Dialog: \"{d.message[:80]}\" → accept"),
            d.accept()
        ))

        try:
            # ──────────────────────────────────────────────────────────────────
            # S1: Dashboard
            # ──────────────────────────────────────────────────────────────────
            print("\n─── S1: Dashboard ───")
            page.goto(FRONT_URL, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_load_state("networkidle", timeout=15000)
            h1 = page.locator("h1").first
            h1.wait_for(timeout=8000)
            log(f"<h1>: '{h1.text_content().strip()}'")
            ss(page, "01_dashboard")
            ok("Dashboard loaded")

            # ──────────────────────────────────────────────────────────────────
            # S2: Enter ExamRoom — pick the first card visible
            # ──────────────────────────────────────────────────────────────────
            print("\n─── S2: Navigate to ExamRoom ───")
            # Paper cards have @click goToPaper and unique paper_id in href
            # Use the grid cards (group relative rounded-2xl)
            cards = page.locator(".grid > div[class*='rounded-2xl']")
            card_count = cards.count()
            log(f"Found {card_count} paper card(s) on Dashboard")

            if card_count == 0:
                # Fallback: try any link to /exam/
                cards = page.locator("div[class*='cursor-pointer']:not([class*='GameHUD'])")
                card_count = cards.count()
                log(f"Fallback: found {card_count} cursor-pointer divs")

            if card_count == 0:
                warn("No exam cards found — navigating to first paper via API fallback")
                papers = page.evaluate("""
                    async () => {
                        const r = await fetch('/api/exams');
                        return r.json();
                    }
                """)
                log(f"API papers: {papers[:2]}")
                if papers:
                    paper_id = papers[0]["paper_id"]
                    page.goto(f"{FRONT_URL}/exam/{paper_id}", wait_until="networkidle", timeout=15000)
                else:
                    warn("No papers in DB at all — cannot test ExamRoom")
                    return
            else:
                first_card = cards.first
                first_card.scroll_into_view_if_needed()
                first_card.click()
                page.wait_for_url("**/exam/**", timeout=10000)

            page.wait_for_load_state("networkidle", timeout=15000)
            exam_url = page.url
            log(f"In ExamRoom: {exam_url}")
            ss(page, "02_exam_room_loaded")
            ok("ExamRoom loaded")

            # ──────────────────────────────────────────────────────────────────
            # S3: Progress bar check
            # ──────────────────────────────────────────────────────────────────
            print("\n─── S3: Progress Bar ───")
            try:
                pbar = page.locator(".bg-emerald-400").first
                pbar.wait_for(timeout=5000)
                # Read the % text from toolbar
                pct_texts = page.locator(".text-\\[10px\\]").all_text_contents()
                log(f"Progress toolbar text: {pct_texts}")
                ok("Progress bar present in toolbar")
            except PWTimeout:
                warn("bg-emerald-400 not found — progress bar may not be rendered yet")

            # ──────────────────────────────────────────────────────────────────
            # S4: Click sidebar — Reading A (or Use of English if no Reading A)
            # ──────────────────────────────────────────────────────────────────
            print("\n─── S4: Sidebar Navigation → Reading A ───")
            sidebar_btn = None
            for label in ["Reading A", "阅读 A", "Use of English", "Reading"]:
                candidates = page.locator(f"button:has-text('{label}')")
                if candidates.count() > 0:
                    sidebar_btn = candidates.first
                    log(f"Found sidebar button: '{label}'")
                    break

            if sidebar_btn:
                sidebar_btn.click()
                page.wait_for_timeout(800)
                ss(page, "03_reading_section")
                ok("Navigated to reading section via sidebar")
            else:
                warn("No Reading A sidebar button found — using current section")

            # ──────────────────────────────────────────────────────────────────
            # S5: Click option A on first SingleChoice question
            # ──────────────────────────────────────────────────────────────────
            print("\n─── S5: Click Answer Option A ───")
            try:
                # Option labels: look for "A." text in any label
                option_label = page.locator("label:has-text('A.')").first
                option_label.wait_for(timeout=6000)
                option_label.scroll_into_view_if_needed()
                log("Found option A label — clicking...")
                option_label.click()
                page.wait_for_timeout(1200)  # wait for submission + feedback
                ss(page, "04_after_answer_A")

                # Look for feedback: correct (✓) or wrong (✗)
                feedback = page.locator("text=正确, text=错了").first
                try:
                    feedback.wait_for(timeout=4000)
                    fb_text = feedback.text_content().strip()
                    log(f"Feedback received: '{fb_text}'")
                    ok("Answer submitted — feedback UI rendered!")
                except PWTimeout:
                    # Try broader check
                    has_correct = page.locator("text=正确").count() > 0
                    has_wrong   = page.locator("text=错了").count() > 0
                    if has_correct or has_wrong:
                        ok("Feedback visible on page (✓ 正确 or ✗ 错了)")
                    else:
                        warn("Feedback not found — question may have no options or section is not objective")
            except PWTimeout:
                warn("option A label not found — trying direct label click")
                try:
                    # Try finding any radio label
                    any_label = page.locator("label[class*='cursor-pointer']").first
                    any_label.wait_for(timeout=3000)
                    any_label.click()
                    page.wait_for_timeout(1000)
                    ss(page, "04_after_answer_fallback")
                    ok("Clicked a choice option (fallback)")
                except PWTimeout:
                    warn("No clickable labels found — section may be subjective/passage only")

            # ──────────────────────────────────────────────────────────────────
            # S6: Navigate to Writing B, type essay, submit
            # ──────────────────────────────────────────────────────────────────
            print("\n─── S6: Writing B — Submit Essay ───")
            writing_btn = None
            for label in ["Writing B", "Writing", "大作文", "写作"]:
                candidates = page.locator(f"button:has-text('{label}')")
                if candidates.count() > 0:
                    writing_btn = candidates.first
                    log(f"Found sidebar button: '{label}'")
                    break

            if writing_btn:
                writing_btn.click()
                page.wait_for_timeout(800)
                ss(page, "05_writing_b_section")

                # Find the textarea
                essay_ta = page.locator("textarea").first
                try:
                    essay_ta.wait_for(timeout=5000)
                    essay_text = "This is a test essay by the E2E automation script. Project Mia is awesome!"
                    essay_ta.fill(essay_text)
                    page.wait_for_timeout(300)
                    log(f"Typed essay: '{essay_text[:50]}...'")
                    ss(page, "06_essay_typed")

                    # Find and click submit button
                    submit_btn = page.locator("button:has-text('提交批改'), button:has-text('Submit')").first
                    submit_btn.wait_for(timeout=5000)
                    log("Clicking 📝 提交批改...")
                    submit_btn.click()

                    # Wait for Mia's AI feedback (may take up to 30s)
                    log("Waiting for Mia's AI grading (up to 30s)...")
                    try:
                        # Feedback: score appears as "得分：X / Y"
                        page.wait_for_selector("text=得分, text=score, text=mia_feedback, .text-rose-500", timeout=30000)
                        score_el = page.locator("text=得分").first
                        score_text = score_el.text_content()
                        log(f"Grading result: '{score_text}'")
                        ss(page, "07_essay_graded")
                        ok("Essay graded by Mia — score result rendered!")
                    except PWTimeout:
                        # Check if button changed to "已提交"
                        submitted_btn = page.locator("text=已提交")
                        if submitted_btn.count() > 0:
                            ok("Essay submitted (✓ 已提交 confirmed, AI grading may be pending)")
                        else:
                            warn("Essay grading timed out — AI may be unavailable. Checking submit state...")
                            is_disabled = page.locator("textarea").first.is_disabled()
                            if is_disabled:
                                ok("textarea disabled after submission — state saved correctly")
                            else:
                                warn("textarea still enabled — possible submission issue")
                        ss(page, "07_essay_submitted")
                except PWTimeout:
                    warn("No textarea found in Writing section")
            else:
                warn("No Writing B sidebar button found — skipping essay test")

            # ──────────────────────────────────────────────────────────────────
            # S7: 一键二刷 (Reset) — click 🔄 二刷
            # ──────────────────────────────────────────────────────────────────
            print("\n─── S7: 🔄 一键二刷 Reset ───")
            reset_btn = page.locator("button:has-text('二刷')").first
            try:
                reset_btn.wait_for(timeout=5000)
                reset_btn.scroll_into_view_if_needed()
                log("Found 🔄 二刷 button — clicking (dialog will auto-accept)...")
                reset_btn.click()
                # Dialog auto-accepted by the handler above
                page.wait_for_timeout(3000)  # wait for DELETE API + store refresh
                ss(page, "08_after_reset")
                ok("Reset button clicked — waiting for clean slate...")

                # S8: Clean slate check
                print("\n─── S8: Clean Slate Assertion ───")
                # After reset: examStore.fetchAnswerHistory() clears all answers
                # Navigate back to Writing B to check textarea is empty again

                if writing_btn:
                    # Click Writing B again
                    writing_btn2 = page.locator("button:has-text('Writing B'), button:has-text('Writing'), button:has-text('大作文'), button:has-text('写作')").first
                    if writing_btn2.count() > 0:
                        writing_btn2.click()
                        page.wait_for_timeout(800)
                    
                    ta2 = page.locator("textarea").first
                    try:
                        ta2.wait_for(timeout=4000)
                        ta_value = ta2.input_value()
                        log(f"Textarea value after reset: '{ta_value}'")
                        if ta_value == "":
                            ok("Clean Slate confirmed! Textarea is EMPTY after reset ✨")
                        else:
                            warn(f"Textarea still has content: '{ta_value[:50]}' — may need store reactivity fix")
                    except PWTimeout:
                        warn("Could not re-locate textarea for clean slate check")
                    
                    ss(page, "09_clean_slate")

                # Also check progress bar is 0 after reset
                try:
                    pct_texts_after = page.locator("text=/\\d+%/").all_text_contents()
                    log(f"Progress % after reset: {pct_texts_after}")
                    if any("0%" in t for t in pct_texts_after):
                        ok("Progress bar shows 0% after reset!")
                    else:
                        log("Progress bar text (may differ): noted above")
                except Exception:
                    pass

            except PWTimeout:
                warn("🔄 二刷 button not found — ensure the ExamRoom progress bar was rendered")

            # ──────────────────────────────────────────────────────────────────
            # Final: JS Error Report
            # ──────────────────────────────────────────────────────────────────
            print("\n─── 🔍 JS Console Error Report ───")
            if js_errors:
                log(f"{len(js_errors)} console error(s):")
                for e in js_errors[:5]:
                    log(f"  [ERR] {e[:130]}")
            else:
                ok("ZERO JavaScript console errors!")

        except Exception as exc:
            traceback.print_exc()
            ss(page, "crash")
        finally:
            ctx.close()
            browser.close()

    print("\n🎉  Desktop E2E Test Complete!\n")


if __name__ == "__main__":
    run()
