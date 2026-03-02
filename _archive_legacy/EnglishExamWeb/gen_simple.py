"""
简化版剧情生成器 - 直接生成文本，不要求特定格式
"""

import json
import sqlite3
import time
import requests
from pathlib import Path

API_KEY = "sk-bKBD5dwJCsaZRgKov0QCRxbOU1KogukIRjLCLx8Mp1NLJwYv"
BASE_URL = "https://api.vectorengine.ai/v1"
MODEL_NAME = "gemini-3-flash-preview"
DB_PATH = "story_content.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS stories (
        q_id INT, year INT, correct_text TEXT, wrong_text TEXT, 
        PRIMARY KEY(q_id, year))""")
    conn.commit()
    conn.close()

def call_api(prompt, max_tokens=200):
    try:
        r = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.9,
                "max_tokens": max_tokens
            },
            timeout=30
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Error: {e}")
    return None

def gen_story(q, year, sec, correct):
    status = "答对了" if correct else "答错了"
    prompt = f"""你是Mia，傲娇猫娘。Master刚{status}{year}年{sec}的一道题。

请用100-120字生成Mia的Galgame式对话：
- {"开心夸奖，但要傲娇口吻" if correct else "温柔安慰，鼓励继续"}
- 用颜文字和"喵~"
- 有代入感，像真的在陪伴他学习
- 不要复述题目内容

直接回复对话，不要其他格式："""
    
    return call_api(prompt, 200)

def main():
    init_db()
    data_dir = Path("../data" if Path("../data").exists() else "data")
    files = sorted(data_dir.glob("2010.json"))  # 先测试一个文件
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    for f in files:
        data = json.load(open(f, 'r', encoding='utf-8'))
        year = data['meta']['year']
        print(f"\n📚 {year}年")
        
        for sec in data['sections'][:1]:  # 先测试一个section
            name = sec['section_info']['name']
            print(f"  📖 {name}")
            
            for q in sec['questions'][:3]:  # 先测试3题
                qid = q['id']
                c.execute("SELECT q_id FROM stories WHERE q_id=? AND year=?", (qid, year))
                if c.fetchone():
                    print(f"  ⏭️  #{qid}")
                    continue
                
                print(f"  ✍️  #{qid} 生成中...")
                
                correct_story = gen_story(q, year, name, True)
                if not correct_story:
                    print(f"  ❌ #{qid} 失败")
                    continue
                
                time.sleep(1.5)
                wrong_story = gen_story(q, year, name, False)
                if not wrong_story:
                    print(f"  ❌ #{qid} 失败")
                    continue
                
                c.execute("INSERT INTO stories VALUES (?,?,?,?)", 
                         (qid, year, correct_story, wrong_story))
                conn.commit()
                
                print(f"  ✅ #{qid} 完成")
                print(f"     答对: {correct_story[:40]}...")
                print(f"     答错: {wrong_story[:40]}...")
                time.sleep(2)
    
    conn.close()
    print("\n🎉 完成！")

if __name__ == "__main__":
    main()
