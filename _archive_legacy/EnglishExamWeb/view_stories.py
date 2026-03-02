"""
查看已生成的剧情内容
"""
import sqlite3

conn = sqlite3.connect("story_content.db")
c = conn.cursor()

c.execute("SELECT q_id, year, correct_text, wrong_text FROM stories")
rows = c.fetchall()

print(f"📊 数据库中共有 {len(rows)} 道题目的剧情\n")
print("="*80)

for row in rows:
    qid, year, correct, wrong = row
    print(f"\n【题目 #{qid} - {year}年】")
    print(f"\n✅ 答对剧情：")
    print(f"{correct}\n")
    print(f"❌ 答错剧情：")
    print(f"{wrong}\n")
    print("-"*80)

conn.close()
