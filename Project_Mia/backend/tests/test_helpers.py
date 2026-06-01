"""T2: helpers.py 单元测试 — ensure_auto_save 表创建逻辑"""
import sqlite3
import pytest
from pathlib import Path
import tempfile

from app.db.helpers import ensure_auto_save


@pytest.fixture
def temp_db():
    """临时 SQLite 文件数据库连接"""
    tmpdir = Path(tempfile.mkdtemp())
    db_path = tmpdir / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = lambda c, r: {col[0]: r[i] for i, col in enumerate(c.description)}
    yield conn
    conn.close()
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)


class TestEnsureAutoSave:
    """ensure_auto_save 表创建与迁移"""

    def test_creates_all_required_tables(self, temp_db):
        """应创建所有核心表"""
        ensure_auto_save(temp_db)
        tables = temp_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = {t["name"] for t in tables}
        for required in [
            "game_saves", "user_answers", "exam_attempts",
            "attempt_question_times", "vocab_sessions",
            "vocab_session_words"
        ]:
            assert required in table_names, f"Missing table: {required}"

    def test_game_saves_has_required_columns(self, temp_db):
        """game_saves 表应有完整字段"""
        ensure_auto_save(temp_db)
        cols = temp_db.execute("PRAGMA table_info(game_saves)").fetchall()
        col_names = {c["name"] for c in cols}
        for required in [
            "save_id", "slot_id", "hp", "max_hp", "level", "exp",
            "mia_mood", "daily_new_words_limit", "slot_name",
            "daily_reset_time", "today_learned_count", "today_reviewed_count",
            "last_reset_day", "daily_streak", "today_focus_time",
            "snapshot_json", "current_paper_id"
        ]:
            assert required in col_names, f"Missing column: {required}"

    def test_game_saves_defaults(self, temp_db):
        """game_saves 默认值正确"""
        ensure_auto_save(temp_db)
        temp_db.execute("INSERT OR IGNORE INTO game_saves (slot_id) VALUES (0)")
        temp_db.commit()
        row = temp_db.execute("SELECT hp, max_hp, level, mia_mood FROM game_saves WHERE slot_id=0").fetchone()
        assert row["hp"] == 100
        assert row["max_hp"] == 100
        assert row["level"] == 1
        assert row["mia_mood"] == "normal"

    def test_idempotent(self, temp_db):
        """多次调用 ensure_auto_save 不会出错"""
        for _ in range(5):
            ensure_auto_save(temp_db)
        # 不应抛异常

    def test_exam_attempts_table_schema(self, temp_db):
        """exam_attempts 表结构"""
        ensure_auto_save(temp_db)
        cols = temp_db.execute("PRAGMA table_info(exam_attempts)").fetchall()
        col_names = {c["name"] for c in cols}
        for required in [
            "attempt_id", "slot_id", "paper_id", "attempt_number",
            "status", "total_time", "total_score", "started_at", "finished_at"
        ]:
            assert required in col_names

    def test_user_answers_table_schema(self, temp_db):
        """user_answers 表结构"""
        ensure_auto_save(temp_db)
        cols = temp_db.execute("PRAGMA table_info(user_answers)").fetchall()
        col_names = {c["name"] for c in cols}
        for required in [
            "id", "attempt_id", "slot_id", "q_id", "section_type",
            "user_answer", "score", "is_correct", "ai_feedback"
        ]:
            assert required in col_names

    def test_vocab_sessions_table_schema(self, temp_db):
        """vocab_sessions 表结构"""
        ensure_auto_save(temp_db)
        cols = temp_db.execute("PRAGMA table_info(vocab_sessions)").fetchall()
        col_names = {c["name"] for c in cols}
        for required in ["session_id", "slot_id", "total_time", "words_learned", "words_reviewed"]:
            assert required in col_names

    def test_attempt_question_times_unique_constraint(self, temp_db):
        """attempt_question_times 有 UNIQUE(attempt_id, q_id)"""
        ensure_auto_save(temp_db)
        idxs = temp_db.execute("PRAGMA index_list(attempt_question_times)").fetchall()
        # SQLite UNIQUE creates an auto-index
        has_unique = any(
            "unique" in (idx.get("origin", "") or "").lower()
            or "auto" in str(idx).lower()
            for idx in idxs
        )
        # At minimum, the table should exist without error
        temp_db.execute(
            "INSERT INTO attempt_question_times (attempt_id, q_id, time_spent) VALUES (1, 'q1', 30)"
        )
        temp_db.commit()
        # Second insert with same keys should fail
        import pytest
        with pytest.raises(sqlite3.IntegrityError):
            temp_db.execute(
                "INSERT INTO attempt_question_times (attempt_id, q_id, time_spent) VALUES (1, 'q1', 40)"
            )
