"""
数据迁移脚本: V1 → V2
将原EnglishExamWeb的7个数据库合并为Project_Mia的2个数据库

作者: 绯墨 (Femo)
日期: 2026-02-15
"""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class DatabaseMigrator:
    def __init__(self, old_root: str, new_root: str):
        self.old_root = Path(old_root)
        self.new_root = Path(new_root)
        
        # 旧数据库路径
        self.old_dbs = {
            'webnav': self.old_root / 'EnglishExamWeb' / 'webnav_rpg.db',
            'story': self.old_root / 'EnglishExamWeb' / 'story_content.db',
            'user_vocab': self.old_root / 'VocabWeb' / 'user_vocab.db',
            'vocab_prebuilt': self.old_root / 'VocabWeb' / 'vocab_prebuilt.db',
        }
        
        # 新数据库路径
        self.new_static_db = self.new_root / 'backend' / 'data' / 'static_content.db'
        self.new_profile_db = self.new_root / 'backend' / 'data' / 'femo_profile.db'
        
        # JSON数据目录
        self.json_dir = self.old_root / 'EnglishExamWeb' / 'data'
        
        self.stats = {
            'papers': 0,
            'questions': 0,
            'dictionary': 0,
            'stories': 0,
            'vocab_progress': 0,
            'exam_history': 0,
        }
    
    def run(self):
        """执行完整迁移流程"""
        print("🚀 开始数据迁移: EnglishExamWeb V1 → Project_Mia V2")
        print("=" * 60)
        
        # 1. 验证旧数据库存在
        self._validate_old_dbs()
        
        # 2. 创建新数据库
        self._create_new_dbs()
        
        # 3. 迁移静态内容
        self._migrate_static_content()
        
        # 4. 迁移用户数据
        self._migrate_user_data()
        
        # 5. 数据验证
        self._validate_migration()
        
        # 6. 生成报告
        self._generate_report()
        
        print("\n✅ 迁移完成!")
    
    def _validate_old_dbs(self):
        """验证旧数据库文件存在"""
        print("\n📋 检查旧数据库文件...")
        missing = []
        for name, path in self.old_dbs.items():
            if path.exists():
                print(f"  ✓ {name}: {path}")
            else:
                print(f"  ✗ {name}: {path} (缺失)")
                missing.append(name)
        
        if missing:
            raise FileNotFoundError(f"缺少数据库: {', '.join(missing)}")
    
    def _create_new_dbs(self):
        """创建新数据库并初始化表结构"""
        print("\n🏗️  创建新数据库...")
        
        # 确保目录存在
        self.new_static_db.parent.mkdir(parents=True, exist_ok=True)
        
        # 读取建表SQL
        models_path = self.new_root / 'backend' / 'app' / 'db' / 'models.py'
        with open(models_path, 'r', encoding='utf-8') as f:
            content = f.read()
            static_sql = content.split('STATIC_CONTENT_SQL = """')[1].split('"""')[0]
            profile_sql = content.split('FEMO_PROFILE_SQL = """')[1].split('"""')[0]
        
        # 创建static_content.db
        print(f"  创建: {self.new_static_db}")
        conn = sqlite3.connect(self.new_static_db)
        conn.executescript(static_sql)
        conn.commit()
        conn.close()
        
        # 创建femo_profile.db
        print(f"  创建: {self.new_profile_db}")
        conn = sqlite3.connect(self.new_profile_db)
        conn.executescript(profile_sql)
        conn.commit()
        conn.close()
    
    def _migrate_static_content(self):
        """迁移静态内容到static_content.db"""
        print("\n📚 迁移静态内容...")
        
        conn = sqlite3.connect(self.new_static_db)
        cursor = conn.cursor()
        
        # 1. 迁移试卷和题目数据 (从JSON文件)
        self._migrate_exam_papers(cursor)
        
        # 2. 迁移词典数据 (从vocab_prebuilt.db)
        self._migrate_dictionary(cursor)
        
        # 3. 迁移剧情数据 (从story_content.db)
        self._migrate_stories(cursor)
        
        conn.commit()
        conn.close()
    
    def _migrate_exam_papers(self, cursor):
        """从JSON文件迁移试卷和题目数据"""
        print("  ⏳ 正在迁移试卷数据...")
        
        json_files = sorted(self.json_dir.glob("20*.json"))
        
        for json_path in json_files:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            meta = data.get('meta', {})
            year = meta.get('year')
            exam_type = meta.get('exam_type', 'English I')
            
            if not year:
                continue
            
            paper_id = f"{year}-{exam_type.lower().replace(' ', '')}"
            
            # 插入paper
            cursor.execute("""
                INSERT OR IGNORE INTO papers (paper_id, year, exam_type, title, total_score, time_limit)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                paper_id,
                year,
                exam_type,
                f"{year}年考研英语{exam_type.split()[-1]}",
                meta.get('total_score', 100.0),
                meta.get('time_limit', 180)
            ))
            self.stats['papers'] += 1
            
            # 插入questions
            questions = self._extract_questions_from_json(data, paper_id)
            for q in questions:
                cursor.execute("""
                    INSERT OR IGNORE INTO questions 
                    (q_id, paper_id, q_type, section_name, question_number, passage_text, 
                     content, options_json, correct_answer, official_analysis, difficulty, score, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    q['q_id'],
                    paper_id,
                    q['q_type'],
                    q.get('section_name'),
                    q.get('question_number'),
                    q.get('passage_text'),
                    q.get('content'),
                    json.dumps(q.get('options'), ensure_ascii=False) if q.get('options') else None,
                    q.get('correct_answer'),
                    q.get('official_analysis'),
                    q.get('difficulty', 3),
                    q.get('score', 2.0),
                    json.dumps(q.get('tags', []), ensure_ascii=False)
                ))
                self.stats['questions'] += 1
        
        print(f"    ✓ 迁移 {self.stats['papers']} 份试卷, {self.stats['questions']} 道题目")
    
    def _extract_questions_from_json(self, data: Dict, paper_id: str) -> List[Dict]:
        """从JSON数据中提取题目"""
        questions = []
        sections = data.get('sections', [])
        
        for section in sections:
            section_info = section.get('section_info', {})
            section_name = section_info.get('name', '')
            section_type = section_info.get('type', '')
            
            # 处理parts
            parts = section.get('parts', [])
            for part in parts:
                passage_text = part.get('content', '')
                
                # 处理questions
                part_questions = part.get('questions', [])
                for q in part_questions:
                    q_num = q.get('number')
                    q_id = f"{paper_id}-{section_type.lower()}-q{q_num}"
                    
                    questions.append({
                        'q_id': q_id,
                        'q_type': section_type.lower(),
                        'section_name': section_name,
                        'question_number': q_num,
                        'passage_text': passage_text,
                        'content': q.get('text', ''),
                        'options': q.get('options', {}),
                        'correct_answer': q.get('answer'),
                        'official_analysis': q.get('analysis', ''),
                        'difficulty': 3,
                        'score': q.get('score', 2.0),
                        'tags': []
                    })
        
        return questions
    
    def _migrate_dictionary(self, cursor):
        """从vocab_prebuilt.db迁移词典数据"""
        print("  ⏳ 正在迁移词典数据...")
        
        old_conn = sqlite3.connect(self.old_dbs['vocab_prebuilt'])
        old_cursor = old_conn.cursor()
        
        # 读取vocabulary表
        old_cursor.execute("SELECT id, word, meaning, pos, frequency FROM vocabulary")
        vocab_rows = old_cursor.fetchall()
        
        for row in vocab_rows:
            vocab_id, word, meaning, pos, freq = row
            
            # 获取该词的例句
            old_cursor.execute("""
                SELECT sentence, year, section_name 
                FROM sentences 
                WHERE word_id = ? 
                LIMIT 3
            """, (vocab_id,))
            sentences = old_cursor.fetchall()
            
            example_sentences = [
                {
                    'sentence': s[0],
                    'year': s[1],
                    'section': s[2]
                }
                for s in sentences
            ]
            
            # 插入新词典表
            cursor.execute("""
                INSERT OR IGNORE INTO dictionary (word, meaning, pos, frequency, example_sentences)
                VALUES (?, ?, ?, ?, ?)
            """, (
                word,
                meaning,
                pos,
                freq or 0,
                json.dumps(example_sentences, ensure_ascii=False)
            ))
            self.stats['dictionary'] += 1
        
        old_conn.close()
        print(f"    ✓ 迁移 {self.stats['dictionary']} 个单词")
    
    def _migrate_stories(self, cursor):
        """从story_content.db迁移剧情数据"""
        print("  ⏳ 正在迁移剧情数据...")
        
        if not self.old_dbs['story'].exists():
            print("    ⚠️  story_content.db不存在,跳过")
            return
        
        old_conn = sqlite3.connect(self.old_dbs['story'])
        old_cursor = old_conn.cursor()
        
        old_cursor.execute("""
            SELECT q_id, year, section_type, correct_cn, wrong_cn, correct_en, wrong_en
            FROM stories
        """)
        
        for row in old_cursor.fetchall():
            cursor.execute("""
                INSERT OR IGNORE INTO stories 
                (q_id, year, section_type, correct_cn, wrong_cn, correct_en, wrong_en)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, row)
            self.stats['stories'] += 1
        
        old_conn.close()
        print(f"    ✓ 迁移 {self.stats['stories']} 条剧情")
    
    def _migrate_user_data(self):
        """迁移用户数据到femo_profile.db"""
        print("\n👤 迁移用户数据...")
        
        conn = sqlite3.connect(self.new_profile_db)
        cursor = conn.cursor()
        
        # 1. 迁移词汇学习进度
        self._migrate_vocab_progress(cursor)
        
        # 2. 迁移答题历史
        self._migrate_exam_history(cursor)
        
        # 3. 迁移游戏存档
        self._migrate_game_saves(cursor)
        
        conn.commit()
        conn.close()
    
    def _migrate_vocab_progress(self, cursor):
        """从user_vocab.db迁移词汇进度"""
        print("  ⏳ 正在迁移词汇学习进度...")
        
        if not self.old_dbs['user_vocab'].exists():
            print("    ⚠️  user_vocab.db不存在,跳过")
            return
        
        old_conn = sqlite3.connect(self.old_dbs['user_vocab'])
        old_cursor = old_conn.cursor()
        
        # 检查表是否存在
        old_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='learning_records'")
        if not old_cursor.fetchone():
            old_conn.close()
            print("    ⚠️  learning_records表不存在,跳过")
            return
        
        old_cursor.execute("""
            SELECT DISTINCT word_id FROM learning_records
        """)
        word_ids = [row[0] for row in old_cursor.fetchall()]
        
        for word_id in word_ids:
            # 获取词汇名称
            old_cursor.execute("SELECT word FROM vocabulary WHERE id = ?", (word_id,))
            word_row = old_cursor.fetchone()
            if not word_row:
                continue
            word = word_row[0]
            
            # 获取最新的学习记录
            old_cursor.execute("""
                SELECT repetition, easiness_factor, interval, next_review, last_review,
                       is_correct, consecutive_correct, is_mistake
                FROM learning_records
                WHERE word_id = ?
                ORDER BY last_review DESC
                LIMIT 1
            """, (word_id,))
            lr = old_cursor.fetchone()
            
            if not lr:
                continue
            
            # 统计总复习次数和正确次数
            old_cursor.execute("""
                SELECT COUNT(*), SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END)
                FROM learning_records
                WHERE word_id = ?
            """, (word_id,))
            stats = old_cursor.fetchone()
            total_reviews, correct_reviews = stats if stats else (0, 0)
            
            # 插入vocab_progress
            cursor.execute("""
                INSERT OR IGNORE INTO vocab_progress 
                (word, repetition, easiness_factor, interval, next_review, last_review,
                 mistake_count, consecutive_correct, is_in_mistake_book, 
                 total_reviews, correct_reviews)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                word,
                lr[0],  # repetition
                lr[1],  # easiness_factor
                lr[2],  # interval
                lr[3],  # next_review
                lr[4],  # last_review
                0,      # mistake_count (可从is_correct=0的记录统计)
                lr[6] if len(lr) > 6 else 0,  # consecutive_correct
                lr[7] if len(lr) > 7 else False,  # is_in_mistake_book
                total_reviews or 0,
                correct_reviews or 0
            ))
            self.stats['vocab_progress'] += 1
        
        old_conn.close()
        print(f"    ✓ 迁移 {self.stats['vocab_progress']} 个词汇进度记录")
    
    def _migrate_exam_history(self, cursor):
        """从webnav_rpg.db迁移答题历史"""
        print("  ⏳ 正在迁移答题历史...")
        
        # 这个功能在V1中可能没有完整实现,这里预留接口
        print("    ⚠️  V1无完整答题历史,跳过")
    
    def _migrate_game_saves(self, cursor):
        """从webnav_rpg.db迁移游戏存档"""
        print("  ⏳ 正在迁移游戏存档...")
        
        if not self.old_dbs['webnav'].exists():
            print("    ⚠️  webnav_rpg.db不存在,跳过")
            return
        
        old_conn = sqlite3.connect(self.old_dbs['webnav'])
        old_cursor = old_conn.cursor()
        
        # 检查表是否存在
        old_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='game_saves'")
        if not old_cursor.fetchone():
            old_conn.close()
            print("    ⚠️  game_saves表不存在,跳过")
            return
        
        old_cursor.execute("""
            SELECT slot_id, data_json, updated_at
            FROM game_saves
        """)
        
        for row in old_cursor.fetchall():
            slot_id, data_json, updated_at = row
            
            # 解析旧存档JSON
            try:
                old_save = json.loads(data_json)
                stats = old_save.get('stats', {})
                
                # 转换为新格式
                cursor.execute("""
                    INSERT OR REPLACE INTO game_saves 
                    (slot_id, hp, max_hp, exp, level, mia_mood, snapshot_json, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    slot_id,
                    stats.get('hp', 100),
                    stats.get('maxHp', 100),
                    stats.get('exp', 0),
                    stats.get('level', 1),
                    'normal',
                    data_json,
                    updated_at
                ))
            except json.JSONDecodeError:
                print(f"    ⚠️  存档槽{slot_id}数据损坏,跳过")
        
        old_conn.close()
        print(f"    ✓ 迁移游戏存档")
    
    def _validate_migration(self):
        """验证迁移结果"""
        print("\n🔍 验证迁移结果...")
        
        # 检查static_content.db
        conn = sqlite3.connect(self.new_static_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM papers")
        papers_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM questions")
        questions_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM dictionary")
        dict_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"  ✓ static_content.db:")
        print(f"    - {papers_count} 份试卷")
        print(f"    - {questions_count} 道题目")
        print(f"    - {dict_count} 个单词")
        
        # 检查femo_profile.db
        conn = sqlite3.connect(self.new_profile_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM vocab_progress")
        progress_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"  ✓ femo_profile.db:")
        print(f"    - {progress_count} 个词汇进度")
    
    def _generate_report(self):
        """生成迁移报告"""
        report_path = self.new_root / 'scripts' / 'migration_report.txt'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("数据迁移报告\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"迁移时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("迁移统计:\n")
            for key, value in self.stats.items():
                f.write(f"  - {key}: {value}\n")
        
        print(f"\n📄 迁移报告已保存: {report_path}")

# ============================================================================
# 主函数
# ============================================================================

if __name__ == '__main__':
    import sys
    
    # 路径配置
    OLD_ROOT = r'F:\sanity_check_avg'
    NEW_ROOT = r'F:\sanity_check_avg\Project_Mia'
    
    # 允许从命令行传入路径
    if len(sys.argv) > 1:
        OLD_ROOT = sys.argv[1]
    if len(sys.argv) > 2:
        NEW_ROOT = sys.argv[2]
    
    try:
        migrator = DatabaseMigrator(OLD_ROOT, NEW_ROOT)
        migrator.run()
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
