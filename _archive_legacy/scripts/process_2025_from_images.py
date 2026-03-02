import os
import json
import time
import glob
import re
import sys
import docx
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found.")
    exit(1)

genai.configure(api_key=api_key)

def extract_docx_text(file_path):
    """Extract text from DOCX"""
    text = ""
    try:
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Error reading DOCX: {e}")
        return None
    return text

def get_page_num(filename):
    match = re.search(r'page_(\d+)', filename)
    return int(match.group(1)) if match else 0

def upload_images(image_dir):
    """Upload all images in the directory to Gemini"""
    all_files = sorted(glob.glob(os.path.join(image_dir, "*.jpg")), key=get_page_num)
    # Filter for pages 15 to 55 to reduce upload size for Text 4 (likely location)
    image_files = [f for f in all_files if 15 <= get_page_num(f) <= 55]
    
    uploaded_files = []
    
    print(f"Found {len(image_files)} images (filtered for Text 4). Uploading...")
    
    for i, img_path in enumerate(image_files):
        print(f"Uploading {i+1}/{len(image_files)}: {os.path.basename(img_path)}...")
        try:
            file = genai.upload_file(img_path, mime_type="image/jpeg")
            uploaded_files.append(file)
        except Exception as e:
            print(f"Failed to upload {img_path}: {e}")
            
    print("Waiting for files to be processed...")
    # Wait for all files to be active
    for file in uploaded_files:
        while file.state.name == "PROCESSING":
            time.sleep(1)
            file = genai.get_file(file.name)
        if file.state.name != "ACTIVE":
            print(f"Warning: File {file.name} is not ACTIVE ({file.state.name})")
            
    return uploaded_files

def clean_json_string(json_str):
    """Clean JSON string"""
    if not json_str: return None
    json_str = json_str.strip()
    if json_str.startswith("```json"): json_str = json_str[7:]
    if json_str.startswith("```"): json_str = json_str[3:]
    if json_str.endswith("```"): json_str = json_str[:-3]
    return json_str.strip()

def generate_section(model, docx_text, image_files, task):
    """Generate JSON using Gemini Vision"""
    print(f"Processing {task['name']} ({task['type']})...")
    
    prompt = f"""
    You are an expert English Exam Analyzer.
    
    **Task**: 
    Extract structured JSON data for "{task['type']} - {task['name']}" (Questions {task['q_range']}) from the provided Exam Text and Analysis Images.
    
    **Inputs**:
    1. **Exam Text (DOCX)**: Contains the questions and options.
    {docx_text[:3000]} ... (truncated) ...
    
    2. **Analysis Images**: 64 pages of the scanned analysis book. 
    You need to visually scan these images to find the section corresponding to "{task['name']}" or Questions {task['q_range']}.
    
    **Requirements**:
    1. **Locate**: Find the relevant pages in the images for this specific section.
    2. **Extract**:
       - **Correct Answer**: From the analysis.
       - **Analysis**: The detailed Chinese explanation.
       - **Vocabulary**: Key words and definitions.
       - **Sentence Analysis**: For long/difficult sentences.
    3. **Generate (if missing)**:
       - If the analysis is missing or unclear, GENERATE it yourself.
       - For **Translation**: Provide standard Chinese translation and grammar analysis.
       - For **Writing**: Provide a high-quality sample essay and commentary.
    
    **Output JSON Format**:
    {{
      "section_info": {{ "type": "{task['type']}", "name": "{task['name']}", "q_range": "{task['q_range']}" }},
      "article": {{ "paragraphs": ["Para 1...", "Para 2..."] }},
      "vocabulary": [ {{ "word": "...", "meanings": ["..."], "context_match": "..." }} ],
      "questions": [
        {{
          "id": Question Number (Integer),
          "text": "Question Stem",
          "options": {{ "A": "...", "B": "...", "C": "...", "D": "..." }},
          "correct_answer": "Answer Key / Translation / Essay",
          "analysis_raw": "Detailed Analysis Content",
          "ai_persona_prompt": "A witty/sarcastic teacher's explanation in English"
        }}
      ]
    }}
    
    Return ONLY the JSON string.
    """
    
    try:
        # Construct the content parts: Prompt + All Images
        # Note: Gemini 2.0 Flash supports list of parts
        parts = [prompt] + image_files + [f"Focus on finding the analysis for Questions {task['q_range']}"]
        
        response = model.generate_content(parts)
        return clean_json_string(response.text)
    except Exception as e:
        print(f"Error generating {task['name']}: {e}")
        return None

def main():
    year = "2025"
    base_dir = os.path.dirname(os.path.abspath(__file__))
    docx_path = os.path.join(base_dir, "DOCX", f"{year}年考研英语一真题.docx")
    image_dir = os.path.join(base_dir, "PDF", "2025_images")
    output_path = os.path.join(base_dir, f"{year}_text4.json")
    
    if not os.path.exists(docx_path):
        print("DOCX file not found.")
        return
    if not os.path.exists(image_dir):
        print("Image directory not found.")
        return

    # 1. Read DOCX
    print("Reading DOCX...")
    docx_text = extract_docx_text(docx_path)
    
    # 2. Upload Images
    print("Uploading Images to Gemini...")
    image_files = upload_images(image_dir)
    
    if not image_files:
        print("No images uploaded.")
        return

    # 3. Initialize Model
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    full_data = {
        "meta": {"year": int(year), "exam_type": "English I"},
        "sections": []
    }
    
    tasks = [
        {"type": "Reading Text", "name": "Text 4", "q_range": "36-40"},
    ]
    
    for task in tasks:
        json_str = generate_section(model, docx_text, image_files, task)
        if json_str:
            try:
                data = json.loads(json_str)
                full_data["sections"].append(data)
                print(f"Success: {task['name']}")
            except json.JSONDecodeError:
                print(f"JSON Decode Error for {task['name']}")
        else:
            print(f"Failed: {task['name']}")
            
        # Sleep to avoid rate limits
        time.sleep(2)

    # Save
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(full_data, f, ensure_ascii=False, indent=2)
    print(f"Saved to {output_path}")
    
    # Cleanup (Optional but recommended)
    print("Cleaning up uploaded files...")
    for file in image_files:
        try:
            genai.delete_file(file.name)
        except:
            pass

if __name__ == "__main__":
    main()
