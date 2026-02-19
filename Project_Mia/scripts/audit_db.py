"""
audit_db.py — 真题数据库审计报告
扫描 static_content.db 输出各年份数据完整性报告

使用:
    python scripts/audit_db.py

Author: Femo
Date: 2026-02-18
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine, text

DB_PATH = PROJECT_ROOT / "backend" / "data" / "static_content.db"

# 颜色
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"


def main():
    if not DB_PATH.exists():
        print(f"{RED}[ERROR] Database not found: {DB_PATH}{RESET}")
        return

    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

    print(f"\n{BOLD}{CYAN}{'='*66}")
    print(f"  🐾 Project_Mia — Database Audit Report")
    print(f"{'='*66}{RESET}\n")
    print(f"  Database: {DB_PATH}\n")

    # Header
    print(f"  {'Year':<6}{'Total Qs':<10}{'Cloze':<7}{'RdA':<6}{'RdB':<6}{'Trans':<7}{'WrA':<6}{'WrB':<6}{'Image?':<10}{'Status'}")
    print(f"  {'─'*62}")

    total_all = 0
    years_ok = 0
    years_warn = 0
    issues = []

    with engine.connect() as conn:
        # 获取所有年份
        rows = conn.execute(text(
            "SELECT year FROM papers ORDER BY year"
        )).fetchall()

        for (year,) in rows:
            paper_id = f"{year}-eng1"

            # 各题型统计
            type_counts = {}
            result = conn.execute(text(
                "SELECT section_type, COUNT(*) FROM questions "
                "WHERE paper_id = :pid GROUP BY section_type"
            ), {"pid": paper_id}).fetchall()
            for st, cnt in result:
                type_counts[st] = cnt

            total = sum(type_counts.values())
            total_all += total

            cloze = type_counts.get("use_of_english", 0)
            rda   = type_counts.get("reading_a", 0)
            rdb   = type_counts.get("reading_b", 0)
            trans = type_counts.get("translation", 0)
            wra   = type_counts.get("writing_a", 0)
            wrb   = type_counts.get("writing_b", 0)

            # 图片检查
            img_row = conn.execute(text(
                "SELECT COUNT(*) FROM questions "
                "WHERE paper_id = :pid AND image_base64 IS NOT NULL"
            ), {"pid": paper_id}).fetchone()
            has_img = img_row[0] > 0 if img_row else False

            # 2025年大作文是数据表格题,无需配图
            no_image_ok = (year == 2025)

            # 状态判定
            if total >= 51 and (has_img or no_image_ok):
                status = f"{GREEN}✅ OK{RESET}"
                years_ok += 1
            elif total >= 51 and not has_img:
                status = f"{YELLOW}⚠ No img{RESET}"
                years_warn += 1
                issues.append(f"{year}: Missing Writing B image")
            else:
                status = f"{RED}❌ FAIL{RESET}"
                issues.append(f"{year}: Only {total} questions")

            img_str = "YES" if has_img else ("N/A (table)" if no_image_ok else "NO")

            print(f"  {year:<6}{total:<10}{cloze:<7}{rda:<6}{rdb:<6}{trans:<7}{wra:<6}{wrb:<6}{img_str:<10}{status}")

    print(f"  {'─'*62}")
    print(f"  {BOLD}Total Questions: {total_all}{RESET}")
    print(f"  Years OK: {GREEN}{years_ok}{RESET} | Warnings: {YELLOW}{years_warn}{RESET}\n")

    if issues:
        print(f"  {YELLOW}Issues:{RESET}")
        for issue in issues:
            print(f"    ⚠ {issue}")
        print()
    else:
        print(f"  {GREEN}{BOLD}🎉 All years passed audit!{RESET}\n")


if __name__ == "__main__":
    main()
