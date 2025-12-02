import pdfplumber
import os
import sys

# Ensure we are running in the right environment
print(f"Python executable: {sys.executable}")

pdf_path = r"F:\sanity_check_avg\PDF\2025年考研英语一真题解析.pdf"
output_dir = r"F:\sanity_check_avg\PDF\2025_images"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def convert_all_pages():
    print(f"Opening {pdf_path}...")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"Total pages: {total_pages}")
            
            for i, page in enumerate(pdf.pages):
                image_path = os.path.join(output_dir, f"page_{i+1}.jpg")
                
                # Skip if already exists to save time on re-runs
                if os.path.exists(image_path):
                    print(f"Skipping page {i+1} (already exists)")
                    continue

                print(f"Converting page {i+1}/{total_pages}...")
                try:
                    # Resolution 150 is a good balance for OCR/Vision
                    p_im = page.to_image(resolution=150)
                    im = p_im.original
                    if im.mode != 'RGB':
                        im = im.convert('RGB')
                    
                    im.save(image_path, format="JPEG", quality=85)
                except Exception as e:
                    print(f"Error converting page {i+1}: {e}")

    except Exception as e:
        print(f"Error opening PDF: {e}")

if __name__ == "__main__":
    convert_all_pages()
