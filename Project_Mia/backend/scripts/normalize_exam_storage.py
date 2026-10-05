#!/usr/bin/env python3
"""Normalize legacy exam rows without changing exam semantics."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB = REPO_ROOT / "Project_Mia/backend/data/static_content.db"


def decode_json_layers(raw: str | None):
    if not raw:
        return raw
    value = raw
    for _ in range(3):
        if not isinstance(value, str):
            break
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            break
    return value


def normalize_options(raw: str | None) -> str | None:
    value = decode_json_layers(raw)
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return raw


def normalize_tags(raw: str | None) -> str | None:
    value = decode_json_layers(raw)
    if isinstance(value, list):
        cleaned = ["rehearsal room" if item == "rehearsal-worn" else item for item in value]
        return json.dumps(cleaned, ensure_ascii=False, separators=(",", ":"))
    return raw


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    changed = 0
    try:
        rows = conn.execute(
            "SELECT q_id, options_json, tags FROM questions WHERE options_json IS NOT NULL OR tags IS NOT NULL"
        ).fetchall()
        for q_id, raw_options, raw_tags in rows:
            options = normalize_options(raw_options)
            tags = normalize_tags(raw_tags)
            if options != raw_options:
                conn.execute("UPDATE questions SET options_json=? WHERE q_id=?", (options, q_id))
                changed += 1
            if tags != raw_tags:
                conn.execute("UPDATE questions SET tags=? WHERE q_id=?", (tags, q_id))
                changed += 1

        # Test fixtures must never be committed as user-visible exam papers.
        test_papers = [
            row[0]
            for row in conn.execute("SELECT paper_id FROM papers WHERE lower(COALESCE(exam_type, ''))='test'")
        ]
        for paper_id in test_papers:
            conn.execute("DELETE FROM questions WHERE paper_id=?", (paper_id,))
            conn.execute("DELETE FROM papers WHERE paper_id=?", (paper_id,))
            changed += 1

        conn.commit()
        print(f"Normalized exam storage; changed units: {changed}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
