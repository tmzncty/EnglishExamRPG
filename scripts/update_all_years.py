import json
import os
import glob

def update_json_structure(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    changed = False
    for section in data.get('sections', []):
        info = section.get('section_info', {})
        original_name = info.get('name', '')
        original_type = info.get('type', '')
        
        new_name = original_name

        if original_type == 'Use of English':
            new_name = 'Section I Use of English'
        
        elif original_type == 'Reading Text':
            if 'Text 1' in original_name:
                new_name = 'Section II Part A Text 1'
            elif 'Text 2' in original_name:
                new_name = 'Section II Part A Text 2'
            elif 'Text 3' in original_name:
                new_name = 'Section II Part A Text 3'
            elif 'Text 4' in original_name:
                new_name = 'Section II Part A Text 4'
        
        elif original_type == 'Reading Part B' or (original_name == 'Part B' and '41' in info.get('q_range', '')):
            new_name = 'Section II Part B'
            
        elif original_type == 'Translation' or (original_name == 'Part C' and '46' in info.get('q_range', '')):
            new_name = 'Section II Part C'
            
        elif original_type == 'Writing':
            if original_name == 'Part A':
                new_name = 'Section III Part A'
            elif original_name == 'Part B':
                new_name = 'Section III Part B'
        
        # Fallback for cases where type might be generic but name is specific
        if original_name == 'Part A' and '51' in info.get('q_range', ''):
             new_name = 'Section III Part A'
        if original_name == 'Part B' and '52' in info.get('q_range', ''):
             new_name = 'Section III Part B'

        if new_name != original_name:
            print(f"Updating {file_path}: {original_name} -> {new_name}")
            info['name'] = new_name
            changed = True

    if changed:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved {file_path}")

# Get all *_full.json files
files = glob.glob('*_full.json')
files.extend(glob.glob('*_full_vision.json'))

for file in files:
    if file == '2010_full.json':
        continue # Already done
    update_json_structure(file)
