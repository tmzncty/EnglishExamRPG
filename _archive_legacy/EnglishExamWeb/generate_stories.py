"""
Galgame式剧情批量生成器
为每道题目生成详细的、有代入感的猫娘陪伴剧情
包含：角色情绪、详细对话、剧情连贯性
"""

import json
import sqlite3
import time
import requests
from pathlib import Path

# API Configuration
API_KEY = "sk-bKBD5dwJCsaZRgKov0QCRxbOU1KogukIRjLCLx8Mp1NLJwYv"
BASE_URL = "https://api.vectorengine.ai/v1"
MODEL_NAME = "gemini-3-flash-preview"

# Database setup
DB_PATH = "story_content.db"

def init_database():
    """初始化数据库表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS question_stories (
            question_id INTEGER NOT NULL,
            year INTEGER NOT NULL,
            section_name TEXT NOT NULL,
            question_text TEXT,
            correct_story TEXT NOT NULL,
            correct_mood TEXT NOT NULL,
            wrong_story TEXT NOT NULL,
            wrong_mood TEXT NOT NULL,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (question_id, year)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS part_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_name TEXT NOT NULL,
            section_type TEXT NOT NULL,
            year INTEGER NOT NULL,
            high_score_story TEXT NOT NULL,
            high_score_mood TEXT NOT NULL,
            mid_score_story TEXT NOT NULL,
            mid_score_mood TEXT NOT NULL,
            low_score_story TEXT NOT NULL,
            low_score_mood TEXT NOT NULL,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(part_name, year)
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成")

def call_gemini_api(system_prompt, user_prompt, max_tokens=300):
    """调用 Gemini API"""
    try:
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}"
            },
            json={
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.9,
                "max_tokens": max_tokens
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        else:
            print(f"❌ API Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None

def generate_question_story(question, year, section_name, is_correct):
    """生成Galgame式题目剧情"""
    system_prompt = """你是一个专业的 Galgame 编剧，正在为学习游戏编写剧情。

角色设定：Mia - 傲娇猫娘助手
- 外表：粉色双马尾、猫耳、绿色大眼睛
- 性格：外表高冷傲娇，内心温柔关心Master
- 口癖："喵~"、"哼！"、会用各种可爱的颜文字
- 关系：表面上是AI助手，实际上很在意Master的学习进度和心情

剧情要求：
1. **长度**：100-150字，有故事感
2. **情感表达**：要有细腻的情绪描写和动作描写
3. **代入感**：让玩家感受到Mia真的在陪伴他学习
4. **连贯性**：每次反馈都是陪伴故事的一部分
5. **颜文字**：适当使用，增加可爱感
6. **不要重复题目内容**：Master已经做完题了，重点是情感互动

输出格式：
剧情文本|||情绪标签

情绪标签只能是：happy, sad, thinking, angry, normal 之一

示例（答对）：
"哼！这道题居然被你做对了！(๑´ㅂ`๑) Mia还以为你会掉进那个陷阱呢。看来Master每天熬夜刷题还是有效果的嘛...虽、虽然Mia才不会为你高兴！只是觉得...嗯，还不错而已啦！继续保持这个水平，说不定真的能考上研究生喵~ (不过别太骄傲哦！)|||happy"

示例（答错）：
"诶...又错了... (｡•́︿•̀｡) Mia看到Master皱眉的样子，心里也有点难受呢...不过没关系！这种题目本来就很狡猾，连Mia第一次看到时也愣了一下。Master你已经很努力了，Mia都看在眼里的喵~ 我们一起再看一遍解析，下次遇到类似的题目，一定能做对的！加油，Mia会一直陪着你的！(轻轻拍拍Master的肩膀)|||sad"
"""

    question_text = question.get('text', '')[:80]
    correct_answer = question.get('correct_answer', '?')
    section_type = question.get('sectionType', '题目')
    
    if is_correct:
        user_prompt = f"""为以下情况生成Galgame式剧情：

【情况】Master 答对了！
【题目类型】{section_type}
【题目来源】{year}年 {section_name}
【题目片段】{question_text}...

请生成Mia的反应剧情，要有：
- 先是惊讶/高兴的情绪
- 适当的傲娇口吻（"哼！不是因为担心你！"）
- 鼓励继续努力
- 让Master感受到被陪伴的温暖

格式：剧情文本|||情绪标签"""
    else:
        user_prompt = f"""为以下情况生成Galgame式剧情：

【情况】Master 答错了...
【题目类型】{section_type}
【题目来源】{year}年 {section_name}
【题目片段】{question_text}...
【正确答案】{correct_answer}

请生成Mia的反应剧情，要有：
- 安慰和理解（不要责怪）
- 温柔的鼓励
- 承诺会一起克服困难
- 让Master感到不是一个人在战斗

格式：剧情文本|||情绪标签"""
    
    result = call_gemini_api(system_prompt, user_prompt, max_tokens=250)
    if result and '|||' in result:
        return result.split('|||')
    return None

def generate_part_summary(part_name, year, section_type):
    """生成Part完成的Galgame式总结剧情"""
    system_prompt = """你是 Galgame 编剧，需要为完成一个章节（Part）生成总结剧情。

角色：Mia（傲娇猫娘）
场景：Master刚刚完成了一整个Part的题目

要求：
1. **仪式感**：这是一个阶段性的成就，要有庆祝/总结的感觉
2. **情感递进**：根据正确率，Mia的反应要有明显差异
3. **剧情性**：不只是简单的夸奖，要有小故事/小互动
4. **长度**：每段150-200字

需要生成3个版本（对应不同正确率）：

格式：
高分剧情|||high_mood
---
中分剧情|||mid_mood  
---
低分剧情|||low_mood

mood标签：happy, sad, thinking, angry, normal
"""

    user_prompt = f"""为以下Part生成完成总结剧情：

【Part名称】{part_name}
【题目类型】{section_type}  
【年份】{year}年

请生成3个版本：

1. **高分版本**（正确率≥80%）
   - Mia非常高兴，甚至破防了傲娇人设
   - 要有祝贺的仪式感
   - 暗示Master离目标更近了一步

2. **中分版本**（正确率60-80%）
   - Mia认为还不错，鼓励继续
   - 指出进步空间
   - 温柔的陪伴感

3. **低分版本**（正确率<60%）
   - Mia心疼Master，但故作坚强
   - 承诺会帮助他提高
   - 不要气馁，一起加油

用---分隔三段，每段格式：剧情|||mood"""

    result = call_gemini_api(system_prompt, user_prompt, max_tokens=500)
    if result and '---' in result:
        parts = result.split('---')
        if len(parts) >= 3:
            summaries = []
            for part in parts:
                if '|||' in part:
                    summaries.append(part.strip().split('|||'))
            if len(summaries) >= 3:
                return summaries
    return None

def process_json_file(json_path):
    """处理单个JSON文件"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    year = data.get('meta', {}).get('year', 0)
    print(f"\n📚 处理 {year} 年题目...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    question_count = 0
    part_count = 0
    
    for section in data.get('sections', []):
        section_name = section['section_info']['name']
        section_type = section['section_info']['type']
        
        print(f"\n  📖 Section: {section_name}")
        
        # 生成Part总结
        print(f"  🎬 生成Part总结剧情...")
        summaries = generate_part_summary(section_name, year, section_type)
        if summaries and len(summaries) >= 3:
            cursor.execute("""
                INSERT OR REPLACE INTO part_summaries 
                (part_name, section_type, year, high_score_story, high_score_mood, 
                 mid_score_story, mid_score_mood, low_score_story, low_score_mood)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                section_name, section_type, year,
                summaries[0][0], summaries[0][1],  # high
                summaries[1][0], summaries[1][1],  # mid
                summaries[2][0], summaries[2][1]   # low
            ))
            part_count += 1
            print(f"  ✅ Part总结已生成（3个版本）")
            time.sleep(2)
        
        # 处理每道题目
        for question in section.get('questions', []):
            q_id = question.get('id')
            q_text = question.get('text', '')
            
            # 检查是否已存在
            cursor.execute("SELECT question_id FROM question_stories WHERE question_id = ? AND year = ?", (q_id, year))
            if cursor.fetchone():
                print(f"  ⏭️  跳过 #{q_id}")
                continue
            
            # 生成答对剧情
            print(f"  ✍️  生成题目 #{q_id} 答对剧情...")
            correct_result = generate_question_story(question, year, section_name, is_correct=True)
            if not correct_result:
                print(f"  ❌ 题目 #{q_id} 答对剧情失败")
                continue
            
            correct_story, correct_mood = correct_result
            time.sleep(1.5)
            
            # 生成答错剧情
            print(f"  ✍️  生成题目 #{q_id} 答错剧情...")
            wrong_result = generate_question_story(question, year, section_name, is_correct=False)
            if not wrong_result:
                print(f"  ❌ 题目 #{q_id} 答错剧情失败")
                continue
            
            wrong_story, wrong_mood = wrong_result
            
            # 存储到数据库
            cursor.execute("""
                INSERT INTO question_stories 
                (question_id, year, section_name, question_text, correct_story, correct_mood, wrong_story, wrong_mood)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (q_id, year, section_name, q_text, correct_story, correct_mood.strip(), wrong_story, wrong_mood.strip()))
            
            question_count += 1
            print(f"  ✅ 题目 #{q_id} 完成（答对+答错）")
            time.sleep(2)  # API限流
            
            # 每5题提交一次
            if question_count % 5 == 0:
                conn.commit()
                print(f"  💾 已保存 {question_count} 题")
    
    conn.commit()
    conn.close()
    print(f"\n✨ {year}年完成！共 {question_count} 题剧情, {part_count} 个Part总结")

def main():
    """主函数"""
    init_database()
    
    # 获取所有年份的JSON文件
    data_dir = Path("../data")
    if not data_dir.exists():
        data_dir = Path("data")
    
    json_files = sorted(data_dir.glob("*.json"))
    
    print(f"🎮 Galgame剧情批量生成器")
    print(f"📁 找到 {len(json_files)} 个年份文件\n")
    
    for json_file in json_files:
        try:
            process_json_file(json_file)
        except KeyboardInterrupt:
            print("\n\n⏸️  用户中断，已保存当前进度")
            break
        except Exception as e:
            print(f"❌ 处理 {json_file.name} 时出错: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("\n🎉 全部完成！")
    
    # 统计
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM question_stories")
    total_questions = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM part_summaries")
    total_parts = cursor.fetchone()[0]
    conn.close()
    
    print(f"📊 统计: {total_questions} 道题目剧情, {total_parts} 个Part总结")
    print(f"💾 数据库: {DB_PATH}")

if __name__ == "__main__":
    main()
