#!/usr/bin/env python3
"""Normalize legacy exam rows without changing exam semantics."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB = REPO_ROOT / "Project_Mia/backend/data/static_content.db"


def normalize_options(raw: str | None) -> str | None:
    if not raw:
        return raw
    value = raw
    for _ in range(2):
        if not isinstance(value, str):
            break
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            break
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return raw


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    changed = 0
    try:
        rows = conn.execute("SELECT q_id, options_json FROM questions WHERE options_json IS NOT NULL").fetchall()
        for q_id, raw in rows:
            normalized = normalize_options(raw)
            if normalized != raw:
                conn.execute("UPDATE questions SET options_json=? WHERE q_id=?", (normalized, q_id))
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
