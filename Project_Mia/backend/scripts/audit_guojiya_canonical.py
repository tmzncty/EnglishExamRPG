#!/usr/bin/env python3
"""Audit objective question text/option ordering against full-paper transcriptions.

The full-paper pages keep each question's option labels next to the answer, which is
exactly what the first answer-letter-only pass failed to preserve. This script is
read-only: it writes a discrepancy report for human review and never mutates bundles.
"""

from __future__ import annotations

import html
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
IMPORT_DIR = ROOT / "Project_Mia/backend/data_import"
OUT = ROOT / "Project_Mia/backend/manual_review/guojiya-canonical-audit.json"
UA = "Mozilla/5.0 Project-Mia-corpus-audit/1.0"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", errors="replace")


def visible_text(raw: str) -> str:
    raw = re.sub(r"<script\b[^>]*>.*?</script>", "\n", raw, flags=re.I | re.S)
    raw = re.sub(r"<style\b[^>]*>.*?</style>", "\n", raw, flags=re.I | re.S)
    raw = re.sub(r"<(?:br|/p|/div|/li|/h\d|hr)\b[^>]*>", "\n", raw, flags=re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw).replace("\xa0", " ")
    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r"\n\s*\n+", "\n", raw)
    return raw.strip()


def norm(s: str | None) -> str:
    if not s:
        return ""
    s = html.unescape(str(s)).replace("’", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"\s+", " ", s)
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def source_blocks(text: str) -> dict[int, str]:
    # Question headings on these pages are rendered as a number followed by a full stop.
    # Require a line boundary so numbered blanks in passages are not mistaken for headings.
    hits = list(re.finditer(r"(?m)^\s*(\d{1,2})\.\s*$", text))
    blocks: dict[int, str] = {}
    for i, m in enumerate(hits):
        qn = int(m.group(1))
        if not 1 <= qn <= 45 or qn in blocks:
            continue
        end = hits[i + 1].start() if i + 1 < len(hits) else len(text)
        blocks[qn] = text[m.end():end].strip()
    return blocks


def parse_block(block: str) -> tuple[dict[str, str], str | None]:
    answer = None
    m_answer = re.search(r"(?:答案|Answer)\s*[:：]?\s*([A-H])\b", block, flags=re.I)
    if m_answer:
        answer = m_answer.group(1).upper()

    # Capture option text until the next option label or answer marker.
    options: dict[str, str] = {}
    matches = list(re.finditer(r"(?m)^\s*([A-H])\)\s*(.+?)\s*$", block))
    if not matches:
        matches = list(re.finditer(r"(?m)^\s*\[([A-H])\]\s*(.+?)\s*$", block))
    for m in matches:
        label = m.group(1).upper()
        value = m.group(2).strip()
        # The page puts one option per line, so this is intentionally conservative.
        options[label] = value
    return options, answer


def bundle_options(q: dict) -> dict[str, str]:
    value = q.get("options")
    if isinstance(value, dict):
        return {str(k).upper(): str(v) for k, v in value.items()}
    return {}


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    report = {"note": "Read-only canonical option/order discrepancy finder.", "years": {}}

    for year in range(2010, 2027):
        url = f"https://www.guojiya.cn/exam/neem_{year}_1"
        item = {"url": url, "parsed_questions": 0, "diffs": [], "errors": []}
        try:
            text = visible_text(fetch(url))
            blocks = source_blocks(text)
            item["parsed_questions"] = len(blocks)
        except Exception as exc:  # noqa: BLE001
            item["errors"].append(f"fetch/parse: {type(exc).__name__}: {exc}")
            report["years"][str(year)] = item
            continue

        bundle = json.loads((IMPORT_DIR / f"{year}-eng1.json").read_text(encoding="utf-8"))
        by_num = {int(q["question_number"]): q for q in bundle["questions"]}

        for qn in range(1, 46):
            block = blocks.get(qn)
            if not block:
                continue
            src_options, src_answer = parse_block(block)
            q = by_num[qn]
            db_options = bundle_options(q)
            diff: dict[str, object] = {"question_number": qn, "q_id": q["q_id"]}
            changed = False

            if src_answer and (q.get("correct_answer") or "").upper() != src_answer:
                diff["answer"] = {"bundle": q.get("correct_answer"), "source": src_answer}
                changed = True

            if src_options:
                option_diffs = {}
                for label, src_text in src_options.items():
                    db_text = db_options.get(label)
                    if norm(db_text) != norm(src_text):
                        option_diffs[label] = {"bundle": db_text, "source": src_text}
                if option_diffs:
                    diff["options"] = option_diffs
                    changed = True

            if changed:
                item["diffs"].append(diff)

        item["diff_count"] = len(item["diffs"])
        report["years"][str(year)] = item
        print(f"{year}: parsed={item['parsed_questions']} diffs={item.get('diff_count', 0)} errors={len(item['errors'])}")

    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
