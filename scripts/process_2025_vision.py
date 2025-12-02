import os
import json
import time
import docx
import google.generativeai as genai
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置 Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found.")
    exit(1)

genai.configure(api_key=api_key)

def extract_docx_text(file_path):
    """从 DOCX 提取文本"""
    text = ""
    try:
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Error reading DOCX: {e}")
        return None
    return text

def upload_to_gemini(path, mime_type="application/pdf"):
    """上传文件到 Gemini"""
    print(f"Uploading {path}...")
    file = genai.upload_file(path, mime_type=mime_type)
    print(f"Completed upload: {file.uri}")
    
    # 等待文件处理完成
    while file.state.name == "PROCESSING":
        print("Processing file...")
        time.sleep(2)
        file = genai.get_file(file.name)
        
    if file.state.name == "FAILED":
        raise ValueError(f"File processing failed: {file.state.name}")
        
    print(f"File is ready: {file.name}")
    return file

def clean_json_string(json_str):
    """清理 JSON 字符串"""
    if not json_str: return None
    json_str = json_str.strip()
    if json_str.startswith("```json"): json_str = json_str[7:]
    if json_str.startswith("```"): json_str = json_str[3:]
    if json_str.endswith("```"): json_str = json_str[:-3]
    return json_str.strip()

def generate_section_with_vision(model, docx_text, pdf_file, task):
    """使用视觉模型生成 JSON"""
    print(f"Processing {task['name']} ({task['type']})...")
    
    prompt = f"""
    你是一个专业的英语教学助手。
    
    **任务**: 
    结合【真题文本】和【解析PDF文件】，生成 "{task['type']} - {task['name']}" (题号 {task['q_range']}) 的结构化 JSON 数据。
    
    **输入**:
    1. **真题文本**: 下面是 DOCX 提取的纯文本，包含题目和选项。
    {docx_text[:2000]} ... (省略部分文本, 请根据题号在PDF中查找对应解析) ...
    
    2. **解析PDF**: 这是一个扫描版 PDF，请利用你的视觉能力阅读其中的解析内容。
    
    **要求**:
    1. 在 PDF 中找到 "{task['name']}" 或对应题号 {task['q_range']} 的解析部分。
    2. 提取正确答案、中文解析、词汇注释、长难句分析。
    3. 如果 PDF 中缺少某部分（如写作范文），请你自行生成高质量内容。
    4. **Translation (翻译)**: 必须包含标准译文和语法分析。
    5. **Writing (写作)**: 必须包含满分范文和点评。
    
    **输出 JSON 格式**:
    {{
      "section_info": {{ "type": "{task['type']}", "name": "{task['name']}", "q_range": "{task['q_range']}" }},
      "article": {{ "paragraphs": ["段落1...", "段落2..."] }},
      "vocabulary": [ {{ "word": "...", "meanings": ["..."], "context_match": "..." }} ],
      "questions": [
        {{
          "id": 题号,
          "text": "题干",
          "options": {{ "A": "...", "B": "...", "C": "...", "D": "..." }},
          "correct_answer": "答案/译文/范文",
          "analysis_raw": "来自PDF的解析内容 (如果PDF看不清或缺失，请AI生成)",
          "ai_persona_prompt": "毒舌老师风格的英文解释"
        }}
      ]
    }}
    
    只返回 JSON 字符串。
    """
    
    try:
        # 传入 prompt 和 file
        response = model.generate_content([prompt, pdf_file, "Please focus on questions " + task['q_range']])
        return clean_json_string(response.text)
    except Exception as e:
        print(f"Error generating {task['name']}: {e}")
        return None

def main():
    year = "2025"
    base_dir = os.path.dirname(os.path.abspath(__file__))
    docx_path = os.path.join(base_dir, "DOCX", f"{year}年考研英语一真题.docx")
    pdf_path = os.path.join(base_dir, "PDF", f"{year}年考研英语一真题解析.pdf")
    output_path = os.path.join(base_dir, f"{year}_full_vision.json")
    
    if not os.path.exists(docx_path) or not os.path.exists(pdf_path):
        print("Files not found.")
        return

    # 1. 读取 DOCX
    print("Reading DOCX...")
    docx_text = extract_docx_text(docx_path)
    
    # 2. 上传 PDF
    print("Uploading PDF to Gemini...")
    try:
        pdf_file = upload_to_gemini(pdf_path)
    except Exception as e:
        print(f"Upload failed: {e}")
        return

    # 3. 初始化模型
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    full_data = {
        "meta": {"year": int(year), "exam_type": "English I"},
        "sections": []
    }
    
    tasks = [
        {"type": "Use of English", "name": "Section I", "q_range": "1-20"},
        {"type": "Reading Text", "name": "Text 1", "q_range": "21-25"},
        {"type": "Reading Text", "name": "Text 2", "q_range": "26-30"},
        {"type": "Reading Text", "name": "Text 3", "q_range": "31-35"},
        {"type": "Reading Text", "name": "Text 4", "q_range": "36-40"},
        {"type": "Reading Part B", "name": "Part B", "q_range": "41-45"},
        {"type": "Translation", "name": "Part C", "q_range": "46-50"},
        {"type": "Writing", "name": "Part A", "q_range": "51"},
        {"type": "Writing", "name": "Part B", "q_range": "52"}
    ]
    
    for task in tasks:
        json_str = generate_section_with_vision(model, docx_text, pdf_file, task)
        if json_str:
            try:
                data = json.loads(json_str)
                full_data["sections"].append(data)
                print(f"Success: {task['name']}")
            except json.JSONDecodeError:
                print(f"JSON Decode Error for {task['name']}")
        else:
            print(f"Failed: {task['name']}")
            
        # 避免触发速率限制
        time.sleep(5)

    # 保存
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(full_data, f, ensure_ascii=False, indent=2)
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    main()
