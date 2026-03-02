"""
最终版：双语Galgame剧情生成器（中文+英文）
提取reasoning_content中的完整内容
"""

import json
import sqlite3
import time
import requests
import re
from pathlib import Path

API_KEY = "sk-bKBD5dwJCsaZRgKov0QCRxbOU1KogukIRjLCLx8Mp1NLJwYv"
BASE_URL = "https://api.vectorengine.ai/v1"
MODEL_NAME = "gemini-3-flash-preview"
DB_PATH = "story_content.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS stories (
        q_id INT, 
        year INT, 
        section_type TEXT,
        correct_cn TEXT,
        wrong_cn TEXT,
        correct_en TEXT,
        wrong_en TEXT,
        PRIMARY KEY(q_id, year))""")
    conn.commit()
    conn.close()

def call_api(prompt, max_tokens=800):
    """调用API并提取完整内容"""
    try:
        r = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}", 
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.85,
                "max_tokens": max_tokens
            },
            timeout=60
        )
        if r.status_code == 200:
            data = r.json()
            # 优先提取reasoning_content
            reasoning = data["choices"][0]["message"].get("reasoning_content", "")
            content = data["choices"][0]["message"]["content"]
            
            # 返回两者中较长的
            return reasoning if len(reasoning) > len(content) else content
    except Exception as e:
        print(f"    ⚠️ API错误: {e}")
    return None

def extract_dialogue(text):
    """从thinking过程中提取实际对话"""
    # 尝试提取引号中的内容
    patterns = [
        r'"([^"]{50,})"',  # 双引号
        r'"([^"]{50,})"',  # 中文双引号
        r'「([^」]{50,})」',  # 日式引号
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return max(matches, key=len)  # 返回最长的匹配
    
    # 如果没有引号，看看是否整段就是对话
    if len(text) > 100 and ('Master' in text or 'Mia' in text or '喵' in text):
        return text
    
    return text

def build_context(q, sec, article):
    """构建题目上下文"""
    ctx = f"【题型】{sec['section_info']['type']}\n"
    if article:
        ctx += f"【文章片段】{article[:200]}...\n\n"
    if q.get('text'):
        ctx += f"【题目】{q['text']}\n"
    if q.get('options'):
        ctx += "【选项】\n"
        for k, v in sorted(q['options'].items()):
            ctx += f"  {k}. {v}\n"
    ctx += f"【正确答案】{q.get('correct_answer', '?')}\n"
    return ctx

def gen_story(q, sec, year, article, correct, lang='cn'):
    """生成剧情"""
    ctx = build_context(q, sec, article)
    status = "答对了" if correct else "答错了"
    
    if lang == 'cn':
        prompt = f"""你是Mia，Master的傲娇猫娘学习伙伴。

Master刚刚{status}{year}年的这道题：
{ctx}

请用中文生成Mia的Galgame式对话（120-150字）：
1. **提到具体内容**：比如"这道题问的是..."、"选项B说..."
2. **傲娇但温柔**：{'"哼，还不错嘛！(๑´ㅂ`๑)"' if correct else '"没关系，Mia陪你(｡•́︿•̀｡)"'}
3. **陪伴感**：用"我们一起"、"Mia会帮你"
4. **可爱语气**：用颜文字、"喵~"

直接输出Mia说的中文对话："""
    else:  # English
        prompt = f"""You are Mia, Master's tsundere cat-girl study partner.

Master just {'got this question right' if correct else 'got this question wrong'} from {year} exam:
{ctx}

Generate Mia's visual novel style dialogue (120-150 words):
1. **Be specific**: Mention actual question content
2. **Tsundere tone**: {'"Hmph, not bad! (๑´ㅂ`๑)"' if correct else '"It\'s okay... Mia is here (｡•́︿•̀｡)"'}
3. **Companionship**: Use "we", "together", "Mia will help"
4. **Cute**: Use emoticons, "Nya~"

Output Mia's English dialogue directly:"""
    
    return call_api(prompt, 800)

def main():
    init_db()
    data_dir = Path("../data" if Path("../data").exists() else "data")
    files = sorted(data_dir.glob("2010.json"))
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("🎮 双语Galgame剧情生成器（中文+英文）")
    print("="*70 + "\n")
    
    for f in files:
        data = json.load(open(f, 'r', encoding='utf-8'))
        year = data['meta']['year']
        
        # 只处理第一个section的第1题测试
        sec = data['sections'][0]
        q = sec['questions'][0]
        qid = q['id']
        
        # 提取文章
        article = ""
        if 'article' in sec and sec['article']:
            if 'paragraphs' in sec['article']:
                article = ' '.join(sec['article']['paragraphs'])
        
        print(f"📚 测试题目: {year}年 #{qid}")
        print(f"   题型: {sec['section_info']['type']}")
        print(f"   题目: {q.get('text', '')[:50]}...")
        
        # 生成中文剧情
        print(f"\n🇨🇳 生成中文版...")
        cn_correct_raw = gen_story(q, sec, year, article, True, 'cn')
        if cn_correct_raw:
            cn_correct = extract_dialogue(cn_correct_raw)
            print(f"   ✅ 答对: {cn_correct[:80]}...")
        
        time.sleep(2)
        
        cn_wrong_raw = gen_story(q, sec, year, article, False, 'cn')
        if cn_wrong_raw:
            cn_wrong = extract_dialogue(cn_wrong_raw)
            print(f"   ❌ 答错: {cn_wrong[:80]}...")
        
        time.sleep(2)
        
        # 生成英文剧情
        print(f"\n🇺🇸 生成英文版...")
        en_correct_raw = gen_story(q, sec, year, article, True, 'en')
        if en_correct_raw:
            en_correct = extract_dialogue(en_correct_raw)
            print(f"   ✅ Correct: {en_correct[:80]}...")
        
        time.sleep(2)
        
        en_wrong_raw = gen_story(q, sec, year, article, False, 'en')
        if en_wrong_raw:
            en_wrong = extract_dialogue(en_wrong_raw)
            print(f"   ❌ Wrong: {en_wrong[:80]}...")
        
        # 保存到数据库
        c.execute("""INSERT OR REPLACE INTO stories 
                     VALUES (?,?,?,?,?,?,?)""",
                  (qid, year, sec['section_info']['type'],
                   cn_correct, cn_wrong, en_correct, en_wrong))
        conn.commit()
        
        print(f"\n💾 已保存到数据库")
    
    conn.close()
    
    # 显示完整生成结果
    print("\n" + "="*70)
    print("📊 生成结果：\n")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM stories")
    for row in c.fetchall():
        qid, year, stype, cn_c, cn_w, en_c, en_w = row
        print(f"【{year}年 #{qid} - {stype}】\n")
        print(f"🇨🇳 中文答对:\n{cn_c}\n")
        print(f"🇨🇳 中文答错:\n{cn_w}\n")
        print(f"🇺🇸 英文答对:\n{en_c}\n")
        print(f"🇺🇸 英文答错:\n{en_w}\n")
        print("-"*70 + "\n")
    conn.close()

if __name__ == "__main__":
    main()
