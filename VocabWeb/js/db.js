/**
 * 数据库管理模块 - 使用 sql.js
 */

class DatabaseManager {
    constructor() {
        this.db = null;
        this.SQL = null;
    }

    async init() {
        // 加载 sql.js
        this.SQL = await initSqlJs({
            locateFile: file => `https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.8.0/${file}`
        });

        // 尝试从 localStorage 加载数据库
        const savedDB = localStorage.getItem('vocabDB');
        if (savedDB) {
            try {
                // 尝试解析为 JSON (旧格式)
                const uint8Array = new Uint8Array(JSON.parse(savedDB));
                this.db = new this.SQL.Database(uint8Array);
                console.log('✅ 已加载现有数据库 (JSON格式)');
                // 确保 schema 是最新的
                this.ensureSchemaUpgrades();
            } catch (e) {
                // 尝试解析为 Base64 (新格式)
                try {
                    const binaryString = window.atob(savedDB);
                    const len = binaryString.length;
                    const bytes = new Uint8Array(len);
                    for (let i = 0; i < len; i++) {
                        bytes[i] = binaryString.charCodeAt(i);
                    }
                    this.db = new this.SQL.Database(bytes);
                    console.log('✅ 已加载现有数据库 (Base64格式)');
                    // 确保 schema 是最新的
                    this.ensureSchemaUpgrades();
                } catch (e2) {
                    console.error('无法加载数据库，使用预构建数据库', e2);
                    await this.loadPrebuiltDatabase();
                }
            }
        } else {
            // 没有保存的数据库，加载预构建数据库
            console.log('📦 首次使用，加载预构建数据库...');
            await this.loadPrebuiltDatabase();
        }
    }

    async loadPrebuiltDatabase() {
        try {
            // 加载预构建的数据库
            const response = await fetch('data/vocab_prebuilt.txt');
            const base64Data = await response.text();
            
            // Base64 解码
            const binaryString = window.atob(base64Data);
            const len = binaryString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            
            this.db = new this.SQL.Database(bytes);
            console.log('✅ 预构建数据库加载成功');
            
            // 确保 schema 是最新的
            this.ensureSchemaUpgrades();
            
            // 保存到 localStorage
            this.save();
            console.log('💾 数据库已保存到本地');
        } catch (error) {
            console.error('❌ 加载预构建数据库失败，创建空数据库', error);
            this.db = new this.SQL.Database();
            await this.createTables();
        }
    }

    async createTables() {
        // 词汇表
        this.db.run(`
            CREATE TABLE IF NOT EXISTS vocabulary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT UNIQUE NOT NULL,
                meaning TEXT NOT NULL,
                frequency INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        `);

        // 例句表
        this.db.run(`
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

        // 学习记录表
        this.db.run(`
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
                consecutive_correct INTEGER DEFAULT 0,
                is_mistake BOOLEAN DEFAULT 0,
                FOREIGN KEY (word_id) REFERENCES vocabulary(id),
                FOREIGN KEY (sentence_id) REFERENCES sentences(id)
            )
        `);

        // AI讲解缓存表
        this.db.run(`
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

        // 设置表
        this.db.run(`
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        `);

        // 默认设置
        this.setSetting('dailyGoal', '20');
        this.setSetting('sleepTime', '23:00');
        this.setSetting('notificationEnabled', 'false');
        this.setSetting('notificationTime', '20:00');

        this.ensureSchemaUpgrades();
        this.save();
    }

    ensureSchemaUpgrades() {
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
                this.db.run(`ALTER TABLE sentences ADD COLUMN ${column} ${type}`);
            } catch (error) {
                if (!String(error).includes('duplicate column name')) {
                    console.warn(`无法为 sentences 添加列 ${column}:`, error);
                }
            }
        });

        try {
            this.db.run(`ALTER TABLE vocabulary ADD COLUMN pos TEXT`);
        } catch (error) {
             if (!String(error).includes('duplicate column name')) {
                console.warn(`无法为 vocabulary 添加列 pos:`, error);
            }
        }

        // 添加错题本相关字段
        let schemaUpdated = false;
        
        try {
            this.db.run(`ALTER TABLE learning_records ADD COLUMN consecutive_correct INTEGER DEFAULT 0`);
            console.log('✅ 添加字段: consecutive_correct');
            schemaUpdated = true;
        } catch (error) {
            if (!String(error).includes('duplicate column name')) {
                console.warn('添加 consecutive_correct 失败:', error);
            }
        }
        
        try {
            this.db.run(`ALTER TABLE learning_records ADD COLUMN is_mistake BOOLEAN DEFAULT 0`);
            console.log('✅ 添加字段: is_mistake');
            schemaUpdated = true;
        } catch (error) {
            if (!String(error).includes('duplicate column name')) {
                console.warn('添加 is_mistake 失败:', error);
            }
        }
        
        // 如果有更新，保存数据库
        if (schemaUpdated) {
            console.log('💾 Schema 已更新，保存数据库...');
            this.save();
        }
    }

    // 保存数据库到 localStorage
    save() {
        const data = this.db.export();
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

    // 词汇操作
    addWord(word, meaning, pos = '') {
        try {
            this.db.run('INSERT INTO vocabulary (word, meaning, pos) VALUES (?, ?, ?)', [word, meaning, pos]);
            this.save();
            return this.db.exec('SELECT last_insert_rowid()')[0].values[0][0];
        } catch (e) {
            // 如果已存在，尝试更新
             try {
                const result = this.db.exec('SELECT id FROM vocabulary WHERE word = ?', [word]);
                if (result.length > 0 && result[0].values.length > 0) {
                    const id = result[0].values[0][0];
                    this.db.run('UPDATE vocabulary SET meaning = ?, pos = ? WHERE id = ?', [meaning, pos, id]);
                    this.save();
                    return id;
                }
            } catch (updateError) {
                console.error('更新词汇失败:', updateError);
            }
            console.error('添加词汇失败:', e);
            return null;
        }
    }

    getWordByText(word) {
        const result = this.db.exec('SELECT * FROM vocabulary WHERE word = ?', [word]);
        if (result.length > 0) {
            return this.rowToObject(result[0]);
        }
        return null;
    }

    getWordById(id) {
        const result = this.db.exec('SELECT * FROM vocabulary WHERE id = ?', [id]);
        if (result.length > 0) {
            return this.rowToObject(result[0]);
        }
        return null;
    }

    // 例句操作
    addSentence(wordId, sentence, translation, metadata = {}) {
        const {
            year = null,
            questionNumber = null,
            sectionName = null,
            sectionType = null,
            examType = null,
            questionRange = null,
            questionLabel = null,
            sourceLabel = null,
            questionText = null
        } = metadata;

        this.db.run(
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
                sentence,
                translation,
                year,
                questionNumber,
                sectionName,
                sectionType,
                examType,
                questionRange,
                questionLabel,
                sourceLabel,
                questionText
            ]
        );
        this.save();
        return this.db.exec('SELECT last_insert_rowid()')[0].values[0][0];
    }

    getSentencesByWordId(wordId) {
        const result = this.db.exec('SELECT * FROM sentences WHERE word_id = ?', [wordId]);
        if (result.length > 0) {
            return this.rowsToObjects(result[0]);
        }
        return [];
    }

    getSentenceById(id) {
        const result = this.db.exec('SELECT * FROM sentences WHERE id = ?', [id]);
        if (result.length > 0) {
            return this.rowToObject(result[0]);
        }
        return null;
    }

    // 学习记录操作
    addLearningRecord(wordId, sentenceId, isCorrect) {
        this.db.run(
            'INSERT INTO learning_records (word_id, sentence_id, is_correct) VALUES (?, ?, ?)',
            [wordId, sentenceId, isCorrect ? 1 : 0]
        );
        this.save();
    }

    updateLearningRecord(wordId, sentenceId, repetition, easinessFactor, interval, nextReview, isCorrect) {
        const record = this.getLearningRecord(wordId, sentenceId);
        let consecutiveCorrect = record?.consecutive_correct || 0;
        let isMistake = record?.is_mistake || 0;

        if (isCorrect) {
            consecutiveCorrect++;
            // 如果是错题且连续答对3次，移出错题本
            if (isMistake && consecutiveCorrect >= 3) {
                isMistake = 0;
                consecutiveCorrect = 0;
            }
        } else {
            consecutiveCorrect = 0;
            isMistake = 1; // 标记为错题
        }

        this.db.run(`
            UPDATE learning_records 
            SET repetition = ?, easiness_factor = ?, interval = ?, next_review = ?, 
                last_review = CURRENT_TIMESTAMP, consecutive_correct = ?, is_mistake = ?
            WHERE word_id = ? AND sentence_id = ?
        `, [repetition, easinessFactor, interval, nextReview, consecutiveCorrect, isMistake, wordId, sentenceId]);
        this.save();
    }

    getLearningRecord(wordId, sentenceId) {
        const result = this.db.exec(
            'SELECT * FROM learning_records WHERE word_id = ? AND sentence_id = ? ORDER BY last_review DESC LIMIT 1',
            [wordId, sentenceId]
        );
        if (result.length > 0) {
            return this.rowToObject(result[0]);
        }
        return null;
    }

    // 获取错题列表
    getMistakeWords(limit = 5) {
        const result = this.db.exec(`
            SELECT DISTINCT 
                v.*, 
                s.id as sentence_id, 
                s.sentence, 
                s.translation,
                s.year as sentence_year,
                s.question_number as sentence_question_number,
                s.section_name as sentence_section_name,
                s.section_type as sentence_section_type,
                s.exam_type as sentence_exam_type,
                s.question_range as sentence_question_range,
                s.question_label as sentence_question_label,
                s.source_label as sentence_source_label,
                s.question_text as sentence_question_text,
                lr.consecutive_correct
            FROM learning_records lr
            JOIN vocabulary v ON lr.word_id = v.id
            JOIN sentences s ON lr.sentence_id = s.id
            WHERE lr.is_mistake = 1
            ORDER BY RANDOM()
            LIMIT ?
        `, [limit]);

        if (result.length > 0) {
            return this.rowsToObjects(result[0]);
        }
        return [];
    }

    // 获取错题数量
    getMistakeCount() {
        const result = this.db.exec(`
            SELECT COUNT(DISTINCT word_id) as count 
            FROM learning_records 
            WHERE is_mistake = 1
        `);
        return result[0]?.values[0][0] || 0;
    }

    // 获取今日需要学习的词汇
    getTodayWords(limit) {
        const today = new Date().toISOString().split('T')[0];
        
        // 获取需要复习的词汇
        const reviewWords = this.db.exec(`
            SELECT DISTINCT 
                v.*, 
                s.id as sentence_id, 
                s.sentence, 
                s.translation,
                s.year as sentence_year,
                s.question_number as sentence_question_number,
                s.section_name as sentence_section_name,
                s.section_type as sentence_section_type,
                s.exam_type as sentence_exam_type,
                s.question_range as sentence_question_range,
                s.question_label as sentence_question_label,
                s.source_label as sentence_source_label,
                s.question_text as sentence_question_text
            FROM vocabulary v
            JOIN sentences s ON v.id = s.word_id
            JOIN learning_records lr ON v.id = lr.word_id AND s.id = lr.sentence_id
            WHERE date(lr.next_review) <= date('${today}')
            ORDER BY lr.next_review
            LIMIT ${limit}
        `);

        let words = [];
        if (reviewWords.length > 0) {
            words = this.rowsToObjects(reviewWords[0]);
        }

        // 如果不足，添加新词
        if (words.length < limit) {
            const remaining = limit - words.length;
            const newWords = this.db.exec(`
                SELECT DISTINCT 
                    v.*, 
                    s.id as sentence_id, 
                    s.sentence, 
                    s.translation,
                    s.year as sentence_year,
                    s.question_number as sentence_question_number,
                    s.section_name as sentence_section_name,
                    s.section_type as sentence_section_type,
                    s.exam_type as sentence_exam_type,
                    s.question_range as sentence_question_range,
                    s.question_label as sentence_question_label,
                    s.source_label as sentence_source_label,
                    s.question_text as sentence_question_text
                FROM vocabulary v
                JOIN sentences s ON v.id = s.word_id
                LEFT JOIN learning_records lr ON v.id = lr.word_id AND s.id = lr.sentence_id
                WHERE lr.id IS NULL
                ORDER BY v.frequency DESC, RANDOM()
                LIMIT ${remaining}
            `);

            if (newWords.length > 0) {
                words = words.concat(this.rowsToObjects(newWords[0]));
            }
        }

        return words;
    }

    // AI讲解缓存操作
    addExplanation(wordId, sentenceId, explanation) {
        try {
            this.db.run(
                'INSERT OR REPLACE INTO explanations (word_id, sentence_id, explanation) VALUES (?, ?, ?)',
                [wordId, sentenceId, explanation]
            );
            this.save();
        } catch (e) {
            console.error('保存讲解失败:', e);
        }
    }

    getExplanation(wordId, sentenceId) {
        const result = this.db.exec(
            'SELECT explanation FROM explanations WHERE word_id = ? AND sentence_id = ?',
            [wordId, sentenceId]
        );
        if (result.length > 0 && result[0].values.length > 0) {
            return result[0].values[0][0];
        }
        return null;
    }

    // 设置操作
    setSetting(key, value) {
        this.db.run('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', [key, value]);
        this.save();
    }

    getSetting(key) {
        const result = this.db.exec('SELECT value FROM settings WHERE key = ?', [key]);
        if (result.length > 0 && result[0].values.length > 0) {
            return result[0].values[0][0];
        }
        return null;
    }

    // 统计数据
    getTodayStats() {
        const today = new Date().toISOString().split('T')[0];
        
        const learned = this.db.exec(`
            SELECT COUNT(DISTINCT word_id) as count 
            FROM learning_records 
            WHERE date(last_review) = date('${today}') AND repetition = 0
        `);

        const reviewed = this.db.exec(`
            SELECT COUNT(DISTINCT word_id) as count 
            FROM learning_records 
            WHERE date(last_review) = date('${today}') AND repetition > 0
        `);

        const totalLearned = this.db.exec(`
            SELECT COUNT(DISTINCT word_id) as count 
            FROM learning_records
        `);

        const accuracy = this.db.exec(`
            SELECT 
                ROUND(
                    CAST(SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) AS FLOAT) / 
                    COUNT(*) * 100, 
                    1
                ) as accuracy
            FROM learning_records
            WHERE date(last_review) = date('${today}')
        `);

        return {
            learnedToday: learned[0]?.values[0][0] || 0,
            reviewedToday: reviewed[0]?.values[0][0] || 0,
            totalLearned: totalLearned[0]?.values[0][0] || 0,
            accuracy: accuracy[0]?.values[0][0] || 0
        };
    }

    getTotalWords() {
        const result = this.db.exec('SELECT COUNT(*) as count FROM vocabulary');
        return result[0]?.values[0][0] || 0;
    }

    // 辅助函数：将查询结果转换为对象
    rowToObject(result) {
        if (!result || !result.columns || !result.values || result.values.length === 0) {
            return null;
        }
        const obj = {};
        result.columns.forEach((col, i) => {
            obj[col] = result.values[0][i];
        });
        return obj;
    }

    rowsToObjects(result) {
        if (!result || !result.columns || !result.values) {
            return [];
        }
        return result.values.map(row => {
            const obj = {};
            result.columns.forEach((col, i) => {
                obj[col] = row[i];
            });
            return obj;
        });
    }

    // 导出数据库
    exportDB() {
        const data = this.db.export();
        const blob = new Blob([data], { type: 'application/octet-stream' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `vocab_backup_${new Date().toISOString().split('T')[0]}.db`;
        a.click();
        URL.revokeObjectURL(url);
    }

    // 导入数据库
    async importDB(file) {
        const reader = new FileReader();
        return new Promise((resolve, reject) => {
            reader.onload = (e) => {
                try {
                    const uint8Array = new Uint8Array(e.target.result);
                    this.db = new this.SQL.Database(uint8Array);
                    this.save();
                    resolve(true);
                } catch (error) {
                    reject(error);
                }
            };
            reader.onerror = reject;
            reader.readAsArrayBuffer(file);
        });
    }
}

export const db = new DatabaseManager();
