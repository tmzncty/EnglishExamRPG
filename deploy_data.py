import os
import shutil

def deploy_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    web_data_dir = os.path.join(base_dir, "EnglishExamWeb", "data")
    
    if not os.path.exists(web_data_dir):
        os.makedirs(web_data_dir)
        
    # Process 2010-2024
    for year in range(2010, 2025):
        src_filename = f"{year}_full.json"
        src_path = os.path.join(base_dir, src_filename)
        
        if os.path.exists(src_path):
            dst_path = os.path.join(web_data_dir, f"{year}.json")
            shutil.copy2(src_path, dst_path)
            print(f"Deployed {src_filename} to {dst_path}")
        else:
            print(f"Warning: {src_filename} not found.")

    # Process 2025 (prefer vision version)
    vision_src = os.path.join(base_dir, "2025_full_vision.json")
    text_src = os.path.join(base_dir, "2025_full.json")
    dst_path = os.path.join(web_data_dir, "2025.json")
    
    if os.path.exists(vision_src):
        shutil.copy2(vision_src, dst_path)
        print(f"Deployed 2025_full_vision.json to {dst_path}")
    elif os.path.exists(text_src):
        shutil.copy2(text_src, dst_path)
        print(f"Deployed 2025_full.json to {dst_path}")
    else:
        print("Warning: 2025 data not found.")

if __name__ == "__main__":
    deploy_data()
