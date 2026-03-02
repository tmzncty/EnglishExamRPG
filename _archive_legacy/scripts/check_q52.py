#!/usr/bin/env python3
"""检查每年的 Q52 题目结构"""

import json
import os

for year in range(2010, 2026):
    json_file = f'{year}_full.json'
    if not os.path.exists(json_file):
        print(f'{year}: 文件不存在')
        continue
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 查找 Writing sections
    writing_sections = []
    for s in data.get('sections', []):
        section_info = s.get('section_info', {})
        if 'Writing' in section_info.get('type', ''):
            writing_sections.append(s)
    
    # 查找 Q52
    q52_found = False
    has_image = False
    for s in writing_sections:
        for q in s.get('questions', []):
            if q.get('id') == 52:
                q52_found = True
                has_image = 'image' in q and q['image']
                break
    
    status = '✅' if q52_found else '❌'
    img_status = '🖼️' if has_image else '⚠️ 无图'
    print(f'{year}: {len(writing_sections)} writing sections, Q52: {status} {img_status if q52_found else ""}')
