import pdfplumber
import os
import google.generativeai as genai
from dotenv import load_dotenv
import json

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

def get_pdf_structure(pdf_path):
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    page_summaries = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                content = "[Empty/Image]"
            else:
                # Take first 100 and last 100 chars to identify headers/footers/content
                start = text[:150].replace('\n', ' ')
                end = text[-150:].replace('\n', ' ')
                content = f"Start: {start} ... End: {end}"
            
            page_summaries.append(f"Page {i+1}: {content}")
    
    summary_text = "\n".join(page_summaries)
    
    prompt = f"""
    You are a document structure analyzer. I have a PDF of an English Exam Analysis (Answer Key & Explanations).
    Here are the summaries of each page (first and last few characters).
    
    Your task is to identify the PAGE RANGE (start_page, end_page) for each of the following sections.
    The sections are:
    1. Section I Use of English (完形填空)
    2. Section II Reading Part A Text 1
    3. Section II Reading Part A Text 2
    4. Section II Reading Part A Text 3
    5. Section II Reading Part A Text 4
    6. Section II Reading Part B (新题型)
    7. Section II Reading Part C (Translation/翻译)
    8. Section III Writing Part A (小作文)
    9. Section III Writing Part B (大作文)

    Return a JSON object where keys are the section names (use the keys below) and values are lists [start_page, end_page].
    If a section seems to share a page with another, that's fine.
    
    Keys: "Use of English", "Text 1", "Text 2", "Text 3", "Text 4", "Part B", "Translation", "Writing A", "Writing B".

    Page Summaries:
    {summary_text}
    """
    
    response = model.generate_content(prompt)
    print(response.text)

if __name__ == "__main__":
    pdf_path = r"f:\sanity_check_avg\PDF\2010年考研英语一真题解析.pdf"
    get_pdf_structure(pdf_path)
