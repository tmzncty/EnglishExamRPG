#!/usr/bin/env python3
"""Import a curated exam bundle into Project Mia's static-content SQLite database.

The importer is deliberately idempotent: if the paper already matches the bundle,
it performs no write at all. This matters because the export workflow may run again
after committing the updated SQLite file and generated text projection.

A curated bundle may intentionally omit enrichment fields such as reference answers
or analyses. A null value for those fields is treated as "not supplied" so later
human-reviewed enrichments are preserved. Supplying a non-null value remains
authoritative and will be imported normally.
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

PAPER_FIELDS = ("paper_id", "year", "exam_type", "title", "total_score", "time_limit")
QUESTION_FIELDS = (
    "q_id",
    "paper_id",
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

# Null values in a bundle mean "no curated enrichment supplied yet" for these
# fields. This lets deterministic repair/enrichment scripts coexist with bundles
# without forcing a delete/reinsert cycle on every CI run.
PRESERVE_IF_NULL_FIELDS = {"answer_key", "official_analysis"}


def canonical_json(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def encode_image_svg(svg: str | None) -> str | None:
    if not svg:
        return None
    raw = svg.encode("utf-8")
    return "data:image/svg+xml;base64," + base64.b64encode(raw).decode("ascii")


def normalize_question(raw: dict[str, Any], paper_id: str) -> dict[str, Any]:
    q = {field: raw.get(field) for field in QUESTION_FIELDS}
    q["paper_id"] = paper_id

    if "options" in raw:
        q["options_json"] = canonical_json(raw.get("options"))
    elif isinstance(q.get("options_json"), (dict, list)):
        q["options_json"] = canonical_json(q["options_json"])

    if "tags" in raw and not isinstance(raw.get("tags"), str):
        q["tags"] = canonical_json(raw.get("tags"))

    if raw.get("image_svg"):
        q["image_base64"] = encode_image_svg(raw["image_svg"])

    return q


def normalize_db_value(field: str, value: Any) -> Any:
    if field in {"options_json", "tags"} and value:
        try:
            return canonical_json(json.loads(value))
        except (TypeError, json.JSONDecodeError):
            return value
    if field in {"score", "difficulty"} and value is not None:
        return float(value)
    return value


def validate_bundle(bundle: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    paper = bundle["paper"]
    paper_id = paper["paper_id"]
    questions = [normalize_question(q, paper_id) for q in bundle["questions"]]

    expected_numbers = list(range(1, 53))
    numbers = sorted(q["question_number"] for q in questions)
    if numbers != expected_numbers:
        raise SystemExit(
            f"expected exactly question numbers 1..52; got {numbers}"
        )

    qids = [q["q_id"] for q in questions]
    if len(qids) != len(set(qids)):
        raise SystemExit("duplicate q_id in bundle")

    section_counts: dict[str, int] = {}
    for q in questions:
        section_counts[q["section_type"]] = section_counts.get(q["section_type"], 0) + 1

    expected_counts = bundle.get(
        "expected_section_counts",
        {
            "use_of_english": 20,
            "reading_a": 20,
            "reading_b": 5,
            "translation": 5,
            "writing_a": 1,
            "writing_b": 1,
        },
    )
    if section_counts != expected_counts:
        raise SystemExit(
            f"unexpected section counts: {section_counts}; expected {expected_counts}"
        )

    total_score = round(sum(float(q["score"] or 0) for q in questions), 6)
    expected_score = float(paper.get("total_score") or 0)
    if total_score != expected_score:
        raise SystemExit(
            f"question scores total {total_score}, paper total_score is {expected_score}"
        )

    for q in questions:
        if q["section_type"] in {"use_of_english", "reading_a", "reading_b"}:
            if not q["correct_answer"]:
                raise SystemExit(f"objective question missing answer: {q['q_id']}")

    return paper, questions


def row_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def paper_matches(conn: sqlite3.Connection, paper: dict[str, Any], questions: list[dict[str, Any]]) -> bool:
    existing_paper = row_dict(
        conn.execute("SELECT * FROM papers WHERE paper_id = ?", (paper["paper_id"],)).fetchone()
    )
    if not existing_paper:
        return False

    for field in PAPER_FIELDS:
        if normalize_db_value(field, existing_paper.get(field)) != normalize_db_value(field, paper.get(field)):
            return False

    existing_questions = conn.execute(
        "SELECT * FROM questions WHERE paper_id = ? ORDER BY question_number, q_id",
        (paper["paper_id"],),
    ).fetchall()
    if len(existing_questions) != len(questions):
        return False

    desired = sorted(questions, key=lambda q: (q["question_number"], q["q_id"]))
    for db_row, q in zip(existing_questions, desired):
        db_q = dict(db_row)
        for field in QUESTION_FIELDS:
            if field in PRESERVE_IF_NULL_FIELDS and q.get(field) is None:
                continue
            if normalize_db_value(field, db_q.get(field)) != normalize_db_value(field, q.get(field)):
                return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
    paper, questions = validate_bundle(bundle)

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    try:
        table_names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"papers", "questions"} <= table_names:
            raise SystemExit("database is missing papers/questions tables")

        if paper_matches(conn, paper, questions):
            print(f"{paper['paper_id']}: already matches bundle; no database write")
            return 0

        existing_rows = conn.execute(
            "SELECT * FROM questions WHERE paper_id = ?",
            (paper["paper_id"],),
        ).fetchall()
        existing_by_qid = {row["q_id"]: dict(row) for row in existing_rows}

        paper_columns = [f for f in PAPER_FIELDS if f in paper]
        paper_values = [paper[f] for f in paper_columns]
        update_fields = [f for f in paper_columns if f != "paper_id"]
        conn.execute(
            f"""
            INSERT INTO papers ({", ".join(paper_columns)})
            VALUES ({", ".join("?" for _ in paper_columns)})
            ON CONFLICT(paper_id) DO UPDATE SET
            {", ".join(f"{f}=excluded.{f}" for f in update_fields)}
            """,
            paper_values,
        )

        conn.execute("DELETE FROM questions WHERE paper_id = ?", (paper["paper_id"],))

        db_columns = {r[1] for r in conn.execute("PRAGMA table_info(questions)")}
        insert_fields = [f for f in QUESTION_FIELDS if f in db_columns]
        sql = (
            f"INSERT INTO questions ({', '.join(insert_fields)}) "
            f"VALUES ({', '.join('?' for _ in insert_fields)})"
        )
        for q in questions:
            q_to_insert = dict(q)
            existing = existing_by_qid.get(q["q_id"], {})
            for field in PRESERVE_IF_NULL_FIELDS:
                if q_to_insert.get(field) is None and existing.get(field) is not None:
                    q_to_insert[field] = existing[field]
            conn.execute(sql, [q_to_insert.get(f) for f in insert_fields])

        conn.commit()
        print(f"Imported {paper['paper_id']}: {len(questions)} questions, "
              f"{sum(float(q['score'] or 0) for q in questions):g} points")
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
