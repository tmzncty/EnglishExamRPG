/**
 * Storage Manager - 存档管理器
 * 负责本地存储、进度保存、API Key 管理、存档导入导出
 */

const StorageManager = {
    // 存储键名
    KEYS: {
        GAME_DATA: 'englishExam_gameData',
        SETTINGS: 'englishExam_settings',
        API_KEY: 'englishExam_geminiKey',
        ANSWERS_HISTORY: 'englishExam_answersHistory',
        PENDING_ANSWERS: 'englishExam_pendingAnswers',  // 考试模式待提交答案
        VOCABULARY: 'englishExam_vocabulary',  // 单词本
        WEBDAV_CONFIG: 'englishExam_webdavConfig' // WebDAV 配置
    },

    // 默认游戏数据
    defaultGameData: {
        hp: 100,
        maxHp: 100,
        exp: 0,
        level: 1,
        title: '四级萌新',
        totalCorrect: 0,
        totalWrong: 0,
        currentYear: 2010,
        currentQuestionIndex: 0,
        answers: {},           // { questionId: userAnswer }
        wrongQuestions: [],    // 错题集
        notes: {},             // { questionId: noteText }
        vocabulary: [],        // 收藏的生词
        lastPlayTime: null
    },

    // 默认设置
    defaultSettings: {
        theme: 'acg',           // 'default' | 'acg'
        showMascot: true,
        mascotCharacter: 'default',
        soundEnabled: false,
        fontSize: 'medium',     // 'small' | 'medium' | 'large'
        autoSave: true,
        aiEnabled: true
    },

    // 称谓列表（根据等级）
    titles: [
        { level: 1, title: '四级萌新', expRequired: 0 },
        { level: 2, title: '六级选手', expRequired: 100 },
        { level: 3, title: '考研新兵', expRequired: 300 },
        { level: 4, title: '阅读达人', expRequired: 600 },
        { level: 5, title: '完形高手', expRequired: 1000 },
        { level: 6, title: '翻译能手', expRequired: 1500 },
        { level: 7, title: '写作大师', expRequired: 2100 },
        { level: 8, title: '英语学霸', expRequired: 2800 },
        { level: 9, title: '考研战神', expRequired: 3600 },
        { level: 10, title: '传说考生', expRequired: 5000 }
    ],

    /**
     * 初始化存储管理器
     */
    init() {
        // 确保有默认数据
        if (!this.getGameData()) {
            this.saveGameData(this.defaultGameData);
        }
        if (!this.getSettings()) {
            this.saveSettings(this.defaultSettings);
        }
        console.log('[StorageManager] 初始化完成');
    },

    // ==================== 游戏数据 ====================

    /**
     * 获取游戏数据
     */
    getGameData() {
        try {
            const data = localStorage.getItem(this.KEYS.GAME_DATA);
            return data ? JSON.parse(data) : null;
        } catch (e) {
            console.error('[StorageManager] 读取游戏数据失败:', e);
            return null;
        }
    },

    /**
     * 保存游戏数据
     */
    saveGameData(data) {
        try {
            data.lastPlayTime = new Date().toISOString();
            localStorage.setItem(this.KEYS.GAME_DATA, JSON.stringify(data));
            return true;
        } catch (e) {
            console.error('[StorageManager] 保存游戏数据失败:', e);
            return false;
        }
    },

    /**
     * 更新部分游戏数据
     */
    updateGameData(updates) {
        const data = this.getGameData() || { ...this.defaultGameData };
        Object.assign(data, updates);
        return this.saveGameData(data);
    },

    /**
     * 重置游戏数据
     */
    resetGameData() {
        return this.saveGameData({ ...this.defaultGameData });
    },

    // ==================== HP/EXP 系统 ====================

    /**
     * 扣除 HP
     */
    decreaseHP(amount = 10) {
        const data = this.getGameData();
        data.hp = Math.max(0, data.hp - amount);
        this.saveGameData(data);
        return data.hp;
    },

    /**
     * 恢复 HP
     */
    restoreHP(amount = null) {
        const data = this.getGameData();
        data.hp = amount !== null ? amount : data.maxHp;
        this.saveGameData(data);
        return data.hp;
    },

    /**
     * 增加经验值
     */
    addExp(amount = 10) {
        const data = this.getGameData();
        data.exp += amount;
        data.totalCorrect += 1;

        // 检查升级
        const newLevel = this.calculateLevel(data.exp);
        if (newLevel > data.level) {
            data.level = newLevel;
            data.title = this.getTitleByLevel(newLevel);
            data.maxHp += 10; // 升级增加最大HP
            data.hp = data.maxHp; // 升级回满血
        }

        this.saveGameData(data);
        return {
            exp: data.exp,
            level: data.level,
            title: data.title,
            leveledUp: newLevel > data.level
        };
    },

    /**
     * 记录错误
     */
    recordWrong() {
        const data = this.getGameData();
        data.totalWrong += 1;
        this.saveGameData(data);
    },

    /**
     * 根据经验计算等级
     */
    calculateLevel(exp) {
        for (let i = this.titles.length - 1; i >= 0; i--) {
            if (exp >= this.titles[i].expRequired) {
                return this.titles[i].level;
            }
        }
        return 1;
    },

    /**
     * 根据等级获取称谓
     */
    getTitleByLevel(level) {
        const titleInfo = this.titles.find(t => t.level === level);
        return titleInfo ? titleInfo.title : '四级萌新';
    },

    /**
     * 获取下一级所需经验
     */
    getExpToNextLevel(currentExp) {
        for (const t of this.titles) {
            if (t.expRequired > currentExp) {
                return t.expRequired - currentExp;
            }
        }
        return 0; // 已满级
    },

    // ==================== 答题记录 ====================

    /**
     * 记录答案
     */
    recordAnswer(questionId, answer, isCorrect) {
        const data = this.getGameData();
        data.answers[questionId] = {
            answer,
            isCorrect,
            timestamp: new Date().toISOString()
        };

        if (!isCorrect && !data.wrongQuestions.includes(questionId)) {
            data.wrongQuestions.push(questionId);
        }

        this.saveGameData(data);
    },

    /**
     * 获取答题记录
     */
    getAnswer(questionId) {
        const data = this.getGameData();
        return data.answers[questionId] || null;
    },

    /**
     * 清除答题记录
     */
    clearAnswers() {
        const data = this.getGameData();
        data.answers = {};
        data.wrongQuestions = [];
        this.saveGameData(data);
    },

    // ==================== 考试模式待提交答案 ====================

    /**
     * 记录待提交答案（考试模式）
     */
    recordPendingAnswer(questionId, answer) {
        try {
            const pending = this.getPendingAnswers();
            pending[questionId] = answer;
            localStorage.setItem(this.KEYS.PENDING_ANSWERS, JSON.stringify(pending));
        } catch (e) {
            console.error('[StorageManager] 记录待提交答案失败:', e);
        }
    },

    /**
     * 获取待提交答案
     */
    getPendingAnswers() {
        try {
            const data = localStorage.getItem(this.KEYS.PENDING_ANSWERS);
            return data ? JSON.parse(data) : {};
        } catch (e) {
            return {};
        }
    },

    /**
     * 获取单个待提交答案
     */
    getPendingAnswer(questionId) {
        const pending = this.getPendingAnswers();
        return pending[questionId] || null;
    },

    /**
     * 清除待提交答案
     */
    clearPendingAnswers() {
        localStorage.removeItem(this.KEYS.PENDING_ANSWERS);
    },

    // ==================== 设置 ====================

    /**
     * 获取设置
     */
    getSettings() {
        try {
            const data = localStorage.getItem(this.KEYS.SETTINGS);
            return data ? JSON.parse(data) : null;
        } catch (e) {
            console.error('[StorageManager] 读取设置失败:', e);
            return null;
        }
    },

    /**
     * 保存设置
     */
    saveSettings(settings) {
        try {
            localStorage.setItem(this.KEYS.SETTINGS, JSON.stringify(settings));
            return true;
        } catch (e) {
            console.error('[StorageManager] 保存设置失败:', e);
            return false;
        }
    },

    /**
     * 更新部分设置
     */
    updateSettings(updates) {
        const settings = this.getSettings() || { ...this.defaultSettings };
        Object.assign(settings, updates);
        return this.saveSettings(settings);
    },

    // ==================== API Key ====================

    /**
     * 保存 Gemini API Key
     */
    saveApiKey(key) {
        try {
            // 简单混淆存储（不是真正的加密，但比明文好）
            const encoded = btoa(key);
            localStorage.setItem(this.KEYS.API_KEY, encoded);
            return true;
        } catch (e) {
            console.error('[StorageManager] 保存 API Key 失败:', e);
            return false;
        }
    },

    /**
     * 获取 Gemini API Key
     */
    getApiKey() {
        try {
            const encoded = localStorage.getItem(this.KEYS.API_KEY);
            return encoded ? atob(encoded) : null;
        } catch (e) {
            console.error('[StorageManager] 读取 API Key 失败:', e);
            return null;
        }
    },

    /**
     * 删除 API Key
     */
    removeApiKey() {
        localStorage.removeItem(this.KEYS.API_KEY);
    },

    /**
     * 检查是否有 API Key
     */
    hasApiKey() {
        return !!this.getApiKey();
    },

    // ==================== 笔记功能 ====================

    /**
     * 保存笔记
     */
    saveNote(questionId, note) {
        const data = this.getGameData();
        data.notes[questionId] = {
            content: note,
            timestamp: new Date().toISOString()
        };
        this.saveGameData(data);
    },

    /**
     * 获取笔记
     */
    getNote(questionId) {
        const data = this.getGameData();
        return data.notes[questionId] || null;
    },

    // ==================== 生词本 ====================

    /**
     * 添加生词
     */
    addVocabulary(word, meaning, context) {
        const data = this.getGameData();
        const exists = data.vocabulary.find(v => v.word.toLowerCase() === word.toLowerCase());

        if (!exists) {
            data.vocabulary.push({
                word,
                meaning,
                context,
                addedAt: new Date().toISOString()
            });
            this.saveGameData(data);
            return true;
        }
        return false;
    },

    /**
     * 获取生词本
     */
    getVocabulary() {
        const data = this.getGameData();
        return data.vocabulary || [];
    },

    /**
     * 删除生词
     */
    removeVocabulary(word) {
        const data = this.getGameData();
        data.vocabulary = data.vocabulary.filter(v => v.word.toLowerCase() !== word.toLowerCase());
        this.saveGameData(data);
    },

    // ==================== 存档导入导出 ====================

    /**
     * 导出存档
     */
    exportSave() {
        const exportData = {
            version: '1.0',
            exportTime: new Date().toISOString(),
            gameData: this.getGameData(),
            settings: this.getSettings()
            // 注意：不导出 API Key
        };

        const jsonString = JSON.stringify(exportData, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `english_exam_save_${new Date().toISOString().split('T')[0]}.json`;
        a.click();

        URL.revokeObjectURL(url);
        return jsonString;
    },

    /**
     * 导入存档
     */
    async importSave(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();

            reader.onload = (e) => {
                try {
                    const data = JSON.parse(e.target.result);

                    if (!data.version || !data.gameData) {
                        reject(new Error('无效的存档文件'));
                        return;
                    }

                    // 导入游戏数据
                    if (data.gameData) {
                        this.saveGameData(data.gameData);
                    }

                    // 导入设置
                    if (data.settings) {
                        this.saveSettings(data.settings);
                    }

                    resolve({
                        success: true,
                        message: '存档导入成功！',
                        data
                    });
                } catch (err) {
                    reject(new Error('存档文件解析失败'));
                }
            };

            reader.onerror = () => reject(new Error('文件读取失败'));
            reader.readAsText(file);
        });
    },

    /**
     * 获取存档文本（用于复制粘贴）
     */
    getSaveText() {
        const exportData = {
            version: '1.0',
            exportTime: new Date().toISOString(),
            gameData: this.getGameData(),
            settings: this.getSettings()
        };
        return JSON.stringify(exportData);
    },

    /**
     * 从文本导入存档
     */
    importSaveFromText(text) {
        try {
            const data = JSON.parse(text);

            if (!data.version || !data.gameData) {
                return { success: false, message: '无效的存档数据' };
            }

            if (data.gameData) {
                this.saveGameData(data.gameData);
            }

            if (data.settings) {
                this.saveSettings(data.settings);
            }

            return { success: true, message: '存档导入成功！' };
        } catch (err) {
            return { success: false, message: '存档数据解析失败' };
        }
    },

    // ==================== WebDAV 同步 ====================

    getWebDAVConfig() {
        try {
            const data = localStorage.getItem(this.KEYS.WEBDAV_CONFIG);
            return data ? JSON.parse(data) : null;
        } catch (e) {
            return null;
        }
    },

    saveWebDAVConfig(config) {
        localStorage.setItem(this.KEYS.WEBDAV_CONFIG, JSON.stringify(config));
    },

    async syncToCloud() {
        const config = this.getWebDAVConfig();
        if (!config || !config.url || !config.user || !config.password) {
            throw new Error('请先配置 WebDAV 信息');
        }

        const exportData = {
            version: '1.0',
            exportTime: new Date().toISOString(),
            gameData: this.getGameData(),
            settings: this.getSettings(),
            answersHistory: localStorage.getItem(this.KEYS.ANSWERS_HISTORY),
            vocabulary: localStorage.getItem(this.KEYS.VOCABULARY)
        };

        const filename = 'english_exam_rpg_save.json';
        const url = config.url.endsWith('/') ? config.url + filename : config.url + '/' + filename;

        const response = await fetch(url, {
            method: 'PUT',
            headers: {
                'Authorization': 'Basic ' + btoa(config.user + ':' + config.password),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(exportData)
        });

        if (!response.ok) {
            throw new Error(`上传失败: ${response.status} ${response.statusText}`);
        }

        return true;
    },

    async syncFromCloud() {
        const config = this.getWebDAVConfig();
        if (!config || !config.url || !config.user || !config.password) {
            throw new Error('请先配置 WebDAV 信息');
        }

        const filename = 'english_exam_rpg_save.json';
        const url = config.url.endsWith('/') ? config.url + filename : config.url + '/' + filename;

        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Authorization': 'Basic ' + btoa(config.user + ':' + config.password)
            }
        });

        if (!response.ok) {
            throw new Error(`下载失败: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();

        if (data.gameData) this.saveGameData(data.gameData);
        if (data.settings) this.saveSettings(data.settings);
        if (data.answersHistory) localStorage.setItem(this.KEYS.ANSWERS_HISTORY, data.answersHistory);
        if (data.vocabulary) localStorage.setItem(this.KEYS.VOCABULARY, data.vocabulary);

        return true;
    },

    // ==================== 文件导出/导入 ====================

    exportSaveData() {
        const exportData = {
            version: '1.0',
            exportTime: new Date().toISOString(),
            gameData: this.getGameData(),
            settings: this.getSettings(),
            answersHistory: localStorage.getItem(this.KEYS.ANSWERS_HISTORY),
            vocabulary: localStorage.getItem(this.KEYS.VOCABULARY)
        };

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `english_exam_rpg_save_${new Date().toISOString().slice(0, 10)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    },

    async importSaveFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const data = JSON.parse(e.target.result);
                    if (data.gameData) this.saveGameData(data.gameData);
                    if (data.settings) this.saveSettings(data.settings);
                    if (data.answersHistory) localStorage.setItem(this.KEYS.ANSWERS_HISTORY, data.answersHistory);
                    if (data.vocabulary) localStorage.setItem(this.KEYS.VOCABULARY, data.vocabulary);
                    resolve({ success: true, message: '存档导入成功！' });
                } catch (err) {
                    reject(new Error('存档文件格式错误'));
                }
            };
            reader.onerror = () => reject(new Error('读取文件失败'));
            reader.readAsText(file);
        });
    },

    // ==================== 统计数据 ====================

    /**
     * 获取统计信息
     */
    getStats() {
        const data = this.getGameData();
        const total = data.totalCorrect + data.totalWrong;
        const accuracy = total > 0 ? Math.round((data.totalCorrect / total) * 100) : 0;

        return {
            level: data.level,
            title: data.title,
            exp: data.exp,
            expToNext: this.getExpToNextLevel(data.exp),
            hp: data.hp,
            maxHp: data.maxHp,
            totalCorrect: data.totalCorrect,
            totalWrong: data.totalWrong,
            accuracy,
            wrongQuestionsCount: data.wrongQuestions.length,
            vocabularyCount: data.vocabulary.length,
            notesCount: Object.keys(data.notes).length
        };
    },

    // ==================== Backend Save/Load (SQLite) ====================

    /**
     * Save game data to backend (SQLite)
     * @param {number} slotId - 0 = auto-save, 1-5 = manual slots
     * @param {object} customData - optional override for game data
     */
    async saveToBackend(slotId = 0, customData = null) {
        try {
            const dataToSave = customData || this.getGameData();

            // Add metadata for UI preview
            const saveData = {
                ...dataToSave,
                saveMetadata: {
                    slotId,
                    timestamp: new Date().toISOString(),
                    questionProgress: `${(dataToSave.currentQuestionIndex || 0) + 1}/${dataToSave.totalQuestions || '?'}`,
                    examMode: dataToSave.examMode || 'unknown',
                    selectedYears: dataToSave.selectedYears || [dataToSave.currentYear],
                    level: dataToSave.level,
                    hp: dataToSave.hp
                }
            };

            const response = await fetch('/api/save_game', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    slot_id: slotId,
                    data: saveData
                })
            });

            const result = await response.json();
            if (result.success) {
                console.log(`[StorageManager] Saved to backend slot ${slotId}`);
                return true;
            }
            throw new Error(result.message);
        } catch (e) {
            console.error('[StorageManager] Backend save failed:', e);
            return false;
        }
    },

    /**
     * Load game data from backend
     */
    async loadFromBackend(slotId = 0) {
        try {
            const response = await fetch('/api/load_game', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ slot_id: slotId })
            });

            const result = await response.json();
            if (result.success && result.data) {
                // Update localStorage as cache
                this.saveGameData(result.data);
                console.log(`[StorageManager] Loaded from backend slot ${slotId}`);
                return result.data;
            }
            return null;
        } catch (e) {
            console.error('[StorageManager] Backend load failed:', e);
            return null;
        }
    },

    /**
     * List all save slots with metadata
     */
    async listSaveSlots() {
        try {
            const response = await fetch('/api/list_saves', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: 1 })
            });

            const result = await response.json();
            return result.success ? result.saves : [];
        } catch (e) {
            console.error('[StorageManager] List saves failed:', e);
            return [];
        }
    },

    /**
     * Auto-migrate localStorage to backend on first load
     */
    async migrateToBackend() {
        const localData = this.getGameData();
        if (localData && (Object.keys(localData.answers || {}).length > 0 || localData.currentQuestionIndex > 0)) {
            console.log('[StorageManager] Migrating localStorage to backend slot #1...');
            const success = await this.saveToBackend(1, localData);
            if (success) {
                console.log('[StorageManager] Migration complete');
                return true;
            }
        }
        return false;
    }
};

// 导出
window.StorageManager = StorageManager;
