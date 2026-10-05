#!/usr/bin/env python3
"""Compare the corpus against a manually transcribed 2010–2026 objective answer key.

Unlike crosscheck_public_exam_sources.py, this file does not parse letters from HTML.
The sequences below were entered by hand after reading the year-by-year answer tables,
and 2012 was assembled from its four Reading A pages plus Part B. This makes the
report useful for distinguishing real corpus errors from HTML-parser false positives.

This script is audit-only: it never changes the database or bundles.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB = REPO_ROOT / "Project_Mia/backend/data/static_content.db"
DEFAULT_OUT = REPO_ROOT / "Project_Mia/backend/manual_review/manual-objective-key-audit.json"

KEY_STRINGS = {
    2010: "ABCBCBDACDCAADBADCBDBADABCDCBABDACCADCBDBFDGA",
    2011: "CDBBABADCABCDCBDADACCBDBABDCACDCBAACDADBBDACF",
    2012: "BABDCBDBABACCDACACDDDBACDCDADAABBDCCDBCACDAFG",
    2013: "ABCDBDAADCACBCBCDDBAABDCCDDCBDBADBABCACDEFDGA",
    2014: "DABACDCDBCAABDCBABCDACDAADDABBBCCBDADCCBCFGDB",
    2015: "DBCACADABDBABDCCBDCADCBACCADDDBCDCAABACBCEGBA",
    2016: "ADCACBDBDADCBBCABDBAADDCDADCACBCDABABBCBCFDEG",
    2017: "BADCBDBCADABDBCACACDACDDCBABADDBDCACCABDFEACG",
    2018: "CADBDBCDBABBACDACBACDCADBDABCABCDDBBAACDEGABD",
    2019: "CCBDABDCADABDCBDAABCADBCBDAACBCDBACCDCBAEDGBA",
    2020: "BADBCDBCCAACDBADCADBCBDBCDACADACDCBCABCBCEGAD",
    2021: "CDABAACBACDBCDDBDAACCBCDDBDCCAABDAACBBDAGCEBD",
    2022: "ACDCDBCBADCBACBDAADBACDDBCBCDABAABCDADBCFCADG",
    2023: "CADCCABBADDCCBABDADACBACDADBCDACAADBCABDBFDCG",
    2024: "DCBABCADADACCDCBDCBADDABAABDCBBCCDAABADBECFGB",
    2025: "BCBCBADAADDADCDCBBBACAABABDCACDAACDCBBCDDGBEF",
    2026: "ADBCBCADADDDCABCCBBACDABBDABCAAACBDDCBDCBEAGD",
}

SOURCE_NOTES = {
    "primary_table": "https://english-exam.lazynote.cn/kaoyan/paper/{year}-english-one/",
    "2012_part_a_1": "https://english-exam.lazynote.cn/kaoyan/sections/2012-english-one/section2-part-a-1/",
    "2012_part_a_2": "https://english-exam.lazynote.cn/kaoyan/sections/2012-english-one/section2-part-a-2/",
    "2012_part_a_3": "https://english-exam.lazynote.cn/kaoyan/sections/2012-english-one/section2-part-a-3/",
    "2012_part_a_4": "https://english-exam.lazynote.cn/kaoyan/sections/2012-english-one/section2-part-a-4/",
    "2012_part_b": "https://english-exam.lazynote.cn/kaoyan/sections/2012-english-one/section2-part-b/",
}

OBJECTIVE_NUMBERS = list(range(1, 46))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    for year, sequence in KEY_STRINGS.items():
        if len(sequence) != 45:
            raise SystemExit(f"{year}: manual key has {len(sequence)} letters, expected 45")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    report = {
        "note": "Human-transcribed objective key comparison; audit-only.",
        "sources": SOURCE_NOTES,
        "years": {},
    }
    try:
        for year in range(2010, 2027):
            paper_id = f"{year}-eng1"
            rows = conn.execute(
                """
                SELECT q_id, question_number, correct_answer
                FROM questions
                WHERE paper_id=? AND question_number BETWEEN 1 AND 45
                ORDER BY question_number
                """,
                (paper_id,),
            ).fetchall()
            actual_numbers = [row["question_number"] for row in rows]
            if actual_numbers != OBJECTIVE_NUMBERS:
                raise SystemExit(f"{paper_id}: objective numbers are not exactly 1..45")

            expected = KEY_STRINGS[year]
            mismatches = []
            for row, letter in zip(rows, expected):
                actual = (row["correct_answer"] or "").strip().upper()
                if actual != letter:
                    mismatches.append(
                        {
                            "q_id": row["q_id"],
                            "question_number": row["question_number"],
                            "db": actual,
                            "manual": letter,
                        }
                    )
            report["years"][str(year)] = {
                "manual_key": expected,
                "mismatches": mismatches,
                "mismatch_count": len(mismatches),
            }
            print(f"{year}: {len(mismatches)} mismatch(es)")
            for mismatch in mismatches:
                print(
                    f"  Q{mismatch['question_number']}: "
                    f"db={mismatch['db']} manual={mismatch['manual']}"
                )
    finally:
        conn.close()

    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
