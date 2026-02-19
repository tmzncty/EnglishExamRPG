"""
patch_2017_q46.py - Add missing Translation Q46 for 2017
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(r"F:\sanity_check_avg\Project_Mia\backend\data\static_content.db")

conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

# Check if exists
cursor.execute("SELECT q_id FROM questions WHERE q_id='2017-eng1-translation-q46'")
if cursor.fetchone():
    print("Q46 already exists, skipping.")
    conn.close()
    exit(0)

# Get passage_text and tags from sibling question
cursor.execute("SELECT passage_text, section_name, tags FROM questions WHERE q_id='2017-eng1-translation-q47'")
row = cursor.fetchone()
passage_text = row[0] if row else None
section_name = row[1] if row else "Section II Part C"
tags = row[2] if row else None

q46_text = (
    "The growth of the use of English as the world\u2019s primary language "
    "for international communication has obviously been continuing for "
    "several decades."
)
q46_answer = "\u82f1\u8bed\u4f5c\u4e3a\u4e16\u754c\u4e3b\u8981\u56fd\u9645\u4ea4\u6d41\u8bed\u8a00\u7684\u4f7f\u7528\u589e\u957f\uff0c\u663e\u7136\u5df2\u7ecf\u6301\u7eed\u4e86\u6570\u5341\u5e74\u3002"
q46_analysis = (
    "\u672c\u53e5\u4e3b\u8bed\u662f The growth of the use of English as the world\u2019s "
    "primary language for international communication\uff0c\u8c13\u8bed\u662f "
    "has been continuing\uff0c\u65f6\u95f4\u72b6\u8bed\u662f for several decades\u3002"
)
q46_prompt = (
    "Okay, this is a warm-up sentence. The key is the long subject - "
    "it is talking about the GROWTH of English USE, not just English "
    "itself. Do not overthink it!"
)

cursor.execute("""
    INSERT INTO questions (
        q_id, paper_id, q_type, section_type, section_name, group_name,
        question_number, passage_text, content, options_json, correct_answer,
        image_base64, official_analysis, ai_persona_prompt, answer_key,
        difficulty, score, tags
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    "2017-eng1-translation-q46",
    "2017-eng1",
    "translation",
    "translation",
    section_name,
    None,
    46,
    passage_text,
    q46_text,
    None,
    None,
    None,
    q46_analysis,
    q46_prompt,
    q46_answer,
    3,
    2.0,
    tags,
))

conn.commit()
conn.close()
print("Successfully added 2017 Translation Q46!")
