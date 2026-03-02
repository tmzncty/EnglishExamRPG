"""
上下文完整版剧情生成器
提供完整题目信息，让Mia真正参与Master的答题过程
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
        q_id INT, 
        year INT, 
        section_type TEXT,
        correct_text TEXT, 
        wrong_text TEXT, 
        PRIMARY KEY(q_id, year))""")
    conn.commit()
    conn.close()

def call_api(prompt, max_tokens=500):
    """调用API并提取reasoning_content"""
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
            timeout=45
        )
        if r.status_code == 200:
            data = r.json()
            # 优先使用reasoning_content（thinking模型的真实输出）
            reasoning = data["choices"][0]["message"].get("reasoning_content", "")
            if reasoning and len(reasoning) > 50:
                # 从reasoning中提取实际对话（通常在引号中）
                if '"' in reasoning or '"' in reasoning or '「' in reasoning:
                    return reasoning
                return reasoning
            # fallback到content
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"    ⚠️ API错误: {e}")
    return None

def build_question_context(question, section, article_text=""):
    """构建完整的题目上下文"""
    context = f"""【题型】{section['section_info']['type']}
【章节】{section['section_info']['name']}
"""
    
    # 添加文章内容（如果有）
    if article_text:
        preview = article_text[:300] + "..." if len(article_text) > 300 else article_text
        context += f"【文章片段】{preview}\n"
    
    # 添加题目本身
    if question.get('text'):
        context += f"【题目】{question['text']}\n"
    
    # 添加选项
    if question.get('options'):
        context += "【选项】\n"
        for key, val in sorted(question['options'].items()):
            context += f"  {key}. {val}\n"
    
    # 添加正确答案
    context += f"【正确答案】{question.get('correct_answer', '?')}\n"
    
    return context

def gen_story(question, section, year, article_text, correct):
    """生成上下文完整的Galgame剧情"""
    
    qcontext = build_question_context(question, section, article_text)
    section_type = section['section_info']['type']
    section_name = section['section_info']['name']
    
    # 根据题型调整prompt风格
    if 'Use of English' in section_type or 'Cloze' in section_type:
        type_hint = "完形填空题很考验对文章的整体理解和语感"
    elif 'Reading' in section_type or 'Text' in section_type:
        type_hint = "阅读理解需要仔细分析文章，找到对应段落"
    elif 'Translation' in section_type:
        type_hint = "翻译题要注意中英文表达习惯的差异"
    elif 'Writing' in section_type:
        type_hint = "写作题要注意结构和逻辑"
    else:
        type_hint = "这类题目需要扎实的基础"
    
    status = "答对了" if correct else "答错了"
    
    prompt = f"""你是Mia，Master的傲娇猫娘学习伙伴。你和Master正在一起做{year}年考研英语真题。

刚才Master{status}了下面这道题：

{qcontext}

【场景设定】
Mia坐在Master身边，和他一起看着题目。你们刚刚一起读完了文章/题目，Master选了答案。
{type_hint}。

【你的任务】
生成Mia的Galgame式对话（120-150字），要求：

1. **具体性**：提到文章/题目中的具体内容（比如"这篇文章讲的是..."、"选项B提到了..."）
   - 让Master感觉你真的和他一起在看题
   
2. **情感真实**：
   {'- 开心但要傲娇："哼，这种程度还不错嘛...（其实心里很高兴）"' if correct else '- 温柔安慰："没关系，Mia第一次看到这个词组时也...（真心的鼓励）"'}
   - 用颜文字表达情绪：(๑´ㅂ`๑)、(｡•́︿•̀｡)、( ｀ε´ ) 等
   
3. **陪伴感**：
   - 用"我们一起..."、"Mia陪你..."这样的表达
   - 像真的在攻略一样，有共同成长的感觉
   
4. **语气自然**：
   - 口语化，不要太书面
   - 适当用"喵~"
   - 傲娇但温柔

直接输出Mia说的话，不要其他格式："""
    
    result = call_api(prompt, max_tokens=600)
    return result

def extract_article_text(section):
    """提取文章文本"""
    if 'article' in section and section['article']:
        if 'paragraphs' in section['article']:
            return ' '.join(section['article']['paragraphs'])
        elif isinstance(section['article'], str):
            return section['article']
    return ""

def main():
    init_db()
    data_dir = Path("../data" if Path("../data").exists() else "data")
    
    # 测试：先处理一个年份的一个section的2道题
    files = sorted(data_dir.glob("2010.json"))
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("🎮 上下文完整版Galgame剧情生成器")
    print("=" * 70)
    
    for f in files:
        data = json.load(open(f, 'r', encoding='utf-8'))
        year = data['meta']['year']
        print(f"\n📚 {year}年")
        
        # 只处理第一个section用于测试
        for sec in data['sections'][:1]:
            name = sec['section_info']['name']
            sec_type = sec['section_info']['type']
            article = extract_article_text(sec)
            
            print(f"\n  📖 {name} ({sec_type})")
            if article:
                print(f"  📄 文章长度: {len(article)} 字符")
            
            # 只处理前2题测试
            for q in sec['questions'][:2]:
                qid = q['id']
                
                c.execute("SELECT q_id FROM stories WHERE q_id=? AND year=?", (qid, year))
                if c.fetchone():
                    print(f"  ⏭️  #{qid} 已存在")
                    continue
                
                print(f"\n  🎬 题目 #{qid} 生成中...")
                print(f"     题目文本: {q.get('text', '无')[:40]}...")
                
                # 生成答对剧情
                print(f"     ✍️  生成答对剧情...")
                correct_story = gen_story(q, sec, year, article, True)
                
                if not correct_story or len(correct_story) < 30:
                    print(f"     ❌ 答对剧情生成失败或太短")
                    continue
                
                # 从reasoning中提取实际对话
                if '"' in correct_story:
                    parts = correct_story.split('"')
                    if len(parts) >= 2:
                        correct_story = parts[1]
                elif '「' in correct_story:
                    parts = correct_story.split('「')
                    if len(parts) >= 2:
                        correct_story = parts[1].split('」')[0]
                
                print(f"     ✅ 答对: {correct_story[:60]}...")
                time.sleep(2)
                
                # 生成答错剧情
                print(f"     ✍️  生成答错剧情...")
                wrong_story = gen_story(q, sec, year, article, False)
                
                if not wrong_story or len(wrong_story) < 30:
                    print(f"     ❌ 答错剧情生成失败或太短")
                    continue
                
                # 从reasoning中提取实际对话
                if '"' in wrong_story:
                    parts = wrong_story.split('"')
                    if len(parts) >= 2:
                        wrong_story = parts[1]
                elif '「' in wrong_story:
                    parts = wrong_story.split('「')
                    if len(parts) >= 2:
                        wrong_story = parts[1].split('」')[0]
                
                print(f"     ✅ 答错: {wrong_story[:60]}...")
                
                # 存储
                c.execute(
                    "INSERT OR REPLACE INTO stories VALUES (?,?,?,?,?)", 
                    (qid, year, sec_type, correct_story, wrong_story)
                )
                conn.commit()
                
                print(f"     💾 已保存到数据库")
                time.sleep(3)  # API限流
    
    conn.close()
    
    # 查看生成结果
    print("\n" + "=" * 70)
    print("📊 生成完成！查看结果：\n")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT q_id, year, section_type, correct_text, wrong_text FROM stories ORDER BY year, q_id")
    for row in c.fetchall():
        qid, year, stype, correct, wrong = row
        print(f"【{year}年 #{qid} - {stype}】")
        print(f"✅ 答对: {correct[:80]}...")
        print(f"❌ 答错: {wrong[:80]}...")
        print()
    conn.close()

if __name__ == "__main__":
    main()
