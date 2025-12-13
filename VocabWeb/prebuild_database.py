"""
预构建 SQLite 数据库并转换为 Base64
这样用户打开网页就能直接使用，无需导入
"""

import sqlite3
import json
import base64
from pathlib import Path


def create_database():
    """创建并填充 SQLite 数据库"""
    
    # 创建内存数据库
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    # 创建表结构
    cursor.execute('''
        CREATE TABLE vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE NOT NULL,
            meaning TEXT NOT NULL,
            pos TEXT,
            frequency INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE sentences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER NOT NULL,
            sentence TEXT NOT NULL,
            translation TEXT,
            year INTEGER,
            question_number INTEGER,
            section_name TEXT,
            section_type TEXT,
            exam_type TEXT,
            question_range TEXT,
            question_label TEXT,
            source_label TEXT,
            question_text TEXT,
            FOREIGN KEY (word_id) REFERENCES vocabulary(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE learning_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER NOT NULL,
            sentence_id INTEGER NOT NULL,
            is_correct BOOLEAN,
            repetition INTEGER DEFAULT 0,
            easiness_factor REAL DEFAULT 2.5,
            interval INTEGER DEFAULT 0,
            next_review DATETIME,
            last_review DATETIME DEFAULT CURRENT_TIMESTAMP,
            consecutive_correct INTEGER DEFAULT 0,
            is_mistake BOOLEAN DEFAULT 0,
            FOREIGN KEY (word_id) REFERENCES vocabulary(id),
            FOREIGN KEY (sentence_id) REFERENCES sentences(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE explanations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER NOT NULL,
            sentence_id INTEGER NOT NULL,
            explanation TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (word_id) REFERENCES vocabulary(id),
            FOREIGN KEY (sentence_id) REFERENCES sentences(id),
            UNIQUE(word_id, sentence_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    
    cursor.execute("INSERT INTO settings (key, value) VALUES ('dailyGoal', '20')")
    
    # 读取词汇数据
    vocab_file = Path(__file__).parent / 'data' / 'exam_vocabulary.json'
    print(f"📖 正在读取词汇文件: {vocab_file}")
    
    with open(vocab_file, 'r', encoding='utf-8') as f:
        vocabulary = json.load(f)
    
    print(f"📚 共 {len(vocabulary)} 个单词")
    
    # 导入数据
    imported = 0
    skipped = 0
    
    for i, word_data in enumerate(vocabulary):
        try:
            # 格式化释义
            if 'meanings' in word_data and word_data['meanings']:
                meaning = '；'.join(word_data['meanings'])
            elif 'primary_meaning' in word_data:
                meaning = word_data['primary_meaning']
            else:
                meaning = '待补充'
            
            pos = word_data.get('pos', '')
            frequency = word_data.get('frequency', len(word_data.get('sentences', [])))
            
            # 插入单词
            try:
                cursor.execute(
                    'INSERT INTO vocabulary (word, meaning, pos, frequency) VALUES (?, ?, ?, ?)',
                    (word_data['word'], meaning, pos, frequency)
                )
                word_id = cursor.lastrowid
            except sqlite3.IntegrityError:
                # 单词已存在，获取 ID
                cursor.execute('SELECT id FROM vocabulary WHERE word = ?', (word_data['word'],))
                word_id = cursor.fetchone()[0]
            
            # 插入例句
            for sentence in word_data.get('sentences', []):
                try:
                    cursor.execute('''
                        INSERT INTO sentences (
                            word_id, sentence, translation, year, question_number,
                            section_name, section_type, exam_type, question_range,
                            question_label, source_label, question_text
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        word_id,
                        sentence['sentence'],
                        sentence.get('translation'),
                        sentence.get('year'),
                        sentence.get('question_number'),
                        sentence.get('section_name'),
                        sentence.get('section_type'),
                        sentence.get('exam_type'),
                        sentence.get('question_range'),
                        sentence.get('question_label'),
                        sentence.get('source_label'),
                        sentence.get('question_text')
                    ))
                except sqlite3.IntegrityError:
                    pass  # 例句已存在
            
            imported += 1
            
            if (i + 1) % 500 == 0:
                print(f"⏳ 已处理 {i + 1}/{len(vocabulary)} 个单词...")
                
        except Exception as e:
            print(f"❌ 导入 {word_data.get('word', '?')} 失败: {e}")
            skipped += 1
    
    conn.commit()
    
    print(f"\n✅ 导入完成！")
    print(f"   成功: {imported} 个单词")
    print(f"   跳过: {skipped} 个")
    
    # 统计信息
    cursor.execute('SELECT COUNT(*) FROM vocabulary')
    vocab_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM sentences')
    sentence_count = cursor.fetchone()[0]
    
    print(f"\n📊 数据库统计:")
    print(f"   词汇数: {vocab_count}")
    print(f"   例句数: {sentence_count}")
    
    return conn


def export_to_base64(conn):
    """将数据库导出为 Base64"""
    
    # 将内存数据库保存到临时文件
    temp_file = Path(__file__).parent / 'vocab_prebuilt.db'
    backup = sqlite3.connect(str(temp_file))
    conn.backup(backup)
    backup.close()
    
    print(f"\n💾 数据库已保存: {temp_file}")
    print(f"   文件大小: {temp_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    # 读取并转换为 Base64
    with open(temp_file, 'rb') as f:
        db_bytes = f.read()
    
    base64_data = base64.b64encode(db_bytes).decode('ascii')
    
    # 保存 Base64 到文件
    base64_file = Path(__file__).parent / 'data' / 'vocab_prebuilt.txt'
    with open(base64_file, 'w', encoding='utf-8') as f:
        f.write(base64_data)
    
    print(f"📦 Base64 已保存: {base64_file}")
    print(f"   Base64 大小: {len(base64_data) / 1024 / 1024:.2f} MB")
    
    return base64_data, str(base64_file)


def main():
    print("🚀 开始构建预填充数据库...\n")
    
    # 创建并填充数据库
    conn = create_database()
    
    # 导出为 Base64
    base64_data, base64_file = export_to_base64(conn)
    
    conn.close()
    
    print(f"\n✨ 完成！现在可以修改 index.html 自动加载这个数据库")
    print(f"\n使用方法:")
    print(f"1. 在 index.html 中加载 {base64_file}")
    print(f"2. 用户打开页面即可直接使用，无需导入")


if __name__ == '__main__':
    main()
