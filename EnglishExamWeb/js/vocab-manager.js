/**
 * Vocabulary Manager - 单词本前端集成
 * 与后端 API 交互，管理单词学习
 */

const VocabManager = {
    // 后端 API 地址
    API_BASE: 'http://localhost:8000/api',
    
    // 当前状态
    currentWords: [],
    currentIndex: 0,
    todayProgress: {
        total: 0,
        completed: 0,
        correct: 0
    },
    
    /**
     * 初始化单词本
     */
    async init() {
        console.log('[VocabManager] 初始化...');
        
        // 获取每日任务
        await this.loadDailyWords();
        
        // 绑定事件
        this.bindEvents();
        
        // 显示第一个单词
        this.showCurrentWord();
    },
    
    /**
     * 加载每日单词
     */
    async loadDailyWords(count = null) {
        try {
            const url = count 
                ? `${this.API_BASE}/vocab/daily?count=${count}`
                : `${this.API_BASE}/vocab/daily`;
            
            const response = await fetch(url);
            const data = await response.json();
            
            this.currentWords = data.words;
            this.todayProgress.total = data.count;
            this.todayProgress.completed = 0;
            this.todayProgress.correct = 0;
            
            console.log(`[VocabManager] 加载了 ${data.count} 个单词`);
            
            // 更新 UI
            this.updateProgress();
            
            return data.words;
        } catch (error) {
            console.error('[VocabManager] 加载单词失败:', error);
            UIEffects.showToast('加载单词失败，请检查后端服务', 'error');
            return [];
        }
    },
    
    /**
     * 显示当前单词
     */
    showCurrentWord() {
        if (this.currentIndex >= this.currentWords.length) {
            this.showCompletionScreen();
            return;
        }
        
        const word = this.currentWords[this.currentIndex];
        
        // 更新单词卡片
        const wordCard = document.getElementById('vocab-word-card');
        if (wordCard) {
            wordCard.innerHTML = `
                <div class="word-front">
                    <h2 class="vocab-word">${word.word}</h2>
                    <p class="vocab-context">${word.source_sentence || ''}</p>
                    <button class="btn-primary vocab-reveal-btn">显示释义</button>
                </div>
                <div class="word-back" style="display: none;">
                    <h2 class="vocab-word">${word.word}</h2>
                    <p class="vocab-translation">${word.translation || '暂无翻译'}</p>
                    <p class="vocab-context">${word.source_sentence || ''}</p>
                    <div class="vocab-source">
                        <small>来源: ${word.source_year}年 ${word.source_question}</small>
                    </div>
                    <div class="vocab-quality-selector">
                        <p>记忆质量评分:</p>
                        <div class="quality-buttons">
                            ${this.generateQualityButtons()}
                        </div>
                    </div>
                    <button class="btn-secondary vocab-ai-explain-btn">
                        <i class="ph-duotone ph-magic-wand"></i> AI 详细讲解
                    </button>
                </div>
            `;
            
            // 绑定翻转事件
            const revealBtn = wordCard.querySelector('.vocab-reveal-btn');
            if (revealBtn) {
                revealBtn.addEventListener('click', () => this.revealWord());
            }
            
            // 绑定质量评分按钮
            const qualityBtns = wordCard.querySelectorAll('.quality-btn');
            qualityBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    const quality = parseInt(btn.dataset.quality);
                    this.submitReview(quality);
                });
            });
            
            // 绑定 AI 讲解按钮
            const aiBtn = wordCard.querySelector('.vocab-ai-explain-btn');
            if (aiBtn) {
                aiBtn.addEventListener('click', () => this.showAIExplanation(word.word));
            }
        }
        
        // 更新进度
        this.updateProgress();
    },
    
    /**
     * 翻转单词卡片（显示释义）
     */
    revealWord() {
        const card = document.getElementById('vocab-word-card');
        const front = card.querySelector('.word-front');
        const back = card.querySelector('.word-back');
        
        if (front && back) {
            front.style.display = 'none';
            back.style.display = 'block';
            
            // 添加翻转动画
            card.classList.add('flipped');
        }
    },
    
    /**
     * 生成质量评分按钮
     */
    generateQualityButtons() {
        const qualities = [
            { value: 0, label: '完全不记得', emoji: '😵', color: '#e74c3c' },
            { value: 1, label: '有印象', emoji: '😕', color: '#e67e22' },
            { value: 2, label: '想起来了', emoji: '😐', color: '#f39c12' },
            { value: 3, label: '有点难', emoji: '🙂', color: '#3498db' },
            { value: 4, label: '有点犹豫', emoji: '😊', color: '#2ecc71' },
            { value: 5, label: '完全正确', emoji: '😎', color: '#27ae60' }
        ];
        
        return qualities.map(q => `
            <button class="quality-btn" data-quality="${q.value}" 
                    style="background: ${q.color};" 
                    title="${q.label}">
                <span class="quality-emoji">${q.emoji}</span>
                <span class="quality-label">${q.value}</span>
            </button>
        `).join('');
    },
    
    /**
     * 提交复习结果
     */
    async submitReview(quality) {
        const word = this.currentWords[this.currentIndex];
        
        try {
            const response = await fetch(`${this.API_BASE}/vocab/review`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    word: word.word,
                    quality: quality
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // 更新进度
                this.todayProgress.completed++;
                if (quality >= 3) {
                    this.todayProgress.correct++;
                }
                
                // 显示反馈
                const feedback = this.getQualityFeedback(quality);
                UIEffects.showToast(feedback, quality >= 3 ? 'success' : 'info');
                
                // 播放音效
                if (typeof UIEffects.playSound === 'function') {
                    UIEffects.playSound(quality >= 3 ? 'correct' : 'incorrect');
                }
                
                // 延迟后显示下一个单词
                setTimeout(() => {
                    this.nextWord();
                }, 1000);
            }
        } catch (error) {
            console.error('[VocabManager] 提交复习失败:', error);
            UIEffects.showToast('提交失败，请重试', 'error');
        }
    },
    
    /**
     * 获取质量反馈消息
     */
    getQualityFeedback(quality) {
        const messages = {
            0: '没关系，继续努力！',
            1: '有点印象了，再接再厉！',
            2: '想起来了，不错！',
            3: '答对了，但要更熟练哦！',
            4: '很好，继续保持！',
            5: '完美！完全掌握了！'
        };
        return messages[quality] || '继续加油！';
    },
    
    /**
     * 下一个单词
     */
    nextWord() {
        this.currentIndex++;
        this.showCurrentWord();
    },
    
    /**
     * 上一个单词（复习模式）
     */
    prevWord() {
        if (this.currentIndex > 0) {
            this.currentIndex--;
            this.showCurrentWord();
        }
    },
    
    /**
     * 显示 AI 讲解
     */
    async showAIExplanation(word) {
        const currentWord = this.currentWords[this.currentIndex];
        
        try {
            // 显示加载状态
            UIEffects.showLoading('AI 讲解生成中...');
            
            const response = await fetch(`${this.API_BASE}/ai/explain-word`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    word: word,
                    context: currentWord.source_sentence
                })
            });
            
            const data = await response.json();
            
            UIEffects.hideLoading();
            
            // 显示讲解弹窗
            this.showExplanationModal(word, data.explanation);
            
        } catch (error) {
            console.error('[VocabManager] AI 讲解失败:', error);
            UIEffects.hideLoading();
            UIEffects.showToast('AI 讲解失败，请重试', 'error');
        }
    },
    
    /**
     * 显示讲解模态框
     */
    showExplanationModal(word, explanation) {
        // 创建或获取模态框
        let modal = document.getElementById('ai-explanation-modal');
        
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'ai-explanation-modal';
            modal.className = 'modal';
            document.body.appendChild(modal);
        }
        
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3><i class="ph-duotone ph-magic-wand"></i> AI 详细讲解: ${word}</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="ai-explanation-content">
                        ${this.formatExplanation(explanation)}
                    </div>
                </div>
            </div>
        `;
        
        // 显示模态框
        modal.style.display = 'flex';
        
        // 绑定关闭事件
        const closeBtn = modal.querySelector('.modal-close');
        closeBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
        
        // 点击外部关闭
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    },
    
    /**
     * 格式化 AI 讲解内容
     */
    formatExplanation(text) {
        // 将 Markdown 格式转换为 HTML
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/^(.+)$/gm, '<p>$1</p>');
    },
    
    /**
     * 更新进度显示
     */
    updateProgress() {
        const progressEl = document.getElementById('vocab-progress');
        if (progressEl) {
            const percent = this.todayProgress.total > 0
                ? (this.todayProgress.completed / this.todayProgress.total * 100)
                : 0;
            
            progressEl.innerHTML = `
                <div class="progress-info">
                    <span>${this.todayProgress.completed} / ${this.todayProgress.total}</span>
                    <span>正确率: ${this.calculateAccuracy()}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${percent}%"></div>
                </div>
            `;
        }
    },
    
    /**
     * 计算正确率
     */
    calculateAccuracy() {
        if (this.todayProgress.completed === 0) return 0;
        return Math.round(this.todayProgress.correct / this.todayProgress.completed * 100);
    },
    
    /**
     * 显示完成界面
     */
    showCompletionScreen() {
        const card = document.getElementById('vocab-word-card');
        if (card) {
            const accuracy = this.calculateAccuracy();
            
            card.innerHTML = `
                <div class="vocab-completion">
                    <h2>🎉 今日任务完成！</h2>
                    <div class="completion-stats">
                        <div class="stat-item">
                            <span class="stat-label">完成单词</span>
                            <span class="stat-value">${this.todayProgress.completed}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">正确数</span>
                            <span class="stat-value">${this.todayProgress.correct}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">正确率</span>
                            <span class="stat-value">${accuracy}%</span>
                        </div>
                    </div>
                    <div class="completion-actions">
                        <button class="btn-primary" onclick="VocabManager.restart()">
                            <i class="ph-duotone ph-arrow-clockwise"></i> 再来一轮
                        </button>
                        <button class="btn-secondary" onclick="App.showScreen('start-screen')">
                            <i class="ph-duotone ph-house"></i> 返回主页
                        </button>
                    </div>
                </div>
            `;
        }
        
        // 显示庆祝动画
        UIEffects.showConfetti();
    },
    
    /**
     * 重新开始
     */
    async restart() {
        this.currentIndex = 0;
        this.todayProgress = {
            total: 0,
            completed: 0,
            correct: 0
        };
        
        await this.loadDailyWords();
        this.showCurrentWord();
    },
    
    /**
     * 绑定事件
     */
    bindEvents() {
        // 添加导航按钮事件（如果需要）
    },
    
    /**
     * 获取单词本统计
     */
    async getStats() {
        try {
            const response = await fetch(`${this.API_BASE}/vocab/stats`);
            const stats = await response.json();
            return stats;
        } catch (error) {
            console.error('[VocabManager] 获取统计失败:', error);
            return null;
        }
    },
    
    /**
     * 搜索单词
     */
    async searchWord(keyword) {
        try {
            const response = await fetch(`${this.API_BASE}/vocab/search?keyword=${encodeURIComponent(keyword)}`);
            const data = await response.json();
            return data.words;
        } catch (error) {
            console.error('[VocabManager] 搜索失败:', error);
            return [];
        }
    }
};

// 导出到全局
window.VocabManager = VocabManager;
