"""
test_memory_resonance.py — 阶段 3.0 集成测试
==============================================
验证 Mia 的"记忆共鸣"能力:
  1. 在 vocab_progress 中植入 "inexorable" 死对头记录
  2. 提取 2010 Text 1 文章 (含 "inexorable decline")
  3. 调用 MiaContextService 扫描 → 确认检测到 inexorable
  4. 调用 MiaPersonaService 构建 Prompt → 确认包含记忆指令
  5. 模拟 POST /api/mia/interact → 验证回复中提及 inexorable
  6. 清理: 删除伪造记录

Usage:
    python scripts/test_memory_resonance.py
"""

import sys
import json
import sqlite3
from pathlib import Path

# 添加后端到 path
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.db.helpers import PROFILE_DB, STATIC_DB

# --- 颜色 ---
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

PASS = f"{GREEN}[PASS]{RESET}"
FAIL = f"{RED}[FAIL]{RESET}"
INFO = f"{CYAN}[INFO]{RESET}"

TEST_WORD = "inexorable"
TEST_QID  = "2010-eng1-reading_a-q21"

passed = 0
failed = 0


def test_result(name: str, ok: bool, detail: str = ""):
    global passed, failed
    status = PASS if ok else FAIL
    print(f"  {status} {name}")
    if detail:
        print(f"         {DIM}{detail}{RESET}")
    if ok:
        passed += 1
    else:
        failed += 1


def main():
    print(f"\n{BOLD}{CYAN}{'='*60}")
    print(f"  🧪 Phase 3.0 — Memory Resonance Integration Test")
    print(f"{'='*60}{RESET}\n")

    # ========================================================
    # STEP 0: 前置 — 确认 2010 Text 1 文章含 inexorable
    # ========================================================
    print(f"  {BOLD}📋 Step 0: Pre-check{RESET}")

    sconn = sqlite3.connect(str(STATIC_DB))
    sconn.row_factory = sqlite3.Row
    row = sconn.execute(
        "SELECT passage_text, correct_answer FROM questions WHERE q_id = ?",
        (TEST_QID,),
    ).fetchone()
    sconn.close()

    if not row:
        print(f"  {RED}ABORT: Question {TEST_QID} not found in static_content.db!{RESET}")
        return

    article_text = row["passage_text"] or ""
    correct_answer = row["correct_answer"] or ""

    has_inexorable = TEST_WORD in article_text.lower()
    test_result(
        f"2010 Text 1 contains '{TEST_WORD}'",
        has_inexorable,
        f"Article length: {len(article_text)} chars",
    )

    if not has_inexorable:
        # 如果文章没有 inexorable, 尝试从同组其他题的文章中找
        sconn = sqlite3.connect(str(STATIC_DB))
        sconn.row_factory = sqlite3.Row
        rows = sconn.execute(
            """SELECT q_id, passage_text FROM questions
               WHERE paper_id = '2010-eng1' AND passage_text LIKE '%inexorable%'"""
        ).fetchall()
        sconn.close()
        if rows:
            article_text = rows[0]["passage_text"]
            has_inexorable = True
            print(f"         Found in {rows[0]['q_id']} instead")
        else:
            # 用一段包含 inexorable 的测试文本
            article_text = (
                "The decline of rural communities has been inexorable. "
                "Many factors contribute to this phenomenon, including urbanization."
            )
            print(f"         {YELLOW}Using synthetic test text with 'inexorable'{RESET}")

    # ========================================================
    # STEP 1: 植入 "死对头" 记录
    # ========================================================
    print(f"\n  {BOLD}🔧 Step 1: Inject '{TEST_WORD}' as weakness{RESET}")

    pconn = sqlite3.connect(str(PROFILE_DB))

    # 确保表存在
    pconn.execute("""
        CREATE TABLE IF NOT EXISTS vocab_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word VARCHAR(50) UNIQUE NOT NULL,
            repetition INTEGER DEFAULT 0,
            easiness_factor REAL DEFAULT 2.5,
            interval INTEGER DEFAULT 0,
            next_review TIMESTAMP,
            last_review TIMESTAMP,
            mistake_count INTEGER DEFAULT 0,
            consecutive_correct INTEGER DEFAULT 0,
            is_in_mistake_book BOOLEAN DEFAULT 0,
            total_reviews INTEGER DEFAULT 0,
            correct_reviews INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 也确保 dictionary 里有这个词
    dconn = sqlite3.connect(str(STATIC_DB))
    dict_row = dconn.execute("SELECT word FROM dictionary WHERE word = ?", (TEST_WORD,)).fetchone()
    if not dict_row:
        dconn.execute(
            "INSERT OR IGNORE INTO dictionary (word, meaning, pos, frequency) VALUES (?, ?, ?, ?)",
            (TEST_WORD, "adj. 不可遏制的; 不可阻挡的", "adj.", 1),
        )
        dconn.commit()
        print(f"         Added '{TEST_WORD}' to dictionary")
    dconn.close()

    # 插入死对头记录: EF=1.3, 错3次
    pconn.execute("""
        INSERT OR REPLACE INTO vocab_progress
            (word, repetition, easiness_factor, interval,
             mistake_count, consecutive_correct, is_in_mistake_book,
             total_reviews, correct_reviews)
        VALUES (?, 2, 1.3, 1, 3, 0, 1, 5, 2)
    """, (TEST_WORD,))
    pconn.commit()

    # 验证
    check = pconn.execute(
        "SELECT * FROM vocab_progress WHERE word = ?", (TEST_WORD,)
    ).fetchone()
    pconn.close()

    test_result(
        f"'{TEST_WORD}' injected as weakness (EF=1.3, mistakes=3)",
        check is not None,
    )

    # ========================================================
    # STEP 2: 记忆共鸣扫描
    # ========================================================
    print(f"\n  {BOLD}🧠 Step 2: Vocab Resonance Scan{RESET}")

    from app.services.context_service import context_service

    resonance = context_service.get_vocab_resonance(article_text)

    test_result(
        "Resonance scan returned results",
        len(resonance) > 0,
        f"Found {len(resonance)} resonant words",
    )

    # 查找 inexorable
    inexorable_hit = None
    for r in resonance:
        if r["word"] == TEST_WORD:
            inexorable_hit = r
            break

    test_result(
        f"'{TEST_WORD}' detected in resonance",
        inexorable_hit is not None,
        f"Details: {json.dumps(inexorable_hit, ensure_ascii=False)}" if inexorable_hit else "",
    )

    if inexorable_hit:
        test_result(
            f"'{TEST_WORD}' classified as 'weak' (死对头)",
            inexorable_hit["status"] == "weak",
            f"status={inexorable_hit['status']}, ef={inexorable_hit['ef']}",
        )

    # ========================================================
    # STEP 3: 用户状态快照
    # ========================================================
    print(f"\n  {BOLD}📊 Step 3: User Status Snapshot{RESET}")

    snapshot = context_service.get_user_status_snapshot()

    test_result(
        "Status snapshot has HP",
        "hp" in snapshot and "max_hp" in snapshot,
        f"HP={snapshot.get('hp')}/{snapshot.get('max_hp')}",
    )

    test_result(
        "Vocab stats present",
        snapshot.get("total_vocab_learned", 0) > 0,
        f"Learned: {snapshot.get('total_vocab_learned')}, Weak: {snapshot.get('weak_vocab_count')}",
    )

    # ========================================================
    # STEP 4: Prompt 构建
    # ========================================================
    print(f"\n  {BOLD}🎭 Step 4: Persona Prompt Construction{RESET}")

    from app.services.persona_service import persona_service

    context = {
        "vocab_resonance": resonance,
        "user_snapshot": snapshot,
        "question_info": {
            "q_id": TEST_QID,
            "user_answer": "B",
            "correct_answer": correct_answer,
            "article_snippet": article_text[:300],
        },
    }

    prompt = persona_service.construct_system_prompt(context, mood="focused")

    test_result(
        "Prompt contains base persona",
        "Mia" in prompt and "绯墨" in prompt,
        f"Prompt length: {len(prompt)} chars",
    )

    test_result(
        f"Prompt contains '{TEST_WORD}' (记忆共鸣注入)",
        TEST_WORD in prompt,
    )

    test_result(
        "Prompt contains '死对头' marker",
        "死对头" in prompt,
    )

    test_result(
        "Prompt contains forced mention instruction",
        "强制" in prompt,
    )

    # 打印 Prompt (方便调试)
    print(f"\n  {DIM}{'─'*56}{RESET}")
    print(f"  {BOLD}📄 Generated System Prompt (preview):{RESET}")
    for line in prompt.split("\n")[:25]:
        print(f"  {DIM}  {line}{RESET}")
    if prompt.count("\n") > 25:
        print(f"  {DIM}  ... ({prompt.count(chr(10))-25} more lines){RESET}")
    print(f"  {DIM}{'─'*56}{RESET}")

    # ========================================================
    # STEP 5: Mock Agent 回复验证
    # ========================================================
    print(f"\n  {BOLD}🤖 Step 5: Mock Agent Response{RESET}")

    # 直接调用 mock (不需要启动 FastAPI server)
    from app.api.agent import _generate_mock_reply

    mock_context = {
        "q_id": TEST_QID,
        "user_answer": "B",
        "correct_answer": correct_answer,
        "_mock_weak_words": [inexorable_hit] if inexorable_hit else [],
    }
    mock_reply = _generate_mock_reply("focused", mock_context)

    print(f"\n  {BOLD}💬 Mia says:{RESET}")
    for line in mock_reply.split("\n"):
        print(f"  {CYAN}  {line}{RESET}")

    test_result(
        f"Mock reply mentions '{TEST_WORD}'",
        TEST_WORD in mock_reply.lower(),
    )

    # ========================================================
    # STEP 6: 清理
    # ========================================================
    print(f"\n  {BOLD}🧹 Step 6: Cleanup{RESET}")

    pconn = sqlite3.connect(str(PROFILE_DB))
    pconn.execute("DELETE FROM vocab_progress WHERE word = ?", (TEST_WORD,))
    pconn.commit()

    verify_gone = pconn.execute(
        "SELECT COUNT(*) FROM vocab_progress WHERE word = ?", (TEST_WORD,)
    ).fetchone()
    pconn.close()

    cleaned = verify_gone[0] == 0
    test_result("Test data cleaned up", cleaned)

    # ========================================================
    # 总结
    # ========================================================
    print(f"\n{'='*60}")
    total = passed + failed
    if failed == 0:
        print(f"  {GREEN}{BOLD}🎉 ALL {total} TESTS PASSED!{RESET}")
        print(f"  Mia 的记忆共鸣功能已验证!")
    else:
        print(f"  {RED}{BOLD}⚠ {failed}/{total} TESTS FAILED{RESET}")
    print(f"  Passed: {GREEN}{passed}{RESET}  Failed: {RED}{failed}{RESET}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
