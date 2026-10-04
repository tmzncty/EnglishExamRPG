#!/usr/bin/env python3
"""Apply reviewed integrity repairs to Project Mia's static exam database.

Repairs live in JSON so every change is inspectable and reproducible.  This script
supports field updates, question deletion, and small legacy-normalization rules.
It is intentionally idempotent.
"""

from __future__ import annotations

import argparse
import base64
import json
import sqlite3
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB = REPO_ROOT / "Project_Mia/backend/data/static_content.db"


def encode_svg(svg: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


def db_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def encode_field(field: str, value: Any) -> Any:
    if field in {"options_json", "tags"} and isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def update_question(conn: sqlite3.Connection, op: dict[str, Any], valid_columns: set[str]) -> bool:
    q_id = op["q_id"]
    fields = dict(op.get("fields") or {})
    if "image_svg" in op:
        fields["image_base64"] = encode_svg(op["image_svg"])

    unknown = set(fields) - valid_columns
    if unknown:
        raise SystemExit(f"{q_id}: unknown question fields: {sorted(unknown)}")
    if not fields:
        return False

    row = conn.execute("SELECT * FROM questions WHERE q_id = ?", (q_id,)).fetchone()
    if row is None:
        raise SystemExit(f"question not found: {q_id}")

    current = dict(row)
    desired = {k: encode_field(k, v) for k, v in fields.items()}
    changed = any(current.get(k) != v for k, v in desired.items())
    if not changed:
        return False

    assignments = ", ".join(f"{k} = ?" for k in desired)
    conn.execute(
        f"UPDATE questions SET {assignments} WHERE q_id = ?",
        [*desired.values(), q_id],
    )
    return True


def normalize_legacy(conn: sqlite3.Connection, config: dict[str, Any], valid_columns: set[str]) -> int:
    changed = 0

    if config.get("fill_empty_cloze_content"):
        rows = conn.execute(
            """
            SELECT q_id, question_number
            FROM questions
            WHERE paper_id GLOB '[0-9][0-9][0-9][0-9]-eng1'
              AND section_type = 'use_of_english'
              AND (content IS NULL OR trim(content) = '')
            """
        ).fetchall()
        for row in rows:
            conn.execute(
                "UPDATE questions SET content = ? WHERE q_id = ?",
                (f"Choose the best word(s) for blank {row['question_number']}.", row["q_id"]),
            )
            changed += 1

    if config.get("fill_empty_reading_b_content"):
        rows = conn.execute(
            """
            SELECT q_id, question_number
            FROM questions
            WHERE paper_id GLOB '[0-9][0-9][0-9][0-9]-eng1'
              AND section_type = 'reading_b'
              AND (content IS NULL OR trim(content) = '')
            """
        ).fetchall()
        for row in rows:
            conn.execute(
                "UPDATE questions SET content = ? WHERE q_id = ?",
                (f"Choose the most suitable option for blank {row['question_number']}.", row["q_id"]),
            )
            changed += 1

    # Preserve historical task data but stop relying on the API's hidden A-G fallback.
    if config.get("materialize_reading_b_letter_options"):
        h_years = set(config.get("reading_b_h_years", []))
        rows = conn.execute(
            """
            SELECT q_id, paper_id
            FROM questions
            WHERE paper_id GLOB '[0-9][0-9][0-9][0-9]-eng1'
              AND section_type = 'reading_b'
              AND (options_json IS NULL OR trim(options_json) = '')
            """
        ).fetchall()
        for row in rows:
            letters = "ABCDEFGH" if row["paper_id"] in h_years else "ABCDEFG"
            options = json.dumps({c: c for c in letters}, ensure_ascii=False, sort_keys=True)
            conn.execute("UPDATE questions SET options_json = ? WHERE q_id = ?", (options, row["q_id"]))
            changed += 1

    return changed


def validate(conn: sqlite3.Connection) -> None:
    papers = conn.execute(
        """
        SELECT paper_id
        FROM papers
        WHERE paper_id GLOB '[0-9][0-9][0-9][0-9]-eng1'
        ORDER BY paper_id
        """
    ).fetchall()
    expected_sections = {
        "use_of_english": 20,
        "reading_a": 20,
        "reading_b": 5,
        "translation": 5,
        "writing_a": 1,
        "writing_b": 1,
    }

    errors: list[str] = []
    for p in papers:
        paper_id = p["paper_id"]
        rows = conn.execute(
            "SELECT * FROM questions WHERE paper_id = ? ORDER BY question_number, q_id",
            (paper_id,),
        ).fetchall()
        numbered = [r for r in rows if r["question_number"] is not None]
        nums = [int(r["question_number"]) for r in numbered]

        if len(rows) != 52:
            errors.append(f"{paper_id}: expected 52 rows, found {len(rows)}")
        if sorted(nums) != list(range(1, 53)):
            errors.append(f"{paper_id}: question numbers are not exactly 1..52")

        counts: dict[str, int] = {}
        for r in rows:
            counts[r["section_type"]] = counts.get(r["section_type"], 0) + 1
        if counts != expected_sections:
            errors.append(f"{paper_id}: section counts {counts}")

        total = sum(float(r["score"] or 0) for r in rows)
        if abs(total - 100.0) > 1e-9:
            errors.append(f"{paper_id}: total score {total}")

        for r in rows:
            if not (r["content"] or "").strip():
                errors.append(f"{r['q_id']}: empty content")
            if r["section_type"] in {"use_of_english", "reading_a", "reading_b"}:
                if not r["correct_answer"]:
                    errors.append(f"{r['q_id']}: missing objective answer")
                    continue
                raw = r["options_json"]
                if not raw:
                    errors.append(f"{r['q_id']}: missing objective options")
                    continue
                try:
                    opts = json.loads(raw)
                except json.JSONDecodeError:
                    errors.append(f"{r['q_id']}: malformed options_json")
                    continue
                if r["correct_answer"] not in opts:
                    errors.append(
                        f"{r['q_id']}: answer {r['correct_answer']} absent from options {sorted(opts)}"
                    )

    if errors:
        raise SystemExit("Integrity validation failed:\n- " + "\n- ".join(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repairs", type=Path)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    spec = json.loads(args.repairs.read_text(encoding="utf-8"))
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    changed = 0
    deleted = 0

    try:
        valid_columns = db_columns(conn, "questions")

        for q_id in spec.get("delete_questions", []):
            cur = conn.execute("DELETE FROM questions WHERE q_id = ?", (q_id,))
            deleted += cur.rowcount

        for op in spec.get("updates", []):
            changed += int(update_question(conn, op, valid_columns))

        changed += normalize_legacy(conn, spec.get("normalize", {}), valid_columns)
        validate(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print(f"Applied integrity repairs: {changed} updates, {deleted} deletions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
