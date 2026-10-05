#!/usr/bin/env python3
"""Cross-check the English I corpus against independent public transcriptions.

This script is a discrepancy finder, not an authority. It deliberately does not write
exam content. Human review must resolve every reported conflict before a bundle can be
marked reviewed.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sqlite3
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB = REPO_ROOT / "Project_Mia/backend/data/static_content.db"
DEFAULT_OUT = REPO_ROOT / "Project_Mia/backend/manual_review"

UA = "Mozilla/5.0 Project-Mia-manual-corpus-audit/1.0"
OBJECTIVE = {"use_of_english", "reading_a", "reading_b"}


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def strip_html(raw: str) -> str:
    raw = re.sub(r"<script\b[^>]*>.*?</script>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<style\b[^>]*>.*?</style>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(raw)).strip()


def norm(text: str | None) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-").replace("…", "...")
    text = re.sub(r"_[0-9]+_", " ", text)
    text = re.sub(r"\b[0-9]{1,2}\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def word_fingerprint(text: str | None, n: int = 14) -> str:
    words = norm(text).split()
    return " ".join(words[:n]) if len(words) >= n else " ".join(words)


def tail_fingerprint(text: str | None, n: int = 10) -> str:
    words = norm(text).split()
    return " ".join(words[-n:]) if len(words) >= n else " ".join(words)


def extract_answer_pairs(page_text: str) -> dict[int, str]:
    # Restrict parsing to the answer-summary portion so option letters in the paper body
    # do not masquerade as answer keys.
    anchors = ["全卷客观题答案速查", "客观题参考答案速查表", "参考答案速查"]
    start = -1
    for anchor in anchors:
        pos = page_text.find(anchor)
        if pos >= 0:
            start = pos
            break
    if start < 0:
        return {}
    section = page_text[start : start + 18000]
    pairs: dict[int, str] = {}
    patterns = [
        r"(?<!\d)([1-9]|[1-3]\d|4[0-5])\s*[.=：:]?\s*([A-H])\b",
        r"(?<!\d)(4[1-5])\s*=\s*([A-H])\b",
    ]
    for pattern in patterns:
        for num, letter in re.findall(pattern, section, flags=re.I):
            qn = int(num)
            pairs.setdefault(qn, letter.upper())
    return pairs


def load_options(raw: str | None):
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    report: dict[str, object] = {
        "note": "Automated discrepancy finder only; human review is authoritative.",
        "years": {},
    }

    try:
        for year in range(2010, 2027):
            paper_id = f"{year}-eng1"
            page_url = f"https://english-exam.lazynote.cn/kaoyan/paper/{year}-english-one/"
            reading_url = (
                "https://raw.githubusercontent.com/Destinnnnn/"
                "kaoyan-english-1-2005-2026/main/"
                + urllib.parse.quote(f"{year}年考研英语一阅读精翻.md")
            )
            item: dict[str, object] = {
                "paper_url": page_url,
                "reading_crosscheck_url": reading_url,
                "answer_mismatches": [],
                "missing_question_text": [],
                "missing_options": [],
                "passage_fingerprint_misses": [],
                "independent_reading_fingerprint_misses": [],
                "fetch_errors": [],
            }
            try:
                page_html = fetch_text(page_url)
                page_text = strip_html(page_html)
                page_norm = norm(page_text)
            except Exception as exc:  # noqa: BLE001 - audit report should survive source outages
                page_text = ""
                page_norm = ""
                item["fetch_errors"].append(f"paper page: {type(exc).__name__}: {exc}")

            try:
                reading_md = fetch_text(reading_url)
                reading_norm = norm(reading_md)
            except Exception as exc:  # noqa: BLE001
                reading_norm = ""
                item["fetch_errors"].append(f"reading source: {type(exc).__name__}: {exc}")

            questions = conn.execute(
                """
                SELECT q_id, section_type, question_number, passage_text, content,
                       options_json, correct_answer
                FROM questions WHERE paper_id=? ORDER BY question_number
                """,
                (paper_id,),
            ).fetchall()

            answers = extract_answer_pairs(page_text) if page_text else {}
            item["answer_pairs_found"] = len(answers)
            for q in questions:
                qn = int(q["question_number"])
                if q["section_type"] in OBJECTIVE and qn in answers:
                    current = (q["correct_answer"] or "").strip().upper()
                    if current != answers[qn]:
                        item["answer_mismatches"].append(
                            {"q_id": q["q_id"], "db": current, "source": answers[qn]}
                        )

                if page_norm:
                    content_norm = norm(q["content"])
                    # Generic cloze labels are not printed on the paper; ignore them.
                    if (
                        q["section_type"] != "use_of_english"
                        and len(content_norm.split()) >= 5
                        and content_norm not in page_norm
                    ):
                        item["missing_question_text"].append(q["q_id"])

                    options = load_options(q["options_json"])
                    if isinstance(options, dict):
                        for label, value in options.items():
                            option_norm = norm(str(value))
                            if len(option_norm.split()) >= 2 and option_norm not in page_norm:
                                item["missing_options"].append(
                                    {"q_id": q["q_id"], "option": label, "text": value}
                                )

            # Check each unique passage only once.
            seen: set[tuple[str, str]] = set()
            for q in questions:
                passage = q["passage_text"] or ""
                if not passage.strip():
                    continue
                key = (q["section_type"], passage)
                if key in seen:
                    continue
                seen.add(key)
                head = word_fingerprint(passage)
                tail = tail_fingerprint(passage)
                if page_norm and head and (head not in page_norm or (tail and tail not in page_norm)):
                    item["passage_fingerprint_misses"].append(
                        {"section": q["section_type"], "head": head, "tail": tail}
                    )
                if q["section_type"] == "reading_a" and reading_norm and head not in reading_norm:
                    item["independent_reading_fingerprint_misses"].append(
                        {"section": q["section_type"], "head": head}
                    )

            item["counts"] = {
                "questions": len(questions),
                "answer_mismatches": len(item["answer_mismatches"]),
                "missing_question_text": len(item["missing_question_text"]),
                "missing_options": len(item["missing_options"]),
                "passage_fingerprint_misses": len(item["passage_fingerprint_misses"]),
                "independent_reading_fingerprint_misses": len(item["independent_reading_fingerprint_misses"]),
                "fetch_errors": len(item["fetch_errors"]),
            }
            report["years"][str(year)] = item
            print(year, item["counts"])
    finally:
        conn.close()

    json_path = args.out / "public-crosscheck.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Public-source cross-check",
        "",
        "> Automated discrepancy finder only. A clean row is not equivalent to human review.",
        "",
        "| Year | answers found | answer diffs | question text misses | option misses | passage misses | reading-source misses | fetch errors |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for year, item in report["years"].items():
        c = item["counts"]
        lines.append(
            f"| {year} | {item['answer_pairs_found']} | {c['answer_mismatches']} | "
            f"{c['missing_question_text']} | {c['missing_options']} | "
            f"{c['passage_fingerprint_misses']} | {c['independent_reading_fingerprint_misses']} | "
            f"{c['fetch_errors']} |"
        )
    (args.out / "public-crosscheck.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
