"""
词汇导入工具 - 将 exam_vocabulary.json 写入 Web 端 SQLite
"""

from pathlib import Path


def generate_import_html():
    html_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>词汇数据导入工具</title>
    <style>
        body {
            font-family: 'Microsoft YaHei', sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        h1 {
            color: #ff6b9d;
            text-align: center;
        }
        .progress {
            width: 100%;
            height: 30px;
            background: #f0f0f0;
            border-radius: 15px;
            margin: 20px 0;
            overflow: hidden;
        }
        .progress-bar {
            height: 100%;
            background: linear-gradient(135deg, #ff6b9d, #c44569);
            width: 0%;
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #ff6b9d, #c44569);
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: bold;
            cursor: pointer;
            margin: 10px 0;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255, 107, 157, 0.4);
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .log {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            max-height: 300px;
            overflow-y: auto;
            margin-top: 20px;
            font-family: monospace;
            font-size: 0.9rem;
        }
        .log div {
            margin: 5px 0;
        }
        .success { color: #26de81; }
        .error { color: #fc5c65; }
        .info { color: #667eea; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 词汇数据导入工具</h1>
        <p style="text-align: center; color: #7f8c8d;">
            从 EnglishExamWeb/data 聚合的 JSON 导入词汇与题目来源
        </p>

        <div class="progress">
            <div class="progress-bar" id="progressBar">0%</div>
        </div>

        <button id="importBtn" onclick="importVocabulary()">🚀 开始导入数据</button>
        <button id="clearBtn" onclick="clearDatabase()" style="background: #ff4757; margin-top: 10px;">🗑️ 清空数据库 (慎用)</button>
        
        <div class="log" id="logArea"></div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.8.0/sql-wasm.js"></script>
    <script>
        let db;
        let SQL;

        function log(message, type = 'text') {
            const logArea = document.getElementById('logArea');
            const div = document.createElement('div');
            div.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
            div.className = type;
            logArea.appendChild(div);
            logArea.scrollTop = logArea.scrollHeight;
        }

        function updateProgress(current, total) {
            const percentage = Math.round((current / total) * 100);
            const bar = document.getElementById('progressBar');
            bar.style.width = `${percentage}%`;
            bar.textContent = `${percentage}%`;
        }

        async function initSqlJs(config) {
            if (window.initSqlJs) return window.initSqlJs(config);
            throw new Error("sql.js not loaded");
        }

        async function initDatabase() {
            if (db) return;

            SQL = await initSqlJs({
                locateFile: file => `https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.8.0/${file}`
            });

            const savedDB = localStorage.getItem('vocabDB');
            if (savedDB) {
                try {
                    // 尝试解析为 JSON (旧格式)
                    const uint8Array = new Uint8Array(JSON.parse(savedDB));
                    db = new SQL.Database(uint8Array);
                    log('已加载现有数据库 (JSON格式)', 'info');
                } catch (e) {
                    // 尝试解析为 Base64 (新格式)
                    try {
                        const binaryString = window.atob(savedDB);
                        const len = binaryString.length;
                        const bytes = new Uint8Array(len);
                        for (let i = 0; i < len; i++) {
                            bytes[i] = binaryString.charCodeAt(i);
                        }
                        db = new SQL.Database(bytes);
                        log('已加载现有数据库 (Base64格式)', 'info');
                    } catch (e2) {
                        console.error('无法加载数据库，重置为新数据库', e2);
                        db = new SQL.Database();
                        createTables();
                        log('数据库已损坏，重置为新数据库', 'error');
                    }
                }
            } else {
                db = new SQL.Database();
                createTables();
                log('已创建新数据库', 'info');
            }
        }

        function createTables() {
            db.run(`
                CREATE TABLE IF NOT EXISTS vocabulary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT UNIQUE NOT NULL,
                    meaning TEXT NOT NULL,
                    pos TEXT,
                    frequency INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            `);
             db.run(`
                CREATE TABLE IF NOT EXISTS sentences (
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
            `);
             db.run(`
                CREATE TABLE IF NOT EXISTS learning_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word_id INTEGER NOT NULL,
                    sentence_id INTEGER NOT NULL,
                    is_correct BOOLEAN,
                    repetition INTEGER DEFAULT 0,
                    easiness_factor REAL DEFAULT 2.5,
                    interval INTEGER DEFAULT 0,
                    next_review DATETIME,
                    last_review DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (word_id) REFERENCES vocabulary(id),
                    FOREIGN KEY (sentence_id) REFERENCES sentences(id)
                )
            `);
             db.run(`
                CREATE TABLE IF NOT EXISTS explanations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word_id INTEGER NOT NULL,
                    sentence_id INTEGER NOT NULL,
                    explanation TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (word_id) REFERENCES vocabulary(id),
                    FOREIGN KEY (sentence_id) REFERENCES sentences(id),
                    UNIQUE(word_id, sentence_id)
                )
            `);
             db.run(`
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            `);
            db.run("INSERT OR REPLACE INTO settings (key, value) VALUES ('dailyGoal', '20')");
        }

        function ensureSentenceColumns() {
            const sentenceColumns = [
                ['section_name', 'TEXT'],
                ['section_type', 'TEXT'],
                ['exam_type', 'TEXT'],
                ['question_range', 'TEXT'],
                ['question_label', 'TEXT'],
                ['source_label', 'TEXT'],
                ['question_text', 'TEXT']
            ];

            sentenceColumns.forEach(([column, type]) => {
                try {
                    db.run(`ALTER TABLE sentences ADD COLUMN ${column} ${type}`);
                } catch (error) {
                    // Ignore duplicate column errors
                }
            });
            
            try {
                db.run(`ALTER TABLE vocabulary ADD COLUMN pos TEXT`);
            } catch (error) {}
        }

        function saveDatabase() {
            const data = db.export();
            // 使用 Base64 存储，分块处理避免栈溢出
            const chunkSize = 0x8000; // 32KB chunks
            const chunks = [];
            
            for (let i = 0; i < data.length; i += chunkSize) {
                const chunk = data.subarray(i, i + chunkSize);
                chunks.push(String.fromCharCode.apply(null, chunk));
            }
            
            const binary = chunks.join('');
            const base64 = window.btoa(binary);
            localStorage.setItem('vocabDB', base64);
        }

        function clearDatabase() {
            if (confirm('确定要清空数据库吗？这将删除所有学习记录！')) {
                localStorage.removeItem('vocabDB');
                db = null;
                location.reload();
            }
        }

        function formatMeaning(entry) {
            if (entry.meanings && entry.meanings.length) {
                return entry.meanings.join('；');
            }
            if (entry.primary_meaning) {
                return entry.primary_meaning;
            }
            return '待补充';
        }

        async function importVocabulary() {
            const btn = document.getElementById('importBtn');
            btn.disabled = true;
            
            try {
                log('开始导入词汇数据...', 'info');
                
                await initDatabase();
                ensureSentenceColumns();

                log('正在下载数据文件...', 'info');
                const response = await fetch('data/exam_vocabulary.json?t=' + Date.now());
                const payload = await response.json();
                const vocabulary = Array.isArray(payload) ? payload : (payload.entries || []);

                log(`准备导入 ${vocabulary.length} 个单词...`, 'info');

                let imported = 0;
                let skipped = 0;

                // 开启事务以提高性能
                db.run("BEGIN TRANSACTION");

                for (let i = 0; i < vocabulary.length; i++) {
                    const wordData = vocabulary[i];

                    try {
                        const meaningText = formatMeaning(wordData);
                        const pos = wordData.pos || '';
                        const frequency = wordData.frequency || (wordData.sentences ? wordData.sentences.length : 0);

                        // 尝试插入或更新
                        try {
                            db.run(
                                'INSERT INTO vocabulary (word, meaning, pos, frequency) VALUES (?, ?, ?, ?)',
                                [wordData.word, meaningText, pos, frequency]
                            );
                        } catch (e) {
                            // 如果存在，更新
                            db.run(
                                'UPDATE vocabulary SET meaning = ?, pos = ?, frequency = ? WHERE word = ?',
                                [meaningText, pos, frequency, wordData.word]
                            );
                        }

                        const result = db.exec('SELECT id FROM vocabulary WHERE word = ?', [wordData.word]);
                        const wordId = result[0]?.values[0][0];
                        if (!wordId) {
                            skipped++;
                            continue;
                        }

                        for (const sentence of wordData.sentences || []) {
                            const exists = db.exec(
                                'SELECT id FROM sentences WHERE word_id = ? AND sentence = ? LIMIT 1',
                                [wordId, sentence.sentence]
                            );
                            if (exists[0]?.values?.length) {
                                continue;
                            }

                            db.run(
                                `INSERT INTO sentences (
                                    word_id,
                                    sentence,
                                    translation,
                                    year,
                                    question_number,
                                    section_name,
                                    section_type,
                                    exam_type,
                                    question_range,
                                    question_label,
                                    source_label,
                                    question_text
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
                                [
                                    wordId,
                                    sentence.sentence,
                                    sentence.translation || null,
                                    sentence.year || null,
                                    sentence.question_number || null,
                                    sentence.section_name || null,
                                    sentence.section_type || null,
                                    sentence.exam_type || null,
                                    sentence.question_range || null,
                                    sentence.question_label || null,
                                    sentence.source_label || null,
                                    sentence.question_text || null
                                ]
                            );
                        }

                        imported++;
                    } catch (error) {
                        console.error('导入词汇失败', error);
                        skipped++;
                    }

                    if (i % 50 === 0) {
                        updateProgress(i + 1, vocabulary.length);
                    }
                }

                db.run("COMMIT");
                updateProgress(vocabulary.length, vocabulary.length);
                
                log('正在保存数据库...', 'info');
                saveDatabase();

                log('✅ 导入完成！', 'success');
                log(`成功导入: ${imported} 个单词`, 'success');
                log(`跳过: ${skipped} 个（已存在或写入失败）`, 'info');

                setTimeout(() => {
                    if (confirm('导入完成！是否前往学习系统？')) {
                        window.location.href = 'index.html';
                    }
                }, 1000);

            } catch (error) {
                if (db) {
                    try { db.run("ROLLBACK"); } catch(e) {}
                }
                log(`❌ 导入失败: ${error.message}`, 'error');
                console.error(error);
            } finally {
                btn.disabled = false;
            }
        }

        window.addEventListener('load', async () => {
            const savedDB = localStorage.getItem('vocabDB');
            if (savedDB) {
                log('检测到已有数据库', 'info');
                
                await initDatabase();
                try {
                    const result = db.exec('SELECT COUNT(*) as count FROM vocabulary');
                    const count = result[0]?.values[0][0] || 0;
                    log(`当前词汇量: ${count}`, 'info');

                    if (count > 0) {
                        document.getElementById('importBtn').textContent = '重新导入词汇（会保留现有数据）';
                    }
                } catch (e) {
                    log('数据库读取失败，建议清空重置', 'error');
                }
            } else {
                log('未检测到数据库，请导入词汇数据', 'info');
            }
        });
    </script>
</body>
</html>'''

    return html_content


def main():
    base_dir = Path(__file__).parent
    output_file = base_dir / 'import_data.html'

    html_content = generate_import_html()

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ 已生成导入工具: {output_file}")
    print("\n使用说明:")
    print("1. 运行 extract_vocab.py 生成 data/exam_vocabulary.json")
    print("2. 在浏览器中打开 import_data.html")
    print("3. 点击按钮导入词汇及题目元数据")
    print("4. 导入完成后即可开始学习")


if __name__ == '__main__':
    main()
