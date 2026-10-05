#!/usr/bin/env python3
"""Bootstrap review drafts for legacy English I papers.

This is intentionally a one-way scaffold: it writes only missing bundles and never
replaces an existing curated file. The generated 2010–2025 files are *review drafts*,
not evidence of verification. They are meant to be rewritten/cross-checked by a human
review pass and then this bootstrap helper can be removed.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB = REPO_ROOT / "Project_Mia/backend/data/static_content.db"
DEFAULT_OUT = REPO_ROOT / "Project_Mia/backend/data_import"

QUESTION_FIELDS = (
    "q_id",
    "q_type",
    "section_type",
    "section_name",
    "group_name",
    "question_number",
    "passage_text",
    "content",
    "options_json",
    "correct_answer",
    "image_base64",
    "official_analysis",
    "ai_persona_prompt",
    "answer_key",
    "difficulty",
    "score",
    "tags",
)


def decode_json(value):
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    written = 0
    try:
        for year in range(2010, 2026):
            paper_id = f"{year}-eng1"
            dest = args.out / f"{paper_id}.json"
            if dest.exists():
                print(f"{dest.name}: exists; preserving curated file")
                continue

            paper = conn.execute(
                "SELECT paper_id, year, exam_type, title, total_score, time_limit FROM papers WHERE paper_id=?",
                (paper_id,),
            ).fetchone()
            if paper is None:
                raise SystemExit(f"missing paper: {paper_id}")

            rows = conn.execute(
                "SELECT * FROM questions WHERE paper_id=? ORDER BY question_number",
                (paper_id,),
            ).fetchall()
            if len(rows) != 52:
                raise SystemExit(f"{paper_id}: expected 52 questions, got {len(rows)}")

            questions = []
            for row in rows:
                q = {field: row[field] for field in QUESTION_FIELDS}
                q["options"] = decode_json(q.pop("options_json"))
                q["tags"] = decode_json(q.get("tags")) or []
                questions.append(q)

            bundle = {
                "schema_version": 1,
                "review_status": "bootstrap-unverified",
                "provenance": {
                    "note": (
                        "Mechanical review draft exported from the pre-existing SQLite corpus. "
                        "Do not treat as independently verified until review_status is changed."
                    )
                },
                "paper": dict(paper),
                "expected_section_counts": {
                    "use_of_english": 20,
                    "reading_a": 20,
                    "reading_b": 5,
                    "translation": 5,
                    "writing_a": 1,
                    "writing_b": 1,
                },
                "questions": questions,
            }
            dest.write_text(
                json.dumps(bundle, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"Wrote review draft {dest.name}")
            written += 1
    finally:
        conn.close()

    print(f"Legacy bundle drafts written: {written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
