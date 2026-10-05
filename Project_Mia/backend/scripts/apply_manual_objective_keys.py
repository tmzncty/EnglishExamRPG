#!/usr/bin/env python3
"""Write the manually transcribed 2010–2026 objective keys into curated bundles.

This is intentionally data-authoritative for Q1–Q45. The sequences were transcribed
by hand from year-by-year answer tables and independently checked where the automated
HTML parser disagreed. The script does not claim that non-objective content is fully
reviewed; bootstrap drafts advance only to `objective-reviewed` here.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_IMPORT = REPO_ROOT / "Project_Mia/backend/data_import"

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

SOURCES = {
    "answer_table_template": "https://english-exam.lazynote.cn/kaoyan/paper/{year}-english-one/",
    "2012_reading_21_25": "https://english-exam.lazynote.cn/kaoyan/sections/2012-english-one/section2-part-a-1/",
    "2012_reading_26_30": "https://english-exam.lazynote.cn/kaoyan/sections/2012-english-one/section2-part-a-2/",
    "2012_reading_31_35": "https://english-exam.lazynote.cn/kaoyan/sections/2012-english-one/section2-part-a-3/",
    "2012_reading_36_40": "https://english-exam.lazynote.cn/kaoyan/sections/2012-english-one/section2-part-a-4/",
    "2012_reading_41_45": "https://english-exam.lazynote.cn/kaoyan/sections/2012-english-one/section2-part-b/",
}


def main() -> int:
    total_changes = 0
    for year in range(2010, 2027):
        path = DATA_IMPORT / f"{year}-eng1.json"
        bundle = json.loads(path.read_text(encoding="utf-8"))
        sequence = KEY_STRINGS[year]
        if len(sequence) != 45:
            raise SystemExit(f"{year}: expected 45 manual objective answers")

        questions = {int(q["question_number"]): q for q in bundle["questions"]}
        if sorted(questions) != list(range(1, 53)):
            raise SystemExit(f"{year}: bundle question numbers are not exactly 1..52")

        changed = 0
        for qn, expected in zip(range(1, 46), sequence):
            q = questions[qn]
            if q.get("correct_answer") != expected:
                print(f"{year} Q{qn}: {q.get('correct_answer')} -> {expected}")
                q["correct_answer"] = expected
                changed += 1

        provenance = bundle.setdefault("provenance", {})
        audit = provenance.setdefault("manual_review", {})
        desired_audit = {
            "objective_keys": "manually-transcribed-and-cross-checked",
            "answer_table": SOURCES["answer_table_template"].format(year=year),
        }
        if year == 2012:
            desired_audit["section_sources"] = [SOURCES[key] for key in (
                "2012_reading_21_25",
                "2012_reading_26_30",
                "2012_reading_31_35",
                "2012_reading_36_40",
                "2012_reading_41_45",
            )]
        if audit != desired_audit:
            provenance["manual_review"] = desired_audit
            changed += 1

        if bundle.get("review_status") in {None, "bootstrap-unverified"}:
            bundle["review_status"] = "objective-reviewed"
            changed += 1

        if changed:
            path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            total_changes += changed
        print(f"{year}: bundle changes {changed}")

    print(f"Manual objective-key bundle changes: {total_changes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
