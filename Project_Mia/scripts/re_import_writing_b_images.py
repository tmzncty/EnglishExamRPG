#!/usr/bin/env python3
"""
re_import_writing_b_images.py
──────────────────────────────
从 F:\sanity_check_avg\extracted_images\<year>\writing_b.jpeg/jpg/png
重新读取并以 base64 写入 static_content.db 的对应 writing_b 题目。

只更新 image_base64 为 NULL 或 < 2000字节 的记录。
"""
import base64
import sqlite3
from pathlib import Path

STATIC_DB = Path(r'F:\sanity_check_avg\Project_Mia\backend\data\static_content.db')
IMG_ROOT   = Path(r'F:\sanity_check_avg\extracted_images')

YEARS = range(2010, 2026)

# 候选文件名（按优先级）
CANDIDATES = ["writing_b.jpeg", "writing_b.jpg", "writing_b.png",
              "writingb.jpeg", "writingb.jpg", "writing_B.jpeg"]


def find_image(year: int) -> Path | None:
    folder = IMG_ROOT / str(year)
    if not folder.exists():
        return None
    for name in CANDIDATES:
        p = folder / name
        if p.exists():
            return p
    return None


conn = sqlite3.connect(STATIC_DB)
conn.row_factory = sqlite3.Row

rows = conn.execute("""
    SELECT q_id, paper_id, image_base64
    FROM questions
    WHERE section_type = 'writing_b'
    ORDER BY paper_id
""").fetchall()

updated = 0
skipped = 0
missing = 0

print(f"{'Year':<6} {'DB img len':>12}  {'File':>40}  Action")
print(f"  {'-'*65}")

for row in rows:
    year_str = row["paper_id"].split("-")[0]
    try:
        year = int(year_str)
    except ValueError:
        continue

    db_len = len(row["image_base64"]) if row["image_base64"] else 0
    img_path = find_image(year)

    if img_path is None:
        file_str = "(no file)"
        action   = "SKIP (no file)"
        missing += 1
    elif db_len >= 5000:
        file_str = img_path.name
        action   = f"SKIP (DB ok, {db_len}b)"
        skipped += 1
    else:
        raw     = img_path.read_bytes()
        b64     = base64.b64encode(raw).decode("utf-8")
        conn.execute("UPDATE questions SET image_base64=? WHERE q_id=?",
                     (b64, row["q_id"]))
        file_str = img_path.name
        action   = f"UPDATED ({len(raw)//1024}kb → {len(b64)//1024}kb b64)"
        updated += 1

    print(f"  {year:<6} {db_len:>12}  {file_str:>40}  {action}")

conn.commit()
conn.close()

print(f"\nDone. Updated={updated}  Skipped={skipped}  Missing={missing}")
