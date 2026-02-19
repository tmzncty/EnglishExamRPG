"""
import_exam_data.py — 考研英语一真题 ETL 导入工具
按年份将 JSON 数据导入 static_content.db，含图片自动匹配 + Base64 转码

使用:
    python scripts/import_exam_data.py --year 2010
    python scripts/import_exam_data.py --year 2010 --db-path backend/data/static_content.db

Author: Femo
Date: 2026-02-18
"""

import argparse
import base64
import json
import os
import re
import sys
from pathlib import Path

# 确保 backend 可被 import
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.app.db.models import StaticBase, Paper, Question

# ============================================================================
#  配置常量
# ============================================================================

# 源数据根目录
SOURCE_ROOT = Path(r"F:\sanity_check_avg")
IMAGE_ROOT = SOURCE_ROOT / "extracted_images"

# Section Type 映射
SECTION_MAP = {
    "Use of English": "use_of_english",
    "Reading Text":   "reading_a",       # 默认; Part B 单独处理
    "Reading Part B": "reading_b",
    "Translation":    "translation",
    "Writing":        None,              # 需进一步区分 Part A / Part B
}

# 各题型默认分值
SCORE_MAP = {
    "use_of_english": 0.5,
    "reading_a":      2.0,
    "reading_b":      2.0,
    "translation":    2.0,
    "writing_a":      10.0,
    "writing_b":      20.0,
}

# 颜色输出
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"


# ============================================================================
#  辅助函数
# ============================================================================

def resolve_section_type(section_info: dict) -> tuple[str, str | None]:
    """
    从 section_info 推断 section_type 和 group_name

    Returns:
        (section_type, group_name)
    """
    raw_type = section_info.get("type", "")
    name     = section_info.get("name", "")

    # 1) Use of English
    if "Use of English" in raw_type:
        return "use_of_english", None

    # 2) Reading Part B (7选5 / 排序)
    if "Part B" in raw_type or "Part B" in name:
        if "Writing" not in raw_type and "translation" not in raw_type.lower():
            if "Reading" in raw_type or "Section II" in name:
                return "reading_b", None

    # 3) Reading Text → reading_a + group_name
    if raw_type == "Reading Text" or ("Reading" in raw_type and "Part B" not in raw_type):
        group = None
        m = re.search(r"Text\s*(\d+)", name)
        if m:
            group = f"Text {m.group(1)}"
        return "reading_a", group

    # 4) Translation
    if "Translation" in raw_type or "Part C" in name:
        return "translation", None

    # 5) Writing → 区分 Part A / Part B
    if "Writing" in raw_type or "Section III" in name:
        if "Part B" in name:
            return "writing_b", None
        return "writing_a", None

    # fallback
    return "unknown", None


def find_writing_b_image(year: int) -> str | None:
    """
    在 extracted_images/{year}/ 下查找 writing_b 图片并转 Base64

    Returns:
        "data:image/{ext};base64,..." 或 None
    """
    year_dir = IMAGE_ROOT / str(year)
    if not year_dir.exists():
        return None

    for ext in ("jpeg", "jpg", "png", "gif", "webp"):
        for candidate in year_dir.glob(f"*writing*b*.{ext}"):
            return _file_to_base64(candidate, ext)
        for candidate in year_dir.glob(f"*writing_b*.{ext}"):
            return _file_to_base64(candidate, ext)

    # 回退: 任何 writing 图片
    for f in year_dir.iterdir():
        if f.suffix.lower() in (".jpeg", ".jpg", ".png"):
            return _file_to_base64(f, f.suffix.lower().lstrip("."))

    return None


def _file_to_base64(filepath: Path, ext: str) -> str:
    """将图片文件转为 data URI"""
    mime_ext = "jpeg" if ext in ("jpg", "jpeg") else ext
    data = filepath.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/{mime_ext};base64,{b64}"


def build_q_id(year: int, section_type: str, question_id: int) -> str:
    """生成标准题目ID"""
    return f"{year}-eng1-{section_type}-q{question_id}"


# ============================================================================
#  主导入逻辑
# ============================================================================

def import_year(year: int, db_path: str):
    """核心 ETL: 导入指定年份的真题数据"""

    # === 1. 查找 JSON ===
    json_path = SOURCE_ROOT / f"{year}_full.json"
    if not json_path.exists():
        print(f"{RED}[ERROR] JSON not found: {json_path}{RESET}")
        return

    print(f"\n{BOLD}{CYAN}{'='*60}")
    print(f"  🐾 Project_Mia ETL — Importing {year} English I")
    print(f"{'='*60}{RESET}\n")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("meta", {})
    sections = data.get("sections", [])

    if meta.get("exam_type") and "II" in str(meta.get("exam_type")):
        print(f"{YELLOW}[SKIP] {year} appears to be English II. Skipping.{RESET}")
        return

    # === 2. 初始化数据库 ===
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_file}", echo=False)
    StaticBase.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # === 3. 创建 Paper 记录 ===
    paper_id = f"{year}-eng1"
    existing = session.query(Paper).filter_by(paper_id=paper_id).first()
    if existing:
        print(f"{YELLOW}[INFO] Paper '{paper_id}' exists. Replacing questions...{RESET}")
        session.query(Question).filter_by(paper_id=paper_id).delete()
    else:
        paper = Paper(
            paper_id=paper_id,
            year=year,
            exam_type="English I",
            title=f"{year}年考研英语一真题",
            total_score=100.0,
            time_limit=180,
        )
        session.add(paper)

    session.flush()

    # === 4. 遍历 sections ===
    stats = {}   # section_type → count
    errors = []
    image_found = False

    for sec in sections:
        sec_info = sec.get("section_info", {})
        section_type, group_name = resolve_section_type(sec_info)

        # 拼接文章文本
        article = sec.get("article", {})
        paragraphs = article.get("paragraphs", [])
        passage_text = "\n\n".join(paragraphs) if paragraphs else None

        # 词汇表 (存入 tags)
        vocab_list = sec.get("vocabulary", [])
        vocab_words = [v.get("word") for v in vocab_list if v.get("word")]

        questions = sec.get("questions", [])

        for q in questions:
            try:
                qid_num = q.get("id")
                if qid_num is None:
                    continue

                q_id = build_q_id(year, section_type, qid_num)

                # 判断客观/主观
                options = q.get("options", {})
                has_options = bool(options) and any(options.values())
                correct_raw = q.get("correct_answer", "")

                # 客观题: correct_answer 存选项字母
                # 主观题: correct_answer 为 None, answer_key 存参考答案
                if has_options and len(str(correct_raw)) <= 2:
                    correct_answer = str(correct_raw).strip().upper()
                    answer_key = None
                    q_type = "cloze" if section_type == "use_of_english" else "reading"
                else:
                    correct_answer = None
                    answer_key = str(correct_raw) if correct_raw else None
                    if section_type == "translation":
                        q_type = "translation"
                    elif section_type.startswith("writing"):
                        q_type = "writing"
                    else:
                        q_type = "reading"  # fallback (如 reading_b 排序题无选项)

                # 处理 Writing B 图片
                img_b64 = None
                if section_type == "writing_b":
                    # 优先: JSON 内嵌
                    if q.get("image"):
                        img_b64 = q["image"]
                        image_found = True

                # 分值
                score = SCORE_MAP.get(section_type, 2.0)

                # 构造 Question 对象
                question = Question(
                    q_id=q_id,
                    paper_id=paper_id,
                    q_type=q_type,
                    section_type=section_type,
                    section_name=sec_info.get("name"),
                    group_name=group_name,
                    question_number=qid_num,
                    passage_text=passage_text,
                    content=q.get("text"),
                    options_json=json.dumps(options, ensure_ascii=False) if has_options else None,
                    correct_answer=correct_answer,
                    answer_key=answer_key,
                    image_base64=img_b64,
                    official_analysis=q.get("analysis_raw"),
                    ai_persona_prompt=q.get("ai_persona_prompt"),
                    score=score,
                    difficulty=3,
                    tags=json.dumps(vocab_words, ensure_ascii=False) if vocab_words else None,
                )
                session.add(question)

                # 统计
                stats[section_type] = stats.get(section_type, 0) + 1

            except Exception as e:
                errors.append(f"Q{q.get('id', '?')}: {e}")
                continue

    # === 5. 图片补全 — 从 extracted_images/ ===
    if not image_found:
        ext_img = find_writing_b_image(year)
        if ext_img:
            # 找到 Writing B 题目并补图
            wb_q = session.query(Question).filter(
                Question.paper_id == paper_id,
                Question.section_type == "writing_b"
            ).first()
            if wb_q:
                wb_q.image_base64 = ext_img
                image_found = True
                print(f"{GREEN}[IMAGE] Found external image for {year} Writing B{RESET}")

    if not image_found:
        # 检查是否有 writing_b 题目
        has_wb = stats.get("writing_b", 0) > 0
        if has_wb:
            print(f"{RED}{BOLD}[WARNING] No image found for {year} Writing Part B!{RESET}")

    # === 6. 提交 ===
    session.commit()
    session.close()

    # === 7. 打印报告 ===
    total = sum(stats.values())
    print(f"\n{GREEN}{BOLD}✅ Imported {year}: {total} questions total{RESET}")
    print(f"{'─'*40}")

    type_labels = {
        "use_of_english": "完形填空 (Cloze)",
        "reading_a":      "阅读A (Text 1-4)",
        "reading_b":      "阅读B (Part B)",
        "translation":    "翻译 (Translation)",
        "writing_a":      "小作文 (Writing A)",
        "writing_b":      "大作文 (Writing B)",
    }
    for st, label in type_labels.items():
        count = stats.get(st, 0)
        if count:
            img_note = " 📷" if st == "writing_b" and image_found else ""
            print(f"  {label:.<30} {count:>3}{img_note}")

    if image_found:
        print(f"\n  {GREEN}Images: ✓ Writing Part B image loaded{RESET}")
    elif stats.get("writing_b", 0) > 0:
        print(f"\n  {RED}Images: ✗ MISSING Writing Part B image!{RESET}")
    else:
        print(f"\n  Images: N/A (no Writing B section)")

    if errors:
        print(f"\n{YELLOW}⚠ Errors ({len(errors)}):{RESET}")
        for e in errors[:10]:
            print(f"  {e}")
        if len(errors) > 10:
            print(f"  ... and {len(errors)-10} more")

    print(f"\n{CYAN}Database: {db_file.resolve()}{RESET}")
    print()


# ============================================================================
#  CLI 入口
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="🐾 Project_Mia ETL — Import English I exam data by year"
    )
    parser.add_argument(
        "--year", type=int, required=True,
        help="Year to import (e.g. 2010)"
    )
    parser.add_argument(
        "--db-path", type=str,
        default=str(PROJECT_ROOT / "backend" / "data" / "static_content.db"),
        help="Path to static_content.db"
    )

    args = parser.parse_args()
    import_year(args.year, args.db_path)


if __name__ == "__main__":
    main()
