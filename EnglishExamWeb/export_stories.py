"""
导出故事数据库为JSON
供前端直接加载，无需API调用
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = "story_content.db"
OUTPUT_PATH = "data/stories.json"

def export_stories_to_json():
    """导出数据库中的所有剧情为JSON"""
    
    if not Path(DB_PATH).exists():
        print("❌ 数据库不存在！请先运行生成脚本。")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 获取所有剧情
    c.execute("""
        SELECT q_id, year, section_type, 
               correct_cn, correct_en, wrong_cn, wrong_en 
        FROM stories 
        ORDER BY year, q_id
    """)
    
    rows = c.fetchall()
    conn.close()
    
    # 构建JSON结构
    stories = {}
    for row in rows:
        q_id, year, section_type, cn_correct, en_correct, cn_wrong, en_wrong = row
        
        # 使用 "year_qid" 作为key
        key = f"{year}_{q_id}"
        stories[key] = {
            "year": year,
            "question_id": q_id,
            "section_type": section_type,
            "correct": {
                "cn": cn_correct,
                "en": en_correct
            },
            "wrong": {
                "cn": cn_wrong,
                "en": en_wrong
            }
        }
    
    # 创建输出目录
    output_file = Path(OUTPUT_PATH)
    output_file.parent.mkdir(exist_ok=True)
    
    # 写入JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(stories, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 成功导出 {len(stories)} 道题目的剧情")
    print(f"📁 输出文件: {OUTPUT_PATH}")
    print(f"📊 文件大小: {output_file.stat().st_size / 1024:.2f} KB")
    
    # 显示示例
    if stories:
        first_key = list(stories.keys())[0]
        print(f"\n📝 示例数据 ({first_key}):")
        print(json.dumps(stories[first_key], ensure_ascii=False, indent=2)[:300] + "...")

if __name__ == "__main__":
    export_stories_to_json()
