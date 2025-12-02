#!/usr/bin/env python3
"""
批量从所有年份的 DOCX 文件中提取图片，并添加到对应的 JSON 文件中
图片用于 Writing Part B (Q52) 题目
"""

import zipfile
import os
import json
import base64
import shutil

DOCX_DIR = 'DOCX'
OUTPUT_DIR = 'extracted_images'
YEARS = range(2010, 2026)

def extract_images_from_docx(year):
    """从指定年份的 DOCX 提取图片"""
    docx_file = os.path.join(DOCX_DIR, f'{year}年考研英语一真题.docx')
    
    if not os.path.exists(docx_file):
        print(f"  ❌ {year}: DOCX 文件不存在")
        return None
    
    with zipfile.ZipFile(docx_file, 'r') as z:
        # 获取所有有效图片（大于 1KB）
        images = []
        for f in z.namelist():
            if f.startswith('word/media/') and not f.endswith('/'):
                info = z.getinfo(f)
                if info.file_size > 1024:  # 忽略小于 1KB 的占位图
                    images.append((f, info.file_size))
        
        if not images:
            print(f"  ⚠️ {year}: 没有找到有效图片")
            return None
        
        # 取最大的图片（通常是作文题的图）
        images.sort(key=lambda x: x[1], reverse=True)
        main_image = images[0][0]
        
        # 提取图片
        year_dir = os.path.join(OUTPUT_DIR, str(year))
        os.makedirs(year_dir, exist_ok=True)
        
        # 读取图片数据
        img_data = z.read(main_image)
        ext = os.path.splitext(main_image)[1].lower()
        
        # 保存到文件
        output_path = os.path.join(year_dir, f'writing_b{ext}')
        with open(output_path, 'wb') as f:
            f.write(img_data)
        
        print(f"  ✅ {year}: 提取了 {main_image} ({len(img_data) // 1024} KB)")
        
        return {
            'path': output_path,
            'data': img_data,
            'ext': ext
        }

def add_image_to_json(year, img_info):
    """将图片以 Base64 格式添加到 JSON 文件中已存在的 Q52"""
    full_json = f'{year}_full.json'
    if not os.path.exists(full_json):
        print(f"  ⚠️ {year}: {full_json} 不存在，跳过")
        return False
    
    # 读取 JSON
    with open(full_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 转换图片为 Base64
    b64_data = base64.b64encode(img_info['data']).decode('utf-8')
    ext = img_info['ext'].replace('.', '')
    mime_type = 'image/jpeg' if ext in ['jpg', 'jpeg'] else f'image/{ext}'
    image_data_uri = f'data:{mime_type};base64,{b64_data}'
    
    # 查找 Q52 并添加图片
    found = False
    for section in data.get('sections', []):
        section_info = section.get('section_info', {})
        if 'Writing' in section_info.get('type', ''):
            for q in section.get('questions', []):
                if q.get('id') == 52:
                    # 检查是否已有图片
                    if q.get('image'):
                        print(f"  ℹ️ {year}: Q52 已有图片，跳过")
                        return True
                    q['image'] = image_data_uri
                    found = True
                    print(f"  ✅ {year}: 已添加图片到 Q52")
                    break
        if found:
            break
    
    if not found:
        print(f"  ⚠️ {year}: 未找到 Q52 题目")
        return False
    
    # 保存 JSON
    with open(full_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return True

def sync_to_web(year):
    """同步到 Web 目录"""
    src = f'{year}_full.json'
    dst = f'EnglishExamWeb/data/{year}.json'
    
    if os.path.exists(src):
        shutil.copy(src, dst)
        print(f"  ✅ {year}: 已同步到 Web 目录")
        return True
    return False

def main():
    print("=" * 50)
    print("批量提取图片并添加到 JSON")
    print("=" * 50)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    results = {
        'extracted': [],
        'added': [],
        'synced': [],
        'skipped': [],
        'failed': []
    }
    
    for year in YEARS:
        print(f"\n处理 {year} 年...")
        
        # 1. 提取图片
        img_info = extract_images_from_docx(year)
        if img_info:
            results['extracted'].append(year)
            
            # 2. 添加到 JSON
            if add_image_to_json(year, img_info):
                results['added'].append(year)
                
                # 3. 同步到 Web
                if sync_to_web(year):
                    results['synced'].append(year)
        else:
            results['failed'].append(year)
    
    # 打印总结
    print("\n" + "=" * 50)
    print("处理完成！")
    print("=" * 50)
    print(f"✅ 提取图片: {len(results['extracted'])} 年")
    print(f"✅ 添加/更新JSON: {len(results['added'])} 年")
    print(f"✅ 同步到Web: {len(results['synced'])} 年")
    if results['failed']:
        print(f"❌ 失败: {results['failed']}")

if __name__ == '__main__':
    main()
