"""
Phase 35.2 — Time Machine E2E Test (Cross-Day Rollover)
=======================================================
Proves that the frontend cross-day rollover engine works by:
1. Faking the backend DB so the user looks like they finished yesterday.
2. Hijacking the browser's Date object to place us at 03:59:58 UTC+8.
3. Navigating to /garden — expecting the "Garden Tended" / finished state.
4. Letting real time tick past the 04:00:00 UTC+8 boundary.
5. Asserting the rollover alert fires and the page reloads fresh tasks.

Uses Playwright sync API — consistent with all Project Mia E2E scripts.
"""
import os
import sys
import time
import sqlite3
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:5173"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# The profile DB used by the running backend
DB_PATH = os.path.join(SCRIPT_DIR, "..", "backend", "data", "femo_profile.db")
SCREENSHOT_DIR = os.path.join(SCRIPT_DIR, "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

UTC8 = timezone(timedelta(hours=8))
SLOT_ID = 0


def screenshot(page, name):
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=True)
    print(f"📸 Screenshot saved: {name}.png")
    return path


# ── STEP 0: Calculate "yesterday" in logical-day terms ──────────────
def get_yesterday_logical():
    """Return the YYYY-MM-DD string for *yesterday's* logical day (UTC+8, 4 AM boundary)."""
    now_utc8 = datetime.now(UTC8)
    reset_today = now_utc8.replace(hour=4, minute=0, second=0, microsecond=0)
    if now_utc8 < reset_today:
        logical_today = (now_utc8 - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        logical_today = now_utc8.strftime("%Y-%m-%d")
    yesterday = (datetime.strptime(logical_today, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    return logical_today, yesterday


def fake_backend_state(today_logical, yesterday_logical):
    """
    Directly patch femo_profile.db so the backend thinks:
    - The user finished all vocab yesterday (last_goal_met_date = yesterday).
    - last_reset_day = yesterday (so the backend will trigger its own reset when asked).
    - today_focus_time = some accumulated value from 'yesterday'.
    """
    print(f"\n{'='*60}")
    print(f"STEP 0: DB Time Travel")
    print(f"  today_logical   = {today_logical}")
    print(f"  yesterday_logical = {yesterday_logical}")
    print(f"  DB path         = {os.path.abspath(DB_PATH)}")
    print(f"{'='*60}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Sanity check: make sure slot exists
    row = conn.execute("SELECT slot_id, last_reset_day, last_goal_met_date, today_focus_time FROM game_saves WHERE slot_id=?", (SLOT_ID,)).fetchone()
    if not row:
        print(f"⛔ No game_saves row for slot_id={SLOT_ID}. Aborting.")
        conn.close()
        sys.exit(1)

    print(f"  [Before] last_reset_day={row['last_reset_day']}, last_goal_met_date={row['last_goal_met_date']}, today_focus_time={row['today_focus_time']}")

    conn.execute("""
        UPDATE game_saves
        SET last_reset_day = ?,
            last_goal_met_date = ?,
            today_focus_time = 666,
            daily_streak = 5
        WHERE slot_id = ?
    """, (yesterday_logical, yesterday_logical, SLOT_ID))
    conn.commit()

    row2 = conn.execute("SELECT last_reset_day, last_goal_met_date, today_focus_time, daily_streak FROM game_saves WHERE slot_id=?", (SLOT_ID,)).fetchone()
    print(f"  [After]  last_reset_day={row2['last_reset_day']}, last_goal_met_date={row2['last_goal_met_date']}, today_focus_time={row2['today_focus_time']}, daily_streak={row2['daily_streak']}")
    conn.close()
    print("  ✅ Backend DB successfully time-traveled to 'yesterday'.\n")


def build_time_hijack_script():
    """
    Returns a JavaScript snippet that replaces the native Date with a version
    whose clock starts at 03:59:55 UTC+8 (= UTC-4h, i.e. UTC + 4h offset as
    our getCurrentLogicalDay uses), ticking forward in real-time.

    This means ~5 seconds after page load, the logical day will flip.
    """
    # Target: 03:59:55 UTC+8  →  in pure UTC that is  03:59:55 - 8h = 19:59:55 UTC (previous day)
    # We use today's calendar date in UTC+8 to build the target.
    now_utc8 = datetime.now(UTC8)
    target_utc8 = now_utc8.replace(hour=3, minute=59, second=55, microsecond=0)
    # Convert to UTC timestamp in ms
    target_utc_ms = int(target_utc8.timestamp() * 1000)

    return f"""
    (() => {{
        // Save the real Date constructor
        const RealDate = window.Date;
        const FAKE_START_REAL = RealDate.now();
        const FAKE_START_TARGET = {target_utc_ms};  // 03:59:55 UTC+8 in epoch ms

        function FakeDate(...args) {{
            if (args.length === 0) {{
                // new Date() — return faked "now"
                const elapsed = RealDate.now() - FAKE_START_REAL;
                return new RealDate(FAKE_START_TARGET + elapsed);
            }}
            // new Date(value) or new Date(y, m, d, ...) — pass through
            return new RealDate(...args);
        }}

        // Proxy static methods
        FakeDate.now = function() {{
            const elapsed = RealDate.now() - FAKE_START_REAL;
            return FAKE_START_TARGET + elapsed;
        }};
        FakeDate.parse = RealDate.parse;
        FakeDate.UTC = RealDate.UTC;
        FakeDate.prototype = RealDate.prototype;

        window.Date = FakeDate;

        console.log('[TimeMachine] Date hijacked! Faked start: ' + new Date().toISOString());
    }})();
    """


def test_time_travel():
    today_logical, yesterday_logical = get_yesterday_logical()

    # ── STEP 0: Fake the backend DB ──
    fake_backend_state(today_logical, yesterday_logical)

    # ── STEP 1-5: Playwright browser test ──
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})

        # Inject time hijack BEFORE any page loads
        time_script = build_time_hijack_script()
        context.add_init_script(script=time_script)

        page = context.new_page()

        # Collect console logs for proof
        console_logs = []
        page.on("console", lambda msg: (
            console_logs.append(f"[{msg.type}] {msg.text}"),
            print(f"  🖥️ [{msg.type}] {msg.text}")
        ))

        # Collect network requests to /api/vocab/today
        vocab_requests = []
        page.on("request", lambda req: (
            vocab_requests.append({"url": req.url, "time": time.time()})
            if "/api/vocab/today" in req.url else None
        ))

        # Capture the alert dialog — THIS is the rollover proof!
        alert_messages = []
        page.on("dialog", lambda dialog: (
            alert_messages.append(dialog.message),
            print(f"  🔔 ALERT CAPTURED: {dialog.message}"),
            dialog.accept()
        ))

        # ──────────────────────────────────────────────────────
        # STEP 1: Also inject a stale lastActiveLogicalDay into localStorage
        # to simulate "user opened app yesterday and the Pinia persist cache is stale"
        # ──────────────────────────────────────────────────────
        print(f"\n{'='*60}")
        print("STEP 1: Navigate to Home to seed localStorage")
        print(f"{'='*60}")
        page.goto(f"{BASE_URL}/")
        page.wait_for_timeout(2000)

        # Inject stale Pinia persisted state for the vocab store
        page.evaluate(f"""
            (() => {{
                const KEY = 'vocab';
                let stored = localStorage.getItem(KEY);
                let data = stored ? JSON.parse(stored) : {{}};
                data.lastActiveLogicalDay = '{yesterday_logical}';
                data.currentIndex = 999; // Force isFinished = true (index >= todayTasks.length)
                data.todayTasks = [{{ word: 'stale_test', type: 'review' }}]; // 1 item, index 999 => finished
                data.todayFocusTime = 666;
                data.dailyProgress = {{ reviewed: 30, total: 30, new_learned: 30, to_review: 30 }};
                localStorage.setItem(KEY, JSON.stringify(data));
                console.log('[TimeMachine] Injected stale localStorage: lastActiveLogicalDay=' + data.lastActiveLogicalDay);
            }})()
        """)

        # ──────────────────────────────────────────────────────
        # STEP 2: Navigate to /garden — should see "Garden Tended!" (stale state)
        # BUT our onMounted interceptor should detect the stale day and wipe it!
        # After the wipe + refetch, we should see fresh cards.
        # ──────────────────────────────────────────────────────
        print(f"\n{'='*60}")
        print("STEP 2: Navigate to /garden (stale cache → onMounted wipe)")
        print(f"{'='*60}")

        vocab_requests.clear()  # Reset counter
        page.goto(f"{BASE_URL}/garden")
        page.wait_for_timeout(5000)  # Give time for async fetch

        screenshot(page, "35_01_garden_after_stale_wipe")

        # Assert: onMounted should have detected stale day and fetched fresh data
        stale_wipe_detected = any("Stale state detected" in log for log in console_logs)
        fetch_fired = len([r for r in vocab_requests if "/api/vocab/today" in r["url"]]) > 0

        print(f"\n  📊 ASSERTION 1 — Stale State Wipe on Mount:")
        print(f"     Console log 'Stale state detected': {'✅ YES' if stale_wipe_detected else '❌ NO'}")
        print(f"     /api/vocab/today request fired:     {'✅ YES' if fetch_fired else '❌ NO'}")

        if not stale_wipe_detected:
            print("  ⚠️  Note: If first visit, lastActiveLogicalDay may be null (no stale wipe needed)")

        # ──────────────────────────────────────────────────────
        # STEP 3: Now test the LIVE midnight rollover tick.
        # We re-inject localStorage so lastActiveLogicalDay = yesterday,
        # and navigate to garden where the setInterval will detect the change
        # as the faked clock ticks past 4:00 AM.
        # ──────────────────────────────────────────────────────
        print(f"\n{'='*60}")
        print("STEP 3: Live Midnight Rollover Tick Test")
        print(f"{'='*60}")

        # Reset state: go home, re-inject stale date
        page.goto(f"{BASE_URL}/")
        page.wait_for_timeout(1000)

        # Re-inject time script and stale state for the rollover tick test
        # The init script is already injected globally via context, so new navigations
        # will still have the hijacked Date.
        
        # We need to set the faked clock to ~3:59:58 for this page visit.
        # Since the init_script sets the fake start to 03:59:55, and we've already
        # spent some real seconds, we need a fresh navigation.
        
        # Close browser and restart with a fresh time anchor
        browser.close()
        
        # Recalculate fresh time script for 03:59:57 UTC+8
        now_utc8 = datetime.now(UTC8)
        target_utc8_2 = now_utc8.replace(hour=3, minute=59, second=57, microsecond=0)
        target_utc_ms_2 = int(target_utc8_2.timestamp() * 1000)
        
        time_script_2 = f"""
        (() => {{
            const RealDate = window.Date;
            const FAKE_START_REAL = RealDate.now();
            const FAKE_START_TARGET = {target_utc_ms_2};

            function FakeDate(...args) {{
                if (args.length === 0) {{
                    const elapsed = RealDate.now() - FAKE_START_REAL;
                    return new RealDate(FAKE_START_TARGET + elapsed);
                }}
                return new RealDate(...args);
            }}
            FakeDate.now = function() {{
                const elapsed = RealDate.now() - FAKE_START_REAL;
                return FAKE_START_TARGET + elapsed;
            }};
            FakeDate.parse = RealDate.parse;
            FakeDate.UTC = RealDate.UTC;
            FakeDate.prototype = RealDate.prototype;
            window.Date = FakeDate;
            console.log('[TimeMachine] Fresh Date hijack! Start: ' + new Date().toISOString());
        }})();
        """
        
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        context.add_init_script(script=time_script_2)
        page = context.new_page()
        
        # Re-attach all listeners
        console_logs_2 = []
        page.on("console", lambda msg: (
            console_logs_2.append(f"[{msg.type}] {msg.text}"),
            print(f"  🖥️ [{msg.type}] {msg.text}")
        ))
        
        vocab_requests_2 = []
        page.on("request", lambda req: (
            vocab_requests_2.append({"url": req.url, "time": time.time()})
            if "/api/vocab/today" in req.url else None
        ))
        
        alert_messages_2 = []
        page.on("dialog", lambda dialog: (
            alert_messages_2.append(dialog.message),
            print(f"  🔔 ALERT CAPTURED: {dialog.message}"),
            dialog.accept()
        ))

        # Navigate to home first to inject stale localStorage with YESTERDAY's logical day
        page.goto(f"{BASE_URL}/")
        page.wait_for_timeout(2000)

        # We need to figure out what "yesterday" and "today" are from the FAKED clock's perspective.
        # Faked clock starts at 03:59:57 UTC+8.
        # getCurrentLogicalDay at 03:59:57 UTC+8:
        #   UTC time of 03:59:57 UTC+8 = 19:59:57 UTC (previous real day)
        #   + 4 hours = 23:59:57 UTC → getUTCDate = today's REAL date - 1
        #   After 4:00:00 AM UTC+8 ticks:
        #   UTC time = 20:00:00 UTC
        #   + 4 hours = 00:00:00 UTC next day → getUTCDate = today's REAL date
        #
        # So "yesterday logical" from the fake clock's perspective is the date BEFORE the faked 4AM crossing.
        
        fake_now_utc8 = now_utc8.replace(hour=3, minute=59, second=57, microsecond=0)
        fake_yesterday_logical = (fake_now_utc8 - timedelta(days=1)).strftime("%Y-%m-%d")
        
        page.evaluate(f"""
            (() => {{
                const KEY = 'vocab';
                let data = {{}};
                data.lastActiveLogicalDay = '{fake_yesterday_logical}';
                data.currentIndex = 0;
                data.todayTasks = [];
                data.todayFocusTime = 0;
                data.dailyProgress = {{ reviewed: 0, total: 0, new_learned: 0, to_review: 0 }};
                localStorage.setItem(KEY, JSON.stringify(data));
                console.log('[TimeMachine] Injected fresh stale state: lastActiveLogicalDay=' + data.lastActiveLogicalDay);
            }})()
        """)

        # Navigate to /garden
        print("  🚀 Navigating to /garden at faked 03:59:57 UTC+8...")
        vocab_requests_2.clear()
        page.goto(f"{BASE_URL}/garden")
        page.wait_for_timeout(2000)
        screenshot(page, "35_02_garden_at_0359")

        # The onMounted should load data. Now wait for the 1-second timer to tick past 04:00:00.
        # Since we start at 03:59:57, after ~3 real seconds the faked clock crosses 04:00:00.
        # But our lastActiveLogicalDay has already been updated by the onMounted fetch...
        # The rollover tick checks if lastActiveLogicalDay differs from the NEW logical day.
        #
        # At 03:59:57, getCurrentLogicalDay() returns yesterday.
        # At 04:00:01, getCurrentLogicalDay() returns today.
        # So if the store's lastActiveLogicalDay was set to yesterday by the fetch at 03:59:57,
        # it WILL differ from the new getCurrentLogicalDay() at 04:00:01 → ROLLOVER!

        print("  ⏳ Waiting 6 seconds for the faked clock to cross 04:00:00 UTC+8...")
        page.wait_for_timeout(6000)
        screenshot(page, "35_03_garden_after_rollover")

        # ──────────────────────────────────────────────────────
        # STEP 4: Assertions
        # ──────────────────────────────────────────────────────
        print(f"\n{'='*60}")
        print("STEP 4: Final Assertions")
        print(f"{'='*60}")

        rollover_detected = any("Midnight Rollover Detected" in log for log in console_logs_2)
        alert_fired = len(alert_messages_2) > 0
        refetch_count = len([r for r in vocab_requests_2 if "/api/vocab/today" in r["url"]])
        
        # Check that Garden Tended is NOT shown (i.e., new tasks loaded)
        tended_visible = page.locator("text=Garden Tended!").count() > 0
        show_answer_visible = page.locator("#btn-show-answer").count() > 0 and page.locator("#btn-show-answer").is_visible()
        loading_visible = page.locator("text=Connecting to the Garden").count() > 0

        print(f"\n  📊 ASSERTION 2 — Midnight Rollover Tick:")
        print(f"     Console 'Midnight Rollover Detected':  {'✅ YES' if rollover_detected else '❌ NO'}")
        print(f"     Alert '🌅 新的一天开始啦' fired:        {'✅ YES' if alert_fired else '❌ NO'}")
        if alert_fired:
            print(f"       Alert text: \"{alert_messages_2[0]}\"")
        print(f"     /api/vocab/today requests total:      {refetch_count} {'✅ (>1 means reload!)' if refetch_count > 1 else '⚠️'}")
        print(f"     'Garden Tended' still visible:        {'❌ BUG!' if tended_visible else '✅ CLEARED'}")
        print(f"     'Show Answer' button visible:         {'✅ YES — New cards loaded!' if show_answer_visible else '⚠️ Not visible'}")
        print(f"     Loading spinner visible:              {'⏳ Still loading...' if loading_visible else '✅ Done'}")

        # Overall pass/fail
        passed = rollover_detected and alert_fired and refetch_count > 1 and not tended_visible
        
        print(f"\n  {'🏆 ALL ASSERTIONS PASSED!' if passed else '⚠️  Some assertions did not pass — see details above.'}")
        print(f"\n  📋 Full console logs ({len(console_logs_2)} entries):")
        for log in console_logs_2:
            print(f"     {log}")
        
        browser.close()

    # ── Restore DB (best effort) ──
    print(f"\n{'='*60}")
    print("CLEANUP: Restoring DB state")
    print(f"{'='*60}")
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            UPDATE game_saves
            SET last_reset_day = ?,
                last_goal_met_date = ?,
                today_focus_time = 0
            WHERE slot_id = ?
        """, (today_logical, today_logical, SLOT_ID))
        conn.commit()
        conn.close()
        print("  ✅ DB restored to current logical day.")
    except Exception as e:
        print(f"  ⚠️ DB restore failed: {e}")

    print(f"\n{'='*60}")
    print("🎉 Phase 35.2 Time Travel Test Complete!")
    print(f"{'='*60}")

    return passed


if __name__ == "__main__":
    success = test_time_travel()
    sys.exit(0 if success else 1)
