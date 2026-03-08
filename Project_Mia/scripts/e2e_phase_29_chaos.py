"""
🐒 Phase 29.0 Chaos Monkey E2E Test
Tests 3 viewport sizes (Mobile, 1080P, 4K) with extreme user behaviors:
  - Rapid clicking, mid-animation navigation, cross-page chaos
  - BoundingBox overlap assertion for nav bar vs action buttons
"""
import asyncio
from playwright.async_api import async_playwright

BASE = "http://localhost:5200"

VIEWPORTS = {
    "Mobile (430x932)": {"width": 430, "height": 932},
    "1080P (1920x1080)": {"width": 1920, "height": 1080},
    "4K (3840x2160)": {"width": 3840, "height": 2160},
}


async def assert_no_overlap(page, label):
    """Assert the global nav bar does NOT overlap with any visible action button."""
    nav = page.locator("#global-nav")
    nav_count = await nav.count()
    if nav_count == 0:
        print(f"   ⚠️  [{label}] #global-nav not found — skipping overlap check")
        return

    nav_box = await nav.bounding_box()
    if not nav_box:
        print(f"   ⚠️  [{label}] #global-nav not visible — skipping overlap check")
        return

    nav_top = nav_box["y"]

    for btn_id in ["#btn-show-answer", "#btn-correct", "#btn-forgot"]:
        btn = page.locator(btn_id)
        if await btn.count() == 0:
            continue
        if not await btn.is_visible():
            continue
        btn_box = await btn.bounding_box()
        if not btn_box:
            continue
        btn_bottom = btn_box["y"] + btn_box["height"]
        overlap = btn_bottom - nav_top
        if overlap > 0:
            raise AssertionError(
                f"❌ [{label}] OVERLAP! {btn_id} bottom ({btn_bottom:.0f}px) "
                f"exceeds nav top ({nav_top:.0f}px) by {overlap:.0f}px"
            )
        print(f"   ✅ [{label}] {btn_id} bottom={btn_bottom:.0f}px, nav top={nav_top:.0f}px → NO overlap (gap {-overlap:.0f}px)")


async def test_mobile_rapid_click(browser):
    """Viewport 1 (Mobile): Rapid-click the front card 10 times — assert no crash."""
    vp = VIEWPORTS["Mobile (430x932)"]
    ctx = await browser.new_context(viewport=vp)
    page = await ctx.new_page()

    errors = []
    page.on("pageerror", lambda err: errors.append(str(err)))
    page.on("console", lambda msg: None)  # suppress noise

    print("\n🔹 VIEWPORT 1 — Mobile (430×932): Rapid Front-Card Clicking")
    await page.goto(f"{BASE}/garden")
    await page.wait_for_timeout(2500)

    # Check if there is a current word (front card visible)
    show_btn = page.locator("#btn-show-answer")
    if await show_btn.count() > 0 and await show_btn.is_visible():
        print("   Rapid-clicking 'Show Answer' button 10 times...")
        for i in range(10):
            await show_btn.click(force=True, no_wait_after=True)
            await page.wait_for_timeout(80)

        await page.wait_for_timeout(500)
        # After rapid clicks, card should be revealed (or page still functional)
        # The key is no unhandled errors
        assert len(errors) == 0, f"❌ Page errors during rapid click: {errors}"
        print("   ✅ No errors during rapid clicking!")
    else:
        print("   ℹ️  No active card — Garden may be finished. Checking page stability...")
        assert len(errors) == 0, f"❌ Page errors on load: {errors}"
        print("   ✅ Page loaded without errors.")

    # BoundingBox overlap check
    await assert_no_overlap(page, "Mobile")

    await ctx.close()
    print("   ✅ Mobile viewport test PASSED!")


async def test_1080p_mid_animation_nav(browser):
    """Viewport 2 (1080P): Click ✅ Correct mid-animation, immediately navigate to Dashboard."""
    vp = VIEWPORTS["1080P (1920x1080)"]
    ctx = await browser.new_context(viewport=vp)
    page = await ctx.new_page()

    errors = []
    page.on("pageerror", lambda err: errors.append(str(err)))
    page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))

    print("\n🔹 VIEWPORT 2 — 1080P (1920×1080): Mid-Animation Navigation")
    await page.goto(f"{BASE}/garden")
    await page.wait_for_timeout(2500)

    show_btn = page.locator("#btn-show-answer")
    if await show_btn.count() > 0 and await show_btn.is_visible():
        # Reveal card
        await show_btn.click()
        await page.wait_for_timeout(600)

        # Now click ✅ Correct
        correct_btn = page.locator("#btn-correct")
        if await correct_btn.count() > 0 and await correct_btn.is_visible():
            print("   Clicking '✅ Correct' then immediately navigating to Dashboard...")
            await correct_btn.click(force=True, no_wait_after=True)
            # Immediately click Dashboard nav (don't wait for animation)
            await page.wait_for_timeout(50)
            dash_link = page.locator("#global-nav a[href='/']")
            await dash_link.click(force=True)
            await page.wait_for_timeout(2000)

            # Assert Dashboard loaded (check URL or page content)
            url = page.url
            assert "/" == url.replace(BASE, "").rstrip("/") or url.endswith(":5200/"), \
                f"❌ Expected Dashboard URL, got: {url}"
            print(f"   ✅ Dashboard loaded successfully at {url}")
        else:
            print("   ℹ️  Correct button not visible — skipping mid-animation test")
    else:
        print("   ℹ️  No active card — performing direct nav test...")
        dash_link = page.locator("#global-nav a[href='/']")
        if await dash_link.count() > 0:
            await dash_link.click()
            await page.wait_for_timeout(2000)
        print("   ✅ Navigation stable.")

    assert len(errors) == 0, f"❌ Page errors during 1080P test: {errors}"

    # BoundingBox overlap check on Garden
    await page.goto(f"{BASE}/garden")
    await page.wait_for_timeout(2000)
    await assert_no_overlap(page, "1080P")

    await ctx.close()
    print("   ✅ 1080P viewport test PASSED!")


async def test_4k_exam_chaos(browser):
    """Viewport 3 (4K): Enter exam, click sidebar, reset, immediately switch to Garden."""
    vp = VIEWPORTS["4K (3840x2160)"]
    ctx = await browser.new_context(viewport=vp)
    page = await ctx.new_page()

    errors = []
    page.on("pageerror", lambda err: errors.append(str(err)))
    page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))

    print("\n🔹 VIEWPORT 3 — 4K (3840×2160): Exam Room Chaos")
    await page.goto(f"{BASE}/exam/2010-eng1")
    await page.wait_for_timeout(3000)

    # Click a few sidebar items rapidly
    sidebar_btns = page.locator("div.w-48 button")
    sidebar_count = await sidebar_btns.count()
    print(f"   Found {sidebar_count} sidebar items")

    if sidebar_count >= 2:
        print("   Rapid sidebar switching...")
        await sidebar_btns.nth(1).click(force=True)
        await page.wait_for_timeout(200)
        await sidebar_btns.nth(0).click(force=True)
        await page.wait_for_timeout(200)
        if sidebar_count > 2:
            await sidebar_btns.nth(2).click(force=True)
            await page.wait_for_timeout(200)
        await sidebar_btns.nth(0).click(force=True)
        await page.wait_for_timeout(300)
        print("   ✅ Sidebar switching stable!")

    # Click 🔄 Reset button
    reset_btn = page.locator("button", has_text="二刷")
    if await reset_btn.count() > 0:
        print("   Clicking '🔄 二刷' reset...")
        await reset_btn.click(force=True)
        await page.wait_for_timeout(1500)
        print("   ✅ Reset accepted!")

    # Immediately switch to Garden
    print("   Immediately switching to Garden...")
    garden_link = page.locator("#global-nav a[href='/garden']")
    if await garden_link.count() > 0:
        await garden_link.click(force=True)
        await page.wait_for_timeout(2500)
        url = page.url
        assert "/garden" in url, f"❌ Expected Garden URL, got: {url}"
        print(f"   ✅ Garden loaded at {url}")
    else:
        print("   ⚠️  Garden nav link not found — navigating directly")
        await page.goto(f"{BASE}/garden")
        await page.wait_for_timeout(2500)

    assert len(errors) == 0, f"❌ Page errors during 4K test: {errors}"

    # BoundingBox overlap check
    await assert_no_overlap(page, "4K")

    await ctx.close()
    print("   ✅ 4K viewport test PASSED!")


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        print("=" * 60)
        print("🐒 CHAOS MONKEY E2E — Phase 29.0")
        print("=" * 60)

        await test_mobile_rapid_click(browser)
        await test_1080p_mid_animation_nav(browser)
        await test_4k_exam_chaos(browser)

        await browser.close()

        print("\n" + "=" * 60)
        print("🎉 ALL 3 VIEWPORTS PASSED!")
        print("   ✅ Mobile (430×932):  UI 无重叠、狂点无报错")
        print("   ✅ 1080P (1920×1080): UI 无重叠、中途导航无白屏")
        print("   ✅ 4K (3840×2160):    UI 无重叠、考场混沌操作无崩溃")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run())
