/**
 * UI Effects - 界面效果模块
 * 负责看板娘、游戏化 HUD、动画效果、AI 工具提示等
 */

const UIEffects = {
    // 看板娘状态
    mascotState: 'normal', // normal | happy | sad | thinking

    // 看板娘台词
    dialogues: {
        welcome: [
            'Master，今天也要努力学习哦！',
            '欢迎回来！准备好刷题了吗？',
            '加油！我相信你可以的！'
        ],
        correct: [
            '太棒了！答对了！✨',
            'Master 真厉害！',
            '正确！继续保持！',
            '你真是太聪明了！'
        ],
        wrong: [
            '呜呜，答错了...',
            '没关系，下次一定能答对！',
            '别灰心，我们再想想~',
            '这道题有点难呢...'
        ],
        thinking: [
            '让我想想...',
            '这道题很有意思呢~',
            'Master 在认真思考呢！'
        ],
        gameOver: [
            '胜败乃兵家常事，大侠请重新来过！',
            'HP 归零了！休息一下吧~',
            '不要气馁，重新开始！'
        ],
        levelUp: [
            '恭喜升级！🎉',
            'Master 变强了！',
            '太厉害了，升级啦！'
        ],
        idle: [
            '要选哪个选项呢~',
            '认真读题哦！',
            '加油加油！'
        ]
    },

    // 当前气泡计时器
    bubbleTimer: null,

    /**
     * 初始化 UI 效果
     */
    init() {
        this.initHUD();
        this.initTextSelection();
        this.initTooltip();
        this.initSettingsEvents();
        console.log('[UIEffects] 初始化完成');
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
    },

    /**
     * 保存设置
     */
    async saveSettings() {
        // 保存 API Key
        const apiKeyInput = document.getElementById('apiKeyInput');
        if (apiKeyInput?.value) {
            const result = await GeminiService.validateApiKey(apiKeyInput.value);
            if (result.valid) {
                this.showToast('API Key 保存成功！', 'success');
            } else {
                this.showToast(result.message, 'error');
                return;
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

        // 保存其他设置
        const themeSelect = document.getElementById('themeSelect');
        const mascotToggle = document.getElementById('mascotToggle');

        StorageManager.updateSettings({
            theme: themeSelect?.value || 'acg',
            showMascot: mascotToggle?.checked !== false
        });

        // 应用主题
        this.applyTheme(themeSelect?.value || 'acg');

        this.showToast('设置已保存！', 'success');
        this.closeSettings();
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
