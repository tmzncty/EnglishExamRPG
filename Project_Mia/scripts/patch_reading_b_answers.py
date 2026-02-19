#!/usr/bin/env python3
"""
patch_reading_b_answers.py
──────────────────────────
从 EnglishExamWeb/data/<year>.json 读取 reading_b 题目的 correct_answer
写入 static_content.db

JSON 里 Reading B 的 section_info.type 通常是 "New Question Type" 或类似的。
题目 id 规则: JSON id 41-45 对应 reading_b (考研英语一 Part B 是 41-45)

Strategy A: JSON correct_answer 字段
Strategy B: official_analysis 正则匹配 【答案】([A-G])
Strategy C: 打印缺失，报告人工补录

Usage:
    python scripts/patch_reading_b_answers.py [--dry-run]
"""

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT        = Path(__file__).resolve().parent.parent
DATA_DIR    = ROOT / "backend" / "data"
JSON_DIR    = ROOT.parent / "EnglishExamWeb" / "data"   # F:\sanity_check_avg\EnglishExamWeb\data\
STATIC_DB   = DATA_DIR / "static_content.db"

# Part B 的题目 id 范围 (考研英语一)
READING_B_RANGE = range(41, 46)   # 41,42,43,44,45


def extract_answer_from_analysis(text: str) -> str | None:
    """从解析文本中提取 【答案】X 格式的答案"""
    if not text:
        return None
    m = re.search(r'[【\[]答案[】\]]\s*([A-G])', text)
    return m.group(1) if m else None


def load_json_answers(year: int) -> dict:
    """
    从 EnglishExamWeb/data/<year>.json 读取 reading_b 答案。
    返回 {q_num: answer_letter}
    """
    path = JSON_DIR / f"{year}.json"
    if not path.exists():
        return {}

    with open(path, encoding='utf-8') as f:
        data = json.load(f)

    answers = {}
    for section in data.get("sections", []):
        stype = section.get("section_info", {}).get("type", "")
        # Reading B 在 JSON 里的类型名可能是 "New Question Type" 或含 "Part B"
        is_rb = ("New Question" in stype or "Part B" in stype or
                 "reading_b" in stype.lower())
        if not is_rb:
            # 也检查 q_range
            qr = section.get("section_info", {}).get("q_range", "")
            if "41" in qr or "46" in qr:
                is_rb = True

        if is_rb:
            for q in section.get("questions", []):
                qid = q.get("id")
                ans = q.get("correct_answer", "")
                if qid and ans:
                    answers[int(qid)] = ans.strip()

    return answers


def main():
    parser = argparse.ArgumentParser(description="Patch reading_b correct_answer from JSON")
    parser.add_argument("--dry-run", action="store_true", help="Don't write to DB, just print")
    args = parser.parse_args()

    conn = sqlite3.connect(STATIC_DB)
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))

    # 找出所有 correct_answer IS NULL 的 reading_b 题目
    nulls = conn.execute("""
        SELECT q_id, question_number, paper_id, official_analysis
        FROM questions
        WHERE section_type = 'reading_b' AND (correct_answer IS NULL OR correct_answer = '')
        ORDER BY paper_id, question_number
    """).fetchall()

    print(f"Found {len(nulls)} reading_b questions with NULL correct_answer\n")

    patched   = 0
    fallback_b = []
    manual    = []

    for q in nulls:
        q_id   = q["q_id"]
        q_num  = q["question_number"]
        p_id   = q["paper_id"]
        anal   = q.get("official_analysis", "") or ""

        # 提取年份 (paper_id 格式: 2013-eng1)
        year = int(p_id.split("-")[0]) if p_id else 0

        answer = None

        # Strategy A: JSON
        if year:
            json_answers = load_json_answers(year)
            answer = json_answers.get(q_num)

        # Strategy B: official_analysis regex
        if not answer and anal:
            answer = extract_answer_from_analysis(anal)
            if answer:
                fallback_b.append(q_id)

        if answer:
            if not args.dry_run:
                conn.execute(
                    "UPDATE questions SET correct_answer = ? WHERE q_id = ?",
                    (answer, q_id)
                )
            print(f"  PATCH  {q_id:<45}  answer={answer}")
            patched += 1
        else:
            manual.append(q_id)
            print(f"  MANUAL {q_id:<45}  ← needs human review")

    if not args.dry_run:
        conn.commit()

    conn.close()

    print(f"\n{'='*60}")
    print(f"  Patch Summary (dry_run={args.dry_run})")
    print(f"  Total NULL   : {len(nulls)}")
    print(f"  Patched (A)  : {patched - len(fallback_b)}")
    print(f"  Patched (B)  : {len(fallback_b)}")
    print(f"  Manual needed: {len(manual)}")
    if manual:
        print(f"\n  Manual review required:")
        for qid in manual:
            print(f"    {qid}")
    print(f"{'='*60}\n")

    # Verify
    if not args.dry_run:
        conn2 = sqlite3.connect(STATIC_DB)
        conn2.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        remaining = conn2.execute(
            "SELECT COUNT(*) as cnt FROM questions "
            "WHERE section_type='reading_b' AND (correct_answer IS NULL OR correct_answer='')"
        ).fetchone()["cnt"]
        conn2.close()
        print(f"  Remaining NULL in DB: {remaining}")
        if remaining == 0:
            print("  ✓ All reading_b answers are now populated!")


if __name__ == "__main__":
    main()
