"""
重新生成有问题的题目
只处理 regenerate_list.txt 中的题目
"""

import json
import sqlite3
import asyncio
import aiohttp
from pathlib import Path

API_KEY = "sk-bKBD5dwJCsaZRgKov0QCRxbOU1KogukIRjLCLx8Mp1NLJwYv"
BASE_URL = "https://api.vectorengine.ai/v1"
GEMINI_MODEL = "gemini-3-flash-preview"
DEEPSEEK_MODEL = "deepseek-v3.2"
DB_PATH = "story_content.db"

async def call_api(session, prompt, model, max_tokens=600):
    """API调用"""
    try:
        async with session.post(
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
            timeout=aiohttp.ClientTimeout(total=90)
        ) as response:
            if response.status == 200:
                data = await response.json()
                reasoning = data["choices"][0]["message"].get("reasoning_content") or ""
                content = data["choices"][0]["message"].get("content") or ""
                return reasoning if len(reasoning) > len(content) else content
    except Exception as e:
        print(f"❌ API错误: {e}")
    return None

def build_context(q, sec, article):
    """构建上下文"""
    ctx = f"Q from {sec['section_info']['name']}"
    if article and len(article) > 100:
        ctx += f"\nArticle: {article[:200]}..."
    if q.get('text'):
        ctx += f"\nQ: {q['text'][:100]}..."
    if q.get('options'):
        opts = ", ".join([f"{k}:{v[:30]}" for k,v in list(q['options'].items())[:2]])
        ctx += f"\nOptions: {opts}"
    ctx += f"\nAns: {q.get('correct_answer', '?')}"
    return ctx

async def regenerate_question(session, year, qid):
    """重新生成单个题目"""
    
    # 找到题目数据
    data_dir = Path("../data" if Path("../data").exists() else "data")
    json_file = data_dir / f"{year}.json"
    
    if not json_file.exists():
        print(f"❌ {year}.json 不存在")
        return None
    
    data = json.load(open(json_file, 'r', encoding='utf-8'))
    
    # 查找对应题目
    question = None
    section = None
    article = ""
    
    for sec in data.get('sections', []):
        for q in sec.get('questions', []):
            if q.get('id') == qid:
                question = q
                section = sec
                
                # 提取文章
                if 'article' in sec and sec['article']:
                    if 'paragraphs' in sec['article']:
                        article = ' '.join(sec['article']['paragraphs'])
                break
        if question:
            break
    
    if not question or not section:
        print(f"❌ {year}年 Q{qid} 未找到")
        return None
    
    print(f"🔄 重新生成 {year}年 Q{qid}")
    
    # 生成所有4个版本
    ctx = build_context(question, section, article)
    
    # 英文 - 答对
    prompt_en_correct = f"""Mia (tsundere cat-girl) reacts to Master getting correct on {year} question:
{ctx}

Generate 120-150 word dialogue with specific content, tsundere + happy tone, emoticons, companionship feel.

Dialogue:"""
    
    en_correct = await call_api(session, prompt_en_correct, GEMINI_MODEL, 600)
    if not en_correct or len(en_correct) < 50:
        print(f"  ❌ 英文答对太短或失败")
        return None
    await asyncio.sleep(1)
    
    # 英文 - 答错
    prompt_en_wrong = f"""Mia (tsundere cat-girl) reacts to Master getting wrong on {year} question:
{ctx}

Generate 120-150 word dialogue with specific content, tsundere + comforting tone, emoticons, companionship feel.

Dialogue:"""
    
    en_wrong = await call_api(session, prompt_en_wrong, GEMINI_MODEL, 600)
    if not en_wrong or len(en_wrong) < 50:
        print(f"  ❌ 英文答错太短或失败")
        return None
    await asyncio.sleep(1)
    
    # 中文翻译
    cn_correct = await call_api(session, f"翻译为中文，保持傲娇猫娘语气，颜文字，可加\"喵~\"：\n\n{en_correct}\n\n中文：", DEEPSEEK_MODEL, 400)
    if not cn_correct:
        cn_correct = en_correct
    await asyncio.sleep(1)
    
    cn_wrong = await call_api(session, f"翻译为中文，保持傲娇猫娘语气，颜文字，可加\"喵~\"：\n\n{en_wrong}\n\n中文：", DEEPSEEK_MODEL, 400)
    if not cn_wrong:
        cn_wrong = en_wrong
    
    sec_type = section['section_info'].get('type', 'Unknown')
    
    print(f"  ✅ 生成完成")
    print(f"    中文答对: {len(cn_correct)}字")
    print(f"    中文答错: {len(cn_wrong)}字")
    print(f"    英文答对: {len(en_correct)}字")
    print(f"    英文答错: {len(en_wrong)}字")
    
    return (qid, year, sec_type, cn_correct, cn_wrong, en_correct, en_wrong)

async def main():
    """主函数"""
    
    # 读取需要重新生成的列表
    regen_file = Path("regenerate_list.txt")
    if not regen_file.exists():
        print("❌ regenerate_list.txt 不存在")
        return
    
    tasks_to_regen = []
    with open(regen_file, 'r') as f:
        for line in f:
            if line.strip():
                year, qid = line.strip().split(',')
                tasks_to_regen.append((int(year), int(qid)))
    
    print(f"📋 需要重新生成 {len(tasks_to_regen)} 道题目\n")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    async with aiohttp.ClientSession() as session:
        for year, qid in tasks_to_regen:
            result = await regenerate_question(session, year, qid)
            
            if result:
                # 更新数据库
                c.execute("""UPDATE stories 
                           SET correct_cn=?, wrong_cn=?, correct_en=?, wrong_en=?
                           WHERE q_id=? AND year=?""",
                         (result[3], result[4], result[5], result[6], qid, year))
                conn.commit()
                print(f"  💾 已更新数据库\n")
            else:
                print(f"  ❌ 重新生成失败\n")
    
    conn.close()
    print("🎉 重新生成完成！")

if __name__ == "__main__":
    asyncio.run(main())
