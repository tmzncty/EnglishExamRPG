import pdfplumber
import os

pdf_path = r"F:\sanity_check_avg\PDF\2010年考研英语一真题解析.pdf"

def check_text_layer(path):
    print(f"Checking {path}...")
    try:
        with pdfplumber.open(path) as pdf:
            print(f"Total pages: {len(pdf.pages)}")
            for i, page in enumerate(pdf.pages[:3]): # Check first 3 pages
                text = page.extract_text()
                print(f"--- Page {i+1} ---")
                if text:
                    print(f"Text length: {len(text)}")
                    print(f"Preview: {text[:100]}...")
                else:
                    print("No text extracted (Empty string).")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if os.path.exists(pdf_path):
        check_text_layer(pdf_path)
    else:
        print("File not found.")
