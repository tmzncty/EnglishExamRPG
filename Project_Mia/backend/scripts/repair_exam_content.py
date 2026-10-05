#!/usr/bin/env python3
"""Apply deterministic, write-idempotent repairs to legacy English I content.

Older papers were imported from OCR-heavy sources before curated bundles existed.
Repairs here are narrow and asserted. If the database already contains the desired
values, this script performs no UPDATE at all, keeping the SQLite file byte-stable
across repeated CI runs.

Reference essays added below are study/model answers, not official scoring keys.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB = REPO_ROOT / "Project_Mia/backend/data/static_content.db"

TEXT1_2025 = """The grammar school boy from Stratford-upon-Avon has landed a scholarly punch after groundbreaking research showed that Shakespeare does benefit children's literacy and emotional development. But only if you act him out.

A study found that a “rehearsal room” approach to teaching Shakespeare broadened children's vocabulary and the complexity of their writing as well as their emotional literacy. “The research shows that the way actors work makes a big difference to the way children use language and also how they think about themselves,” Jacqui O'Hanlon of the Royal Shakespeare Company (RSC), which commissioned the study, said.

The randomised control trial involved hundreds of year 5 pupils—aged nine and ten—at 45 state primary schools that had not been “previously exposed to RSC pedagogy”. They were split into target and control groups and asked to write, for example, a message in a bottle as Ferdinand after the shipwreck in The Tempest. The target group was given a 30-minute drama-based activity to accompany the passage.

The peer-reviewed results showed that the target group of pupils drew on a wider vocabulary, used words “classed as more sophisticated or rarer”, and wrote at greater length. They also “appear to be more comfortable writing in role … while [control] pupils imagine how they themselves would react to being shipwrecked, [target] children put themselves in the shoes of a literary character and express that character's emotion”.

The Time to Act study also found that while control pupils relied on “desert island clichés” such as palm trees, target pupils were “more expansive [giving] a broader picture of the sky, the sea and the atmospheric conditions”.

O'Hanlon said she had been most surprised by the “emotional literacy that was evident in the [target] children's writing” and that they were “more resilient in their writing, more hopeful”. She added: “The emotional understanding was very evident and it is probably related to the [rehearsal room process] where you are used to trying to imagine your way through. They were comfortable in describing different emotional states and part of what you do in drama is put yourself in different shoes.” The study showed the importance of embedding arts in education, she said.

But could the results be replicated with any old dramatist? O'Hanlon said more research would be needed but suggested that Shakespeare's use of 20,000 words, compared with the everyday 2,000 words, gave a “massive expansion of language into children's lives”, which was combined with children “using their whole bodies to bring words to life”."""

QUESTIONS_2025 = {
    21: (
        'The “rehearsal room” approach requires pupils to',
        {
            "A": "rewrite the lines from Shakespeare.",
            "B": "watch RSC actors’ performances.",
            "C": "play the roles in Shakespeare.",
            "D": "study drama under RSC artists.",
        },
    ),
    22: (
        "The study divided the pupils into two groups to find whether",
        {
            "A": "the change in instruction enhances learning outcomes.",
            "B": "expanding vocabulary helps develop reading fluency.",
            "C": "emotion affects understanding of sophisticated works.",
            "D": "the classroom activity stimulates interest in the arts.",
        },
    ),
    23: (
        'Control pupils’ reliance on “desert island clichés” shows their',
        {
            "A": "weakness in description.",
            "B": "omission of small details.",
            "C": "casual style of writing.",
            "D": "preference for big words.",
        },
    ),
    24: (
        "According to O'Hanlon, what can promote children's emotional literacy?",
        {
            "A": "Writing in an imaginative manner.",
            "B": "Identifying with literary characters.",
            "C": "Drawing inspiration from nature.",
            "D": "Concentrating on real-life situations.",
        },
    ),
    25: (
        "It can be inferred from the last paragraph that",
        {
            "A": "the new teaching method may work best with Shakespeare.",
            "B": "the language of Shakespeare may be formidable for pupils.",
            "C": "other old dramatists may be included in primary education.",
            "D": "pupils may be reluctant to work on other old dramatists.",
        },
    ),
}

WRITING_2025_CONTENT = """Directions:

Write an essay of 160–200 words based on the following drawing. In your essay you should

1) describe the drawing briefly,
2) explain its intended meaning, and
3) give your comments.

You should write neatly on the ANSWER SHEET. (20 points)"""

WRITING_2025_PASSAGE = WRITING_2025_CONTENT + "\n\n近年来全国居民平均每百户年末主要耐用消费品拥有量"

MODEL_2012_Q52 = """As is vividly shown in the drawing, a bottle has fallen to the ground and part of its contents has spilled out. Faced with the same scene, two men react in completely different ways. One complains in despair that everything is gone, while the other feels relieved that some is still left. The contrast reveals how differently people may interpret the same setback.

The picture reminds us that attitude can strongly influence our response to difficulties. A negative mindset tends to magnify losses and make us overlook what remains, whereas an optimistic outlook helps us recognize available resources and possible solutions. Optimism does not mean denying problems. Rather, it means accepting reality while still looking for a constructive way forward.

In study, work and daily life, setbacks are unavoidable. When difficulties arise, we should examine them calmly, learn from what has happened and make use of what is still in our hands. A positive and realistic attitude can give us the confidence to recover and continue moving ahead."""

MODEL_2026_Q51 = """Dear Paul,

I'm glad the letters interested you. They were written by ordinary Chinese families over different periods and record everyday experiences, family affection and changes in social life. What makes them especially valuable is that history appears in the voices of real people rather than only in textbooks.

A selection of the letters is currently on public display in a local cultural exhibition, together with photographs and background notes. If you come, I would be happy to visit it with you and explain some of the stories behind the letters.

Yours,
Li Ming"""

MODEL_2026_Q52 = """The charts present a survey of consumers’ attitudes toward eldercare robots. Overall, 39.3% of respondents fully accept such robots and another 32.8% partially accept them, while 27.9% do not. Among the concerns reported, safety ranks first at 46.3%, followed by price at 24.9% and convenience at 10.7%.

These figures suggest that eldercare robots already enjoy considerable public acceptance, probably because they may reduce repetitive care work, provide timely assistance and help older people live more independently. At the same time, the prominence of safety concerns shows that consumers will not embrace the technology simply because it is novel. Reliability, privacy protection and emergency handling are essential when machines work closely with vulnerable users.

Therefore, developers and policymakers should focus first on strict safety standards, transparent testing and affordable pricing. Eldercare robots should also be designed as assistants rather than replacements for human caregivers. If technological efficiency is combined with dependable protection and genuine human care, these robots can become a useful part of an aging society."""

ANALYSIS_2012 = "参考范文（非官方标准答案）。范文完整覆盖图画描述、寓意阐释和个人评论，并满足160–200词要求。"
ANALYSIS_2026_A = "参考范文（非官方标准答案）。回复覆盖来信中的两个核心问题，并保持约100词的邮件体例。"
ANALYSIS_2026_B = "参考范文（非官方标准答案）。范文先准确概括两组数据，再解释公众接受度与安全顾虑，最后提出规范、安全与人机协作建议；正文控制在160–200词。"


def require_question(conn: sqlite3.Connection, q_id: str) -> None:
    row = conn.execute("SELECT 1 FROM questions WHERE q_id=?", (q_id,)).fetchone()
    if row is None:
        raise SystemExit(f"required question not found: {q_id}")


def update_if_different(
    conn: sqlite3.Connection, q_id: str, values: dict[str, Any]
) -> bool:
    """Update only when at least one selected field differs."""
    require_question(conn, q_id)
    fields = list(values)
    row = conn.execute(
        f"SELECT {', '.join(fields)} FROM questions WHERE q_id=?", (q_id,)
    ).fetchone()
    assert row is not None
    if all(row[index] == values[field] for index, field in enumerate(fields)):
        return False

    assignments = ", ".join(f"{field}=?" for field in fields)
    conn.execute(
        f"UPDATE questions SET {assignments} WHERE q_id=?",
        [values[field] for field in fields] + [q_id],
    )
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    writes = 0
    try:
        # 2023 contained a second, unnumbered Writing B placeholder in addition to Q52.
        before = conn.total_changes
        conn.execute("DELETE FROM questions WHERE q_id='2023-eng1-writing-partB'")
        writes += conn.total_changes - before

        # Repair the OCR-heavy 2025 Text 1 transcription and question formatting.
        for number, (content, options) in QUESTIONS_2025.items():
            q_id = f"2025-eng1-reading_a-q{number}"
            canonical_options = json.dumps(
                options, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            writes += int(
                update_if_different(
                    conn,
                    q_id,
                    {
                        "passage_text": TEXT1_2025,
                        "content": content,
                        "options_json": canonical_options,
                    },
                )
            )

        writes += int(
            update_if_different(
                conn,
                "2025-eng1-writing_b-q52",
                {"passage_text": WRITING_2025_PASSAGE, "content": WRITING_2025_CONTENT},
            )
        )
        writes += int(
            update_if_different(
                conn,
                "2012-eng1-writing_b-q52",
                {"answer_key": MODEL_2012_Q52, "official_analysis": ANALYSIS_2012},
            )
        )
        writes += int(
            update_if_different(
                conn,
                "2026-eng1-writing_a-q51",
                {"answer_key": MODEL_2026_Q51, "official_analysis": ANALYSIS_2026_A},
            )
        )
        writes += int(
            update_if_different(
                conn,
                "2026-eng1-writing_b-q52",
                {"answer_key": MODEL_2026_Q52, "official_analysis": ANALYSIS_2026_B},
            )
        )

        if conn.total_changes:
            conn.commit()

        duplicate = conn.execute(
            "SELECT COUNT(*) FROM questions WHERE q_id='2023-eng1-writing-partB'"
        ).fetchone()[0]
        if duplicate != 0:
            raise SystemExit("2023 duplicate Writing B row still exists")

        count_2023 = conn.execute(
            "SELECT COUNT(*) FROM questions WHERE paper_id='2023-eng1'"
        ).fetchone()[0]
        if count_2023 != 52:
            raise SystemExit(f"2023-eng1 should have 52 questions after repair, got {count_2023}")

        print(f"Applied deterministic English I content repairs; writes: {writes}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
