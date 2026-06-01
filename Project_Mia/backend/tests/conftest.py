"""Project Mia 测试基础设施 — 共享 fixtures"""
import pytest
import pytest_asyncio
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import patch

# ──────────────────────────────────────────────
# 测试数据库 schema 与种子数据
# ──────────────────────────────────────────────

STATIC_DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
    paper_id VARCHAR(20) PRIMARY KEY,
    year INTEGER NOT NULL,
    exam_type VARCHAR(20),
    title VARCHAR(100),
    total_score FLOAT DEFAULT 100.0,
    time_limit INTEGER DEFAULT 180,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS questions (
    q_id VARCHAR(50) PRIMARY KEY,
    paper_id VARCHAR(20) NOT NULL,
    q_type VARCHAR(20) NOT NULL,
    section_type VARCHAR(30),
    section_name VARCHAR(100),
    group_name VARCHAR(50),
    question_number INTEGER,
    passage_text TEXT,
    content TEXT,
    options_json TEXT,
    correct_answer VARCHAR(10),
    image_base64 TEXT,
    official_analysis TEXT,
    ai_persona_prompt TEXT,
    answer_key TEXT,
    difficulty INTEGER DEFAULT 3,
    score FLOAT DEFAULT 2.0,
    tags TEXT
);

CREATE TABLE IF NOT EXISTS vocabulary (
    word TEXT PRIMARY KEY,
    phonetic TEXT,
    pos TEXT,
    meanings TEXT,
    sentences TEXT
);
"""

STATIC_DB_SEED = """
INSERT OR IGNORE INTO papers VALUES ('2023-eng1', 2023, 'English I', '2023年考研英语一', 100.0, 180, '2024-01-01');

INSERT OR IGNORE INTO questions VALUES 
('2023-eng1-cloze-q1', '2023-eng1', 'cloze', 'use_of_english', 'Section I', NULL, 1, 
 'Long passage text here...', 'The caravanserai was ___ than a mere inn.',
 '{"A":"more","B":"less","C":"rather","D":"other"}', 'A',
 NULL, NULL, NULL, NULL, 2, 0.5, NULL),
('2023-eng1-reading-text1-q21', '2023-eng1', 'reading', 'reading_a', 'Section II Part A Text 1', 'Text 1', 21,
 'Reading passage about climate...', 'According to Paragraph 1, the author argues that ___',
 '{"A":"Option A","B":"Option B","C":"Option C","D":"Option D"}', 'C',
 NULL, NULL, NULL, NULL, 3, 2.0, NULL),
('2023-eng1-translation-q1', '2023-eng1', 'translation', 'translation', 'Section III', NULL, 1,
 NULL, 'Translate the underlined sentence.',
 NULL, NULL, NULL, NULL, NULL, '标准翻译答案', 3, 2.0, NULL),
('2023-eng1-writing-a-1', '2023-eng1', 'writing', 'writing_a', 'Section IV Part A', NULL, 1,
 NULL, 'Write a notice of about 100 words.', NULL, NULL,
 NULL, NULL, NULL, 'Notice writing sample', 3, 10.0, NULL),
('2023-eng1-writing-b-1', '2023-eng1', 'writing', 'writing_b', 'Section IV Part B', NULL, 1,
 NULL, 'Write an essay of 160-200 words based on the picture.', NULL, NULL,
 NULL, NULL, NULL, 'Essay writing sample', 4, 20.0, NULL);

INSERT OR IGNORE INTO vocabulary VALUES
('abandon', '/əˈbændən/', 'v.', '["放弃","抛弃","放纵"]', '[{"en":"He abandoned his plan.","zh":"他放弃了他的计划。"}]'),
('persistent', '/pərˈsɪstənt/', 'adj.', '["坚持的","持续的"]', '[{"en":"She is persistent in her efforts.","zh":"她坚持不懈。"}]'),
('notorious', '/noʊˈtɔriəs/', 'adj.', '["臭名昭著的"]', '[]'),
('serendipity', '/ˌserənˈdɪpəti/', 'n.', '["意外发现珍奇事物的本领"]', '[]'),
('vocab5', '/test/', 'n.', '["测试"]', '[{"en":"Test sentence.","zh":"测试句。"}]');
"""


def _create_static_db(db_path: Path):
    """创建测试用 static_content.db"""
    conn = sqlite3.connect(str(db_path))
    conn.executescript(STATIC_DB_SCHEMA)
    conn.executescript(STATIC_DB_SEED)
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture(scope="session")
def temp_data_dir():
    """Session-scoped 临时数据目录，隔离生产数据库"""
    import shutil
    tmpdir = Path(tempfile.mkdtemp(prefix="mia_test_"))
    static_db = tmpdir / "static_content.db"
    profile_db = tmpdir / "femo_profile.db"

    _create_static_db(static_db)

    # ── Monkeypatch 数据库路径 (在所有 app import 之前) ──
    import app.db.helpers as helpers
    import app.db.session as session_mod

    helpers.DATA_DIR = tmpdir
    helpers.STATIC_DB = static_db
    helpers.PROFILE_DB = profile_db

    session_mod.DATA_DIR = tmpdir
    session_mod.STATIC_DB_PATH = static_db
    session_mod.PROFILE_DB_PATH = profile_db

    # 重建 SQLAlchemy engines（指向临时数据库）
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    session_mod.static_engine = create_engine(f"sqlite:///{static_db}", echo=False)
    session_mod.profile_engine = create_engine(f"sqlite:///{profile_db}", echo=False)
    session_mod.StaticSessionLocal = sessionmaker(bind=session_mod.static_engine)
    session_mod.ProfileSessionLocal = sessionmaker(bind=session_mod.profile_engine)

    yield tmpdir

    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture(scope="session")
def app(temp_data_dir):
    """FastAPI 测试应用"""
    from app.main import app
    # 确保 conversations/messages 表存在
    import app.db.helpers as _helpers2
    with _helpers2.get_profile_conn() as _conn:
        _conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                bound_q_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                attempt_id INTEGER,
                word_id TEXT
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                image_base64 TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        _conn.commit()
    return app


@pytest_asyncio.fixture
async def client(app):
    """Async HTTP 测试客户端"""
    from httpx import AsyncClient, ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def mock_llm():
    """Mock LLM service — 返回预设 Mia 回复"""
    with patch('app.services.llm_service.llm_service.generate_stream') as mock_stream:
        async def fake_stream(*args, **kwargs):
            yield "测试回复：喵！这道题很简单喵～"
        mock_stream.side_effect = fake_stream
        yield mock_stream
