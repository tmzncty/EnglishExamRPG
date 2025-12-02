"""
Sync JSON files from root to EnglishExamWeb/data
Copy {year}_full.json to {year}.json in web data folder
"""

import os
import shutil

def sync_json_files():
    base_dir = r"F:\sanity_check_avg"
    web_data_dir = os.path.join(base_dir, "EnglishExamWeb", "data")
    
    for year in range(2010, 2026):
        src = os.path.join(base_dir, f"{year}_full.json")
        dst = os.path.join(web_data_dir, f"{year}.json")
        
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"Copied {year}_full.json -> {year}.json")
        else:
            print(f"Warning: {src} not found")

if __name__ == "__main__":
    sync_json_files()
    print("\nDone! All JSON files synced.")
