#!/usr/bin/env python3
"""Replace overlong legacy writing samples with exam-length study models.

These are reference/model answers for practice, not official scoring keys. The
script only writes rows whose answer actually differs, keeping repeated CI runs
byte-stable when no repair is needed.
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB = REPO_ROOT / "Project_Mia/backend/data/static_content.db"

SAMPLES = {
    "2013-eng1-writing_a-q51": """Dear Professor Smith,

On behalf of the Student Union, I am writing to invite you to serve as a judge for our English Speech Contest. The event will be held in the university auditorium from 2:00 to 5:00 p.m. this Friday. Contestants will give prepared speeches and answer questions from the judges. We would greatly value your expertise in English and your experience in public speaking. Your comments would also help the students improve their communication skills.

We sincerely hope you can join us. Please let me know if you are available.

Yours sincerely,
Li Ming""",
    "2014-eng1-writing_a-q51": """Dear Mr. President,

I am writing to suggest several ways to improve students’ physical condition. First, the university could provide more varied sports courses and encourage every student to exercise regularly. Second, sports facilities should stay open longer so that students can use them after classes. In addition, campus-wide activities such as running clubs, ball games and fitness challenges could make exercise more attractive and social. Short lectures on sleep, diet and injury prevention would also help students develop healthier habits.

I hope these suggestions will be considered and help create a more active campus.

Yours sincerely,
Li Ming""",
    "2016-eng1-writing_a-q51": """Notice

Welcome to our university library. New international students can enter and borrow books with their student ID cards. The library provides printed books, journals, electronic databases, computers and quiet study areas. It is open from 8:00 a.m. to 10:00 p.m. on weekdays and from 9:00 a.m. to 5:00 p.m. at weekends. If you need help finding materials or using online resources, please ask the staff at the information desk. A short library tour will also be offered this Friday afternoon.

We hope the library will support both your study and campus life.

Li Ming""",
    "2017-eng1-writing_a-q51": """Dear Professor Cook,

Welcome to our city. I would like to recommend three places for your first visit. The Forbidden City is ideal if you are interested in Chinese history and traditional architecture. The Great Wall at Mutianyu offers magnificent mountain views and is usually less crowded than some other sections. You may also enjoy walking through the hutongs, where old courtyards, small restaurants and local shops provide a closer look at everyday life.

These attractions show different sides of the city, from imperial history to natural scenery and local culture. I hope you enjoy exploring them.

Yours sincerely,
Li Ming""",
    "2019-eng1-writing_a-q51": """Dear Volunteer,

Thank you for your interest in our “Aiding Rural Primary School” project. The program will last two weeks during the summer vacation. Volunteers will assist local teachers with English classes, reading activities and sports, and may also organize simple cultural-exchange events. The school is about 100 kilometers from our university, and transportation will be arranged. Accommodation and meals will be provided at the school.

Before departure, we will hold an orientation covering teaching tasks, safety and local customs. Please bring basic personal necessities and any teaching materials you find useful. Feel free to contact me if you need further information.

Yours,
Li Ming""",
    "2024-eng1-writing_a-q51": """Dear Paul,

I’m glad to help with your oral report. I suggest choosing one ancient Chinese scientist, such as Zhang Heng or Zu Chongzhi, rather than introducing too many people. You can organize the report around three points: the scientist’s background, major achievements and influence on later generations. A short story about the discovery or invention would make the opening more interesting, while a picture or simple diagram could help explain difficult ideas. Finally, practice the report several times so that you can speak clearly and keep within the time limit.

I hope these suggestions are useful. Good luck with your presentation!

Yours,
Li Ming""",
    "2025-eng1-writing_a-q51": """Dear Library Staff,

I am writing to suggest several books for our university library. I hope you could purchase more recent works on artificial intelligence and data science, because students in many majors now need a basic understanding of these fields. I would also recommend adding accessible books on Chinese history and traditional culture, which would be useful to both domestic and international students. Finally, a few practical guides to academic writing and research methods would help students prepare papers and projects.

These books would broaden the collection and meet a wide range of study needs. Thank you for considering my suggestions.

Yours sincerely,
Li Ming""",
    "2017-eng1-writing_b-q52": """The two pictures present a sharp contrast in attitudes toward reading. In the first, a man sits beside a large pile of books and proudly says that he owns many of them. In the second, another man is absorbed in reading a single book. The message is clear: possessing books is not the same as gaining knowledge from them.

Today, buying books has become easier than ever, and many people enjoy collecting attractive volumes or sharing reading lists online. Yet books have value only when we actually open them, think about their ideas and apply what we learn. A small number of books read carefully can be far more useful than a huge collection left untouched.

For students, this contrast is especially meaningful. Instead of pursuing the appearance of being well read, we should develop a steady reading habit, take notes, question the author and connect new knowledge with our own experience. Genuine learning depends not on how many books stand on a shelf, but on how deeply we engage with them.""",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    writes = 0
    try:
        for q_id, answer in SAMPLES.items():
            row = conn.execute(
                "SELECT answer_key FROM questions WHERE q_id=?", (q_id,)
            ).fetchone()
            if row is None:
                raise SystemExit(f"required writing question missing: {q_id}")
            if row[0] == answer:
                continue
            conn.execute(
                "UPDATE questions SET answer_key=? WHERE q_id=?",
                (answer, q_id),
            )
            writes += 1

        if writes:
            conn.commit()
        print(f"Updated writing reference samples; writes: {writes}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
