
import sqlite3
conn = sqlite3.connect('backend/data/static_content.db')
cursor = conn.cursor()
cursor.execute("SELECT q_id, length(passage_text), quote(passage_text), length(image_base64) FROM questions WHERE paper_id='2013-eng1' AND section_type='writing_b'")
rows = cursor.fetchall()
print("q_id | passage_len | quote(passage) | img_len")
for r in rows:
    print(r)
print("done")
conn.close()
