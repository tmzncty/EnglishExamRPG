import json
import os

def merge_json():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, "2025_full_vision.json")
    text4_path = os.path.join(base_dir, "2025_text4.json")
    
    if not os.path.exists(full_path) or not os.path.exists(text4_path):
        print("Files not found.")
        return

    with open(full_path, 'r', encoding='utf-8') as f:
        full_data = json.load(f)
        
    with open(text4_path, 'r', encoding='utf-8') as f:
        text4_data = json.load(f)
        
    # Insert Text 4 into the correct position (after Text 3)
    # Current order: Section I, Text 1, Text 2, Text 3, Part B, Part C, Writing A, Writing B
    # We want: ..., Text 3, Text 4, Part B, ...
    
    new_sections = []
    inserted = False
    
    # Extract the Text 4 section object (it's wrapped in "sections" list in the temp file)
    text4_section = text4_data["sections"][0]
    
    for section in full_data["sections"]:
        new_sections.append(section)
        if section["section_info"]["name"] == "Text 3":
            new_sections.append(text4_section)
            inserted = True
            
    if not inserted:
        # If Text 3 not found, just append (fallback)
        new_sections.append(text4_section)
        
    full_data["sections"] = new_sections
    
    # Save back to full file
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(full_data, f, ensure_ascii=False, indent=2)
        
    print("Merged Text 4 into 2025_full_vision.json successfully.")
    
    # Clean up temp file
    os.remove(text4_path)

if __name__ == "__main__":
    merge_json()
