"""
Add extracted images to JSON files for 2015 and 2022.
Also update the JSON files in EnglishExamWeb/data/
"""

import os
import json
import base64

def image_to_base64_url(image_path):
    """Convert image file to base64 data URL"""
    ext = os.path.splitext(image_path)[1].lower()
    
    mime_map = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
    }
    mime = mime_map.get(ext, 'image/png')
    
    with open(image_path, 'rb') as f:
        img_data = f.read()
    
    b64 = base64.b64encode(img_data).decode('utf-8')
    return f"data:{mime};base64,{b64}"

def update_json_with_image(json_path, image_base64, question_id=52):
    """Update the JSON file, adding image to the specified question"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Find the question with the specified ID
    for section in data.get('sections', []):
        for question in section.get('questions', []):
            if question.get('id') == question_id:
                question['image'] = image_base64
                print(f"  Added image to question {question_id}")
                break
    
    # Write back
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"  Updated: {json_path}")

def main():
    base_dir = r"F:\sanity_check_avg"
    extracted_dir = os.path.join(base_dir, "extracted_images")
    web_data_dir = os.path.join(base_dir, "EnglishExamWeb", "data")
    
    # 2015
    print("=" * 60)
    print("Processing 2015...")
    print("=" * 60)
    
    img_2015 = os.path.join(extracted_dir, "2015_image_2.jpeg")
    if os.path.exists(img_2015):
        b64_2015 = image_to_base64_url(img_2015)
        print(f"  Image size: {len(b64_2015)} characters")
        
        # Update both full JSON and web JSON
        update_json_with_image(os.path.join(base_dir, "2015_full.json"), b64_2015, 52)
        update_json_with_image(os.path.join(web_data_dir, "2015.json"), b64_2015, 52)
    else:
        print(f"  Image not found: {img_2015}")
    
    # 2022
    print("\n" + "=" * 60)
    print("Processing 2022...")
    print("=" * 60)
    
    img_2022 = os.path.join(extracted_dir, "2022_image_1.png")
    if os.path.exists(img_2022):
        b64_2022 = image_to_base64_url(img_2022)
        print(f"  Image size: {len(b64_2022)} characters")
        
        # Update both full JSON and web JSON
        update_json_with_image(os.path.join(base_dir, "2022_full.json"), b64_2022, 52)
        update_json_with_image(os.path.join(web_data_dir, "2022.json"), b64_2022, 52)
    else:
        print(f"  Image not found: {img_2022}")
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

if __name__ == "__main__":
    main()
