/**
 * Vocabulary UI - 单词本界面控制
 * 处理单词本界面的交互逻辑
 */

const VocabUI = {
    currentTab: 'my-words',

    /**
     * 初始化
     */
    init() {
        this.bindEvents();
        this.refreshVocabulary();
        this.refreshWordBooks();
        console.log('[VocabUI] 初始化完成');
    },

    /**
     * 绑定事件
     */
    bindEvents() {
        // 标签页切换
        document.querySelectorAll('.vocab-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                this.switchTab(tab.dataset.tab);
            });
        });

        // 搜索
        const searchInput = document.getElementById('vocab-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterVocabulary(e.target.value);
            });
        }
    },

    /**
     * 切换标签页
     */
    switchTab(tabName) {
        this.currentTab = tabName;

        // 更新标签样式
        document.querySelectorAll('.vocab-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });

        // 显示对应内容
        document.querySelectorAll('.vocab-content').forEach(content => {
            content.style.display = 'none';
        });
        const activeContent = document.getElementById(`tab-${tabName}`);
        if (activeContent) {
            activeContent.style.display = 'block';
        }

        // 刷新数据
        if (tabName === 'my-words') {
            this.refreshVocabulary();
        } else if (tabName === 'word-books') {
            this.refreshWordBooks();
        } else if (tabName === 'study') {
            this.refreshStudyOptions();
        }
    },

    // ==================== 生词本 ====================

    /**
     * 刷新生词列表
     */
    refreshVocabulary() {
        const vocabulary = VocabularyManager.getVocabulary();
        const listEl = document.getElementById('vocab-list');
        const countEl = document.getElementById('vocab-count');

        if (countEl) countEl.textContent = vocabulary.length;

        if (!listEl) return;

        if (vocabulary.length === 0) {
            listEl.innerHTML = `
                <div class="empty-state">
                    <p>📝 生词本还是空的</p>
                    <p style="font-size: 0.9rem; color: var(--text-muted);">
                        在答题时选中单词可以添加到生词本
                    </p>
                </div>
            `;
            return;
        }

        listEl.innerHTML = vocabulary.map(word => `
            <div class="vocab-item" data-word="${word.word}">
                <div class="vocab-word">
                    <strong>${word.word}</strong>
                    ${word.phonetic ? `<span class="phonetic">${word.phonetic}</span>` : ''}
                </div>
                <div class="vocab-translation">${word.translation}</div>
                <div class="vocab-meta">
                    <span class="mastery">熟练度: ${'⭐'.repeat(word.mastery)}${'☆'.repeat(5 - word.mastery)}</span>
                    <span class="review-count">复习 ${word.reviewCount} 次</span>
                </div>
                <div class="vocab-actions">
                    <button class="btn-small" onclick="VocabUI.explainWord('${word.word}', '${(word.sentence || '').replace(/'/g, "\\'")}')">🤖 AI讲解</button>
                    <button class="btn-small btn-danger" onclick="VocabUI.removeWord('${word.word}')">🗑️</button>
                </div>
            </div>
        `).join('');
    },

    /**
     * 过滤生词
     */
    filterVocabulary(keyword) {
        const items = document.querySelectorAll('.vocab-item');
        const lowerKeyword = keyword.toLowerCase();

        items.forEach(item => {
            const word = item.dataset.word.toLowerCase();
            item.style.display = word.includes(lowerKeyword) ? 'block' : 'none';
        });
    },

    /**
     * 删除生词
     */
    removeWord(word) {
        if (confirm(`确定要删除 "${word}" 吗？`)) {
            VocabularyManager.removeWord(word);
            this.refreshVocabulary();
            UIEffects.showToast('已删除', 'success');
        }
    },

    /**
     * 导出生词本
     */
    exportVocabulary() {
        const result = VocabularyManager.exportVocabularyCSV();
        if (result.success) {
            UIEffects.showToast(result.message, 'success');
        } else {
            UIEffects.showToast(result.message, 'error');
        }
    },

    // ==================== 词书管理 ====================

    // 内置词书列表
    builtInBooks: [
        { filename: '2025考研英语7000词.csv', name: '2025考研英语7000词' }
    ],

    /**
     * 刷新词书列表
     */
    refreshWordBooks() {
        const books = VocabularyManager.getWordBooks();
        const listEl = document.getElementById('word-books-list');

        if (!listEl) return;

        // 检查是否有内置词书未导入
        const importedNames = books.map(b => b.name);
        const availableBuiltIn = this.builtInBooks.filter(b => !importedNames.includes(b.name));

        let html = '';

        // 显示可用的内置词书
        if (availableBuiltIn.length > 0) {
            html += `
                <div class="built-in-books">
                    <h4 style="margin-bottom: 10px; color: var(--text-secondary);">📦 内置词书（点击加载）</h4>
                    ${availableBuiltIn.map(book => `
                        <div class="word-book-item built-in" onclick="VocabUI.loadBuiltInBook('${book.filename}', '${book.name}')">
                            <div class="book-info">
                                <strong>${book.name}</strong>
                                <span class="word-count">点击加载</span>
                            </div>
                            <div class="book-actions">
                                <button class="btn-small btn-primary">📥 加载</button>
                            </div>
                        </div>
                    `).join('')}
                </div>
                <hr style="border: none; border-top: 1px solid rgba(255,255,255,0.1); margin: 20px 0;">
            `;
        }

        if (books.length === 0 && availableBuiltIn.length === 0) {
            html += `
                <div class="empty-state">
                    <p>📖 还没有词书</p>
                    <p style="font-size: 0.9rem; color: var(--text-muted);">
                        点击上方按钮导入 CSV 格式的词书
                    </p>
                </div>
            `;
        } else {
            // 显示已导入的词书
            html += books.map(book => {
                const progress = VocabularyManager.getWordProgress(book.id);
                const progressPercent = Math.round((progress.learned || 0) / book.wordCount * 100);

                return `
                    <div class="word-book-item">
                        <div class="book-info">
                            <strong>${book.name}</strong>
                            <span class="word-count">${book.wordCount} 词 ${book.isBuiltIn ? '(内置)' : ''}</span>
                        </div>
                        <div class="book-progress">
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${progressPercent}%"></div>
                            </div>
                            <span class="progress-text">${progress.learned || 0}/${book.wordCount}</span>
                        </div>
                        <div class="book-actions">
                            <button class="btn-small btn-primary" onclick="VocabUI.startStudy('${book.id}')">📖 学习</button>
                            <button class="btn-small btn-danger" onclick="VocabUI.deleteWordBook('${book.id}')">🗑️</button>
                        </div>
                    </div>
                `;
            }).join('');
        }

        listEl.innerHTML = html;
    },

    /**
     * 加载内置词书
     */
    async loadBuiltInBook(filename, bookName) {
        UIEffects.showToast('正在加载词书...', 'info');
        
        const result = await VocabularyManager.loadBuiltInWordBook(filename, bookName);
        
        if (result.success) {
            UIEffects.showToast(result.message, 'success');
            this.refreshWordBooks();
            this.refreshStudyOptions();
        } else {
            UIEffects.showToast(result.message, 'error');
        }
    },

    /**
     * 显示导入对话框
     */
    showImportDialog() {
        document.getElementById('import-modal').style.display = 'flex';
    },

    /**
     * 隐藏导入对话框
     */
    hideImportDialog() {
        document.getElementById('import-modal').style.display = 'none';
        document.getElementById('book-name-input').value = '';
        document.getElementById('csv-file-input').value = '';
    },

    /**
     * 导入词书
     */
    async importWordBook() {
        const fileInput = document.getElementById('csv-file-input');
        const nameInput = document.getElementById('book-name-input');

        if (!fileInput.files[0]) {
            UIEffects.showToast('请选择 CSV 文件', 'error');
            return;
        }

        try {
            const result = await VocabularyManager.importWordBook(
                fileInput.files[0],
                nameInput.value.trim()
            );

            this.hideImportDialog();
            this.refreshWordBooks();
            UIEffects.showToast(result.message, 'success');
        } catch (error) {
            UIEffects.showToast(error.message, 'error');
        }
    },

    /**
     * 删除词书
     */
    deleteWordBook(bookId) {
        const book = VocabularyManager.getWordBook(bookId);
        if (confirm(`确定要删除词书 "${book?.name}" 吗？`)) {
            VocabularyManager.deleteWordBook(bookId);
            this.refreshWordBooks();
            UIEffects.showToast('已删除', 'success');
        }
    },

    // ==================== 背单词 ====================

    /**
     * 刷新学习选项
     */
    refreshStudyOptions() {
        const books = VocabularyManager.getWordBooks();
        const optionsEl = document.getElementById('study-book-options');

        if (!optionsEl) return;

        optionsEl.innerHTML = books.map(book => {
            const progress = VocabularyManager.getWordProgress(book.id);
            return `
                <div class="study-option" onclick="VocabUI.startStudy('${book.id}')">
                    <span class="study-icon">📖</span>
                    <div>
                        <strong>${book.name}</strong>
                        <p>已学 ${progress.learned || 0}/${book.wordCount} 词</p>
                    </div>
                </div>
            `;
        }).join('');
    },

    /**
     * 开始学习
     */
    startStudy(source) {
        if (this.currentTab !== 'study') {
            this.switchTab('study');
        }

        const session = VocabularyManager.startStudySession(source, 20);

        if (session.words.length === 0) {
            UIEffects.showToast('没有可学习的单词', 'error');
            return;
        }

        // 隐藏选项，显示卡片
        document.getElementById('study-options').style.display = 'none';
        document.getElementById('study-card').style.display = 'block';
        document.getElementById('study-result').style.display = 'none';

        this.showCurrentCard();
    },

    /**
     * 显示当前卡片
     */
    showCurrentCard() {
        const word = VocabularyManager.getCurrentWord();
        const session = VocabularyManager.studySession;

        if (!word) {
            this.showStudyResult();
            return;
        }

        document.getElementById('study-progress').textContent = 
            `${session.currentIndex + 1}/${session.words.length}`;
        document.getElementById('study-score').textContent = 
            `✅ ${session.correct} | ❌ ${session.wrong}`;

        document.getElementById('card-word').textContent = word.word;
        document.getElementById('card-phonetic').textContent = word.phonetic || '';
        document.getElementById('card-translation').textContent = word.translation;
        document.getElementById('card-translation').style.display = 'none';
        document.getElementById('card-result').style.display = 'none';
        document.querySelector('.card-actions').style.display = 'flex';
    },

    /**
     * 显示答案
     */
    showAnswer() {
        document.getElementById('card-translation').style.display = 'block';
        document.querySelector('.card-actions').style.display = 'none';
        document.getElementById('card-result').style.display = 'flex';
    },

    /**
     * 记录结果
     */
    recordResult(isCorrect) {
        VocabularyManager.recordWordResult(isCorrect);
        this.showCurrentCard();
    },

    /**
     * 显示学习结果
     */
    showStudyResult() {
        const result = VocabularyManager.endStudySession();

        document.getElementById('study-card').style.display = 'none';
        document.getElementById('study-result').style.display = 'block';

        document.getElementById('study-total').textContent = result.total;
        document.getElementById('study-correct').textContent = result.correct;
        document.getElementById('study-rate').textContent = result.accuracy + '%';

        // 给经验值奖励
        const expGain = result.correct * 5;
        if (expGain > 0) {
            StorageManager.addExp(expGain);
            UIEffects.updateHUD();
            UIEffects.showToast(`背单词完成！获得 ${expGain} 经验`, 'success');
        }
    },

    /**
     * 重置学习
     */
    resetStudy() {
        document.getElementById('study-options').style.display = 'block';
        document.getElementById('study-card').style.display = 'none';
        document.getElementById('study-result').style.display = 'none';
        this.refreshStudyOptions();
    },

    // ==================== AI 功能 ====================

    /**
     * AI 讲解单词
     */
    async explainWord(word, sentence = '') {
        const modal = document.getElementById('ai-modal');
        const body = document.getElementById('ai-modal-body');

        modal.style.display = 'flex';
        body.innerHTML = '<div class="loading">🤖 AI 正在分析中...</div>';

        let fullText = '';
        const onStream = (text) => {
            fullText += text;
            // 简单的 Markdown 渲染：将 **text** 转换为 <b>text</b>，\n 转换为 <br>
            // 实际项目中建议使用 marked.js 等库
            body.innerHTML = `<div class="ai-explanation">${UIEffects.renderMarkdown(fullText)}</div>`;
            // 自动滚动到底部
            body.scrollTop = body.scrollHeight;
        };

        try {
            const result = await VocabularyManager.explainWord(word, sentence, onStream);
            
            if (result.success) {
                // 最终渲染一次，确保格式正确
                body.innerHTML = `<div class="ai-explanation">${UIEffects.renderMarkdown(result.explanation)}</div>`;
            } else {
                body.innerHTML = `<div class="error">${result.message}</div>`;
            }
        } catch (error) {
            body.innerHTML = `<div class="error">AI 分析失败: ${error.message}</div>`;
        }
    },

    /**
     * 背单词时 AI 讲解
     */
    async askAI() {
        const word = VocabularyManager.getCurrentWord();
        if (word) {
            await this.explainWord(word.word, word.sentence || '');
        }
    },

    /**
     * 关闭 AI 弹窗
     */
    closeAIModal() {
        document.getElementById('ai-modal').style.display = 'none';
    }
};

// 导出为全局变量
window.VocabUI = VocabUI;

// 页面加载时初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => VocabUI.init());
} else {
    VocabUI.init();
}
