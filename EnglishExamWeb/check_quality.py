"""
检查数据库中的故事质量
找出有问题的记录（空、太短、placeholder等）
"""

import sqlite3
from pathlib import Path

DB_PATH = "story_content.db"

def check_story_quality():
    """检查故事质量并报告问题"""
    
    if not Path(DB_PATH).exists():
        print("❌ 数据库不存在")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 获取所有记录
    c.execute("""
        SELECT q_id, year, section_type, 
               correct_cn, correct_en, wrong_cn, wrong_en 
        FROM stories 
        ORDER BY year, q_id
    """)
    
    rows = c.fetchall()
    conn.close()
    
    print(f"📊 数据库中共 {len(rows)} 道题目\n")
    
    # 检查问题
    problems = {
        'empty_cn_correct': [],
        'empty_cn_wrong': [],
        'empty_en_correct': [],
        'empty_en_wrong': [],
        'short_cn_correct': [],  # <50字
        'short_cn_wrong': [],
        'short_en_correct': [],  # <50字
        'short_en_wrong': [],
        'placeholder': [],  # 包含 [Generated story]
    }
    
    for row in rows:
        q_id, year, sec_type, cn_c, cn_w, en_c, en_w = row
        
        # 检查空值
        if not cn_c or cn_c.strip() == '':
            problems['empty_cn_correct'].append((year, q_id))
        if not cn_w or cn_w.strip() == '':
            problems['empty_cn_wrong'].append((year, q_id))
        if not en_c or en_c.strip() == '':
            problems['empty_en_correct'].append((year, q_id))
        if not en_w or en_w.strip() == '':
            problems['empty_en_wrong'].append((year, q_id))
        
        # 检查太短（<50字）
        if cn_c and len(cn_c) < 50:
            problems['short_cn_correct'].append((year, q_id, len(cn_c)))
        if cn_w and len(cn_w) < 50:
            problems['short_cn_wrong'].append((year, q_id, len(cn_w)))
        if en_c and len(en_c) < 50:
            problems['short_en_correct'].append((year, q_id, len(en_c)))
        if en_w and len(en_w) < 50:
            problems['short_en_wrong'].append((year, q_id, len(en_w)))
        
        # 检查placeholder
        if any('[Generated story' in str(text) for text in [cn_c, cn_w, en_c, en_w] if text):
            problems['placeholder'].append((year, q_id))
    
    # 报告结果
    print("="*70)
    print("问题统计：\n")
    
    total_issues = 0
    problematic_questions = set()
    
    for issue_type, items in problems.items():
        if items:
            count = len(items)
            total_issues += count
            print(f"❌ {issue_type}: {count} 个")
            
            # 记录有问题的题目
            for item in items:
                problematic_questions.add((item[0], item[1]))  # (year, q_id)
    
    print(f"\n📊 总问题数: {total_issues}")
    print(f"📋 有问题的题目数: {len(problematic_questions)}")
    
    if problematic_questions:
        print(f"\n需要重新生成的题目列表:")
        for year, qid in sorted(problematic_questions):
            print(f"  {year}年 Q{qid}")
        
        # 保存到文件
        with open('regenerate_list.txt', 'w') as f:
            for year, qid in sorted(problematic_questions):
                f.write(f"{year},{qid}\n")
        print(f"\n✅ 已保存到 regenerate_list.txt")
    else:
        print(f"\n✅ 所有故事质量良好！")
    
    # 显示几个样本
    print(f"\n" + "="*70)
    print("随机样本（前3题）:\n")
    
    good_samples = [r for r in rows if (r[1], r[0]) not in problematic_questions][:3]
    for row in good_samples:
        q_id, year, sec_type, cn_c, cn_w, en_c, en_w = row
        print(f"【{year}年 Q{q_id} - {sec_type}】")
        print(f"中文答对 ({len(cn_c)}字): {cn_c[:80]}...")
        print(f"中文答错 ({len(cn_w)}字): {cn_w[:80]}...")
        print()

if __name__ == "__main__":
    check_story_quality()
