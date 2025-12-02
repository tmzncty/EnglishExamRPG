import json

# 检查 2010.json 中是否包含图片
with open('EnglishExamWeb/data/2010.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 查找第52题
q52 = None
for section in data['sections']:
    for question in section['questions']:
        if question['id'] == 52:
            q52 = question
            break

if q52:
    print("✓ 找到第52题")
    print(f"题目类型: {'图片作文题' if 'image' in q52 else '普通题'}")
    
    if 'image' in q52:
        image_length = len(q52['image'])
        print(f"图片数据长度: {image_length:,} 字符")
        print(f"图片数据前缀: {q52['image'][:80]}...")
        
        # 检查是否为有效的 Data URL
        if q52['image'].startswith('data:image/'):
            print("✓ 图片格式正确 (Data URL)")
        else:
            print("✗ 图片格式错误")
    else:
        print("✗ 缺少图片数据")
    
    print(f"\n题目文本: {q52['text'][:100]}...")
else:
    print("✗ 未找到第52题")
