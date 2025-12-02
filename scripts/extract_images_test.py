import pdfplumber
import os

pdf_path = r"F:\sanity_check_avg\PDF\2025年考研英语一真题解析.pdf"
output_dir = r"F:\sanity_check_avg\PDF\2025_images"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def extract_images():
    print(f"Opening {pdf_path}...")
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages[:5]): # Try first 5 pages
            print(f"Processing page {i+1}...")
            # For scanned PDF, usually there is one big image
            if page.images:
                for j, img in enumerate(page.images):
                    # Get the image object
                    # pdfplumber doesn't provide direct 'save' method for images easily without 'stream'
                    # But we can try to access the raw stream if we know how.
                    # Actually, page.to_image() is the intended way but requires dependencies.
                    pass
            
            # Let's try page.to_image() which renders the page
            try:
                p_im = page.to_image(resolution=100)
                im = p_im.original # Get the PIL image
                if im.mode != 'RGB':
                    im = im.convert('RGB')
                im.save(os.path.join(output_dir, f"page_{i+1}.jpg"), format="JPEG", quality=80)
                print(f"Saved page_{i+1}.jpg")
            except Exception as e:
                print(f"Failed to render page {i+1}: {e}")
                # If to_image fails (missing dependencies), we are stuck.

if __name__ == "__main__":
    extract_images()
