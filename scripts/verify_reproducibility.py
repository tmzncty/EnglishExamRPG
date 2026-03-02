import os
import subprocess
import sys

def main():
    print("Starting Clean Clone Validation...")
    
    # Get all git tracked files
    result = subprocess.run(['git', 'ls-files'], capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ FAIL: Cannot run git ls-files")
        sys.exit(1)
        
    git_files = result.stdout.splitlines()
    
    # Helper to check if ending path matches
    def is_tracked(suffix):
        return any(f.endswith(suffix.replace('\\', '/')) for f in git_files)

    success = True
    
    # 1. Assert private data does not exist
    private_data_file = 'backend/data/femo_profile.db'
    if is_tracked(private_data_file):
        print(f"❌ FAIL: Private data {private_data_file} IS STILL in Git tracking!")
        success = False
    else:
        print(f"✅ PASS: Private data {private_data_file} is correctly untracked.")

    # 2. Assert core assets exist
    core_assets = ['backend/data/static_content.db', 'backend/data/exam_vocabulary.json']
    for asset in core_assets:
        if is_tracked(asset):
            print(f"✅ PASS: Core asset {asset} is tracked.")
        else:
            print(f"❌ FAIL: Core asset {asset} IS MISSING from Git tracking!")
            success = False

    # 3. Assert dependencies exist
    deps = ['backend/requirements.txt', 'frontend/package.json']
    for dep in deps:
        if is_tracked(dep):
             print(f"✅ PASS: Dependency {dep} is tracked.")
        else:
             print(f"❌ FAIL: Dependency {dep} IS MISSING from Git tracking!")
             success = False

    if success:
        print("🎉 SUCCESS: Clean clone validation passed! 核心题库存在，私人数据已清除。")
        sys.exit(0)
    else:
        print("💥 FAIL: Clean clone validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
