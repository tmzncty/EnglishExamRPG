import pdfplumber
import os

pdf_path = r"f:\sanity_check_avg\PDF\2010年考研英语一真题解析.pdf"

if not os.path.exists(pdf_path):
    print(f"File not found: {pdf_path}")
else:
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Total pages: {len(pdf.pages)}")
        
        keywords = [
            "Section I Use of English",
            "Section II Reading Comprehension",
            "Text 1", "Text 2", "Text 3", "Text 4",
            "Part B",
            "Part C",
            "Section III Writing",
            "Part A",
            "Part B" # Note: Part B appears in Reading and Writing
        ]
        
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text: continue
            
            found = []
            for kw in keywords:
                if kw in text:
                    found.append(kw)
            
            if found:
                print(f"Page {i+1}: Found {found}")
