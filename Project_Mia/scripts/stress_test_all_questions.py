#!/usr/bin/env python3
"""
stress_test_all_questions.py
────────────────────────────
对 static_content.db 中所有题目逐条调用 POST /api/exam/submit_objective
验证：
  1. HTTP 200
  2. JSON 包含 'correct' 和 'correct_answer' 字段
  3. 'correct_answer' 不为 None（答案不缺失）

只对客观题（有选项的）发起提交；主观题（翻译/作文）仅做检测记录。

Usage:
    cd F:\sanity_check_avg\Project_Mia
    python scripts/stress_test_all_questions.py [--base-url http://localhost:8000]
"""

import argparse
import json
import sqlite3
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from collections import defaultdict

# ── 路径 ──
ROOT     = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "backend" / "data"
STATIC_DB = DATA_DIR / "static_content.db"


def main():
    parser = argparse.ArgumentParser(description="Project Mia All-Question Stress Test")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Backend base URL")
    parser.add_argument("--delay",    default=0.05, type=float, help="Delay (s) between requests")
    parser.add_argument("--answer",   default="A",  help="Mock answer to submit for all questions")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    endpoint = f"{base_url}/api/exam/submit_objective"

    if not STATIC_DB.exists():
        print(f"[ERROR] Database not found: {STATIC_DB}", file=sys.stderr)
        sys.exit(1)

    # ── 读取所有题目 ──
    conn = sqlite3.connect(STATIC_DB)
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT q_id, question_number, section_type, q_type,
               correct_answer, options_json, paper_id
        FROM questions
        ORDER BY paper_id, question_number
    """)
    questions = cursor.fetchall()
    conn.close()

    total      = len(questions)
    passed     = 0
    failed     = []
    skipped    = []
    no_answer  = []
    by_section = defaultdict(lambda: {"pass": 0, "fail": 0})

    print(f"\n{'='*60}")
    print(f"  Project Mia — Full Question Stress Test")
    print(f"  Endpoint  : {endpoint}")
    print(f"  Questions : {total}")
    print(f"  Answer    : {args.answer} (mock)")
    print(f"{'='*60}\n")

    for i, q in enumerate(questions, 1):
        q_id         = q.get("q_id")
        section_type = q.get("section_type", "unknown")
        correct_ans  = q.get("correct_answer")
        is_objective = section_type in ("use_of_english", "reading_a", "reading_b")

        # 进度打印（每50道打一次）
        if i % 50 == 0 or i == 1 or i == total:
            print(f"  [{i:>4}/{total}] {q_id:<40} section={section_type}")

        # 主观题：只检查answer字段是否缺失，不发提交请求
        if not is_objective:
            skipped.append({"q_id": q_id, "reason": "subjective"})
            continue

        # 检查答案字段
        if not correct_ans:
            no_answer.append(q_id)

        # 发送请求
        payload = json.dumps({"q_id": q_id, "answer": args.answer}).encode()
        req = urllib.request.Request(
            endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.status
                body   = json.loads(resp.read())

            # 验证
            if status != 200:
                failed.append({"q_id": q_id, "error": f"HTTP {status}"})
                by_section[section_type]["fail"] += 1
            elif "correct" not in body:
                failed.append({"q_id": q_id, "error": "missing 'correct' field in response"})
                by_section[section_type]["fail"] += 1
            else:
                passed += 1
                by_section[section_type]["pass"] += 1

        except urllib.error.HTTPError as e:
            body_bytes = e.read()
            try:
                detail = json.loads(body_bytes).get("detail", body_bytes[:200])
            except Exception:
                detail = body_bytes[:200]
            failed.append({"q_id": q_id, "error": f"HTTP {e.code}: {detail}"})
            by_section[section_type]["fail"] += 1

        except Exception as e:
            failed.append({"q_id": q_id, "error": str(e)})
            by_section[section_type]["fail"] += 1

        if args.delay:
            time.sleep(args.delay)

    # ── 输出报告 ──
    objective_total = total - len(skipped)
    print(f"\n{'='*60}")
    print(f"  [Stress Test Report]")
    print(f"{'='*60}")
    print(f"  Total Questions : {total}")
    print(f"  Objective Tested: {objective_total}")
    print(f"  Subjective Skip : {len(skipped)}")
    print(f"  Passed          : {passed}")
    print(f"  Failed          : {len(failed)}")
    print(f"  Missing Answer  : {len(no_answer)}")
    print(f"\n  Per-section:")
    for sec, counts in sorted(by_section.items()):
        total_sec = counts["pass"] + counts["fail"]
        print(f"    {sec:<25} pass={counts['pass']}/{total_sec}  fail={counts['fail']}")

    if no_answer:
        print(f"\n  ⚠  Questions with NULL correct_answer ({len(no_answer)}):")
        for qid in no_answer[:20]:
            print(f"     {qid}")
        if len(no_answer) > 20:
            print(f"     ... and {len(no_answer)-20} more")

    if failed:
        print(f"\n  ✗ Failed Questions ({len(failed)}):")
        for item in failed[:30]:
            print(f"     {item['q_id']}: {item['error']}")
        if len(failed) > 30:
            print(f"     ... and {len(failed)-30} more")
    else:
        print(f"\n  ✓ All {passed} objective questions passed! 🎉")

    print(f"{'='*60}\n")

    # 非零退出码表示有失败
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
