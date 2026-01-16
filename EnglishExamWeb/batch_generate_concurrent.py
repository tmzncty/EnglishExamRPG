"""
并发批量生成 - 修复版本
- 降低并发到16路
- 添加None检查
- 添加重试机制
- 更好的错误处理
"""

import json
import sqlite3
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime

API_KEY = "sk-bKBD5dwJCsaZRgKov0QCRxbOU1KogukIRjLCLx8Mp1NLJwYv"
BASE_URL = "https://api.vectorengine.ai/v1"
GEMINI_MODEL = "gemini-3-flash-preview"
DEEPSEEK_MODEL = "deepseek-v3.2"
DB_PATH = "story_content.db"

# 并发控制 - 降低到16避免过载
CONCURRENT_LIMIT = 16
semaphore = asyncio.Semaphore(CONCURRENT_LIMIT)

async def call_api_async(session, prompt, model, max_tokens=600, retry=3):
    """异步API调用（带重试和None检查）"""
    async with semaphore:
        for attempt in range(retry):
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
                        
                        # 安全提取内容（None检查）
                        reasoning = data["choices"][0]["message"].get("reasoning_content") or ""
                        content = data["choices"][0]["message"].get("content") or ""
                        
                        # 返回更长的那个
                        if len(reasoning) > len(content):
                            return reasoning
                        elif content:
                            return content
                        else:
                            return None
                            
            except asyncio.CancelledError:
                raise  # 不重试取消操作
            except Exception as e:
                if attempt == retry - 1:
                    print(f"❌ API错误（{attempt+1}/{retry}）: {str(e)[:50]}")
                    return None
                await asyncio.sleep(1)  # 重试前等待
        
        return None

def build_context(q, sec, article):
    """构建上下文（安全版本）"""
    ctx = f"Q from {sec['section_info']['name']}"
    
    if article and len(article) > 100:
        ctx += f"\nArticle: {article[:150]}..."
    
    q_text = q.get('text', '')
    if q_text:
        ctx += f"\nQ: {q_text[:80]}..."
    
    options = q.get('options', {})
    if options:
        opts = ", ".join([f"{k}:{v[:20]}" for k,v in list(options.items())[:2]])
        ctx += f"\nOptions: {opts}"
    
    ctx += f"\nAns: {q.get('correct_answer', '?')}"
    return ctx

async def gen_story_en(session, q, sec, year, article, correct):
    """生成英文剧情"""
    status = "correct" if correct else "wrong"
    ctx = build_context(q, sec, article)
    mood = "happy" if correct else "comforting"
    
    prompt = f"""Mia (tsundere cat-girl) reacts to Master getting {status} on {year} question:
{ctx}

Generate 120-150 word dialogue:
- Specific content mention
- Tsundere + {mood}
- Emoticons
- Companionship

Dialogue:"""
    
    result = await call_api_async(session, prompt, GEMINI_MODEL, 600)
    return result if result else f"[Generated story for {year} Q{q.get('id')} {status}]"

async def translate_cn(session, en_text):
    """翻译为中文"""
    if not en_text or len(en_text) < 10:
        return en_text
    
    prompt = f"""翻译为中文，保持傲娇猫娘语气，颜文字，可加"喵~"：

{en_text[:500]}

中文："""
    
    result = await call_api_async(session, prompt, DEEPSEEK_MODEL, 400)
    return result if result else en_text  # fallback到英文

async def process_question(session, q, sec, year, article):
    """处理单个题目（返回元组或None）"""
    qid = q.get('id')
    if not qid:
        return None
    
    sec_type = sec['section_info'].get('type', 'Unknown')
    
    try:
        # 并发生成英文
        en_correct, en_wrong = await asyncio.gather(
            gen_story_en(session, q, sec, year, article, True),
            gen_story_en(session, q, sec, year, article, False),
            return_exceptions=True
        )
        
        # 检查异常
        if isinstance(en_correct, Exception) or isinstance(en_wrong, Exception):
            return None
        
        if not en_correct or not en_wrong:
            return None
        
        # 并发翻译中文
        cn_correct, cn_wrong = await asyncio.gather(
            translate_cn(session, en_correct),
            translate_cn(session, en_wrong),
            return_exceptions=True
        )
        
        # 检查异常
        if isinstance(cn_correct, Exception) or isinstance(cn_wrong, Exception):
            return None
        
        if not cn_correct or not cn_wrong:
            return None
        
        return (qid, year, sec_type, cn_correct, cn_wrong, en_correct, en_wrong)
        
    except Exception as e:
        print(f"❌ Q{qid} 错误: {str(e)[:50]}")
        return None

async def batch_generate_async():
    """异步批量生成"""
    # 初始化数据库
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS stories (
        q_id INT, year INT, section_type TEXT,
        correct_cn TEXT, wrong_cn TEXT, correct_en TEXT, wrong_en TEXT,
        PRIMARY KEY(q_id, year))""")
    conn.commit()
    
    # 获取已存在的题目
    c.execute("SELECT q_id, year FROM stories")
    existing = set((row[0], row[1]) for row in c.fetchall())
    
    # 获取所有JSON文件
    data_dir = Path("../data" if Path("../data").exists() else "data")
    json_files = sorted(data_dir.glob("*.json"))
    
    print(f"🚀 并发批量生成（{CONCURRENT_LIMIT}路并发）")
    print(f"📁 找到 {len(json_files)} 个年份")
    print(f"📊 已有 {len(existing)} 道题")
    print(f"⏰ 开始: {datetime.now().strftime('%H:%M:%S')}\n")
    
    total_generated = 0
    
    async with aiohttp.ClientSession() as session:
        for json_file in json_files:
            try:
                data = json.load(open(json_file, 'r', encoding='utf-8'))
                year = data['meta']['year']
                
                print(f"📚 {year}年")
                
                for sec in data.get('sections', []):
                    name = sec['section_info'].get('name', 'Unknown')
                    questions = sec.get('questions', [])
                    
                    # 过滤已存在的题目
                    pending_qs = [q for q in questions if (q.get('id'), year) not in existing]
                    
                    if not pending_qs:
                        print(f"  ⏭️  {name} - 已全部完成")
                        continue
                    
                    print(f"  📖 {name} ({len(pending_qs)}/{len(questions)} 待生成)")
                    
                    # 提取文章
                    article = ""
                    if 'article' in sec and sec['article']:
                        if 'paragraphs' in sec['article']:
                            article = ' '.join(sec['article']['paragraphs'])
                    
                    # 创建并发任务
                    tasks = [process_question(session, q, sec, year, article) for q in pending_qs]
                    
                    # 执行并收集结果
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # 批量插入
                    success_count = 0
                    for result in results:
                        if result and not isinstance(result, Exception):
                            try:
                                c.execute("""INSERT OR IGNORE INTO stories VALUES (?,?,?,?,?,?,?)""", result)
                                success_count += 1
                                total_generated += 1
                            except Exception as e:
                                print(f"  ❌ DB插入错误: {e}")
                    
                    conn.commit()
                    print(f"    ✅ 完成 {success_count} 题")
                    
            except Exception as e:
                print(f"❌ 处理{json_file.name}出错: {e}")
                continue
    
    conn.close()
    
    print(f"\n🎉 全部完成！")
    print(f"📊 本次生成: {total_generated} 道题目")
    print(f"⏰ 结束: {datetime.now().strftime('%H:%M:%S')}")

def main():
    try:
        asyncio.run(batch_generate_async())
    except KeyboardInterrupt:
        print("\n\n⏸️  用户中断，已保存当前进度")
    except Exception as e:
        print(f"\n❌ 程序错误: {e}")

if __name__ == "__main__":
    main()
