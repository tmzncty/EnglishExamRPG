"""
Extract the Writing Part B (Q52) images from 2015 and 2022 PDFs.
Convert them to Base64 and update the corresponding JSON files.
"""

import pdfplumber
import os
import json
import base64
from io import BytesIO

def extract_page_image(pdf_path, page_num, output_path=None):
    """Extract a specific page as an image and return as base64."""
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num]
        # Render the page to an image
        p_im = page.to_image(resolution=150)
        im = p_im.original  # Get the PIL image
        
        if im.mode != 'RGB':
            im = im.convert('RGB')
        
        # Save to file if output_path provided
        if output_path:
            im.save(output_path, format="JPEG", quality=85)
            print(f"Saved image to {output_path}")
        
        # Convert to base64
        buffer = BytesIO()
        im.save(buffer, format="JPEG", quality=85)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return img_base64

def find_writing_part_b_page(pdf_path):
    """Find the page containing Writing Part B (Q52) by searching for keywords."""
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            # Look for indicators of Writing Part B / Section III Part B
            if "Part B" in text and ("52" in text or "写作" in text or "Directions" in text):
                if "160-200 words" in text or "picture" in text.lower():
                    print(f"Found Writing Part B on page {i+1}")
                    return i
        # If not found by keywords, try to find the last few pages (usually at the end)
        print("Could not find exact page, returning last few pages for manual check")
        return None

def main():
    base_dir = r"F:\sanity_check_avg"
    pdf_dir = os.path.join(base_dir, "PDF")
    
    # 2015
    pdf_2015 = os.path.join(pdf_dir, "2015年考研英语一真题解析.pdf")
    # 2022
    pdf_2022 = os.path.join(pdf_dir, "2022年考研英语一真题解析.pdf")
    
    # Search for pages with "160-200" or "describe the picture" which are in Writing Part B
    print("=" * 50)
    print("Scanning 2015 PDF for Writing Part B (160-200 words essay)...")
    print("=" * 50)
    
    with pdfplumber.open(pdf_2015) as pdf:
        print(f"Total pages: {len(pdf.pages)}")
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            # Check for Writing Part B indicators
            if "160-200" in text or "describe the picture" in text.lower() or ("Part B" in text and "Writing" in text):
                preview = text[:800].replace('\n', ' ')
                print(f"Page {i+1}: {preview[:300]}...")
                # Check if page has images
                if page.images:
                    print(f"  -> This page has {len(page.images)} image(s)")
    
    print("\n" + "=" * 50)
    print("Scanning 2022 PDF for Writing Part B (160-200 words essay)...")
    print("=" * 50)
    
    with pdfplumber.open(pdf_2022) as pdf:
        print(f"Total pages: {len(pdf.pages)}")
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            # Check for Writing Part B indicators
            if "160-200" in text or "describe the picture" in text.lower() or ("Part B" in text and "Writing" in text):
                preview = text[:800].replace('\n', ' ')
                print(f"Page {i+1}: {preview[:300]}...")
                # Check if page has images
                if page.images:
                    print(f"  -> This page has {len(page.images)} image(s)")

if __name__ == "__main__":
    main()
