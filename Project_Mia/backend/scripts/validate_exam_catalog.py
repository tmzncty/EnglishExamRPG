#!/usr/bin/env python3
"""Strict structural/content validation for committed English I papers."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB = REPO_ROOT / "Project_Mia/backend/data/static_content.db"

EXPECTED_SECTIONS = {
    "use_of_english": set(range(1, 21)),
    "reading_a": set(range(21, 41)),
    "reading_b": set(range(41, 46)),
    "translation": set(range(46, 51)),
    "writing_a": {51},
    "writing_b": {52},
}
OBJECTIVE = {"use_of_english", "reading_a", "reading_b"}
SUBJECTIVE = {"translation", "writing_a", "writing_b"}
KNOWN_BAD_TEXT = {
    "rehearsal worn": "2025 Text 1 OCR: rehearsal room",
    "Fordinand": "2025 Text 1 OCR: Ferdinand",
    "library character": "2025 Text 1 OCR: literary character",
    "retied on": "2025 Text 1 OCR: relied on",
    "desert island cliche's": "2025 Text 1 OCR: clichés",
}


def parse_options(raw: str | None):
    value = raw
    for _ in range(3):
        if not isinstance(value, str) or not value:
            return value
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def english_word_count(text: str) -> int:
    return len(re.findall(r"\b[A-Za-z]+(?:['’][A-Za-z]+)?\b", text))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    errors: list[str] = []
    warnings: list[str] = []
    try:
        papers = conn.execute(
            "SELECT paper_id, year, exam_type FROM papers WHERE exam_type='English I' ORDER BY year"
        ).fetchall()
        years = [row["year"] for row in papers]
        if years != list(range(2010, 2027)):
            errors.append(f"expected English I years 2010..2026, got {years}")

        test_count = conn.execute(
            "SELECT COUNT(*) FROM papers WHERE lower(COALESCE(exam_type, ''))='test'"
        ).fetchone()[0]
        if test_count:
            errors.append(f"committed catalog still contains {test_count} Test paper(s)")

        for paper in papers:
            paper_id = paper["paper_id"]
            qs = conn.execute(
                """
                SELECT q_id, section_type, question_number, passage_text, content,
                       options_json, correct_answer, answer_key
                FROM questions WHERE paper_id=?
                ORDER BY question_number, q_id
                """,
                (paper_id,),
            ).fetchall()

            if len(qs) != 52:
                errors.append(f"{paper_id}: expected 52 questions, got {len(qs)}")

            numbers = [q["question_number"] for q in qs]
            if sorted(n for n in numbers if n is not None) != list(range(1, 53)):
                errors.append(f"{paper_id}: question numbers are not exactly 1..52")
            duplicates = [n for n, count in Counter(numbers).items() if count > 1]
            if duplicates:
                errors.append(f"{paper_id}: duplicate question numbers {duplicates}")

            by_section: dict[str, set[int]] = {}
            for q in qs:
                by_section.setdefault(q["section_type"], set()).add(q["question_number"])
            for section, expected in EXPECTED_SECTIONS.items():
                actual = by_section.get(section, set())
                if actual != expected:
                    errors.append(
                        f"{paper_id}: {section} numbers {sorted(actual)} != {sorted(expected)}"
                    )

            for q in qs:
                qid = q["q_id"]
                section = q["section_type"]
                text_blob = "\n".join(
                    str(v or "") for v in (q["passage_text"], q["content"])
                )
                for bad, label in KNOWN_BAD_TEXT.items():
                    if bad in text_blob:
                        errors.append(f"{qid}: {label}")

                if section in OBJECTIVE:
                    answer = (q["correct_answer"] or "").strip().upper()
                    if not re.fullmatch(r"[A-H]", answer):
                        errors.append(f"{qid}: invalid/missing objective answer {q['correct_answer']!r}")
                    parsed = parse_options(q["options_json"])
                    if section in {"use_of_english", "reading_a"} and not isinstance(parsed, dict):
                        errors.append(f"{qid}: options are not a JSON object after normalization")
                    if isinstance(parsed, str) and parsed.lstrip().startswith(("{", "[")):
                        errors.append(f"{qid}: options remain double-encoded JSON")

                elif section in SUBJECTIVE:
                    answer_key = (q["answer_key"] or "").strip()
                    if not answer_key:
                        errors.append(f"{qid}: missing reference answer")
                    elif section == "writing_a":
                        words = english_word_count(answer_key)
                        if words and not 70 <= words <= 130:
                            warnings.append(f"{qid}: writing A reference has {words} English words")
                    elif section == "writing_b":
                        words = english_word_count(answer_key)
                        if words and not 140 <= words <= 220:
                            errors.append(f"{qid}: writing B reference has {words} English words")

        if warnings:
            print("Warnings:")
            for item in warnings:
                print(f"  - {item}")

        if errors:
            print("Validation errors:")
            for item in errors:
                print(f"  - {item}")
            print(f"FAILED: {len(errors)} error(s), {len(warnings)} warning(s)")
            return 1

        print(f"PASS: {len(papers)} English I papers, 2010–2026, structurally clean")
        if warnings:
            print(f"Warnings: {len(warnings)}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
