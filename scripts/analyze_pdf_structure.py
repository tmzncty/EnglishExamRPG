"""
Analyze PDF structure to create question-to-page mapping.
This will help users jump to the correct page for each question's official analysis.
"""

import pdfplumber
import os
import json
import re

def analyze_pdf(pdf_path, year):
    """Analyze a PDF and extract page mappings for each section/question."""
    
    result = {
        "year": year,
        "pdf_file": f"{year}年考研英语一真题解析.pdf",
        "total_pages": 0,
        "sections": {}
    }
    
    print(f"\n{'='*60}")
    print(f"Analyzing {year} PDF: {pdf_path}")
    print(f"{'='*60}")
    
    with pdfplumber.open(pdf_path) as pdf:
        result["total_pages"] = len(pdf.pages)
        print(f"Total pages: {len(pdf.pages)}")
        
        # Scan each page for section/question markers
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            
            # Look for section markers
            # Use of English / Section I
            if re.search(r'(Section\s*I|完形填空|Use of English)', text, re.I):
                if "use_of_english" not in result["sections"]:
                    result["sections"]["use_of_english"] = {
                        "name": "Section I Use of English",
                        "start_page": page_num,
                        "questions": "1-20"
                    }
                    print(f"  Page {page_num}: Section I Use of English")
            
            # Reading Comprehension / Section II
            if re.search(r'(Section\s*II|Part\s*A|阅读理解)', text, re.I) and "Reading" not in str(result["sections"]):
                # Check for Text 1-4
                for text_num in [1, 2, 3, 4]:
                    pattern = rf'(Text\s*{text_num}|Passage\s*{text_num})'
                    if re.search(pattern, text, re.I):
                        key = f"reading_text_{text_num}"
                        if key not in result["sections"]:
                            q_start = 21 + (text_num - 1) * 5
                            q_end = q_start + 4
                            result["sections"][key] = {
                                "name": f"Section II Reading Part A Text {text_num}",
                                "start_page": page_num,
                                "questions": f"{q_start}-{q_end}"
                            }
                            print(f"  Page {page_num}: Reading Text {text_num} (Q{q_start}-{q_end})")
            
            # Part B (Reading)
            if re.search(r'Part\s*B', text, re.I) and "reading_part_b" not in result["sections"]:
                if "41" in text or "45" in text:
                    result["sections"]["reading_part_b"] = {
                        "name": "Section II Reading Part B",
                        "start_page": page_num,
                        "questions": "41-45"
                    }
                    print(f"  Page {page_num}: Reading Part B (Q41-45)")
            
            # Translation / Section III Part A
            if re.search(r'(翻译|Translation|46)', text, re.I):
                if "translation" not in result["sections"] and ("Part A" in text or "46" in text):
                    result["sections"]["translation"] = {
                        "name": "Section III Writing Part A (Translation)",
                        "start_page": page_num,
                        "questions": "46"
                    }
                    print(f"  Page {page_num}: Translation (Q46)")
            
            # Writing Part A (小作文 / Application)
            if re.search(r'(小作文|应用文|Part\s*A.*Writing|Writing.*Part\s*A|51)', text, re.I):
                if "writing_a" not in result["sections"]:
                    result["sections"]["writing_a"] = {
                        "name": "Section III Writing Part A",
                        "start_page": page_num,
                        "questions": "51"
                    }
                    print(f"  Page {page_num}: Writing Part A (Q51)")
            
            # Writing Part B (大作文 / Essay)
            if re.search(r'(大作文|Part\s*B.*Writing|Writing.*Part\s*B|160-200|52)', text, re.I):
                if "writing_b" not in result["sections"]:
                    if "writing_a" in result["sections"]:  # Must be after Part A
                        result["sections"]["writing_b"] = {
                            "name": "Section III Writing Part B",
                            "start_page": page_num,
                            "questions": "52"
                        }
                        print(f"  Page {page_num}: Writing Part B (Q52)")
    
    return result

def create_page_mapping_for_all_years():
    """Create page mappings for all PDF files."""
    pdf_dir = r"F:\sanity_check_avg\PDF"
    output_file = r"F:\sanity_check_avg\EnglishExamWeb\data\pdf_mappings.json"
    
    all_mappings = {}
    
    for year in range(2010, 2026):
        pdf_path = os.path.join(pdf_dir, f"{year}年考研英语一真题解析.pdf")
        if os.path.exists(pdf_path):
            mapping = analyze_pdf(pdf_path, year)
            all_mappings[str(year)] = mapping
        else:
            print(f"Warning: {pdf_path} not found")
    
    # Save to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_mappings, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Saved mappings to: {output_file}")
    print(f"{'='*60}")
    
    return all_mappings

if __name__ == "__main__":
    create_page_mapping_for_all_years()
