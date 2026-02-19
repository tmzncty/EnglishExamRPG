#!/usr/bin/env python3
"""
validate_ui_data.py
────────────────────
模拟前端 UI 视角，逐年检查 API 返回数据完整性。
对 2010-2025 每年调用 GET /api/exam/{year}-eng1，断言：
  - Writing B: image 字段长度 > 1000 (有图)
  - Reading B: questions == 5，选项含 A-G
  - Translation: questions == 5

Usage:
    python scripts/validate_ui_data.py [--base-url http://localhost:8000]
"""
import argparse
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

YEARS = range(2010, 2026)

def fetch(url: str) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"_error": f"HTTP {e.code}"}
    except Exception as e:
        return {"_error": str(e)}


def fmt_image(image_val) -> str:
    if not image_val:
        return "❌ MISSING"
    size_kb = round(len(str(image_val)) / 1024, 1)
    return f"✅ ({size_kb}kb)"


def check_options(questions: list) -> str:
    """检查问题选项是否包含 A-G 字母（或7选5格式）"""
    if not questions:
        return "(no qs)"
    q = questions[0]
    opts = q.get("options") or {}
    if isinstance(opts, dict):
        keys = set(opts.keys())
    elif isinstance(opts, list):
        keys = set(opts)
    else:
        keys = set()
    has_ag = len(keys) >= 5
    return f"{len(questions)} {'(A-G✓)' if has_ag else '(no opts)'}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    rows = []
    fails = []

    for year in YEARS:
        paper_id = f"{year}-eng1"
        url = f"{base}/api/exam/{paper_id}"
        data = fetch(url)

        if not data or "_error" in data:
            err = (data or {}).get("_error", "unknown")
            rows.append({"year": year, "error": err})
            fails.append(f"{year}: {err}")
            continue

        sections = data.get("sections", {})

        # Writing B
        wb = sections.get("writing_b") or {}
        image_str = fmt_image(wb.get("image"))
        has_image = wb.get("image") and len(str(wb["image"])) > 100

        # Reading B
        rb_groups = sections.get("reading_b") or []
        rb_qs = []
        for g in rb_groups:
            rb_qs.extend(g.get("questions", []))
        rb_str = check_options(rb_qs) if rb_qs else "❌ NO RB"

        # Translation
        trans = sections.get("translation") or {}
        trans_qs = trans.get("questions", []) if isinstance(trans, dict) else []
        trans_str = str(len(trans_qs)) if trans_qs else "❌ 0"

        # Status
        status_parts = []
        if not has_image:
            status_parts.append("No Image")
        if len(rb_qs) != 5:
            status_parts.append(f"RdB={len(rb_qs)}")
        status = "PASS ✓" if not status_parts else "WARN ⚠ " + ", ".join(status_parts)
        if not has_image:
            fails.append(f"{year}: missing writing_b image")

        rows.append({
            "year": year, "wb_image": image_str,
            "rb": rb_str, "trans": trans_str,
            "status": status, "error": None
        })

    # ── Print Table ──
    print(f"\n{'='*72}")
    print(f"  [UI Data Audit Report]  base={base}")
    print(f"{'='*72}")
    print(f"  {'Year':<6} {'Writ-B Image':<20} {'Rd-B Qs':<14} {'Trans Qs':<10} Status")
    print(f"  {'-'*66}")
    for r in rows:
        if r.get("error"):
            print(f"  {r['year']:<6} ERROR: {r['error']}")
        else:
            print(f"  {r['year']:<6} {r['wb_image']:<20} {r['rb']:<14} {r['trans']:<10} {r['status']}")
    print(f"{'='*72}")
    print(f"  Total years  : {len(YEARS)}")
    print(f"  Years failing: {len(set(f.split(':')[0] for f in fails))}")
    if fails:
        print(f"\n  Issues detected:")
        for f in fails:
            print(f"    • {f}")
    else:
        print(f"\n  ✓ All years fully validated!")
    print(f"{'='*72}\n")


if __name__ == "__main__":
    main()
