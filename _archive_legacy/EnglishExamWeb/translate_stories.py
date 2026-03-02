"""
使用 DeepSeek-V3.2 翻译剧情
将英文Galgame剧情翻译为中文，保持角色人设和颜文字
"""

import sqlite3
import requests
import json
import time

# DeepSeek API 配置（通过 VectorEngine）
API_KEY = "sk-bKBD5dwJCsaZRgKov0QCRxbOU1KogukIRjLCLx8Mp1NLJwYv"
BASE_URL = "https://api.vectorengine.ai/v1"
DEEPSEEK_MODEL = "deepseek-v3.2"
DB_PATH = "story_content.db"

def translate_with_deepseek(english_text):
    """使用 DeepSeek-V3.2 翻译"""
    
    prompt = f"""请将以下Galgame风格的英文对话翻译成中文。

要求：
1. 保持傲娇猫娘Mia的人设（外冷内热、关心但嘴硬）
2. 保留所有颜文字和emoticons（如 (๑´ㅂ\`๑)、(｡•́︿•̀｡) 等）
3. 保持口语化、自然的中文表达
4. 适当加入"喵~"等可爱语气词
5. 不要改变原文的情感和语气

原文：
{english_text}

请直接输出翻译后的中文对话："""

    try:
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,  # 翻译用低温度保证准确性
                "max_tokens": 800
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        else:
            print(f"❌ API错误: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 翻译失败: {e}")
        return None

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("🌐 使用 DeepSeek-V3.2 翻译英文剧情为中文")
    print("="*70 + "\n")
    
    # 获取所有需要翻译的内容
    c.execute("SELECT q_id, year, section_type, correct_en, wrong_en FROM stories")
    rows = c.fetchall()
    
    print(f"📊 找到 {len(rows)} 道题目需要翻译\n")
    
    for row in rows:
        qid, year, stype, en_correct, en_wrong = row
        
        print(f"📖 翻译题目 #{qid} ({year}年 - {stype})")
        
        # 翻译答对剧情
        print(f"   ✍️  翻译答对剧情...")
        print(f"   原文: {en_correct[:60]}...")
        
        cn_correct = translate_with_deepseek(en_correct)
        if cn_correct:
            print(f"   ✅ 译文: {cn_correct[:60]}...")
        else:
            print(f"   ❌ 翻译失败")
            continue
        
        time.sleep(2)  # API限流
        
        # 翻译答错剧情
        print(f"   ✍️  翻译答错剧情...")
        print(f"   原文: {en_wrong[:60]}...")
        
        cn_wrong = translate_with_deepseek(en_wrong)
        if cn_wrong:
            print(f"   ✅ 译文: {cn_wrong[:60]}...")
        else:
            print(f"   ❌ 翻译失败")
            continue
        
        # 更新数据库
        c.execute("""UPDATE stories 
                     SET correct_cn = ?, wrong_cn = ? 
                     WHERE q_id = ? AND year = ?""",
                  (cn_correct, cn_wrong, qid, year))
        conn.commit()
        
        print(f"   💾 已保存\n")
        time.sleep(2)
    
    conn.close()
    
    # 显示最终结果
    print("\n" + "="*70)
    print("📊 翻译完成！查看结果：\n")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM stories")
    
    for row in c.fetchall():
        qid, year, stype, cn_c, cn_w, en_c, en_w = row
        
        print(f"【{year}年 #{qid} - {stype}】\n")
        
        print(f"🇨🇳 中文答对:")
        print(f"{cn_c}\n")
        
        print(f"🇨🇳 中文答错:")
        print(f"{cn_w}\n")
        
        print(f"🇺🇸 英文答对:")
        print(f"{en_c}\n")
        
        print(f"🇺🇸 英文答错:")
        print(f"{en_w}\n")
        
        print("-"*70 + "\n")
    
    conn.close()
    
    print("✨ 完成！现在所有剧情都有中英文双语版本了！")

if __name__ == "__main__":
    main()
