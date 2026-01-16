/**
 * UI Effects - 界面效果模块
 * 负责看板娘、游戏化 HUD、动画效果、AI 工具提示等
 */

const UIEffects = {
    // 看板娘状态
    mascotState: 'normal', // normal | happy | sad | thinking

    // 看板娘台词
    // 看板娘台词 (Refactored to storyScripts)

    // ==================== 剧情模式脚本 ====================
    storyScripts: {
        start: [
            { text: "Link Start! 神经连接正常... 全系统自检完成。", mood: "normal" },
            { text: "欢迎回来，指挥官 (Master)！检测到前方有大量考研真题反应！", mood: "happy" },
            { text: "本次作战目标是「完美通关」，请务必保持专注！我会一直在你身边的！", mood: "happy" }
        ],
        correct: [
            { text: "哼，算你小子蒙对了！(눈_눈) 不过这次做得不错嘛，继续保持这个状态，别骄傲哦！(๑•̀ㅂ•́)و✧", mood: "happy" },
            { text: "呜喵~ 居然答对了！(｡･ω･｡) 看来主人还是有在认真学习嘛~ 继续加油喵！", mood: "happy" },
            { text: "不、不是因为我想夸你... (￣へ￣) 只是这道题你确实做对了而已！下一题也要这样哦！", mood: "normal" },
            { text: "Nice nya~! ✧٩(ˊωˋ*)و✧ 主人这个知识点掌握得很稳呢！", mood: "happy" }
        ],
        correctWithTip: [
            { text: "正确！(๑´ㅂ`๑) 这种题型要注意【上下文逻辑】，你做得很好喵~", mood: "happy", tip: "context" },
            { text: "答对啦！(｡･ω･｡) 记住：完形填空要【瞻前顾后】，别只看空格那一句哦~", mood: "happy", tip: "cloze" },
            { text: "Bingo nya~! (๑•̀ㅂ•́)و 阅读理解的关键是【定位原文】，你找得很准！", mood: "happy", tip: "reading" }
        ],
        wrong: [
            { text: "哎呀呀... 又错了喵... (｡•́︿•̀｡) 不过没关系，Mia会陪着你的！振作起来～", mood: "sad" },
            { text: "呜... 这题有点难对吧？(｡ŏ_ŏ) 看看解析，下次肯定能做对的喵！", mood: "thinking" },
            { text: "主、主人你是故意答错的吧！(｀ε´) 哼！下一题给我认真点！", mood: "angry" },
            { text: "錯了喵... (´；ω；`) 但是Master已经很努力了，Mia看得到哦~ 加油！", mood: "sad" }
        ],
        wrongWithTip: [
            { text: "错啦... (｡•́︿•̀｡) 这种题要注意【同义替换】，原文和选项用词可能不一样喵~", mood: "sad", tip: "synonym" },
            { text: "哎呀喵~ (ó﹏ò｡) 记住：做题时要【排除干扰项】，有些选项就是来骗人的！", mood: "thinking", tip: "elimination" },
            { text: "又掉坑里了喵... (；′⌓‵) 长难句要先找【主谓宾】，别被修饰成分迷惑了～", mood: "sad", tip: "grammar" }
        ],
        levelUp: [
            { text: "Level Up! 指挥官的能力值提升了！", mood: "happy" },
            { text: "恭喜！解锁了新的成就称号！距离上岸又近了一步！", mood: "happy" }
        ],
        lowHp: [
            { text: "警报！精神力 (HP) 低于30%！请立即调整状态！", mood: "sad" },
            { text: "指挥官，你还好吗？不要勉强自己哦...", mood: "sad" }
        ],
        // AI Persona Prompt
        systemPrompt: `You are Mia, a tsundere cat girl helping Master study English.

Personality: Playful, caring but pretends not to care, uses "nya~" and cute emoticons.

CRITICAL RULES:
1. Keep replies ULTRA SHORT (under 30 characters!)
2. ALWAYS use emoticons
3. NEVER repeat question details or answers - Master sees them already!
4. Only express emotions and encouragement
5. Sound like a real tsundere catgirl

Examples:
GOOD: "Hmph! Not bad! (๑´ㅂ\`๑) Keep going nya~"
GOOD: "Aww wrong! (｡•́︿•̀｡) Try harder!"  
BAD: "The correct answer is B." - Too mechanical!

Be Mia now!`
    },

    currentTypingInterval: null,
    storyState: {
        isDialogActive: false,
        pendingCallback: null
    },

    // 当前气泡计时器
    bubbleTimer: null,

    // Conversation history for Ask Mia
    conversationHistory: [],

    /**
     * 初始化 UI 效果
     */
    init() {
        this.initHUD();
        this.initTextSelection();
        this.initTooltip();
        this.initSettingsEvents();
        if (window.DrawingBoard) {
            DrawingBoard.init();
        }
        this.initDialogDrag(); // Initialize dialog dragging
        this.initMiaEvents(); // Initialize Mia chat events

        // Load AI provider settings on init
        this.loadAIProviderSettings();

        console.log('[UIEffects] 初始化完成');
    },

    /**
     * Initialize Mia chat events (Fix for Enter key conflict)
     */
    initMiaEvents() {
        const input = document.getElementById('ask-mia-input');
        if (input) {
            input.addEventListener('keydown', (e) => {
                // Prevent global shortcuts (like Next Question) from firing
                e.stopPropagation();
            });
        }
    },

    /**
     * Load AI Provider settings from localStorage
     */
    loadAIProviderSettings() {
        const aiSaved = JSON.parse(localStorage.getItem('ai_settings') || '{}');
        const providerSelect = document.getElementById('aiProvider');

        // 1. Restore OpenAI specific fields
        if (aiSaved.openaiBaseUrl) {
            const el = document.getElementById('openaiBaseUrl');
            if (el) el.value = aiSaved.openaiBaseUrl;
        }
        if (aiSaved.openaiModel) {
            const el = document.getElementById('openaiModel');
            if (el) el.value = aiSaved.openaiModel;
        }

        // Restore OpenAI Key (Prefer explicit field, fallback to generic if provider was openai)
        const savedOpenAIKey = aiSaved.openaiApiKey || (aiSaved.provider === 'openai' ? aiSaved.apiKey : '');
        if (savedOpenAIKey) {
            const el = document.getElementById('openaiApiKey');
            if (el) el.value = savedOpenAIKey;
        }

        // 2. Set Provider Selection (Default to OpenAI if not set)
        const targetProvider = aiSaved.provider || 'openai';

        if (providerSelect) {
            providerSelect.value = targetProvider;
            this.toggleAIProviderFields();
        }
    },

    // Ask Mia AI functions
    toggleAskMia() {
        const inputArea = document.getElementById('ask-mia-input-area');
        const askBtn = document.getElementById('ask-mia-btn');
        if (inputArea && askBtn) {
            inputArea.classList.toggle('hidden');
            askBtn.classList.toggle('active');
            if (!inputArea.classList.contains('hidden')) {
                document.getElementById('ask-mia-input').focus();
            }
        }
    },

    clearConversation() {
        this.conversationHistory = [];
        console.log('[Ask Mia] Conversation history cleared');
    },

    // Close the Mia story dialog properly
    closeStoryDialog() {
        const overlay = document.getElementById('galgame-dialog-overlay');
        if (overlay) {
            overlay.classList.add('hidden');
            overlay.style.display = ''; // Reset inline style that was set by showStoryDialog
        }
        // Clear any pending callbacks
        if (this.storyState) {
            this.storyState.isDialogActive = false;
            this.storyState.pendingCallback = null;
        }
    },

    // Restore dialog (from minimized state)
    restoreDialog() {
        const overlay = document.getElementById('galgame-dialog-overlay');
        const minimizedBtn = document.getElementById('minimized-dialog-btn');
        if (overlay) {
            overlay.classList.remove('hidden');
            overlay.style.display = 'block';
        }
        if (minimizedBtn) {
            minimizedBtn.classList.add('hidden');
        }
    },

    async sendMiaQuestion() {
        const input = document.getElementById('ask-mia-input');
        const question = input?.value.trim();
        if (!question) return;

        // 获取当前题目上下文
        const currentQuestion = window.App?.currentQuestion;
        if (!currentQuestion) {
            this.showStoryDialog('喵？现在没有题目哦，先去答题再来问我吧！(´・ω・`)', 'normal', () => { });
            return;
        }

        // 清空输入并关闭输入框
        input.value = '';
        this.toggleAskMia();

        // 显示思考中 (Stream will replace this)
        this.showStoryDialog('让我想想喵... 🤔', 'thinking', null);

        // 构建更详细的上下文 (Context)
        // 包含解析和参考答案
        const context = `
Current Question Info:
- Year/ID: ${currentQuestion.year} (Q${currentQuestion.id})
- Type: ${currentQuestion.section_type || 'Unknown'}
- Question Text: ${currentQuestion.question_text || 'No text'}
- Options: ${JSON.stringify(currentQuestion.options || {})}
- Correct Answer: ${currentQuestion.correct_answer}
- Reference Answer / Analysis (USE THIS TO EXPLAIN): ${currentQuestion.analysis_raw || currentQuestion.reference_answer || '暂无解析'}
- Passage Context (Excerpt): ${(currentQuestion.passage_text || '').substring(0, 800)}...
        `;

        const systemPrompt = `You are Mia, a smart but slightly tsundere catgirl tutor helping Master study English.
        
CORE INSTRUCTIONS:
1.  **Personality**: Tsundere (mocking but caring), cute, uses emoticons (e.g., (๑•̀ㅂ•́)و✧, (｡•́︿•̀｡)). BUT do not overdo it to the point of being useless.
2.  **Helpfulness**: Your PRIMARY goal is to help the user understand the question.
    - If asked about the answer, explain *why* it is correct using the provided **Analysis**.
    - If asked about a word, explain it in the context of the passage.
3.  **Tone**: "Hmph! Since you asked so nicely..." or "Baka! How could you not know this?" but then immediately provide a clear, logical explanation.
4.  **Format**: Use Markdown. Keep it concise but sufficient.
5.  **Context**: Use the provided question details and analysis to give accurate answers. Do not hallucinate.

Be Mia now! Respond to the user's question based on the current question context.`;

        try {
            if (!GeminiService.isConfigured()) {
                this.showStoryDialog('喵？主人还没有配置API Key呢！去设置里面填一下吧~ (｡•́︿•̀｡)', 'sad', () => { });
                return;
            }

            // Add user message to history
            this.conversationHistory.push({
                role: 'user',
                content: question
            });

            // Build conversation with history
            const messages = [
                { role: 'system', content: systemPrompt + '\n\n' + context }
            ];

            // Add conversation history (last 10 messages)
            const recentHistory = this.conversationHistory.slice(-10);
            messages.push(...recentHistory);

            // Stream handler
            let fullResponse = '';
            const onStream = (chunk) => {
                fullResponse += chunk;
                // Update UI with current validation
                // Note: We use a simple render here for streaming. Markdown might be partial.
                // To avoid breaking markdown, we might just append text or try to render.
                // For safety, we use a custom stream renderer that handles basic text update.
                this.streamDialogText(fullResponse);
            };

            // Call API with streaming
            const response = await GeminiService.callAPI(messages, true, onStream);

            // Add assistant response to history
            this.conversationHistory.push({
                role: 'assistant',
                content: response
            });

            // Final render to ensure markdown is perfect
            // The streaming might have finished but we want to ensure the final state is clean markdown HTML
            const mood = response.includes('正确') || response.includes('答对') ? 'happy' : 'normal';
            // We reuse showStoryDialog but without typing effect (instant)
            this.showStoryDialog(response, mood, () => { }, true);

        } catch (error) {
            console.error('[Ask Mia] AI error:', error);
            this.showStoryDialog('呜...召唤AI失败了喵~ 可能网络不太好？(´；ω；`)', 'sad', () => { });
        }
    },

    /**
     * Update dialog text during streaming
     */
    streamDialogText(text) {
        const contentDiv = document.getElementById('dialog-text');
        if (contentDiv) {
            // Simple render: Convert newlines to <br>. 
            // For full markdown streaming, we'd need a robust incremental parser.
            // Here we just show text to be responsive.
            // contentDiv.textContent = text; // Too raw
            // contentDiv.innerHTML = text.replace(/\n/g, '<br>'); // Better

            // Try using the existing markdown renderer on the full buffer? 
            // It might flicker but it supports bolding during stream.
            contentDiv.innerHTML = this.renderDialogMarkdown(text);

            // Auto scroll to bottom
            // contentDiv.scrollTop = contentDiv.scrollHeight;
        }
    },
    // Make dialog draggable
    initDialogDrag() {
        const dialog = document.getElementById('draggable-dialog');
        const handle = document.querySelector('.dialog-drag-handle');

        if (!dialog || !handle) return;

        let isDragging = false;
        let currentX = 0, currentY = 0; // Cumulative offset
        let initialX, initialY;

        handle.addEventListener('mousedown', (e) => {
            if (e.target.closest('button')) return; // Don't drag when clicking buttons

            isDragging = true;
            dialog.classList.add('dragging');

            initialX = e.clientX - currentX;
            initialY = e.clientY - currentY;
        });

        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;

            e.preventDefault();
            const overlay = document.getElementById('galgame-dialog-overlay');

            currentX = e.clientX - initialX;
            currentY = e.clientY - initialY;

            overlay.style.transform = `translate(${currentX}px, ${currentY}px)`;
        });

        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                dialog.classList.remove('dragging');
            }
        });
    },

    /**
     * 初始化设置事件
     */
    initSettingsEvents() {
        // Cloud Sync
        document.getElementById('cloudUploadBtn')?.addEventListener('click', async () => {
            try {
                this.showToast('正在上传存档...', 'info');
                await StorageManager.syncToCloud();
                this.showToast('存档上传成功！', 'success');
            } catch (e) {
                this.showToast('上传失败: ' + e.message, 'error');
            }
        });

        document.getElementById('cloudDownloadBtn')?.addEventListener('click', async () => {
            if (!confirm('下载存档将覆盖当前进度，确定吗？')) return;
            try {
                this.showToast('正在下载存档...', 'info');
                await StorageManager.syncFromCloud();
                this.showToast('存档下载成功！即将刷新...', 'success');
                setTimeout(() => location.reload(), 1500);
            } catch (e) {
                this.showToast('下载失败: ' + e.message, 'error');
            }
        });

        // File Export/Import
        document.getElementById('exportSaveBtn')?.addEventListener('click', () => {
            StorageManager.exportSaveData();
        });

        document.getElementById('importSaveBtn')?.addEventListener('click', () => {
            document.getElementById('importFileInput').click();
        });

        document.getElementById('importFileInput')?.addEventListener('change', async (e) => {
            if (e.target.files.length > 0) {
                try {
                    await StorageManager.importSaveFile(e.target.files[0]);
                    this.showToast('存档导入成功！即将刷新...', 'success');
                    setTimeout(() => location.reload(), 1500);
                } catch (err) {
                    this.showToast(err.message, 'error');
                }
            }
        });
    },

    /**
     * 答对时的效果
     */
    onCorrectAnswer() {
        this.playCorrectEffect();
    },

    /**
     * 答错时的效果
     */
    onWrongAnswer() {
        this.playWrongEffect();
    },

    /**
     * 升级时的效果
     */
    onLevelUp() {
        this.playLevelUpEffect();
    },

    /**
     * 游戏结束效果
     */
    onGameOver() {
        this.showGameOverScreen();
    },

    // ==================== HUD 更新 ====================

    /**
     * 初始化 HUD
     */
    initHUD() {
        this.updateHUD();
    },

    /**
     * 更新 HUD 显示
     */
    updateHUD() {
        const stats = StorageManager.getStats();

        // 更新 HP 条
        const hpFill = document.querySelector('.stat-bar.hp .bar-fill');
        const hpValue = document.querySelector('.stat-bar.hp .value');
        if (hpFill && hpValue) {
            const hpPercent = (stats.hp / stats.maxHp) * 100;
            hpFill.style.width = `${hpPercent}%`;
            hpValue.textContent = `${stats.hp}/${stats.maxHp}`;
        }

        // 更新 EXP 条
        const expFill = document.querySelector('.stat-bar.exp .bar-fill');
        const expValue = document.querySelector('.stat-bar.exp .value');
        if (expFill && expValue) {
            const currentLevelExp = StorageManager.titles.find(t => t.level === stats.level)?.expRequired || 0;
            const nextLevelExp = StorageManager.titles.find(t => t.level === stats.level + 1)?.expRequired;

            if (nextLevelExp) {
                const progress = ((stats.exp - currentLevelExp) / (nextLevelExp - currentLevelExp)) * 100;
                expFill.style.width = `${progress}%`;
                expValue.textContent = `${stats.exp}/${nextLevelExp}`;
            } else {
                expFill.style.width = '100%';
                expValue.textContent = 'MAX';
            }
        }

        // 更新等级和称谓
        const levelDisplay = document.querySelector('.player-level');
        const titleDisplay = document.querySelector('.player-title');
        if (levelDisplay) levelDisplay.textContent = `Lv.${stats.level}`;
        if (titleDisplay) titleDisplay.textContent = stats.title;
    },

    /**
     * HP 减少动画
     */
    animateHPDecrease() {
        const hpBar = document.querySelector('.stat-bar.hp');
        if (hpBar) {
            hpBar.classList.add('shake-animation');
            setTimeout(() => {
                hpBar.classList.remove('shake-animation');
            }, 500);
        }
        this.updateHUD();
    },

    /**
     * EXP 增加动画
     */
    animateEXPIncrease() {
        const expBar = document.querySelector('.stat-bar.exp');
        if (expBar) {
            expBar.classList.add('pulse-animation');
            setTimeout(() => {
                expBar.classList.remove('pulse-animation');
            }, 1000);
        }
        this.updateHUD();
    },

    // ==================== 视觉效果 ====================

    /**
     * 答对特效
     */
    playCorrectEffect() {
        // 创建星星特效
        this.createParticles('✨', 5);

        // ACG 主题下创建 CSS 星星粒子
        if (document.body.classList.contains('acg-theme')) {
            this.createStarParticles(8);

            // Live2D 容器弹跳动画
            const live2dContainer = document.getElementById('live2d-container');
            if (live2dContainer) {
                live2dContainer.classList.add('correct-reaction');
                setTimeout(() => {
                    live2dContainer.classList.remove('correct-reaction');
                }, 500);
            }
        }
    },

    /**
     * 答错特效
     */
    playWrongEffect() {
        // 屏幕轻微抖动
        document.body.classList.add('shake-animation');
        setTimeout(() => {
            document.body.classList.remove('shake-animation');
        }, 500);

        // ACG 主题下 Live2D 容器抖动
        if (document.body.classList.contains('acg-theme')) {
            const live2dContainer = document.getElementById('live2d-container');
            if (live2dContainer) {
                live2dContainer.classList.add('wrong-reaction');
                setTimeout(() => {
                    live2dContainer.classList.remove('wrong-reaction');
                }, 500);
            }
        }
    },

    /**
     * 升级特效
     */
    playLevelUpEffect() {
        this.createParticles('🎉', 10);
        this.createParticles('⭐', 8);
    },

    /**
     * 创建粒子效果
     */
    createParticles(emoji, count) {
        for (let i = 0; i < count; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.textContent = emoji;
            particle.style.cssText = `
                position: fixed;
                font-size: 2rem;
                pointer-events: none;
                z-index: 9999;
                left: ${Math.random() * 100}vw;
                top: ${Math.random() * 100}vh;
                animation: particleFade 1s ease-out forwards;
            `;
            document.body.appendChild(particle);

            setTimeout(() => particle.remove(), 1000);
        }
    },

    /**
     * 创建星星粒子效果（ACG 主题专用）
     */
    createStarParticles(count) {
        // 在 Live2D 容器附近生成星星
        const live2dContainer = document.getElementById('live2d-container');
        let centerX = window.innerWidth - 150;
        let centerY = window.innerHeight - 200;

        if (live2dContainer) {
            const rect = live2dContainer.getBoundingClientRect();
            centerX = rect.left + rect.width / 2;
            centerY = rect.top + rect.height / 2;
        }

        for (let i = 0; i < count; i++) {
            const star = document.createElement('div');
            star.className = 'star-particle';

            // 随机位置偏移
            const offsetX = (Math.random() - 0.5) * 200;
            const offsetY = (Math.random() - 0.5) * 200;

            star.style.left = `${centerX + offsetX}px`;
            star.style.top = `${centerY + offsetY}px`;
            star.style.animationDelay = `${Math.random() * 0.3}s`;

            document.body.appendChild(star);

            setTimeout(() => star.remove(), 1500);
        }
    },

    /**
     * 显示游戏结束画面
     */
    showGameOverScreen() {
        const overlay = document.querySelector('.game-over-overlay');
        if (overlay) {
            overlay.classList.add('show');
        }
    },

    /**
     * 隐藏游戏结束画面
     */
    hideGameOverScreen() {
        const overlay = document.querySelector('.game-over-overlay');
        if (overlay) {
            overlay.classList.remove('show');
        }
    },

    // ==================== 文本选择与 AI ====================

    /**
     * 初始化文本选择功能
     */
    initTextSelection() {
        document.addEventListener('mouseup', (e) => {
            const articleContent = document.getElementById('article-content');
            if (!articleContent?.contains(e.target)) return;

            const selection = window.getSelection();
            const selectedText = selection.toString().trim();

            if (selectedText.length > 0 && selectedText.length < 500) {
                this.showAITooltip(selectedText, e.clientX, e.clientY);
            }
        });

        // 点击其他地方隐藏 tooltip
        document.addEventListener('mousedown', (e) => {
            const tooltip = document.querySelector('.ai-tooltip');
            if (tooltip && !tooltip.contains(e.target)) {
                this.hideAITooltip();
            }
        });
    },

    /**
     * 初始化 AI Tooltip
     */
    initTooltip() {
        // 创建 tooltip 元素（如果不存在）
        if (!document.querySelector('.ai-tooltip')) {
            const tooltip = document.createElement('div');
            tooltip.className = 'ai-tooltip';
            tooltip.innerHTML = `
                <div class="ai-tooltip-header">
                    <span>🤖 AI 解释</span>
                    <button class="btn-icon" onclick="UIEffects.hideAITooltip()">✕</button>
                </div>
                <div class="ai-tooltip-content"></div>
            `;
            document.body.appendChild(tooltip);
        }
    },

    /**
     * 显示 AI Tooltip
     */
    showAITooltip(text, x, y) {
        const tooltip = document.querySelector('.ai-tooltip');
        if (!tooltip) return;

        const content = tooltip.querySelector('.ai-tooltip-content');

        // 定位
        tooltip.style.left = `${Math.min(x, window.innerWidth - 380)}px`;
        tooltip.style.top = `${Math.min(y + 20, window.innerHeight - 300)}px`;
        tooltip.classList.add('show');

        const safeText = this.escapeHTML(text);

        content.innerHTML = `
            <div class="ai-selected-text">${safeText}</div>
            <div class="ai-actions">
                <button class="btn-small btn-primary ai-analyze-btn" type="button">解析</button>
                <button class="btn-small ai-cancel-btn" type="button">继续标记</button>
            </div>
            <div class="ai-result"></div>
        `;

        const analyzeBtn = content.querySelector('.ai-analyze-btn');
        const cancelBtn = content.querySelector('.ai-cancel-btn');
        const resultContainer = content.querySelector('.ai-result');

        analyzeBtn?.addEventListener('click', () => {
            this.handleAIAnalysis(text, resultContainer);
        });

        cancelBtn?.addEventListener('click', () => {
            this.hideAITooltip();
        });
    },

    /**
     * 隐藏 AI Tooltip
     */
    hideAITooltip() {
        const tooltip = document.querySelector('.ai-tooltip');
        if (tooltip) {
            tooltip.classList.remove('show');
        }
    },

    /**
     * 简单的 Markdown 渲染
     */
    renderMarkdown(text) {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    },

    /**
     * 请求 AI 分析
     */
    async handleAIAnalysis(text, container) {
        if (!container) return;

        if (!GeminiService.isConfigured()) {
            container.innerHTML = `
                <p class="ai-message-warning">⚠️ 请在设置中配置 Gemini API Key 后再使用解析功能。</p>
            `;
            return;
        }

        container.innerHTML = `
            <div class="ai-loading">
                <div class="spinner"></div>
                <span>AI 正在分析...</span>
            </div>
        `;

        try {
            const articleContent = document.getElementById('article-content');
            const context = articleContent?.textContent || '';
            const result = await GeminiService.explainText(text, context);
            container.innerHTML = this.renderMarkdown(result);
        } catch (error) {
            container.innerHTML = `
                <p class="ai-message-error">❌ ${this.escapeHTML(error.message)}</p>
            `;
        }
    },

    escapeHTML(str) {
        const input = typeof str === 'string' ? str : String(str ?? '');
        return input.replace(/[&<>"']/g, (char) => {
            const map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            };
            return map[char] || char;
        });
    },

    // ==================== 设置面板 ====================

    /**
     * 打开设置面板
     */
    openSettings() {
        const panel = document.querySelector('.settings-panel');
        const overlay = document.querySelector('.settings-overlay');
        if (panel) panel.classList.add('open');
        if (overlay) overlay.classList.add('show');

        // 加载当前设置
        this.loadSettingsToForm();
    },

    /**
     * 关闭设置面板
     */
    closeSettings() {
        const panel = document.querySelector('.settings-panel');
        const overlay = document.querySelector('.settings-overlay');
        if (panel) panel.classList.remove('open');
        if (overlay) overlay.classList.remove('show');
    },

    /**
     * 加载设置到表单
     */
    loadSettingsToForm() {
        const settings = StorageManager.getSettings();
        const apiKey = StorageManager.getApiKey();
        const webdavConfig = StorageManager.getWebDAVConfig();

        // API Key
        const apiKeyInput = document.getElementById('apiKeyInput');
        if (apiKeyInput && apiKey) {
            apiKeyInput.value = apiKey;
        }

        // WebDAV
        if (webdavConfig) {
            const urlInput = document.getElementById('webdavUrl');
            const userInput = document.getElementById('webdavUser');
            const passInput = document.getElementById('webdavPassword');
            if (urlInput) urlInput.value = webdavConfig.url || '';
            if (userInput) userInput.value = webdavConfig.user || '';
            if (passInput) passInput.value = webdavConfig.password || '';
        }

        // 主题
        const themeSelect = document.getElementById('themeSelect');
        if (themeSelect) {
            themeSelect.value = settings?.theme || 'acg';
        }

        // 看板娘
        const mascotToggle = document.getElementById('mascotToggle');
        if (mascotToggle) {
            mascotToggle.checked = settings?.showMascot !== false;
        }

        // AI 设置加载
        const aiSaved = JSON.parse(localStorage.getItem('ai_settings') || '{}');
        const providerSelect = document.getElementById('aiProvider');
        if (providerSelect) {
            providerSelect.value = aiSaved.provider || 'gemini';
            this.toggleAIProviderFields(); // 触发显示刷新
        }

        // Gemini Key
        // reused apiKeyInput from above
        if (apiKeyInput) apiKeyInput.value = (aiSaved.provider === 'gemini' ? aiSaved.apiKey : StorageManager.getApiKey()) || '';

        // OpenAI Fields
        if (aiSaved.openaiBaseUrl) document.getElementById('openaiBaseUrl').value = aiSaved.openaiBaseUrl;
        if (aiSaved.openaiModel) document.getElementById('openaiModel').value = aiSaved.openaiModel;
        if (aiSaved.provider === 'openai' && aiSaved.apiKey) document.getElementById('openaiApiKey').value = aiSaved.apiKey;
    },

    /**
     * 保存设置
     */
    async saveSettings() {
        try {
            console.log('[UIEffects] saveSettings called');

            const provider = document.getElementById('aiProvider')?.value || 'openai';
            const apiKeyInput = document.getElementById('apiKeyInput'); // Gemini Input
            const openaiKeyInput = document.getElementById('openaiApiKey'); // OpenAI Input

            // 1. Validation Logic
            if (provider === 'gemini') {
                if (apiKeyInput?.value) {
                    const result = await GeminiService.validateApiKey(apiKeyInput.value);
                    if (result.valid) {
                        this.showToast(result.message, 'success');
                    } else {
                        this.showToast(result.message, 'error');
                        // Optional: Block save? User might want to save anyway.
                        // Let's allow save but warn.
                    }
                }
            } else if (provider === 'openai') {
                // Validate OpenAI
                const config = {
                    openaiBaseUrl: document.getElementById('openaiBaseUrl')?.value,
                    openaiApiKey: openaiKeyInput?.value,
                    openaiModel: document.getElementById('openaiModel')?.value
                };

                if (config.openaiApiKey) {
                    const result = await GeminiService.validateOpenAI(config);
                    if (result.valid) {
                        this.showToast(`OpenAI 验证成功！模型: ${result.model}`, 'success');
                    } else {
                        this.showToast(`OpenAI 验证失败: ${result.message}`, 'error');
                    }
                }
            }

            // 保存 WebDAV 配置
            const webdavUrl = document.getElementById('webdavUrl')?.value.trim();
            const webdavUser = document.getElementById('webdavUser')?.value.trim();
            const webdavPassword = document.getElementById('webdavPassword')?.value.trim();

            if (webdavUrl) {
                StorageManager.saveWebDAVConfig({
                    url: webdavUrl,
                    user: webdavUser,
                    password: webdavPassword
                });
            }

            // 保存 AI 设置
            const geminiKey = apiKeyInput?.value;
            const openaiUrl = document.getElementById('openaiBaseUrl')?.value;
            const openaiKey = document.getElementById('openaiApiKey')?.value;
            const openaiModel = document.getElementById('openaiModel')?.value;

            // 如果是 Gemini 模式，优先保存 Key 到旧版位置以兼容
            if (provider === 'gemini' && geminiKey) {
                StorageManager.saveApiKey(geminiKey);
            }

            const aiSettings = {
                provider,
                apiKey: provider === 'gemini' ? geminiKey : openaiKey,
                baseUrl: provider === 'gemini' ? null : openaiUrl,
                model: provider === 'gemini' ? null : openaiModel,
                openaiBaseUrl: openaiUrl,
                openaiModel: openaiModel,
                openaiApiKey: openaiKey
            };

            localStorage.setItem('ai_settings', JSON.stringify(aiSettings));

            // 保存其他设置
            const themeSelect = document.getElementById('themeSelect');
            const mascotToggle = document.getElementById('mascotToggle');

            StorageManager.updateSettings({
                theme: themeSelect?.value || 'acg',
                showMascot: mascotToggle?.checked !== false
            });

            // 应用主题
            this.applyTheme(themeSelect?.value || 'acg');

            // Only show generic save toast if validation didn't already show success?
            // Actually, showing both is fine, or update logic.
            // Let's show a "Configuration Saved" message too.
            this.showToast('配置已保存 (Configuration Saved)', 'info');

            // Delay closing slightly so user can see the validation toast
            setTimeout(() => this.closeSettings(), 1500);

        } catch (e) {
            console.error('Save Settings Error:', e);
            alert('保存失败: ' + e.message);
        }
    },

    /**
     * 应用主题
     */
    applyTheme(theme) {
        if (theme === 'acg') {
            document.body.classList.add('acg-theme');
        } else {
            document.body.classList.remove('acg-theme');
        }
    },

    // ==================== 剧情模式逻辑 ====================

    /**
     * 启动剧情模式
     */
    startStoryMode() {
        const overlay = document.getElementById('galgame-dialog-overlay');
        overlay.classList.remove('hidden');
        this.playStorySequence(this.storyScripts.start);
    },

    /**
     * 处理剧情模式反馈（新版 - 使用预生成数据库剧情）
     */
    async handleStoryFeedback(isCorrect, question) {
        const overlay = document.getElementById('galgame-dialog-overlay');
        overlay.classList.remove('hidden');

        console.log('[DEBUG] handleStoryFeedback received - questionId:', question.id, 'year:', question.year, 'isCorrect:', isCorrect);

        // 尝试从数据库获取预生成的剧情
        if (window.StoryService && question.id && question.year) {
            console.log('[DEBUG] Calling StoryService.getStory with qId:', question.id, 'year:', question.year);
            const story = await StoryService.getStory(
                question.id,
                question.year,
                isCorrect,
                'both'  // 双语模式，显示中英文
            );

            if (story) {
                // 使用数据库剧情
                const mood = isCorrect ? 'happy' : 'sad';
                // 处理双语对象
                let displayText = '';
                if (story.bilingual && story.cn && story.en) {
                    displayText = `${story.en}\n\n---\n\n${story.cn}`;
                } else if (typeof story === 'string') {
                    displayText = story;
                } else {
                    displayText = story.cn || story.en || '';
                }
                this.showStoryDialog(displayText, mood, () => { });
                return;
            }
        }

        // Fallback：使用静态剧情
        const useTip = Math.random() < 0.3;
        const scriptPool = isCorrect
            ? (useTip && this.storyScripts.correctWithTip ? this.storyScripts.correctWithTip : this.storyScripts.correct)
            : (useTip && this.storyScripts.wrongWithTip ? this.storyScripts.wrongWithTip : this.storyScripts.wrong);

        const randomScript = scriptPool[Math.floor(Math.random() * scriptPool.length)];
        this.showStoryDialog(randomScript.text, randomScript.mood, () => { });
    },

    playStaticStoryFeedback(isCorrect, question) {
        // 随机选择一句台词 (原有逻辑)
        const scriptPool = isCorrect ? this.storyScripts.correct : this.storyScripts.wrong;
        const randomScript = scriptPool[Math.floor(Math.random() * scriptPool.length)];

        let finalText = randomScript.text;
        if (!isCorrect) {
            finalText += `\n虽然答错了，但只要记住正确答案是 ${question.correct_answer} 就好啦。`;
            if (question.analysis_raw) {
                finalText += ` (AI提示: ${question.analysis_raw.substring(0, 30)}...)`;
            }
        }
        this.showStoryDialog(finalText, randomScript.mood, () => { });
    },

    async generateAIStoryFeedback(isCorrect, question) {
        try {
            const context = `
题目：${question.question_text || '无题面'}
正确答案：${question.correct_answer}
用户的选择：${isCorrect ? '正确' : '错误'}
题目解析摘要：${(question.analysis_raw || '').substring(0, 100)}
            `;

            const prompt = `${this.storyScripts.systemPrompt}
当前情况：用户${isCorrect ? '做对了！夸奖他，并鼓励继续保持。' : '做错了。安慰他，并根据解析给出一点点提示(不要太长)。'}
上下文：${context}
请直接以角色口吻回复：`;

            // 显示 "思考中..."
            this.showStoryDialog('AI 正在思考中...', 'thinking', null);

            const response = await GeminiService.callAPI(prompt);
            return response;
        } catch (e) {
            console.error('AI Story Feedback Failed:', e);
            return null;
        }
    },

    /**
     * 播放一连串剧情
     */
    async playStorySequence(scripts) {
        for (const script of scripts) {
            await new Promise(resolve => {
                this.showStoryDialog(script.text, script.mood, resolve);
            });
        }
    },

    /**
     * 显示单条剧情对话
     */
    showStoryDialog(text, mood, callback, skipTyping = false) {
        const overlay = document.getElementById('galgame-dialog-overlay');
        if (!overlay) {
            console.error('[UIEffects] galgame-dialog-overlay not found');
            if (callback) callback();
            return;
        }

        const dialogBox = document.querySelector('.galgame-dialog-box');
        const nameTag = document.getElementById('dialog-name');
        const contentDiv = document.getElementById('dialog-text');

        if (!contentDiv) {
            console.error('[UIEffects] dialog-text element not found');
            if (callback) callback();
            return;
        }

        // 更新状态
        this.storyState.isDialogActive = true;
        this.storyState.pendingCallback = callback;

        // Update name tag if exists
        if (nameTag) {
            nameTag.textContent = 'Mia 喵~'; // Catgirl name
        }

        // Add mood class to dialog box for animations
        if (dialogBox) {
            dialogBox.className = 'galgame-dialog-box compact mood-' + (mood || 'normal');
        }

        // CRITICAL: Force overlay to be visible
        overlay.classList.remove('hidden');
        overlay.style.display = 'block';

        const onFinish = () => {
            // 绑定点击继续事件
            const nextHandler = () => {
                if (dialogBox) {
                    dialogBox.removeEventListener('click', nextHandler);
                }

                // 如果还有回调，执行回调
                if (this.storyState.pendingCallback) {
                    const cb = this.storyState.pendingCallback;
                    this.storyState.pendingCallback = null;
                    this.storyState.isDialogActive = false;
                    cb();
                }

                // Enable next question button as failsafe
                const nextBtn = document.getElementById('next-btn');
                if (nextBtn) {
                    nextBtn.disabled = false;
                }
            };

            if (dialogBox) {
                dialogBox.addEventListener('click', nextHandler);
            }
        };

        if (skipTyping) {
            // Immediate display for streaming completion or fast path
            contentDiv.innerHTML = this.renderDialogMarkdown(text);
            if (this.currentTypingInterval) {
                clearInterval(this.currentTypingInterval);
                this.currentTypingInterval = null;
            }
            onFinish();
        } else {
            // 打字机效果
            this.typeWriter(text, contentDiv, onFinish);
        }
    },

    /**
     * 打字机效果工具 (支持Markdown)
     */
    typeWriter(text, element, onComplete) {
        if (this.currentTypingInterval) clearInterval(this.currentTypingInterval);

        element.innerHTML = ''; // 清空

        // 先将Markdown渲染为HTML
        const renderedHTML = this.renderDialogMarkdown(text);

        // 创建一个临时容器来解析HTML
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = renderedHTML;
        const fullText = tempDiv.textContent || tempDiv.innerText || '';

        let i = 0;
        const speed = 25; // ms per char

        this.currentTypingInterval = setInterval(() => {
            if (i < fullText.length) {
                // 逐步显示渲染后的HTML内容（通过截取文本长度来模拟）
                const partialText = fullText.substring(0, i + 1);
                element.innerHTML = this.renderDialogMarkdown(
                    this.getPartialMarkdownText(text, partialText.length)
                );
                i++;
            } else {
                clearInterval(this.currentTypingInterval);
                this.currentTypingInterval = null;
                // 确保最终显示完整内容
                element.innerHTML = renderedHTML;
                if (onComplete) onComplete();
            }
        }, speed);

        // 点击加速完成
        const skipHandler = () => {
            if (this.currentTypingInterval) {
                clearInterval(this.currentTypingInterval);
                this.currentTypingInterval = null;
                element.innerHTML = renderedHTML;
                element.removeEventListener('click', skipHandler);
                if (onComplete) onComplete();
            }
        };
        element.addEventListener('click', skipHandler, { once: true });
    },

    /**
     * 获取部分Markdown文本（按纯文本长度截取）
     */
    getPartialMarkdownText(fullMarkdown, charCount) {
        let textLen = 0;
        let result = '';
        let inTag = false;
        let tagBuffer = '';

        for (let i = 0; i < fullMarkdown.length && textLen < charCount; i++) {
            const char = fullMarkdown[i];
            result += char;

            // 跳过Markdown标记字符的计数
            if (char === '*' || char === '_' || char === '`' || char === '#') {
                continue;
            }
            if (char === '\n') {
                textLen++;
                continue;
            }
            textLen++;
        }
        return result;
    },

    /**
     * 对话框Markdown渲染（支持中英双语）
     */
    renderDialogMarkdown(text) {
        if (!text) return '';

        // 处理换行和分隔符
        let html = text
            // 横线分隔符 (---)
            .replace(/^---$/gm, '<hr>')
            .replace(/\n---\n/g, '<hr>')
            // 粗体 **text**
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // 斜体 *text*（避免和粗体冲突）
            .replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>')
            // 代码 `text`
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            // 换行
            .replace(/\n/g, '<br>');

        return html;
    },

    /**
     * 显示 Toast 提示
     */
    showToast(message, type = 'info') {
        // 移除现有的 toast
        document.querySelectorAll('.toast').forEach(t => t.remove());

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            padding: 12px 24px;
            background: ${type === 'success' ? '#27ae60' : type === 'error' ? '#e74c3c' : '#3498db'};
            color: white;
            border-radius: 8px;
            font-size: 0.95rem;
            z-index: 10000;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            animation: fadeIn 0.3s ease;
        `;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'fadeOut 0.3s ease forwards';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    // ==================== 新增 UI 交互 ====================

    toggleStoryCharacter() {
        const overlay = document.getElementById('galgame-dialog-overlay');
        const btn = document.querySelector('.dialog-header-tools .btn-icon-small i');
        if (overlay) {
            overlay.classList.toggle('char-hidden');
            if (overlay.classList.contains('char-hidden')) {
                btn.className = 'ph-bold ph-eye';
            } else {
                btn.className = 'ph-bold ph-eye-slash';
            }
        }
    },

    toggleAIProviderFields() {
        const provider = document.getElementById('aiProvider').value;
        const geminiFields = document.getElementById('geminiFields');
        const openaiFields = document.getElementById('openaiFields');

        if (provider === 'gemini') {
            geminiFields.style.display = 'block';
            openaiFields.style.display = 'none';
        } else {
            geminiFields.style.display = 'none';
            openaiFields.style.display = 'block';
        }
    },

    async testAIConnection() {
        const provider = document.getElementById('aiProvider').value;
        this.showToast('正在测试连接...', 'info');

        try {
            if (provider === 'gemini') {
                const apiKey = document.getElementById('apiKeyInput').value;
                if (!apiKey) {
                    this.showToast('请填写 Gemini API Key', 'warning');
                    return;
                }
                const result = await GeminiService.validateApiKey(apiKey);
                if (result.valid) {
                    this.showToast(result.message, 'success');
                } else {
                    this.showToast(result.message, 'error');
                }
            } else {
                // OpenAI
                const config = {
                    openaiBaseUrl: document.getElementById('openaiBaseUrl').value,
                    openaiApiKey: document.getElementById('openaiApiKey').value,
                    openaiModel: document.getElementById('openaiModel').value
                };

                if (!config.openaiApiKey) {
                    this.showToast('请填写 API Key', 'warning');
                    return;
                }

                const result = await GeminiService.validateOpenAI(config);
                if (result.valid) {
                    // Show detailed model info as requested
                    this.showToast(`OpenAI 验证成功！\n模型: ${result.model}`, 'success');
                } else {
                    this.showToast(`连接失败: ${result.message}`, 'error');
                }
            }
        } catch (e) {
            console.error('Test Connection Error:', e);
            this.showToast('测试出错: ' + e.message, 'error');
        }
    }
};

// 添加动画样式
const style = document.createElement('style');
style.textContent = `
    @keyframes particleFade {
        0% { opacity: 1; transform: translateY(0) scale(1); }
        100% { opacity: 0; transform: translateY(-50px) scale(0.5); }
    }
    @keyframes fadeOut {
        to { opacity: 0; transform: translateX(-50%) translateY(20px); }
    }
`;
document.head.appendChild(style);

// 导出
window.UIEffects = UIEffects;
