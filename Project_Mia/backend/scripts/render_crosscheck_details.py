#!/usr/bin/env python3
"""Render public-crosscheck.json into a human review queue."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "Project_Mia/backend/manual_review/public-crosscheck.json"
DST = ROOT / "Project_Mia/backend/manual_review/review-queue.md"


def main() -> int:
    report = json.loads(SRC.read_text(encoding="utf-8"))
    lines = [
        "# Manual review queue",
        "",
        "> Every item below requires a human decision; fingerprints are hints, not verdicts.",
        "",
    ]
    for year, item in report["years"].items():
        categories = [
            ("Question text", item.get("missing_question_text", [])),
            ("Options", item.get("missing_options", [])),
            ("Full-paper passage fingerprint", item.get("passage_fingerprint_misses", [])),
            ("Independent Reading A fingerprint", item.get("independent_reading_fingerprint_misses", [])),
            ("Fetch errors", item.get("fetch_errors", [])),
        ]
        if not any(values for _, values in categories):
            continue
        lines += [f"## {year}", "", f"- Full paper: {item['paper_url']}", f"- Reading cross-check: {item['reading_crosscheck_url']}", ""]
        for heading, values in categories:
            if not values:
                continue
            lines += [f"### {heading}", ""]
            for value in values:
                if isinstance(value, str):
                    lines.append(f"- `{value}`")
                else:
                    qid = value.get("q_id")
                    if qid:
                        lines.append(f"- `{qid}` option `{value.get('option')}`: {value.get('text')}")
                    else:
                        lines.append(f"- `{json.dumps(value, ensure_ascii=False)}`")
            lines.append("")
    DST.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {DST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
