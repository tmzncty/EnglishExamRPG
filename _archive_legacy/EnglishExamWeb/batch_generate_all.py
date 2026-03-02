"""
批量生成所有年份的剧情
运行这个脚本来预生成所有题目的双语剧情
"""

import json
import sqlite3
import time
import requests
from pathlib import Path

API_KEY = "sk-bKBD5dwJCsaZRgKov0QCRxbOU1KogukIRjLCLx8Mp1NLJwYv"
BASE_URL = "https://api.vectorengine.ai/v1"
GEMINI_MODEL = "gemini-3-flash-preview"
DEEPSEEK_MODEL = "deepseek-v3.2"

DB_PATH = "story_content.db"

def call_api(prompt, model, max_tokens=600):
    """调用API"""
    try:
        r = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.85,
                "max_tokens": max_tokens
            },
            timeout=60
        )
        
        if r.status_code == 200:
            data = r.json()
            # 优先使用reasoning_content（thinking模型）
            reasoning = data["choices"][0]["message"].get("reasoning_content", "")
            content = data["choices"][0]["message"]["content"]
            return reasoning if len(reasoning) > len(content) else content
    except Exception as e:
        print(f"❌ API错误: {e}")
    return None

def gen_story_en(q, sec, year, article, correct):
    """生成英文剧情"""
    status = "got correct" if correct else "got wrong"
    
    # 构建上下文
    ctx = f"Question from {year} {sec['section_info']['name']}"
    if article:
        ctx += f"\nArticle: {article[:200]}..."
    if q.get('text'):
        ctx += f"\nQuestion: {q['text']}"
    if q.get('options'):
        ctx += f"\nOptions: " + ", ".join([f"{k}:{v}" for k,v in list(q['options'].items())[:2]])
    ctx += f"\nCorrect answer: {q.get('correct_answer', '?')}"
    
    mood_hint = "happy, praise" if correct else "comforting, encouraging"
    
    prompt = f"""You are Mia, a tsundere cat-girl study partner.

Master just {status} this question:
{ctx}

Generate Mia's visual novel dialogue (120-150 words):
- Mention specific content from the question
- Tsundere tone ({mood_hint})
- Use emoticons
- Make it feel like real companionship

Output dialogue directly:"""
    
    return call_api(prompt, GEMINI_MODEL, 600)

def translate_to_cn(en_text):
    """翻译为中文"""
    prompt = f"""将以下Galgame风格对话翻译为中文。

要求：
- 保持傲娇猫娘语气
- 保留颜文字
- 自然口语化
- 可适当加"喵~"

原文：
{en_text}

直接输出中文翻译："""
    
    return call_api(prompt, DEEPSEEK_MODEL, 400)

def batch_generate():
    """批量生成"""
    # 初始化数据库
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS stories (
        q_id INT, year INT, section_type TEXT,
        correct_cn TEXT, wrong_cn TEXT, correct_en TEXT, wrong_en TEXT,
        PRIMARY KEY(q_id, year))""")
    conn.commit()
    
    # 获取所有JSON文件
    data_dir = Path("../data" if Path("../data").exists() else "data")
    json_files = sorted(data_dir.glob("*.json"))
    
    print(f"🚀 批量生成剧情")
    print(f"📁 找到 {len(json_files)} 个年份\n")
    
    total_generated = 0
    
    for json_file in json_files:
        data = json.load(open(json_file, 'r', encoding='utf-8'))
        year = data['meta']['year']
        
        print(f"\n📚 {year}年")
        
        for sec in data['sections'][:]:  # 处理所有sections
            name = sec['section_info']['name']
            sec_type = sec['section_info']['type']
            
            # 提取文章
            article = ""
            if 'article' in sec and sec['article']:
                if 'paragraphs' in sec['article']:
                    article = ' '.join(sec['article']['paragraphs'])
            
            print(f"  📖 {name}")
            
            for q in sec['questions'][:5]:  # 每个section前5题（防止太长）
                qid = q['id']
                
                # 检查是否已存在
                c.execute("SELECT q_id FROM stories WHERE q_id=? AND year=?", (qid, year))
                if c.fetchone():
                    print(f"    ⏭️  #{qid} 已存在")
                    continue
                
                print(f"    🎬 #{qid} 生成中...")
                
                # 生成英文
                en_correct = gen_story_en(q, sec, year, article, True)
                if not en_correct:
                    continue
                time.sleep(2)
                
                en_wrong = gen_story_en(q, sec, year, article, False)
                if not en_wrong:
                    continue
                time.sleep(2)
                
                # 翻译中文
                cn_correct = translate_to_cn(en_correct)
                if not cn_correct:
                    continue
                time.sleep(2)
                
                cn_wrong = translate_to_cn(en_wrong)
                if not cn_wrong:
                    continue
                
                # 保存
                c.execute("""INSERT INTO stories VALUES (?,?,?,?,?,?,?)""",
                         (qid, year, sec_type, cn_correct, cn_wrong, en_correct, en_wrong))
                conn.commit()
                
                total_generated += 1
                print(f"    ✅ #{qid} 完成 (总计: {total_generated})")
                time.sleep(3)
    
    conn.close()
    print(f"\n🎉 完成！共生成 {total_generated} 道题目")

if __name__ == "__main__":
    batch_generate()
