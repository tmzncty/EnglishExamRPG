/**
 * Vocabulary Manager - 单词本管理器
 * 负责单词收藏、背单词功能、词库管理
 * 支持导入 maimemo-export 格式的 CSV 词库
 */

const VocabularyManager = {
    // 存储键名
    KEYS: {
        VOCABULARY: 'englishExam_vocabulary',       // 收藏的生词
        WORD_PROGRESS: 'englishExam_wordProgress',  // 背单词进度
        WORD_BOOKS: 'englishExam_wordBooks'         // 已导入的词书
    },

    // 当前词库
    currentWordBook: null,
    
    // 背单词状态
    studySession: {
        source: null,
        words: [],
        currentIndex: 0,
        correct: 0,
        wrong: 0,
        reviewed: [],
        initialLearned: 0,
        wordCount: 0
    },

    /**
     * 初始化
     */
    init() {
        console.log('[VocabularyManager] 初始化完成');
    },

    // ==================== 生词本（收藏） ====================

    /**
     * 添加生词
     * @param {Object} word - { word, translation, context?, sentence?, questionId? }
     */
    addWord(word) {
        const vocabulary = this.getVocabulary();
        
        // 检查是否已存在
        if (vocabulary.some(w => w.word.toLowerCase() === word.word.toLowerCase())) {
            return { success: false, message: '该单词已在生词本中' };
        }

        vocabulary.push({
            ...word,
            addedAt: Date.now(),
            mastery: 0,  // 熟练度 0-5
            reviewCount: 0,
            lastReviewAt: null
        });

        this.saveVocabulary(vocabulary);
        return { success: true, message: '已添加到生词本' };
    },

    /**
     * 获取生词本
     */
    getVocabulary() {
        try {
            const data = localStorage.getItem(this.KEYS.VOCABULARY);
            return data ? JSON.parse(data) : [];
        } catch (e) {
            console.error('[VocabularyManager] 读取生词本失败:', e);
            return [];
        }
    },

    /**
     * 保存生词本
     */
    saveVocabulary(vocabulary) {
        try {
            localStorage.setItem(this.KEYS.VOCABULARY, JSON.stringify(vocabulary));
            return true;
        } catch (e) {
            console.error('[VocabularyManager] 保存生词本失败:', e);
            return false;
        }
    },

    /**
     * 删除生词
     */
    removeWord(word) {
        const vocabulary = this.getVocabulary();
        const filtered = vocabulary.filter(w => w.word.toLowerCase() !== word.toLowerCase());
        this.saveVocabulary(filtered);
        return filtered;
    },

    /**
     * 更新单词熟练度
     */
    updateMastery(word, isCorrect) {
        const vocabulary = this.getVocabulary();
        const wordObj = vocabulary.find(w => w.word.toLowerCase() === word.toLowerCase());
        
        if (wordObj) {
            if (isCorrect) {
                wordObj.mastery = Math.min(5, wordObj.mastery + 1);
            } else {
                wordObj.mastery = Math.max(0, wordObj.mastery - 1);
            }
            wordObj.reviewCount++;
            wordObj.lastReviewAt = Date.now();
            this.saveVocabulary(vocabulary);
        }
        
        return wordObj;
    },

    // ==================== 词书管理 ====================

    /**
     * 导入 CSV 词书
     * 格式：单词,释义 或 单词,音标,释义
     */
    async importWordBook(file, bookName) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                try {
                    const content = e.target.result;
                    const lines = content.split('\n').filter(line => line.trim());
                    const words = [];

                    lines.forEach((line, index) => {
                        // 跳过标题行（如果有）
                        if (index === 0 && (line.includes('word') || line.includes('单词'))) {
                            return;
                        }

                        const parts = line.split(',').map(p => p.trim());
                        if (parts.length >= 2) {
                            const word = {
                                word: parts[0],
                                phonetic: parts.length > 2 ? parts[1] : '',
                                translation: parts.length > 2 ? parts[2] : parts[1]
                            };
                            words.push(word);
                        }
                    });

                    if (words.length === 0) {
                        reject(new Error('词书格式错误或为空'));
                        return;
                    }

                    // 保存词书
                    const books = this.getWordBooks();
                    const newBook = {
                        id: Date.now().toString(),
                        name: bookName || file.name.replace('.csv', ''),
                        wordCount: words.length,
                        words: words,
                        importedAt: Date.now()
                    };
                    books.push(newBook);
                    this.saveWordBooks(books);

                    resolve({
                        success: true,
                        message: `成功导入 ${words.length} 个单词`,
                        book: newBook
                    });
                } catch (err) {
                    reject(new Error('解析词书失败: ' + err.message));
                }
            };

            reader.onerror = () => reject(new Error('读取文件失败'));
            reader.readAsText(file, 'UTF-8');
        });
    },

    /**
     * 加载内置词书（从 data/wordbooks 目录）
     */
    async loadBuiltInWordBook(filename, bookName) {
        try {
            const response = await fetch(`data/wordbooks/${filename}`);
            if (!response.ok) {
                throw new Error('词书文件不存在');
            }
            
            const content = await response.text();
            const lines = content.split('\n').filter(line => line.trim());
            const words = [];

            lines.forEach((line, index) => {
                // 跳过标题行
                if (index === 0 && (line.includes('word') || line.includes('单词'))) {
                    return;
                }

                // maimemo-export 格式: word,"translation" 或 word,translation
                const match = line.match(/^([^,]+),(.+)$/);
                if (match) {
                    const word = match[1].trim().replace(/^"|"$/g, '');
                    let translation = match[2].trim().replace(/^"|"$/g, '');
                    // 处理多行翻译（用 \n 分隔的）
                    translation = translation.replace(/\\n/g, '; ');
                    
                    words.push({
                        word: word,
                        translation: translation,
                        phonetic: ''
                    });
                }
            });

            if (words.length === 0) {
                throw new Error('词书格式错误或为空');
            }

            // 检查是否已导入
            const books = this.getWordBooks();
            const existingBook = books.find(b => b.name === bookName);
            if (existingBook) {
                return { success: false, message: '该词书已导入' };
            }

            // 保存词书
            const newBook = {
                id: Date.now().toString(),
                name: bookName,
                wordCount: words.length,
                words: words,
                importedAt: Date.now(),
                isBuiltIn: true
            };
            books.push(newBook);
            this.saveWordBooks(books);

            return {
                success: true,
                message: `成功加载 ${words.length} 个单词`,
                book: newBook
            };
        } catch (error) {
            return { success: false, message: error.message };
        }
    },

    /**
     * 获取所有词书
     */
    getWordBooks() {
        try {
            const data = localStorage.getItem(this.KEYS.WORD_BOOKS);
            return data ? JSON.parse(data) : [];
        } catch (e) {
            return [];
        }
    },

    /**
     * 保存词书
     */
    saveWordBooks(books) {
        try {
            localStorage.setItem(this.KEYS.WORD_BOOKS, JSON.stringify(books));
            return true;
        } catch (e) {
            console.error('[VocabularyManager] 保存词书失败:', e);
            return false;
        }
    },

    /**
     * 删除词书
     */
    deleteWordBook(bookId) {
        const books = this.getWordBooks();
        const filtered = books.filter(b => b.id !== bookId);
        this.saveWordBooks(filtered);
        return filtered;
    },

    /**
     * 获取指定词书
     */
    getWordBook(bookId) {
        const books = this.getWordBooks();
        return books.find(b => b.id === bookId);
    },

    // ==================== 背单词功能 ====================

    /**
     * 开始背单词会话
     * @param {string} source - 'vocabulary' (生词本) 或词书ID
     * @param {number} count - 本次学习单词数量
     */
    startStudySession(source, count = 20) {
        let words = [];
        let initialLearned = 0;
        let totalWordCount = 0;

        if (source === 'vocabulary') {
            const vocabulary = this.getVocabulary();
            words = vocabulary
                .sort((a, b) => a.mastery - b.mastery)
                .slice(0, count)
                .map(w => ({
                    word: w.word,
                    translation: w.translation,
                    phonetic: w.phonetic || '',
                    context: w.context || '',
                    sentence: w.sentence || ''
                }));
            totalWordCount = vocabulary.length;
        } else {
            const book = this.getWordBook(source);
            if (book) {
                const progress = this.getWordProgress(source);
                initialLearned = progress.learned || 0;
                const startIndex = initialLearned;

                const bookWords = Array.isArray(book.words) ? book.words : [];

                words = bookWords
                    .slice(startIndex, startIndex + count)
                    .map(w => ({
                        word: w.word,
                        translation: w.translation,
                        phonetic: w.phonetic || ''
                    }));

                totalWordCount = book.wordCount || (Array.isArray(book.words) ? book.words.length : 0);
            }
        }

        words = this.shuffleArray(words);

        this.studySession = {
            source,
            words,
            currentIndex: 0,
            correct: 0,
            wrong: 0,
            reviewed: [],
            initialLearned,
            wordCount: totalWordCount || words.length
        };

        return this.studySession;
    },

    /**
     * 获取当前学习单词
     */
    getCurrentWord() {
        const { words, currentIndex } = this.studySession;
        if (currentIndex < words.length) {
            return words[currentIndex];
        }
        return null;
    },

    /**
     * 记录单词学习结果
     */
    recordWordResult(isCorrect) {
        const word = this.getCurrentWord();
        if (!word) return null;

        if (isCorrect) {
            this.studySession.correct++;
        } else {
            this.studySession.wrong++;
        }

        this.studySession.reviewed.push({
            word: word.word,
            isCorrect
        });

        // 更新熟练度（如果是生词本中的词）
        if (this.studySession.source === 'vocabulary') {
            this.updateMastery(word.word, isCorrect);
        } else if (this.studySession.source) {
            const bookId = this.studySession.source;
            const progress = this.getWordProgress(bookId);
            const updatedLearned = Math.min(
                this.studySession.wordCount || (this.studySession.initialLearned + this.studySession.reviewed.length),
                this.studySession.initialLearned + this.studySession.reviewed.length
            );
            this.saveWordProgress(bookId, {
                ...progress,
                learned: updatedLearned,
                lastStudyAt: Date.now()
            });
        } else {
            const bookId = this.studySession.source;
            const progress = this.getWordProgress(bookId);
            const updatedLearned = Math.min(
                this.studySession.wordCount || (this.studySession.initialLearned + this.studySession.reviewed.length),
                this.studySession.initialLearned + this.studySession.reviewed.length
            );
            this.saveWordProgress(bookId, {
                ...progress,
                learned: updatedLearned,
                lastStudyAt: Date.now()
            });
        }

        this.studySession.currentIndex++;
        return this.getCurrentWord();
    },

    /**
     * 结束学习会话
     */
    endStudySession() {
        const { source, correct, wrong, reviewed } = this.studySession;
        
        // 更新词书进度
        if (source !== 'vocabulary') {
            const progress = this.getWordProgress(source);
            const updatedLearned = Math.min(
                this.studySession.wordCount || (this.studySession.initialLearned + reviewed.length),
                this.studySession.initialLearned + reviewed.length
            );
            this.saveWordProgress(source, {
                ...progress,
                learned: updatedLearned,
                lastStudyAt: Date.now()
            });
        }

        return {
            total: reviewed.length,
            correct,
            wrong,
            accuracy: reviewed.length > 0 ? Math.round((correct / reviewed.length) * 100) : 0
        };
    },

    /**
     * 获取词书学习进度
     */
    getWordProgress(bookId) {
        try {
            const data = localStorage.getItem(this.KEYS.WORD_PROGRESS);
            const allProgress = data ? JSON.parse(data) : {};
            return allProgress[bookId] || { learned: 0 };
        } catch (e) {
            return { learned: 0 };
        }
    },

    /**
     * 保存词书学习进度
     */
    saveWordProgress(bookId, progress) {
        try {
            const data = localStorage.getItem(this.KEYS.WORD_PROGRESS);
            const allProgress = data ? JSON.parse(data) : {};
            allProgress[bookId] = progress;
            localStorage.setItem(this.KEYS.WORD_PROGRESS, JSON.stringify(allProgress));
        } catch (e) {
            console.error('[VocabularyManager] 保存进度失败:', e);
        }
    },

    // ==================== AI 功能 ====================

    /**
     * AI 讲解单词（结合句子语境）
     * @param {string} word 单词
     * @param {string} sentence 句子
     * @param {function} onStream 流式回调
     */
    async explainWord(word, sentence = '', onStream = null) {
        if (typeof GeminiService === 'undefined' || !GeminiService.isConfigured()) {
            return { success: false, message: '请先设置 Gemini API Key' };
        }

        try {
            const result = await GeminiService.explainWord(word, sentence, onStream);
            return { success: true, explanation: result };
        } catch (error) {
            return { success: false, message: error.message };
        }
    },

    /**
     * AI 生成例句
     */
    async generateSentences(word, count = 3) {
        if (typeof GeminiService === 'undefined' || !GeminiService.isConfigured()) {
            return { success: false, message: '请先设置 Gemini API Key' };
        }

        try {
            const prompt = `Please generate ${count} example sentences using the word "${word}" at a graduate English exam level. 
For each sentence:
1. Include the English sentence
2. Provide Chinese translation
3. Highlight how the word is used

Format as JSON array: [{"en": "...", "zh": "...", "usage": "..."}]`;

            const result = await GeminiService.call(prompt);
            // 尝试解析 JSON
            const jsonMatch = result.match(/\[[\s\S]*\]/);
            if (jsonMatch) {
                const sentences = JSON.parse(jsonMatch[0]);
                return { success: true, sentences };
            }
            return { success: true, sentences: result };
        } catch (error) {
            return { success: false, message: error.message };
        }
    },

    // ==================== 工具方法 ====================

    /**
     * 打乱数组
     */
    shuffleArray(array) {
        const result = [...array];
        for (let i = result.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [result[i], result[j]] = [result[j], result[i]];
        }
        return result;
    },

    /**
     * 导出生词本为 CSV
     */
    exportVocabularyCSV() {
        const vocabulary = this.getVocabulary();
        if (vocabulary.length === 0) {
            return { success: false, message: '生词本为空' };
        }

        let csv = '单词,释义,熟练度,添加时间\n';
        vocabulary.forEach(w => {
            csv += `"${w.word}","${w.translation}",${w.mastery},"${new Date(w.addedAt).toLocaleDateString()}"\n`;
        });

        const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `生词本_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);

        return { success: true, message: '导出成功' };
    },

    /**
     * 获取学习统计
     */
    getStats() {
        const vocabulary = this.getVocabulary();
        const books = this.getWordBooks();
        
        let totalLearned = 0;
        books.forEach(book => {
            const progress = this.getWordProgress(book.id);
            totalLearned += progress.learned || 0;
        });

        return {
            vocabularyCount: vocabulary.length,
            masteredCount: vocabulary.filter(w => w.mastery >= 4).length,
            bookCount: books.length,
            totalLearned
        };
    }
};

// 页面加载时初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => VocabularyManager.init());
} else {
    VocabularyManager.init();
}
