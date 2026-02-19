"""
vocab_audit.py — 阶段 2.9: 词汇质检
==============================================
扫描 dictionary 表，检查总量、空值、例句覆盖率，并随机抽样5条。

Usage:
    python scripts/vocab_audit.py
"""

import sqlite3
import json
import random
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "backend" / "data" / "static_content.db"

# --- 颜色 ---
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def main():
    if not DB_PATH.exists():
        print(f"{RED}[ERROR] Database not found: {DB_PATH}{RESET}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    print(f"\n{BOLD}{CYAN}{'='*60}")
    print(f"  📖 Project_Mia — Vocabulary Audit Report")
    print(f"{'='*60}{RESET}\n")
    print(f"  Database: {DB_PATH}\n")

    # --- 1. 总量 ---
    cursor.execute("SELECT COUNT(*) FROM dictionary")
    total = cursor.fetchone()[0]
    status = GREEN if total >= 5500 else (YELLOW if total >= 3000 else RED)
    print(f"  Total Words:       {status}{total}{RESET}")

    # --- 2. 空值检查 ---
    cursor.execute("SELECT COUNT(*) FROM dictionary WHERE meaning IS NULL OR TRIM(meaning) = ''")
    missing_meaning = cursor.fetchone()[0]
    print(f"  Missing Meanings:  {RED if missing_meaning else GREEN}{missing_meaning}{RESET}")

    cursor.execute("SELECT COUNT(*) FROM dictionary WHERE pos IS NULL OR TRIM(pos) = ''")
    missing_pos = cursor.fetchone()[0]
    print(f"  Missing POS:       {YELLOW if missing_pos else GREEN}{missing_pos}{RESET}")

    # --- 3. 例句覆盖率 ---
    cursor.execute("SELECT COUNT(*) FROM dictionary WHERE example_sentences IS NOT NULL AND example_sentences != '[]'")
    with_sentences = cursor.fetchone()[0]
    pct = (with_sentences / total * 100) if total else 0
    color = GREEN if pct >= 80 else (YELLOW if pct >= 50 else RED)
    print(f"  With Sentences:    {color}{with_sentences} ({pct:.1f}%){RESET}")

    # --- 4. 频次分布 ---
    cursor.execute("SELECT AVG(frequency), MAX(frequency) FROM dictionary")
    avg_freq, max_freq = cursor.fetchone()
    print(f"  Avg Frequency:     {avg_freq:.1f}")
    print(f"  Max Frequency:     {max_freq}")

    # --- 5. Top频次词 ---
    cursor.execute("SELECT word, frequency FROM dictionary ORDER BY frequency DESC LIMIT 5")
    top_words = cursor.fetchall()
    print(f"\n{BOLD}  🔥 Top 5 Highest Frequency Words{RESET}")
    for w, f in top_words:
        print(f"    {w:<20} appears {f} times in exams")

    # --- 6. 随机抽样 ---
    cursor.execute("SELECT word, meaning, pos, frequency, example_sentences FROM dictionary ORDER BY RANDOM() LIMIT 5")
    samples = cursor.fetchall()
    print(f"\n{BOLD}  🎲 Random Sample (5 words){RESET}")
    print(f"  {'─'*56}")
    for word, meaning, pos, freq, sentences_raw in samples:
        print(f"\n  {CYAN}{BOLD}\"{word}\"{RESET}  [{pos or '?'}]  freq={freq}")
        # 截取释义前60字符
        meaning_short = meaning[:60] + "..." if len(meaning) > 60 else meaning
        print(f"    Meaning: {meaning_short}")

        if sentences_raw:
            try:
                sentences = json.loads(sentences_raw)
                if sentences:
                    s = sentences[0]
                    en = s.get("en", "")[:80]
                    source = s.get("source", "")
                    year = s.get("year", "")
                    print(f"    Example: \"{en}...\"")
                    print(f"    Source:  {source}")
            except json.JSONDecodeError:
                print(f"    {RED}[Invalid JSON in sentences]{RESET}")
        else:
            print(f"    {YELLOW}(No sentences){RESET}")

    # --- 7. 年份分布 ---
    print(f"\n{BOLD}  📅 Sentence Year Distribution{RESET}")
    cursor.execute("SELECT example_sentences FROM dictionary WHERE example_sentences IS NOT NULL")
    year_counts = {}
    for (raw,) in cursor.fetchall():
        try:
            for s in json.loads(raw):
                y = s.get("year")
                if y:
                    year_counts[y] = year_counts.get(y, 0) + 1
        except (json.JSONDecodeError, TypeError):
            pass

    for y in sorted(year_counts.keys()):
        bar = "█" * min(50, year_counts[y] // 20)
        print(f"    {y}: {year_counts[y]:>5}  {bar}")

    # --- 结论 ---
    print(f"\n  {'─'*56}")
    issues = []
    if total < 5500:
        issues.append(f"Total words below expected (~6000)")
    if missing_meaning > 0:
        issues.append(f"{missing_meaning} words missing meanings")

    if issues:
        print(f"  {YELLOW}⚠ Issues Found:{RESET}")
        for iss in issues:
            print(f"    - {iss}")
    else:
        print(f"  {GREEN}{BOLD}✅ Vocabulary audit passed!{RESET}")

    conn.close()
    print()


if __name__ == "__main__":
    main()
