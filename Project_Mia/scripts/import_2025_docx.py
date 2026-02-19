"""
import_2025_docx.py — 从 2025 年考研英语一 Word 文档中提取大作文配图
补充到 static_content.db 中已存在的 2025-eng1 Writing B 题目

使用:
    python scripts/import_2025_docx.py

Author: Femo
Date: 2026-02-18
"""

import base64
import io
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.db.models import StaticBase, Question

# ============================================================================
#  配置
# ============================================================================

DOCX_PATH = Path(r"F:\sanity_check_avg\DOCX\2025年考研英语一真题.docx")
DB_PATH = PROJECT_ROOT / "backend" / "data" / "static_content.db"

# 颜色
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"


def extract_images_from_docx(docx_path: Path) -> list[tuple[str, bytes]]:
    """
    从 DOCX 中提取所有内嵌图片
    
    Returns:
        list of (content_type, image_bytes)
    """
    from docx import Document
    from docx.opc.constants import RELATIONSHIP_TYPE as RT
    
    doc = Document(str(docx_path))
    images = []
    
    # 方法1: 通过 document.part.rels 遍历所有关系
    for rel_id, rel in doc.part.rels.items():
        if "image" in rel.reltype:
            try:
                img_part = rel.target_part
                content_type = img_part.content_type  # e.g. "image/jpeg"
                img_bytes = img_part.blob
                images.append((content_type, img_bytes))
            except Exception as e:
                print(f"{YELLOW}[WARN] Could not read image rel {rel_id}: {e}{RESET}")
    
    # 方法2: 遍历 inline_shapes (backup)
    if not images:
        for shape in doc.inline_shapes:
            try:
                blip = shape._inline.graphic.graphicData.pic.blipFill.blip
                rId = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                if rId:
                    img_part = doc.part.related_parts[rId]
                    content_type = img_part.content_type
                    img_bytes = img_part.blob
                    images.append((content_type, img_bytes))
            except Exception as e:
                print(f"{YELLOW}[WARN] Could not read inline shape: {e}{RESET}")
    
    return images


def image_to_base64(content_type: str, img_bytes: bytes) -> str:
    """将图片字节转为 data URI"""
    b64 = base64.b64encode(img_bytes).decode("ascii")
    return f"data:{content_type};base64,{b64}"


def main():
    print(f"\n{BOLD}{CYAN}{'='*60}")
    print(f"  🐾 Project_Mia — 2025 DOCX Image Extraction")
    print(f"{'='*60}{RESET}\n")
    
    # 1. 检查 DOCX
    if not DOCX_PATH.exists():
        print(f"{RED}[ERROR] DOCX not found: {DOCX_PATH}{RESET}")
        return
    
    print(f"  Source: {DOCX_PATH.name}")
    print(f"  Target DB: {DB_PATH}")
    
    # 2. 提取所有图片
    print(f"\n{CYAN}[STEP 1] Extracting images from DOCX...{RESET}")
    images = extract_images_from_docx(DOCX_PATH)
    
    if not images:
        print(f"{RED}[ERROR] No images found in DOCX!{RESET}")
        return
    
    print(f"  Found {len(images)} image(s):")
    for i, (ct, data) in enumerate(images):
        size_kb = len(data) / 1024
        print(f"    [{i}] {ct}, {size_kb:.1f} KB")
    
    # 3. 选择最大的图片作为 Writing B 配图 (通常大作文图片最大)
    best_idx = max(range(len(images)), key=lambda i: len(images[i][1]))
    best_ct, best_data = images[best_idx]
    best_b64 = image_to_base64(best_ct, best_data)
    
    print(f"\n{GREEN}  → Selected image [{best_idx}] ({len(best_data)/1024:.1f} KB) for Writing B{RESET}")
    
    # 4. 更新数据库
    print(f"\n{CYAN}[STEP 2] Updating database...{RESET}")
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 查找 2025 Writing B 题目
    wb_q = session.query(Question).filter(
        Question.paper_id == "2025-eng1",
        Question.section_type == "writing_b"
    ).first()
    
    if not wb_q:
        print(f"{RED}[ERROR] 2025-eng1 writing_b question not found in DB!")
        print(f"  Make sure to run 'import_exam_data.py --year 2025' first.{RESET}")
        session.close()
        return
    
    # 更新图片
    wb_q.image_base64 = best_b64
    session.commit()
    session.close()
    
    print(f"{GREEN}{BOLD}  ✅ Successfully patched image for {wb_q.q_id}{RESET}")
    print(f"     Image size: {len(best_b64):,} chars (Base64)")
    print()


if __name__ == "__main__":
    main()
