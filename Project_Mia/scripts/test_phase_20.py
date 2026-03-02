"""
Phase 20.0 综合自测脚本
覆盖存档 CRUD、参数修改、日限词汇、以及删除验证。
"""
import requests
import sys

BASE = "http://localhost:8000/api"

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


def main():
    global PASS, FAIL

    print("=" * 60)
    print("🧪 Phase 20.0 综合自测")
    print("=" * 60)

    # ──────────────────────────────────────────────
    # 1. 新建存档「考研冲刺档」
    # ──────────────────────────────────────────────
    print("\n📋 Test 1: 创建存档「考研冲刺档」")
    r = requests.post(f"{BASE}/user/slots/new", json={"slot_name": "考研冲刺档"})
    data = r.json()
    check("POST /user/slots/new returns success", data.get("success") is True, str(data))
    new_slot_id = data.get("slot_id")
    check("New slot_id is returned", new_slot_id is not None, str(data))
    check("slot_name echoed back", data.get("slot_name") == "考研冲刺档", str(data))
    print(f"    → slot_id = {new_slot_id}")

    # Verify it appears in slots list
    r2 = requests.get(f"{BASE}/user/slots")
    slots = r2.json()
    slot_ids = [s["slot_id"] for s in slots]
    check("New slot appears in GET /user/slots", new_slot_id in slot_ids, str(slot_ids))
    # Check slot_name is correct in the list
    target_slot = next((s for s in slots if s["slot_id"] == new_slot_id), None)
    check("slot_name in list is '考研冲刺档'", target_slot and target_slot.get("slot_name") == "考研冲刺档", str(target_slot))

    # ──────────────────────────────────────────────
    # 2. 更新存档设置
    # ──────────────────────────────────────────────
    print("\n📋 Test 2: 更新存档 daily_new_words_limit=50, daily_reset_time='05:00'")
    r = requests.put(f"{BASE}/user/slots/{new_slot_id}", json={
        "daily_new_words_limit": 50,
        "daily_reset_time": "05:00"
    })
    data = r.json()
    check("PUT /user/slots/{id} returns success", data.get("success") is True, str(data))

    # Re-fetch and verify
    r2 = requests.get(f"{BASE}/user/slots")
    slots = r2.json()
    target_slot = next((s for s in slots if s["slot_id"] == new_slot_id), None)
    check("daily_new_words_limit updated to 50", target_slot and target_slot.get("daily_new_words_limit") == 50, str(target_slot))
    check("daily_reset_time updated to '05:00'", target_slot and target_slot.get("daily_reset_time") == "05:00", str(target_slot))

    # ──────────────────────────────────────────────
    # 3. 获取今日词汇 — 新词受限于 50
    # ──────────────────────────────────────────────
    print("\n📋 Test 3: 获取今日词汇 (slot_id={})，新词应 ≤ 50".format(new_slot_id))
    r = requests.get(f"{BASE}/vocab/today", params={"slot_id": new_slot_id})
    data = r.json()
    new_count = data.get("new_count", 0)
    daily_limit = data.get("daily_limit", -1)
    check("GET /vocab/today returns tasks", "tasks" in data, str(list(data.keys())))
    check("daily_limit in response equals 50", daily_limit == 50, f"got {daily_limit}")
    check("new_count ≤ 50", new_count <= 50, f"new_count={new_count}")
    print(f"    → date={data.get('date')}, review={data.get('review_count')}, new={new_count}, total={data.get('total_count')}")

    # ──────────────────────────────────────────────
    # 4. 删除存档并验证
    # ──────────────────────────────────────────────
    print(f"\n📋 Test 4: 删除存档 slot_id={new_slot_id}")
    r = requests.delete(f"{BASE}/user/slots/{new_slot_id}")
    data = r.json()
    check("DELETE /user/slots/{id} returns success", data.get("success") is True, str(data))

    # Re-fetch and verify
    r2 = requests.get(f"{BASE}/user/slots")
    slots = r2.json()
    slot_ids = [s["slot_id"] for s in slots]
    check("Deleted slot no longer in list", new_slot_id not in slot_ids, str(slot_ids))

    # Also verify: cannot delete slot 0
    print("\n📋 Test 4b: 尝试删除 slot_id=0 (应被拒绝)")
    r = requests.delete(f"{BASE}/user/slots/0")
    data = r.json()
    check("DELETE slot 0 is rejected", data.get("success") is False, str(data))

    # ──────────────────────────────────────────────
    # Summary
    # ──────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"🏆 Results: {PASS} PASSED, {FAIL} FAILED out of {PASS + FAIL} checks")
    print("=" * 60)

    if FAIL > 0:
        print("❌ Some tests FAILED!")
        sys.exit(1)
    else:
        print("✅ All tests PASSED!")
        sys.exit(0)


if __name__ == "__main__":
    main()
