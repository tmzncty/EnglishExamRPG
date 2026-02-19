"""
quality_check.py — 阶段 2.8: 答案完整性深度质检
===================================================
扫描 static_content.db，对每道题的 correct_answer / answer_key / official_analysis
进行完整性和格式校验，输出缺陷报告。

字段映射（由 import_exam_data.py 导入时决定）:
  - 客观题 (use_of_english, reading_a):
      correct_answer = 单字母 A/B/C/D
  - 客观题 (reading_b):
      correct_answer 或 answer_key = 单字母 A-H (导入脚本不一致，两字段都要检查)
  - 主观题 (translation, writing_a, writing_b):
      answer_key = 参考译文/范文 (correct_answer 为空)

Usage:
    python scripts/quality_check.py
"""

import sqlite3
from pathlib import Path
from collections import defaultdict
import re

DB_PATH = Path(__file__).resolve().parent.parent / "backend" / "data" / "static_content.db"

# --- 颜色常量 ---
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

# --- 合法答案字母 ---
VALID_OBJECTIVE = set("ABCDEFGH")


def check_objective_answer(value, section_type):
    """检查客观题答案格式。返回 (is_valid, issue_description)"""
    if value is None or value.strip() == "":
        return False, "MISSING"
    cleaned = value.strip().upper()
    # 清洗: 去掉 'A.' / 'Answer: A' 等格式
    cleaned = re.sub(r"^(answer\s*[:：]\s*)", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.rstrip(".").strip()
    if len(cleaned) == 1 and cleaned in VALID_OBJECTIVE:
        if cleaned != value.strip():
            return True, f"DIRTY_FORMAT({value.strip()}->{cleaned})"
        return True, None
    return False, f"INVALID_FORMAT({repr(value.strip())})"


def check_subjective_answer(value, section_type):
    """检查主观题答案(参考译文/范文)。返回 (is_valid, issue_description)"""
    if value is None or value.strip() == "":
        return False, "MISSING_REFERENCE_ANSWER"
    text = value.strip()
    if len(text) < 10:
        return False, f"TOO_SHORT(len={len(text)})"
    if text.startswith("[待补充"):
        return False, "PLACEHOLDER"
    return True, None


def main():
    if not DB_PATH.exists():
        print(f"{RED}[ERROR] Database not found: {DB_PATH}{RESET}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # --- 获取所有年份 ---
    cursor.execute("SELECT DISTINCT year FROM papers ORDER BY year")
    years = [r[0] for r in cursor.fetchall()]

    print(f"\n{BOLD}{CYAN}{'='*80}")
    print(f"  🔍 Project_Mia — 阶段 2.8 答案完整性深度质检")
    print(f"{'='*80}{RESET}\n")
    print(f"  Database: {DB_PATH}\n")

    # --- Section Type 分类 ---
    OBJECTIVE_CA = {"use_of_english", "reading_a"}       # correct_answer = 字母
    OBJECTIVE_EITHER = {"reading_b"}                      # correct_answer 或 answer_key = 字母
    SUBJECTIVE   = {"translation", "writing_a", "writing_b"}  # answer_key = 参考文本

    # --- 统计結果 ---
    total_defects = 0
    total_dirty = 0
    total_questions = 0
    analysis_present = 0
    analysis_total = 0
    defect_details = []   # (year, q_id, section_type, issue)

    SECTION_ORDER = ["use_of_english", "reading_a", "reading_b", "translation", "writing_a", "writing_b"]
    SECTION_LABEL = {
        "use_of_english": "Cloze",
        "reading_a": "RdA",
        "reading_b": "RdB",
        "translation": "Trans",
        "writing_a": "WrA",
        "writing_b": "WrB",
    }

    # --- Header ---
    header = f"  {'Year':<6}"
    for st in SECTION_ORDER:
        header += f"{SECTION_LABEL[st]:>8}"
    header += f"  {'Analysis%':>10}  {'Status'}"
    print(header)
    print(f"  {'─'*76}")

    for year in years:
        paper_id = f"{year}-eng1"
        cursor.execute(
            "SELECT q_id, section_type, correct_answer, answer_key, official_analysis "
            "FROM questions WHERE paper_id=? ORDER BY question_number",
            (paper_id,)
        )
        rows = cursor.fetchall()

        year_defects = defaultdict(int)
        year_dirty = defaultdict(int)
        year_ok = defaultdict(int)
        year_analysis_hit = 0
        year_analysis_total = 0

        for q_id, section_type, correct_answer, answer_key, analysis in rows:
            total_questions += 1
            year_analysis_total += 1
            analysis_total += 1

            # 解析检查
            if analysis and len(analysis.strip()) > 5:
                year_analysis_hit += 1
                analysis_present += 1

            # 答案检查
            if section_type in OBJECTIVE_CA:
                valid, issue = check_objective_answer(correct_answer, section_type)
                if not valid:
                    year_defects[section_type] += 1
                    total_defects += 1
                    defect_details.append((year, q_id, section_type, issue))
                elif issue and "DIRTY" in issue:
                    year_dirty[section_type] += 1
                    total_dirty += 1
                    defect_details.append((year, q_id, section_type, issue))
                else:
                    year_ok[section_type] += 1

            elif section_type in OBJECTIVE_EITHER:
                # Reading B: 导入脚本不一致，有的年份存 correct_answer，有的存 answer_key
                val = correct_answer if (correct_answer and correct_answer.strip()) else answer_key
                valid, issue = check_objective_answer(val, section_type)
                if not valid:
                    year_defects[section_type] += 1
                    total_defects += 1
                    defect_details.append((year, q_id, section_type, issue))
                elif issue and "DIRTY" in issue:
                    year_dirty[section_type] += 1
                    total_dirty += 1
                    defect_details.append((year, q_id, section_type, issue))
                else:
                    year_ok[section_type] += 1

            elif section_type in SUBJECTIVE:
                valid, issue = check_subjective_answer(answer_key, section_type)
                if not valid:
                    year_defects[section_type] += 1
                    total_defects += 1
                    defect_details.append((year, q_id, section_type, issue))
                else:
                    year_ok[section_type] += 1

            else:
                defect_details.append((year, q_id, section_type, f"UNKNOWN_TYPE({section_type})"))
                total_defects += 1

        # --- 输出本年行 ---
        line = f"  {year:<6}"
        year_has_issue = False
        for st in SECTION_ORDER:
            defects = year_defects.get(st, 0)
            dirty = year_dirty.get(st, 0)
            if defects > 0:
                line += f"{RED}{defects:>7}!{RESET}"
                year_has_issue = True
            elif dirty > 0:
                line += f"{YELLOW}{dirty:>7}~{RESET}"
            else:
                line += f"{GREEN}{'0':>8}{RESET}"

        # 解析覆盖率
        pct = (year_analysis_hit / year_analysis_total * 100) if year_analysis_total else 0
        if pct >= 90:
            line += f"  {GREEN}{pct:>8.0f}%{RESET}"
        elif pct >= 50:
            line += f"  {YELLOW}{pct:>8.0f}%{RESET}"
        else:
            line += f"  {RED}{pct:>8.0f}%{RESET}"

        if year_has_issue:
            line += f"  {RED}⚠ DEFECT{RESET}"
        else:
            line += f"  {GREEN}✅ OK{RESET}"
        print(line)

    print(f"  {'─'*76}")
    # --- 汇总 ---
    print(f"\n{BOLD}  📊 汇总{RESET}")
    print(f"  Total Questions:   {total_questions}")
    print(f"  Total Defects:     {RED if total_defects else GREEN}{total_defects}{RESET}")
    print(f"  Dirty Formats:     {YELLOW if total_dirty else GREEN}{total_dirty}{RESET}")

    analysis_pct = (analysis_present / analysis_total * 100) if analysis_total else 0
    print(f"  Analysis Coverage: {analysis_present}/{analysis_total} ({analysis_pct:.1f}%)")

    # --- 详细缺陷列表 ---
    if defect_details:
        print(f"\n{BOLD}{RED}  ⚠ 缺陷明细 ({len(defect_details)} items){RESET}")
        print(f"  {'Year':<6}{'Q_ID':<35}{'Type':<18}{'Issue'}")
        print(f"  {'─'*76}")
        for year, q_id, st, issue in defect_details:
            color = RED if "MISSING" in issue or "INVALID" in issue else YELLOW
            print(f"  {year:<6}{q_id:<35}{st:<18}{color}{issue}{RESET}")
    else:
        print(f"\n  {GREEN}{BOLD}🎉 全部通过！无任何缺陷。{RESET}")

    conn.close()

    # --- Return code ---
    if total_defects > 0:
        print(f"\n  {RED}Exit code: 1 (有缺陷需要修复){RESET}\n")
        exit(1)
    else:
        print(f"\n  {GREEN}Exit code: 0 (全部通过){RESET}\n")
        exit(0)


if __name__ == "__main__":
    main()
