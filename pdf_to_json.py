import os
import json
import pdfplumber
import docx
import google.generativeai as genai
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置 Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in environment variables.")
    print("Please create a .env file with your API key.")
    exit(1)

genai.configure(api_key=api_key)

def extract_pdf_pages(file_path):
    """从 PDF 中提取每一页的文本，返回列表"""
    pages_text = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                pages_text.append(text if text else "")
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
        return []
    return pages_text

def get_pdf_structure(model, pages_text):
    """分析 PDF 结构，返回各部分对应的页码范围"""
    print("Analyzing PDF structure...")
    
    # 生成页码摘要
    page_summaries = []
    for i, text in enumerate(pages_text):
        if not text:
            content = "[Empty/Image]"
        else:
            start = text[:100].replace('\n', ' ')
            end = text[-100:].replace('\n', ' ')
            content = f"Start: {start} ... End: {end}"
        page_summaries.append(f"Page {i+1}: {content}")
    
    summary_text = "\n".join(page_summaries)
    
    prompt = f"""
    You are a document structure analyzer. I have a PDF of an English Exam Analysis.
    Here are the summaries of each page.
    Identify the PAGE RANGE (start_page, end_page) for each section.
    
    Sections:
    1. Section I Use of English
    2. Section II Reading Part A Text 1
    3. Section II Reading Part A Text 2
    4. Section II Reading Part A Text 3
    5. Section II Reading Part A Text 4
    6. Section II Reading Part B
    7. Section II Reading Part C (Translation)
    8. Section III Writing Part A
    9. Section III Writing Part B

    Return a JSON object with keys: "Use of English", "Text 1", "Text 2", "Text 3", "Text 4", "Part B", "Translation", "Writing Part A", "Writing Part B".
    Values are lists [start_page, end_page].
    
    Page Summaries:
    {summary_text}
    """
    
    try:
        response = model.generate_content(prompt)
        json_str = clean_json_string(response.text)
        return json.loads(json_str)
    except Exception as e:
        print(f"Error analyzing structure: {e}")
        return None

import zipfile
import xml.etree.ElementTree as ET

def extract_text_from_xml(file_path):
    """Fallback method to extract text directly from document.xml"""
    try:
        with zipfile.ZipFile(file_path) as zf:
            xml_content = zf.read('word/document.xml')
        
        # Parse XML
        # The namespace for Word is usually this, but we can ignore namespaces if we just search for tags ending in 't' or 'p'
        # But using namespace is safer.
        tree = ET.fromstring(xml_content)
        
        # Find all text nodes
        # Namespaces in ElementTree are annoying, let's just iterate
        text_parts = []
        for elem in tree.iter():
            if elem.tag.endswith('}t'):
                if elem.text:
                    text_parts.append(elem.text)
            elif elem.tag.endswith('}p'):
                text_parts.append('\n')
                
        return "".join(text_parts)
    except Exception as e:
        print(f"XML parsing failed for {file_path}: {e}")
        return None

def extract_text(file_path):
    """从 DOCX 或 TXT 文件中提取所有文本 (保留原函数用于非PDF)"""
    text = ""
    try:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.docx':
            try:
                doc = docx.Document(file_path)
                for para in doc.paragraphs:
                    text += para.text + "\n"
            except Exception as e:
                print(f"Standard DOCX read failed: {e}. Trying XML fallback...")
                text = extract_text_from_xml(file_path)
                if not text:
                    raise e
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None
    return text


def generate_section_json(model, clean_text, analysis_text, section_type, section_name, q_range):
    """
    针对特定部分生成 JSON
    section_type: "Use of English" or "Reading Text"
    section_name: "Text 1", "Text 2" etc.
    q_range: "1-20", "21-25" etc.
    """
    print(f"Processing {section_type} - {section_name} (Questions {q_range})...")
    
    prompt = f"""
    你是一个专业的英语教学助手和数据结构化专家。
    
    **任务目标**: 
    从提供的【真题试卷】中提取 "{section_type} - {section_name}" 的文章、题目({q_range}题)和标准答案。
    结合【解析资料】中的词汇注释、长难句分析和题目详解，生成 JSON 数据。

    **输入数据**:
    === 1. 真题试卷 (DOCX Content) ===
    {clean_text}

    === 2. 解析资料 (Analysis Content) ===
    {analysis_text}

    **处理逻辑**:
    1. **定位**: 在真题中找到 "{section_name}" (如果是阅读) 或 "Section I Use of English" (如果是完形)。
    2. **题目**: 提取题号为 {q_range} 的所有题目。
    3. **答案**: 在真题末尾的答案表中找到对应答案。
    4. **解析**: 从解析资料中提取对应内容的详解。
    5. **缺失内容生成**: 
       - 如果【解析资料】中缺少某题的解析（例如 Part B 或 写作部分），**你必须利用你的专业知识自行生成高质量的解析**。
       - 对于 **Writing (写作)** 部分：
         - `correct_answer` 字段请填入一篇你生成的**高质量满分范文**。
         - `analysis_raw` 字段请填入对这篇范文的**点评和写作思路分析**。
         - `options` 字段留空。
       - 对于 **Translation (翻译)** 部分：
         - `correct_answer` 字段请填入**标准中文译文**。
         - `analysis_raw` 字段请填入**语法结构分析和翻译技巧**。
       - 对于 **Reading Part B**:
         - 必须解释为什么这个选项是正确的（例如线索词匹配、段落逻辑）。

    **目标 JSON 结构**:
    ```json
    {{
      "section_info": {{
        "type": "{section_type}",
        "name": "{section_name}",
        "q_range": "{q_range}"
      }},
      "article": {{
        "paragraphs": ["段落1...", "段落2..."] 
        // 如果是完形填空，请保留挖空符号 (如 _1_)
        // 如果是写作，这里放题目要求(Directions)
      }},
      "vocabulary": [
        {{ "word": "...", "meanings": ["..."], "context_match": "..." }}
      ],
      "questions": [
        {{
          "id": 题号,
          "text": "题干 (如果是翻译，则是划线句原文; 如果是写作，则是题目要求)",
          "options": {{ "A": "...", "B": "...", "C": "...", "D": "..." }}, // 写作和翻译可为空对象
          "correct_answer": "答案/译文/范文",
          "analysis_raw": "中文解析/范文点评 (如果原文缺失，请AI自行生成)",
          "ai_persona_prompt": "毒舌老师风格的英文解释 (必须生成，即使原文没有)"
        }}
      ]
    }}
    ```
    **要求**:
    - 只返回 JSON 字符串。
    - 确保包含 {q_range} 范围内的所有题目。
    - **必须生成 ai_persona_prompt**，不要留 null。
    """

    try:
        response = model.generate_content(prompt)
        return clean_json_string(response.text)
    except Exception as e:
        print(f"Error generating {section_name}: {e}")
        return None

def clean_json_string(json_str):
    """清理 Gemini 返回的字符串，确保它是有效的 JSON"""
    if not json_str:
        return None
    
    # 去除可能的 Markdown 标记
    json_str = json_str.strip()
    if json_str.startswith("```json"):
        json_str = json_str[7:]
    if json_str.startswith("```"):
        json_str = json_str[3:]
    if json_str.endswith("```"):
        json_str = json_str[:-3]
    
    return json_str.strip()

def generate_section_json_with_retry(model, clean_text, analysis_text, task, max_retries=3):
    """尝试多次生成 JSON"""
    for attempt in range(max_retries):
        print(f"Attempt {attempt + 1}/{max_retries} for {task['name']}...")
        json_str = generate_section_json(
            model, clean_text, analysis_text, 
            task["type"], task["name"], task["q_range"]
        )
        
        if json_str:
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                print(f"JSON Decode Error on attempt {attempt + 1}")
        else:
            print(f"Empty response on attempt {attempt + 1}")
            
    return None

def main():
    # 基础路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    docx_dir = os.path.join(base_dir, "DOCX")
    pdf_dir = os.path.join(base_dir, "PDF")
    
    # 获取所有年份
    years_to_process = []
    
    # 遍历 DOCX 目录寻找年份
    if os.path.exists(docx_dir):
        for filename in os.listdir(docx_dir):
            if filename.endswith("年考研英语一真题.docx"):
                try:
                    year = filename[:4]
                    if int(year) > 2010:
                        years_to_process.append(year)
                except ValueError:
                    pass
    
    years_to_process.sort()
    print(f"Found years to process: {years_to_process}")

    for year in years_to_process:
        print(f"\n{'='*30}\nProcessing Year: {year}\n{'='*30}")
        
        # 构造文件路径
        clean_docx_path = os.path.join(docx_dir, f"{year}年考研英语一真题.docx")
        analysis_pdf_path = os.path.join(pdf_dir, f"{year}年考研英语一真题解析.pdf")
        output_json_path = os.path.join(base_dir, f"{year}_full.json")

        if os.path.exists(output_json_path):
            print(f"Skipping {year}, output file already exists: {output_json_path}")
            continue

        if not os.path.exists(clean_docx_path):
            print(f"Error: Clean text file not found at {clean_docx_path}")
            continue
            
        if not os.path.exists(analysis_pdf_path):
            print(f"Error: Analysis file not found at {analysis_pdf_path}")
            continue

        print(f"Reading files for {year}...")
        clean_text = extract_text(clean_docx_path)
        
        # 提取 PDF 每一页的文本
        pdf_pages = extract_pdf_pages(analysis_pdf_path)

        if not clean_text or not pdf_pages:
            print(f"Failed to extract text for {year}.")
            continue

        # 初始化 Gemini
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # 获取 PDF 结构映射
        structure_map = get_pdf_structure(model, pdf_pages)
        if not structure_map:
            print("Failed to analyze PDF structure. Falling back to full text (not recommended).")
            analysis_text_full = "\n".join(pdf_pages)
            structure_map = {} 

        full_data = {
            "meta": {"year": int(year), "exam_type": "English I"},
            "sections": []
        }

        # 定义要处理的任务列表
        tasks = [
            # 1. 完形填空
            {"type": "Use of English", "name": "Section I", "q_range": "1-20", "key": "Use of English"},
            # 2. 阅读理解 Part A Text 1
            {"type": "Reading Text", "name": "Text 1", "q_range": "21-25", "key": "Text 1"},
            # 3. 阅读理解 Part A Text 2
            {"type": "Reading Text", "name": "Text 2", "q_range": "26-30", "key": "Text 2"},
            # 4. 阅读理解 Part A Text 3
            {"type": "Reading Text", "name": "Text 3", "q_range": "31-35", "key": "Text 3"},
            # 5. 阅读理解 Part A Text 4
            {"type": "Reading Text", "name": "Text 4", "q_range": "36-40", "key": "Text 4"},
            # 6. 阅读理解 Part B (新题型)
            {"type": "Reading Part B", "name": "Part B", "q_range": "41-45", "key": "Part B"},
            # 7. 翻译 Part C
            {"type": "Translation", "name": "Part C", "q_range": "46-50", "key": "Translation"},
            # 8. 写作 Part A
            {"type": "Writing", "name": "Part A", "q_range": "51", "key": "Writing Part A"},
            # 9. 写作 Part B
            {"type": "Writing", "name": "Part B", "q_range": "52", "key": "Writing Part B"}
        ]

        for task in tasks:
            # Determine analysis text for this task
            task_analysis_text = ""
            if structure_map and task["key"] in structure_map:
                start_page, end_page = structure_map[task["key"]]
                # Adjust for 0-based index. start_page is 1-based.
                # Slice is [start-1 : end]
                # Add a buffer page before and after just in case
                s = max(0, start_page - 2)
                e = min(len(pdf_pages), end_page + 1)
                task_analysis_text = "\n".join(pdf_pages[s:e])
                print(f"Using pages {s+1}-{e} for {task['name']}")
            else:
                print(f"Using full text for {task['name']} (Map not found)")
                task_analysis_text = "\n".join(pdf_pages)

            section_data = generate_section_json_with_retry(model, clean_text, task_analysis_text, task)
            
            if section_data:
                full_data["sections"].append(section_data)
                print(f"Successfully processed {task['name']}")
            else:
                print(f"Failed to generate content for {task['name']} after retries.")

        # 保存最终的大文件
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)
        
        print(f"All done for {year}! Saved to {output_json_path}")

if __name__ == "__main__":
    main()
