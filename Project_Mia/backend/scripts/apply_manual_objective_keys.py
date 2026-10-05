#!/usr/bin/env python3
"""Quarantine the rejected single-table objective-key pass.

A first manual transcription copied answer letters from one public answer table. During
review of 2020 Q1/Q3, we discovered that this source had reordered option labels while
keeping the semantic answer text, so applying its letters to the corpus was unsafe.

This script deliberately restores the affected questions to the pre-pass baseline and
marks legacy bundles as `in-review`. It must run before any independently verified
question-level corrections. Nothing here is claimed as final truth; it only removes the
known-bad single-source mutation so review can proceed from the prior corpus state.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_IMPORT = REPO_ROOT / "Project_Mia/backend/data_import"

# Values recorded immediately before the rejected single-table pass.
BASELINE_ANSWERS = {
    2010: {32: "B", 38: "A", 40: "B"},
    2012: {37: "A"},
    2013: {27: "A"},
    2016: {27: "A"},
    2020: {
        1: "C", 3: "B", 4: "D", 5: "A", 6: "B", 7: "D", 8: "A", 9: "D",
        10: "C", 11: "C", 12: "A", 13: "B", 14: "D", 15: "C", 16: "B",
        17: "A", 18: "B", 19: "C", 20: "D",
    },
    2021: {16: "C"},
    2023: {18: "D", 19: "A", 20: "D", 41: "F", 42: "D", 43: "B"},
    2025: {28: "D", 37: "A", 42: "B", 43: "H", 45: "A"},
}


def main() -> int:
    changed_total = 0
    for year in range(2010, 2027):
        path = DATA_IMPORT / f"{year}-eng1.json"
        bundle = json.loads(path.read_text(encoding="utf-8"))
        questions = {int(q["question_number"]): q for q in bundle["questions"]}
        changed = 0

        for qn, answer in BASELINE_ANSWERS.get(year, {}).items():
            if questions[qn].get("correct_answer") != answer:
                print(f"restore {year} Q{qn}: {questions[qn].get('correct_answer')} -> {answer}")
                questions[qn]["correct_answer"] = answer
                changed += 1

        if year != 2026 and bundle.get("review_status") != "in-review":
            bundle["review_status"] = "in-review"
            changed += 1

        provenance = bundle.setdefault("provenance", {})
        review = provenance.setdefault("manual_review", {})
        rejected = {
            "status": "single-answer-table-pass-rejected",
            "reason": (
                "Answer-letter labels in the first public table were not stable against "
                "canonical option ordering (confirmed at 2020 Q1/Q3); question text, option "
                "mapping and answer must be verified together with independent sources."
            ),
        }
        if review.get("rejected_pass") != rejected:
            review["rejected_pass"] = rejected
            review.pop("objective_keys", None)
            review.pop("answer_table", None)
            review.pop("section_sources", None)
            changed += 1

        if changed:
            path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            changed_total += changed
        print(f"{year}: quarantine changes {changed}")

    print(f"Quarantine changes: {changed_total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
