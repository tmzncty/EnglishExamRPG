#!/usr/bin/env python3
"""Export static_content.db into text files that are easy to inspect and search.

The SQLite database remains the application source of truth. This script creates a
read-only text projection for humans, agents, code search, and tutoring workflows.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB = REPO_ROOT / "Project_Mia/backend/data/static_content.db"
DEFAULT_OUT = REPO_ROOT / "Project_Mia/backend/data_export"


def slug(value: str | None, fallback: str = "unknown") -> str:
    text = (value or fallback).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or fallback


def parse_json(value: Any) -> Any:
    if value is None or value == "":
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return value


def rows(conn: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    cur = conn.execute(sql, tuple(params))
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def render_options(options: Any) -> list[str]:
    parsed = parse_json(options)
    if isinstance(parsed, dict):
        return [f"- **{key}.** {value}" for key, value in parsed.items()]
    if isinstance(parsed, list):
        return [f"- {value}" for value in parsed]
    if parsed:
        return [f"- {parsed}"]
    return []


def clean_question_for_json(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    out["options_json"] = parse_json(out.get("options_json"))
    out["tags"] = parse_json(out.get("tags"))
    image = out.pop("image_base64", None)
    out["has_image"] = bool(image)
    return out


def export_group(path: Path, paper: dict[str, Any], group_rows: list[dict[str, Any]]) -> None:
    first = group_rows[0]
    lines: list[str] = []
    lines.append(f"# {paper['year']} {paper.get('exam_type') or ''} — {first.get('section_name') or first.get('section_type') or 'Section'}")
    if first.get("group_name"):
        lines.append(f"\n## {first['group_name']}")

    passages: list[str] = []
    seen: set[str] = set()
    for q in group_rows:
        passage = (q.get("passage_text") or "").strip()
        if passage and passage not in seen:
            seen.add(passage)
            passages.append(passage)

    for i, passage in enumerate(passages, 1):
        heading = "Passage" if len(passages) == 1 else f"Passage {i}"
        lines.extend([f"\n### {heading}\n", passage])

    lines.append("\n---")
    for q in group_rows:
        number = q.get("question_number")
        label = f"Question {number}" if number is not None else q.get("q_id", "Question")
        lines.append(f"\n### {label}\n")
        if q.get("content"):
            lines.append(str(q["content"]).strip())
        options = render_options(q.get("options_json"))
        if options:
            lines.extend(["", *options])
        if q.get("correct_answer"):
            lines.append(f"\n**Correct answer:** {q['correct_answer']}")
        if q.get("answer_key"):
            lines.append(f"\n**Answer key / reference answer:**\n\n{str(q['answer_key']).strip()}")
        if q.get("official_analysis"):
            lines.append(f"\n**Analysis:**\n\n{str(q['official_analysis']).strip()}")
        if q.get("image_base64"):
            lines.append("\n> This question has an image in the SQLite source; base64 image data is intentionally omitted from the text export.")
        meta: list[str] = []
        if q.get("q_id"):
            meta.append(f"q_id={q['q_id']}")
        if q.get("difficulty") is not None:
            meta.append(f"difficulty={q['difficulty']}")
        if q.get("score") is not None:
            meta.append(f"score={q['score']}")
        tags = parse_json(q.get("tags"))
        if tags:
            meta.append(f"tags={json.dumps(tags, ensure_ascii=False)}")
        if meta:
            lines.append("\n<!-- " + "; ".join(meta) + " -->")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    db = args.db.resolve()
    out = args.out.resolve()
    if not db.exists():
        raise SystemExit(f"database not found: {db}")

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        table_names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "papers" not in table_names or "questions" not in table_names:
            raise SystemExit("static content database is missing required papers/questions tables")

        papers = rows(conn, "SELECT * FROM papers ORDER BY year, exam_type, paper_id")
        questions = rows(
            conn,
            """
            SELECT * FROM questions
            ORDER BY paper_id,
                     CASE section_type
                       WHEN 'use_of_english' THEN 1
                       WHEN 'reading_a' THEN 2
                       WHEN 'reading_b' THEN 3
                       WHEN 'translation' THEN 4
                       WHEN 'writing_a' THEN 5
                       WHEN 'writing_b' THEN 6
                       ELSE 99
                     END,
                     COALESCE(group_name, ''),
                     COALESCE(question_number, 999),
                     q_id
            """,
        )

        q_by_paper: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for q in questions:
            q_by_paper[q["paper_id"]].append(q)

        generated_groups = 0
        index_lines = [
            "# Static content text export",
            "",
            "> Generated from `Project_Mia/backend/data/static_content.db`. Do not edit generated files by hand.",
            "",
            "The SQLite database remains the source of truth. This directory exists so humans and agents can inspect/search exam content without opening SQLite.",
            "",
            "| Year | Paper | Questions | Text groups |",
            "| ---: | --- | ---: | ---: |",
        ]

        for paper in papers:
            paper_id = paper["paper_id"]
            paper_questions = q_by_paper.get(paper_id, [])
            grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
            for q in paper_questions:
                key = (
                    q.get("section_type") or "other",
                    q.get("section_name") or "",
                    q.get("group_name") or "ungrouped",
                )
                grouped[key].append(q)

            paper_dir = out / "papers" / paper_id
            for (section_type, section_name, group_name), group_rows in grouped.items():
                filename = f"{slug(section_type)}--{slug(group_name)}"
                dest = paper_dir / f"{filename}.md"
                if dest.exists():
                    dest = paper_dir / f"{filename}--{slug(section_name)}.md"
                export_group(dest, paper, group_rows)
                generated_groups += 1

            index_lines.append(
                f"| {paper['year']} | `{paper_id}` ({paper.get('exam_type') or ''}) | {len(paper_questions)} | {len(grouped)} |"
            )

        write_jsonl(out / "questions.jsonl", (clean_question_for_json(q) for q in questions))
        write_jsonl(out / "papers.jsonl", papers)

        dictionary_count = 0
        if "dictionary" in table_names:
            dictionary = rows(conn, "SELECT * FROM dictionary ORDER BY word")
            for item in dictionary:
                item["example_sentences"] = parse_json(item.get("example_sentences"))
            write_jsonl(out / "dictionary.jsonl", dictionary)
            dictionary_count = len(dictionary)

        stories_count = 0
        if "stories" in table_names:
            stories = rows(conn, "SELECT * FROM stories ORDER BY year, q_id, id")
            write_jsonl(out / "stories.jsonl", stories)
            stories_count = len(stories)

        index_lines.extend(
            [
                "",
                "## Export summary",
                "",
                f"- papers: {len(papers)}",
                f"- questions: {len(questions)}",
                f"- markdown groups: {generated_groups}",
                f"- dictionary entries: {dictionary_count}",
                f"- story rows: {stories_count}",
                "",
                "For tutoring, start with `papers/<paper-id>/reading-a--text-*.md`. For broad retrieval, search `questions.jsonl`.",
            ]
        )
        (out / "README.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")

        manifest = {
            "source": str(db.relative_to(REPO_ROOT)),
            "papers": len(papers),
            "questions": len(questions),
            "markdown_groups": generated_groups,
            "dictionary_entries": dictionary_count,
            "story_rows": stories_count,
        }
        (out / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    finally:
        conn.close()

    print(f"Exported {db} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
