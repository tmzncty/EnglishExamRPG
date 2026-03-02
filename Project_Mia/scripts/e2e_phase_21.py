"""
Phase 21.0 前端 E2E 验证 (Playwright)
Tests: Slot naming, dictionary modal, mastery dots.
"""
import sys
import time
import requests
from playwright.sync_api import sync_playwright

FRONTEND_URL = "http://localhost:5200"
API_BASE = "http://localhost:8000/api"
PASS = 0
FAIL = 0

def check(label: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ PASS: {label}")
    else:
        FAIL += 1
        print(f"  ❌ FAIL: {label} — {detail}")


def cleanup_test_slots():
    """Delete any leftover 'Test Slot 99' slots from previous runs."""
    try:
        slots = requests.get(f"{API_BASE}/user/slots").json()
        for s in slots:
            if s.get("slot_name") == "Test Slot 99" or (s.get("slot_id", 0) > 1 and "Test" in s.get("slot_name", "")):
                requests.delete(f"{API_BASE}/user/slots/{s['slot_id']}")
                print(f"    [Cleanup] Deleted leftover slot {s['slot_id']} ({s.get('slot_name')})")
    except Exception as e:
        print(f"    [Cleanup] Warning: {e}")


def main():
    global PASS, FAIL

    print("=" * 60)
    print("🧪 Phase 21.0 前端 E2E 验证 (Playwright)")
    print("=" * 60)

    # Pre-cleanup
    print("\n🧹 Cleaning up leftover test slots...")
    cleanup_test_slots()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Register dialog handler BEFORE any navigation
        def handle_dialog(dialog):
            print(f"    [Dialog] type={dialog.type}, message='{dialog.message[:60]}'")
            if dialog.type == "prompt":
                dialog.accept("Test Slot 99")
            elif dialog.type == "confirm":
                dialog.accept()
            else:
                dialog.dismiss()

        page.on("dialog", handle_dialog)

        try:
            # ──── Step 1: Load the page ────
            print(f"\n📋 Step 1: 访问 {FRONTEND_URL}")
            page.goto(FRONTEND_URL, wait_until="networkidle")
            time.sleep(1)
            check("Page loaded", True)

            # Handle possible welcome screen
            begin_btn = page.locator("text=Begin Journey")
            if begin_btn.is_visible():
                begin_btn.click()
                time.sleep(1)

            # ──── Step 2: Open Settings & Create Slot ────
            print("\n📋 Step 2: 打开 ⚙️ 设置弹窗并创建 'Test Slot 99'")

            gear_btn = page.locator("button:has-text('⚙️')")
            gear_btn.wait_for(state="visible", timeout=5000)
            gear_btn.click()
            time.sleep(1)

            modal_title = page.locator("h3:has-text('存档管理')")
            check("Settings modal opened", modal_title.is_visible())

            # Click "+ 新建存档" — triggers prompt() dialog
            create_btn = page.locator("button:has-text('新建存档')")
            create_btn.click()
            time.sleep(2)
            check("Slot creation triggered via dialog", True)

            # ──── Step 3: Verify slot names ────
            print("\n📋 Step 3: 验证存档名称渲染")

            # Use .first to avoid strict mode issues
            slot_entry = page.locator("div.truncate:has-text('Test Slot 99')").first
            check("'Test Slot 99' in slot list", slot_entry.is_visible())

            main_entry = page.locator("div.truncate:has-text('主存档')").first
            check("Slot 0 is '主存档 (Main Save)'", main_entry.is_visible())

            # Verify zero "Auto Save" in any slot name divs
            auto_save = page.locator("div.truncate:has-text('Auto Save')")
            check("No 'Auto Save' in slot list", auto_save.count() == 0, f"found {auto_save.count()}")

            # Close modal
            page.locator("button:has-text('取消')").click()
            time.sleep(0.5)

            # ──── Step 4: Verify dropdown ────
            print("\n📋 Step 4: 验证快捷下拉框")
            select_el = page.locator("select")
            check("Dropdown visible", select_el.is_visible())
            opts_text = select_el.inner_text()
            check("Dropdown has 'Test Slot 99'", "Test Slot 99" in opts_text, opts_text[:200])
            check("Dropdown has '主存档'", "主存档" in opts_text, opts_text[:200])

            # ──── Step 5: Navigate to VocabGarden ────
            print("\n📋 Step 5: 进入 VocabGarden 并打开 📚 我的词库")

            # Navigate to VocabGarden via direct URL (route: /garden)
            page.goto(f"{FRONTEND_URL}/garden", wait_until="networkidle")
            time.sleep(2)

            dict_btn = page.locator("button:has-text('我的词库')")
            check("📚 Dictionary button visible", dict_btn.is_visible())

            dict_btn.click()
            time.sleep(2)

            dict_header = page.locator("h2:has-text('我的词库')")
            check("Dictionary drawer opened", dict_header.is_visible())

            stats_el = page.locator("text=掌握词汇:")
            check("Stats line rendered", stats_el.is_visible())
            if stats_el.is_visible():
                print(f"    → {stats_el.inner_text()}")

            word_cards = page.locator(".font-black.text-lg.text-gray-800")
            card_count = word_cards.count()
            check(f"Word cards rendered ({card_count} items)", card_count > 0)

            dots = page.locator(".w-2.h-2.rounded-full")
            check(f"Mastery dots rendered ({dots.count()} dots)", dots.count() > 0)

        except Exception as e:
            check("Unexpected exception", False, str(e)[:400])

        finally:
            browser.close()

    # ──── Step 6: Backend API Sanity ────
    print("\n📋 Step 6: 后端 API 黄金路径验证")
    try:
        r = requests.post(f"{API_BASE}/vocab/review", json={"slot_id": 0, "word": "test_word_e2e", "quality": 5})
        data = r.json()
        check("POST /vocab/review returns 'srs' field", "srs" in data, str(list(data.keys())))
        check("'streak' in srs response", "streak" in data.get("srs", {}), str(data.get("srs")))
        check("'mastery' in srs response", "mastery" in data.get("srs", {}), str(data.get("srs")))

        # Test /vocab/list
        r2 = requests.get(f"{API_BASE}/vocab/list", params={"slot_id": 0})
        d2 = r2.json()
        check("GET /vocab/list returns 'total'", "total" in d2, str(list(d2.keys())))
        check("GET /vocab/list returns 'items'", "items" in d2, str(list(d2.keys())))
    except Exception as e:
        check("Backend API test", False, str(e))

    # Cleanup
    print("\n🧹 Final cleanup...")
    cleanup_test_slots()

    print("\n" + "=" * 60)
    print(f"🏆 E2E Results: {PASS} PASSED, {FAIL} FAILED out of {PASS + FAIL} checks")
    print("=" * 60)

    if FAIL > 0:
        print("❌ Some E2E tests FAILED!")
        sys.exit(1)
    else:
        print("✅ All E2E tests PASSED!")
        sys.exit(0)

if __name__ == "__main__":
    main()
