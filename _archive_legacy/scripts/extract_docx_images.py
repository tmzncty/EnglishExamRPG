"""
Extract images from DOCX files (specifically for Writing Part B Q52)
"""

import os
import zipfile
import base64
from io import BytesIO

def extract_images_from_docx(docx_path):
    """
    DOCX files are actually ZIP archives. 
    Images are stored in word/media/ folder.
    """
    images = []
    
    with zipfile.ZipFile(docx_path, 'r') as zip_ref:
        # List all files in the archive
        for file_info in zip_ref.filelist:
            if file_info.filename.startswith('word/media/'):
                # This is an image
                img_data = zip_ref.read(file_info.filename)
                ext = os.path.splitext(file_info.filename)[1].lower()
                images.append({
                    'filename': file_info.filename,
                    'extension': ext,
                    'data': img_data,
                    'size': len(img_data)
                })
    
    return images

def image_to_base64(img_data, ext):
    """Convert image bytes to base64 data URL"""
    b64 = base64.b64encode(img_data).decode('utf-8')
    
    # Determine MIME type
    mime_map = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.emf': 'image/emf',
        '.wmf': 'image/wmf'
    }
    mime = mime_map.get(ext, 'image/png')
    
    return f"data:{mime};base64,{b64}"

def main():
    docx_dir = r"F:\sanity_check_avg\DOCX"
    output_dir = r"F:\sanity_check_avg\extracted_images"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Extract from 2015
    print("=" * 60)
    print("Extracting images from 2015年考研英语一真题.docx")
    print("=" * 60)
    
    docx_2015 = os.path.join(docx_dir, "2015年考研英语一真题.docx")
    images_2015 = extract_images_from_docx(docx_2015)
    
    print(f"Found {len(images_2015)} images:")
    for i, img in enumerate(images_2015):
        print(f"  {i+1}. {img['filename']} ({img['extension']}, {img['size']} bytes)")
        # Save to file for inspection
        out_path = os.path.join(output_dir, f"2015_image_{i+1}{img['extension']}")
        with open(out_path, 'wb') as f:
            f.write(img['data'])
        print(f"     Saved to: {out_path}")
    
    # Extract from 2022
    print("\n" + "=" * 60)
    print("Extracting images from 2022年考研英语一真题.docx")
    print("=" * 60)
    
    docx_2022 = os.path.join(docx_dir, "2022年考研英语一真题.docx")
    images_2022 = extract_images_from_docx(docx_2022)
    
    print(f"Found {len(images_2022)} images:")
    for i, img in enumerate(images_2022):
        print(f"  {i+1}. {img['filename']} ({img['extension']}, {img['size']} bytes)")
        # Save to file for inspection
        out_path = os.path.join(output_dir, f"2022_image_{i+1}{img['extension']}")
        with open(out_path, 'wb') as f:
            f.write(img['data'])
        print(f"     Saved to: {out_path}")

if __name__ == "__main__":
    main()
