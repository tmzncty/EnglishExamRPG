"""
数据库Schema定义 - Project_Mia
使用SQLAlchemy ORM定义两个数据库的表结构
"""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

# ============================================================================
# static_content.db - 静态内容数据库 (只读)
# ============================================================================

StaticBase = declarative_base()

class Paper(StaticBase):
    """试卷元数据表"""
    __tablename__ = 'papers'
    
    paper_id = Column(String(20), primary_key=True)  # '2011-eng1', '2023-eng2'
    year = Column(Integer, nullable=False, index=True)
    exam_type = Column(String(20))  # 'English I', 'English II'
    title = Column(String(100))
    total_score = Column(Float, default=100.0)
    time_limit = Column(Integer, default=180)  # 分钟
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    questions = relationship("Question", back_populates="paper")


class Question(StaticBase):
    """题目表 - 包含客观题和主观题"""
    __tablename__ = 'questions'
    
    q_id = Column(String(50), primary_key=True)  # '2023-eng1-reading-text1-q1'
    paper_id = Column(String(20), ForeignKey('papers.paper_id'), nullable=False, index=True)
    
    # 题目分类
    q_type = Column(String(20), nullable=False, index=True)  # 'reading', 'cloze', 'translation', 'writing'
    section_type = Column(String(30), index=True)  # 'use_of_english', 'reading_a', 'reading_b', 'translation', 'writing_a', 'writing_b'
    section_name = Column(String(100))  # 'Section II Part A Text 1'
    group_name = Column(String(50), nullable=True)  # 'Text 1', 'Text 2' 等分组名
    question_number = Column(Integer)  # 21
    
    # 题目内容
    passage_text = Column(Text)  # 阅读文章原文
    content = Column(Text)  # 题干
    options_json = Column(JSON)  # {"A": "...", "B": "...", "C": "...", "D": "..."}
    correct_answer = Column(String(10))  # 'C' 或 null (主观题)
    
    # 图片 (大作文配图)
    image_base64 = Column(Text, nullable=True)  # Writing B 配图 Base64
    
    # 解析
    official_analysis = Column(Text)  # 官方解析
    ai_persona_prompt = Column(Text, nullable=True)  # Mia人设台词
    answer_key = Column(Text)  # 主观题参考答案
    
    # 元数据
    difficulty = Column(Integer, default=3)  # 1-5
    score = Column(Float, default=2.0)
    tags = Column(JSON)  # ["vocabulary", "inference"]
    
    # 关系
    paper = relationship("Paper", back_populates="questions")


class Dictionary(StaticBase):
    """词典表 - 来自vocab_prebuilt.db"""
    __tablename__ = 'dictionary'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String(50), unique=True, nullable=False, index=True)
    meaning = Column(Text, nullable=False)  # "n. 倾向；易于"
    pos = Column(String(20))  # 'n.', 'v.', 'adj.'
    frequency = Column(Integer, default=0)  # 在真题中出现次数
    example_sentences = Column(JSON)  # 从sentences表预处理的例句列表
    created_at = Column(DateTime, default=datetime.utcnow)


class Story(StaticBase):
    """Mia剧情台词表 - 来自story_content.db"""
    __tablename__ = 'stories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    q_id = Column(String(50), nullable=False, index=True)
    year = Column(Integer)
    section_type = Column(String(50))
    
    # Galgame台词 (中英双语)
    correct_cn = Column(Text)
    wrong_cn = Column(Text)
    correct_en = Column(Text)
    wrong_en = Column(Text)


# ============================================================================
# femo_profile.db - 用户动态数据库 (读写)
# ============================================================================

ProfileBase = declarative_base()

class VocabProgress(ProfileBase):
    """词汇学习进度表 - SuperMemo 2算法"""
    __tablename__ = 'vocab_progress'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String(50), unique=True, nullable=False, index=True)
    
    # SM-2算法字段
    repetition = Column(Integer, default=0)  # 复习次数
    easiness_factor = Column(Float, default=2.5)  # EF值 (1.3-2.5)
    interval = Column(Integer, default=0)  # 间隔天数
    next_review = Column(DateTime, nullable=True, index=True)  # 下次复习时间
    last_review = Column(DateTime, nullable=True)
    
    # 错题本
    mistake_count = Column(Integer, default=0)  # 错误次数
    consecutive_correct = Column(Integer, default=0)  # 连续答对次数
    is_in_mistake_book = Column(Boolean, default=False, index=True)
    
    # 学习统计
    total_reviews = Column(Integer, default=0)
    correct_reviews = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ExamHistory(ProfileBase):
    """答题历史表 - 记录每一次答题"""
    __tablename__ = 'exam_history'
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    q_id = Column(String(50), nullable=False, index=True)
    
    # 答题结果
    user_answer = Column(String(10))  # 'C' 或主观题文本ID
    is_correct = Column(Boolean)
    score = Column(Float)  # 主观题得分(AI判分)
    max_score = Column(Float)
    
    # 元数据
    time_spent = Column(Integer)  # 秒
    attempt_count = Column(Integer, default=1)  # 第几次做这道题
    
    # AI反馈
    ai_feedback = Column(Text)  # 主观题的AI批改意见
    weak_words_detected = Column(JSON)  # ["prone", "inference"]
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class MiaMemory(ProfileBase):
    """Mia记忆库 - 存储Mia的长期记忆"""
    __tablename__ = 'mia_memory'
    
    memory_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 触发类型
    trigger_type = Column(String(50), nullable=False, index=True)
    # 'continuous_errors' - 连续错误
    # 'milestone_reached' - 里程碑(升级/完成试卷)
    # 'weak_topic_detected' - 薄弱知识点发现
    # 'long_absence' - 长时间未学习
    
    # 记忆内容
    content = Column(Text, nullable=False)
    # "绯墨今天在非谓语动词上连错3次"
    # "绯墨已经完成了2023年全部试卷"
    
    # 元数据
    related_topics = Column(JSON)  # ["non-finite_verbs", "grammar"]
    related_q_ids = Column(JSON)  # 相关题目ID列表
    importance = Column(Integer, default=1)  # 1-5 重要程度
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    used_count = Column(Integer, default=0)  # 被AI调用次数
    last_used_at = Column(DateTime, nullable=True)


class UserSettings(ProfileBase):
    """用户设置表"""
    __tablename__ = 'user_settings'
    
    key = Column(String(50), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GameSave(ProfileBase):
    """游戏存档表"""
    __tablename__ = 'game_saves'
    
    save_id = Column(Integer, primary_key=True, autoincrement=True)
    slot_id = Column(Integer, unique=True)  # 0=auto, 1-5=manual
    
    # 游戏进度
    current_paper_id = Column(String(20))
    current_q_index = Column(Integer, default=0)
    
    # 角色状态
    hp = Column(Integer, default=100)
    max_hp = Column(Integer, default=100)
    exp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    
    # Mia状态
    mia_mood = Column(String(20), default='normal')  # normal, happy, angry, sad
    mia_affection = Column(Integer, default=50)  # 好感度 0-100
    
    # 存档快照
    snapshot_json = Column(JSON)  # 完整状态快照
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Conversation(ProfileBase):
    """多轮对话会话表"""
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100))  # 会话标题
    bound_q_id = Column(String(50), nullable=True)  # 绑定的题目ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(ProfileBase):
    """对话消息表"""
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    image_base64 = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    conversation = relationship("Conversation", back_populates="messages")


# ============================================================================
# SQL建表语句(用于直接执行)
# ============================================================================

STATIC_CONTENT_SQL = """
-- static_content.db 建表SQL

CREATE TABLE IF NOT EXISTS papers (
    paper_id TEXT PRIMARY KEY,
    year INTEGER NOT NULL,
    exam_type TEXT,
    title TEXT,
    total_score REAL DEFAULT 100.0,
    time_limit INTEGER DEFAULT 180,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_papers_year ON papers(year);

CREATE TABLE IF NOT EXISTS questions (
    q_id TEXT PRIMARY KEY,
    paper_id TEXT NOT NULL,
    q_type TEXT NOT NULL,
    section_type TEXT,
    section_name TEXT,
    group_name TEXT,
    question_number INTEGER,
    passage_text TEXT,
    content TEXT,
    options_json TEXT,  -- JSON
    correct_answer TEXT,
    image_base64 TEXT,
    official_analysis TEXT,
    ai_persona_prompt TEXT,
    answer_key TEXT,
    difficulty INTEGER DEFAULT 3,
    score REAL DEFAULT 2.0,
    tags TEXT,  -- JSON
    FOREIGN KEY (paper_id) REFERENCES papers(paper_id)
);

CREATE INDEX idx_questions_paper ON questions(paper_id);
CREATE INDEX idx_questions_type ON questions(q_type);

CREATE TABLE IF NOT EXISTS dictionary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT UNIQUE NOT NULL,
    meaning TEXT NOT NULL,
    pos TEXT,
    frequency INTEGER DEFAULT 0,
    example_sentences TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dictionary_word ON dictionary(word);

CREATE TABLE IF NOT EXISTS stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    q_id TEXT NOT NULL,
    year INTEGER,
    section_type TEXT,
    correct_cn TEXT,
    wrong_cn TEXT,
    correct_en TEXT,
    wrong_en TEXT
);

CREATE INDEX idx_stories_qid ON stories(q_id);
"""

FEMO_PROFILE_SQL = """
-- femo_profile.db 建表SQL

CREATE TABLE IF NOT EXISTS vocab_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT UNIQUE NOT NULL,
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
);

CREATE INDEX idx_vocab_word ON vocab_progress(word);
CREATE INDEX idx_vocab_next_review ON vocab_progress(next_review);
CREATE INDEX idx_vocab_mistake_book ON vocab_progress(is_in_mistake_book);

CREATE TABLE IF NOT EXISTS exam_history (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    q_id TEXT NOT NULL,
    user_answer TEXT,
    is_correct BOOLEAN,
    score REAL,
    max_score REAL,
    time_spent INTEGER,
    attempt_count INTEGER DEFAULT 1,
    ai_feedback TEXT,
    weak_words_detected TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_exam_history_qid ON exam_history(q_id);
CREATE INDEX idx_exam_history_created ON exam_history(created_at);

CREATE TABLE IF NOT EXISTS mia_memory (
    memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
    trigger_type TEXT NOT NULL,
    content TEXT NOT NULL,
    related_topics TEXT,  -- JSON
    related_q_ids TEXT,  -- JSON
    importance INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP
);

CREATE INDEX idx_mia_memory_trigger ON mia_memory(trigger_type);
CREATE INDEX idx_mia_memory_importance ON mia_memory(importance DESC, created_at DESC);

CREATE TABLE IF NOT EXISTS user_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS game_saves (
    save_id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_id INTEGER UNIQUE,
    current_paper_id TEXT,
    current_q_index INTEGER DEFAULT 0,
    hp INTEGER DEFAULT 100,
    max_hp INTEGER DEFAULT 100,
    exp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    mia_mood TEXT DEFAULT 'normal',
    mia_affection INTEGER DEFAULT 50,
    snapshot_json TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入默认设置
INSERT OR IGNORE INTO user_settings (key, value) VALUES
    ('daily_vocab_goal', '40'),
    ('theme', 'acg'),
    ('sound_enabled', 'true'),
    ('auto_save', 'true'),
    ('difficulty_level', '3');
"""
