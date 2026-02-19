"""
import_vocab.py — 阶段 2.9: 词汇核心装载
==============================================
将 exam_vocabulary.json 的 6000+ 考研核心词汇导入 static_content.db dictionary 表。

源数据结构:
  { "word": "ability",
    "meanings": ["n. 能力，能耐；才能"],
    "pos": "n.",
    "sentences": [{ "sentence": "...", "translation": "", "year": 2013,
                     "exam_type": "English I", "section_name": "...",
                     "source_label": "2013 English I · ..." }]
  }

目标字段映射:
  word           → word (去空格, 小写)
  meanings[]     → meaning (分号拼接)
  pos            → pos
  len(sentences) → frequency (真题出现次数)
  sentences[]    → example_sentences (JSON)

Usage:
    python scripts/import_vocab.py
"""

import sqlite3
import json
from pathlib import Path

# --- 路径 ---
SRC_JSON = Path(r"F:\sanity_check_avg\VocabWeb\data\exam_vocabulary.json")
DB_PATH  = Path(__file__).resolve().parent.parent / "backend" / "data" / "static_content.db"

# --- 颜色 ---
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def main():
    print(f"\n{BOLD}{CYAN}{'='*60}")
    print(f"  📖 Project_Mia — Vocabulary Import")
    print(f"{'='*60}{RESET}\n")

    # --- 读取源 JSON ---
    print(f"  Reading: {SRC_JSON}")
    if not SRC_JSON.exists():
        print(f"  {RED}[ERROR] Source file not found!{RESET}")
        return

    with open(SRC_JSON, "r", encoding="utf-8") as f:
        vocab_list = json.load(f)

    total = len(vocab_list)
    print(f"  Found: {total} words\n")

    # --- 连接数据库 ---
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # 确保表存在
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dictionary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word VARCHAR(50) UNIQUE NOT NULL,
            meaning TEXT NOT NULL,
            pos VARCHAR(20),
            frequency INTEGER DEFAULT 0,
            example_sentences TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_dictionary_word ON dictionary(word)")

    # --- 批量导入 ---
    inserted = 0
    updated = 0
    errors = 0
    skipped_empty = 0

    batch_size = 500
    batch_count = 0

    for i, item in enumerate(vocab_list):
        try:
            word = item.get("word", "").strip()
            if not word:
                skipped_empty += 1
                continue

            # 释义: 数组拼接为分号分隔
            meanings_raw = item.get("meanings", [])
            if isinstance(meanings_raw, list):
                meaning = "; ".join(m.strip() for m in meanings_raw if m.strip())
            else:
                meaning = str(meanings_raw).strip()

            if not meaning:
                meaning = "[未知释义]"

            pos = item.get("pos", "").strip() or None

            # 例句 (保留完整结构用于跨年份联动)
            sentences = item.get("sentences", [])
            frequency = len(sentences)

            # 简化例句: 只保留 sentence, year, source_label
            clean_sentences = []
            for s in sentences:
                clean_sentences.append({
                    "en": s.get("sentence", ""),
                    "cn": s.get("translation", ""),
                    "year": s.get("year"),
                    "source": s.get("source_label", ""),
                })

            sentences_json = json.dumps(clean_sentences, ensure_ascii=False) if clean_sentences else None

            # Upsert
            cursor.execute("""
                INSERT INTO dictionary (word, meaning, pos, frequency, example_sentences)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(word) DO UPDATE SET
                    meaning = excluded.meaning,
                    pos = excluded.pos,
                    frequency = excluded.frequency,
                    example_sentences = excluded.example_sentences
            """, (word, meaning, pos, frequency, sentences_json))

            if cursor.rowcount > 0:
                inserted += 1
            else:
                updated += 1

            batch_count += 1
            if batch_count >= batch_size:
                conn.commit()
                batch_count = 0

            # 进度条 (每500个打印)
            if (i + 1) % 1000 == 0 or (i + 1) == total:
                pct = (i + 1) / total * 100
                bar_len = 30
                filled = int(bar_len * (i + 1) / total)
                bar = "█" * filled + "░" * (bar_len - filled)
                print(f"\r  [{bar}] {pct:5.1f}% ({i+1}/{total})", end="", flush=True)

        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"\n  {RED}[ERROR] {word}: {e}{RESET}")

    conn.commit()
    conn.close()
    print()

    # --- 报告 ---
    print(f"\n{BOLD}  📊 Import Summary{RESET}")
    print(f"  {'─'*40}")
    print(f"  Total processed:  {total}")
    print(f"  Inserted/Updated: {GREEN}{inserted}{RESET}")
    print(f"  Skipped (empty):  {skipped_empty}")
    print(f"  Errors:           {RED if errors else GREEN}{errors}{RESET}")

    if errors == 0:
        print(f"\n  {GREEN}{BOLD}✅ Vocabulary import complete!{RESET}\n")
    else:
        print(f"\n  {YELLOW}⚠ Import completed with {errors} errors.{RESET}\n")


if __name__ == "__main__":
    main()
