/**
 * English Exam Web - 主应用逻辑
 * ACG & AI Enhanced Version
 */

// ==================== 全局状态 ====================
const App = {
    examData: null,
    allQuestions: [],
    currentQuestionIndex: 0,
    isReviewMode: false,
    examMode: 'exam', // 默认考试模式
    isSubmitted: false,
    currentYear: '2010', // Default year (for backward compatibility)
    selectedYears: ['2010'], // Multi-year selection
    availableYears: Array.from({ length: 16 }, (_, i) => (2010 + i).toString()), // 2010-2025
    pdfMappings: null, // PDF 页码映射

    // 计时器
    examTimer: null,
    examStartTime: null,
    examElapsedSeconds: 0,

    // DOM 元素缓存
    elements: {},

    /**
     * 初始化应用
     */
    async init() {
        console.log('[App] 初始化开始...');

        // 缓存 DOM 元素
        this.cacheElements();

        // 初始化年份选择器
        this.initYearSelector();

        // 初始化存储管理器
        StorageManager.init();

        // NEW: Auto-migrate localStorage to backend on first load
        const migrated = await StorageManager.migrateToBackend();
        if (migrated) {
            UIEffects.showToast('已将本地进度迁移到云端存档 #1', 'success');
        }

        // NEW: Try to load auto-save (slot 0)
        const autoSave = await StorageManager.loadFromBackend(0);
        if (autoSave && autoSave.currentQuestionIndex > 0) {
            console.log('[App] Auto-save found, progress restored');
        }

        // 初始化 UI 效果
        UIEffects.init();

        // 应用主题
        const settings = StorageManager.getSettings();
        UIEffects.applyTheme(settings?.theme || 'acg');

        // 加载 PDF 映射
        await this.loadPDFMappings();

        // 加载题目数据
        await this.loadExamData();

        // 绑定事件
        this.bindEvents();

        // 恢复进度
        this.restoreProgress();

        console.log('[App] 初始化完成');
    },

    /**
     * 缓存 DOM 元素
     */
    cacheElements() {
        this.elements = {
            startScreen: document.getElementById('start-screen'),
            examScreen: document.getElementById('exam-screen'),
            resultScreen: document.getElementById('result-screen'),
            vocabScreen: document.getElementById('vocab-screen'),
            startBtn: document.getElementById('start-btn'),
            continueBtn: document.getElementById('continue-btn'),
            vocabBtn: document.getElementById('vocab-btn'),
            prevBtn: document.getElementById('prev-btn'),
            nextBtn: document.getElementById('next-btn'),
            restartBtn: document.getElementById('restart-btn'),
            reviewBtn: document.getElementById('review-btn'),
            settingsBtn: document.getElementById('settings-btn'),
            articleContent: document.getElementById('article-content'),
            questionText: document.getElementById('question-text'),
            optionsDiv: document.getElementById('options'),
            feedback: document.getElementById('feedback'),
            sectionName: document.getElementById('section-name'),
            currentQ: document.getElementById('current-q'),
            totalQ: document.getElementById('total-q'),
            answeredCount: document.getElementById('answered-count'),
            totalQuestions: document.getElementById('total-questions'),
            yearSelect: document.getElementById('year-select'),
            yearDisplay: document.getElementById('selected-year-display')
        };
    },

    /**
     * 初始化年份选择器 (多选复选框版本)
     */
    initYearSelector() {
        const grid = document.getElementById('year-checkbox-grid');
        if (!grid) return;

        grid.innerHTML = '';
        this.availableYears.forEach(year => {
            const item = document.createElement('label');
            item.className = 'year-checkbox-item';
            item.innerHTML = `
                <input type="checkbox" value="${year}" 
                       ${this.selectedYears.includes(year) ? 'checked' : ''}>
                <span>${year}</span>
            `;
            item.querySelector('input').addEventListener('change', (e) => {
                this.toggleYear(year, e.target.checked);
            });
            grid.appendChild(item);
        });

        this.updateYearStats();
    },

    /**
     * 切换年份选择
     */
    toggleYear(year, isSelected) {
        if (isSelected && !this.selectedYears.includes(year)) {
            this.selectedYears.push(year);
        } else if (!isSelected) {
            this.selectedYears = this.selectedYears.filter(y => y !== year);
        }

        // Ensure at least one year is selected
        if (this.selectedYears.length === 0) {
            this.selectedYears = [year];
            // Re-check the checkbox
            const checkbox = document.querySelector(`.year-checkbox-item input[value="${year}"]`);
            if (checkbox) checkbox.checked = true;
            UIEffects.showToast('至少需要选择一个年份', 'warning');
            return;
        }

        this.selectedYears.sort();
        this.updateYearStats();
    },

    /**
     * 全选年份
     */
    selectAllYears() {
        this.selectedYears = [...this.availableYears];
        document.querySelectorAll('.year-checkbox-item input').forEach(cb => cb.checked = true);
        this.updateYearStats();
    },

    /**
     * 清空年份（保留第一个）
     */
    clearYears() {
        this.selectedYears = [this.availableYears[0]];
        document.querySelectorAll('.year-checkbox-item input').forEach((cb) => {
            cb.checked = cb.value === this.availableYears[0];
        });
        this.updateYearStats();
    },

    /**
     * 更新年份统计并重新加载数据
     */
    async updateYearStats() {
        // Update counts UI immediately for feedback
        const countSpan = document.getElementById('selected-year-count');
        if (countSpan) countSpan.textContent = this.selectedYears.length;

        // Reload data
        await this.loadExamData();
    },

    /**
     * 数组随机打乱 (Fisher-Yates)
     */
    shuffleArray(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
        return array;
    },

    /**
     * 加载题目数据
     */

    /**
     * 加载题目数据 (支持多年份)
     */
    async loadExamData() {
        try {
            console.log(`Loading data for years: ${this.selectedYears.join(', ')}`);
            this.allQuestions = [];
            const allSections = []; // Store complete sections for shuffle

            // Loop through all selected years
            for (const year of this.selectedYears) {
                try {
                    const response = await fetch(`data/${year}.json`);
                    if (!response.ok) {
                        console.warn(`Failed to load data for ${year}`);
                        continue;
                    }
                    const examData = await response.json();

                    // Collect sections as complete units
                    if (examData.sections) {
                        examData.sections.forEach((section) => {
                            const sectionQuestions = [];
                            if (section.questions) {
                                section.questions.forEach(q => {
                                    sectionQuestions.push({
                                        ...q,
                                        year: year,
                                        sectionName: section.section_info.name,
                                        sectionType: section.section_info.type,
                                        article: section.article?.paragraphs || []
                                    });
                                });
                            }
                            // Store complete section
                            allSections.push({
                                year: year,
                                sectionInfo: section.section_info,
                                questions: sectionQuestions
                            });
                        });
                    }
                } catch (e) {
                    console.error(`Error processing year ${year}:`, e);
                }
            }

            // Shuffle sections (not individual questions)
            const shuffleEnabled = document.getElementById('shuffle-toggle')?.checked;
            if (shuffleEnabled && this.selectedYears.length > 0) {
                this.shuffleArray(allSections);
            }

            // Flatten sections into questions array
            allSections.forEach(section => {
                this.allQuestions.push(...section.questions);
            });

            // 更新显示
            if (this.elements.totalQuestions) {
                this.elements.totalQuestions.textContent = this.allQuestions.length;
            }
            if (this.elements.totalQ) {
                this.elements.totalQ.textContent = this.allQuestions.length;
            }

            console.log(`[App] 加载了 ${this.allQuestions.length} 道题目 (来自 ${this.selectedYears.length} 个年份, ${allSections.length} 个sections)`);

            // Update currentYear for compatibility
            if (this.selectedYears.length > 0) {
                this.currentYear = this.selectedYears[0];
            }

        } catch (error) {
            console.error('[App] 加载数据失败:', error);
            UIEffects.showToast('加载题目数据失败', 'error');
        }
    },

    /**
     * 加载 PDF 映射数据
     */
    async loadPDFMappings() {
        try {
            const response = await fetch('data/pdf_mappings.json');
            if (response.ok) {
                this.pdfMappings = await response.json();
                console.log('[App] PDF 映射加载成功');
            }
        } catch (error) {
            console.warn('[App] PDF 映射加载失败:', error);
        }
    },

    /**
     * 获取题目对应的 PDF 页码
     */
    getPDFPageForQuestion(questionId) {
        if (!this.pdfMappings || !this.pdfMappings[this.currentYear]) {
            return null;
        }

        const yearMapping = this.pdfMappings[this.currentYear];
        const qId = parseInt(questionId);

        // 遍历所有 section 找到包含该题目的 section
        for (const [sectionKey, sectionData] of Object.entries(yearMapping.sections)) {
            const questions = sectionData.questions;
            // questions 可能是 [start, end] 或 [single]
            if (questions.length === 2) {
                if (qId >= questions[0] && qId <= questions[1]) {
                    return {
                        page: sectionData.start_page,
                        pdf: yearMapping.pdf_file
                    };
                }
            } else if (questions.length === 1 && qId === questions[0]) {
                return {
                    page: sectionData.start_page,
                    pdf: yearMapping.pdf_file
                };
            }
        }

        return null;
    },

    /**
     * 打开 PDF 解析
     */
    openPDFAnalysis(questionId) {
        const pdfInfo = this.getPDFPageForQuestion(questionId);
        if (!pdfInfo) {
            UIEffects.showToast('暂无该题目的 PDF 解析', 'warning');
            return;
        }

        // 构建 PDF URL（带页码参数）
        const pdfUrl = `assets/pdf/${encodeURIComponent(pdfInfo.pdf)}#page=${pdfInfo.page}`;

        // 在新标签页打开
        window.open(pdfUrl, '_blank');
    },

    /**
     * 打开完整 PDF 解析（从第一页）
     */
    openFullPDFAnalysis() {
        if (!this.pdfMappings || !this.pdfMappings[this.currentYear]) {
            UIEffects.showToast('暂无该年份的 PDF 解析', 'warning');
            return;
        }

        const pdfFile = this.pdfMappings[this.currentYear].pdf_file;
        const pdfUrl = `assets/pdf/${encodeURIComponent(pdfFile)}`;

        window.open(pdfUrl, '_blank');
    },

    /**
     * 绑定事件
     */
    bindEvents() {
        // 开始按钮
        this.elements.startBtn?.addEventListener('click', () => this.startExam());

        // 继续按钮
        this.elements.continueBtn?.addEventListener('click', () => this.continueExam());

        // 单词本按钮
        this.elements.vocabBtn?.addEventListener('click', () => this.showScreen(this.elements.vocabScreen));
        document.getElementById('vocab-card-btn')?.addEventListener('click', () => this.showScreen(this.elements.vocabScreen));

        // 导航按钮
        this.elements.prevBtn?.addEventListener('click', () => this.prevQuestion());
        this.elements.nextBtn?.addEventListener('click', () => this.nextQuestion());

        // 结果界面按钮
        this.elements.restartBtn?.addEventListener('click', () => this.restartExam());
        this.elements.reviewBtn?.addEventListener('click', () => this.reviewWrongQuestions());

        // 设置按钮
        this.elements.settingsBtn?.addEventListener('click', () => UIEffects.openSettings());

        // 键盘快捷键
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));

        // 游戏结束重试按钮
        document.querySelector('.game-over-overlay .btn-primary')?.addEventListener('click', () => {
            UIEffects.hideGameOverScreen();
            StorageManager.restoreHP();
            UIEffects.updateHUD();
        });

        // 设置面板事件
        document.querySelector('.settings-overlay')?.addEventListener('click', () => UIEffects.closeSettings());
        document.getElementById('saveSettingsBtn')?.addEventListener('click', () => UIEffects.saveSettings());
        document.getElementById('exportSaveBtn')?.addEventListener('click', () => this.exportSave());
        document.getElementById('importSaveBtn')?.addEventListener('click', () => this.triggerImportSave());

        // 文件导入
        document.getElementById('importFileInput')?.addEventListener('change', (e) => this.importSave(e));
    },

    /**
     * 恢复进度
     */
    restoreProgress() {
        const gameData = StorageManager.getGameData();
        const pendingAnswers = StorageManager.getPendingAnswers();

        // Update start screen level/title display
        const levelEl = document.getElementById('start-level');
        const titleEl = document.getElementById('start-title');
        if (gameData && levelEl && titleEl) {
            levelEl.textContent = `Lv.${gameData.level || 1}`;
            titleEl.textContent = gameData.title || '四级萌新';
        }

        // Check if there's any progress (from localStorage, or already loaded from backend in init())
        const hasProgress = (gameData && Object.keys(gameData.answers).length > 0) ||
            (pendingAnswers && Object.keys(pendingAnswers).length > 0) ||
            this.currentQuestionIndex > 0;

        if (hasProgress) {
            // 有进度，显示继续按钮
            if (this.elements.continueBtn) {
                this.elements.continueBtn.style.display = 'inline-block';
            }
            // Prioritize gameData's index if available, otherwise keep current
            if (gameData?.currentQuestionIndex !== undefined) {
                this.currentQuestionIndex = gameData.currentQuestionIndex;
            }

            // Show save preview on start screen
            const savePreview = document.getElementById('save-preview');
            const saveDetail = document.getElementById('save-preview-detail');
            if (savePreview && saveDetail) {
                const answeredCount = Object.keys(gameData?.answers || {}).length;
                const lastTime = gameData?.lastPlayTime ? new Date(gameData.lastPlayTime) : null;
                const timeStr = lastTime ?
                    `${lastTime.getMonth() + 1}/${lastTime.getDate()} ${lastTime.getHours()}:${String(lastTime.getMinutes()).padStart(2, '0')}` :
                    '';
                saveDetail.textContent = `已答 ${answeredCount} 题 ${timeStr ? '· ' + timeStr : ''}`;
                savePreview.classList.remove('hidden');
            }
        }

        // 更新 HUD
        UIEffects.updateHUD();
    },

    /**
     * 从首页快速加载存档并继续
     */
    loadSaveAndContinue() {
        const gameData = StorageManager.getGameData();
        if (!gameData) {
            UIEffects.showToast('没有找到存档', 'warning');
            return;
        }

        // Restore progress index
        if (gameData.currentQuestionIndex !== undefined) {
            this.currentQuestionIndex = gameData.currentQuestionIndex;
        }

        // Continue exam
        this.isReviewMode = false;
        this.showScreen(this.elements.examScreen);
        this.showQuestion();

        UIEffects.showToast(`已恢复进度：第 ${this.currentQuestionIndex + 1} 题`, 'success');
    },

    // ==================== 屏幕切换 ====================

    /**
     * 显示屏幕
     */
    showScreen(screen) {
        [this.elements.startScreen, this.elements.examScreen, this.elements.resultScreen, this.elements.vocabScreen]
            .forEach(s => s?.classList.remove('active'));
        screen?.classList.add('active');

        // 进入单词本时刷新数据
        if (screen === this.elements.vocabScreen && typeof VocabUI !== 'undefined') {
            VocabUI.refreshVocabulary();
        }

        // CRITICAL FIX: Hide drawing canvas when not in exam screen
        if (window.DrawingBoard && DrawingBoard.canvas) {
            if (screen === this.elements.examScreen) {
                // Show canvas in exam screen
                DrawingBoard.canvas.style.display = 'block';
            } else {
                // Hide canvas in other screens (home, vocab, etc.)
                DrawingBoard.canvas.style.display = 'none';
                // Also disable draw mode to prevent accidental drawing
                if (DrawingBoard.drawModeActive) {
                    DrawingBoard.toggleDrawMode();
                }
            }
        }
    },

    // ==================== 考试流程 ====================

    /**
     * 开始新考试
     */
    /**
     * 开始新考试
     */
    startExam(mode = 'exam') {
        this.currentQuestionIndex = 0;
        this.isReviewMode = false;
        this.isSubmitted = false;
        this.examMode = mode;

        StorageManager.clearAnswers();
        StorageManager.clearPendingAnswers();

        // 恢复HP
        StorageManager.restoreHP();
        UIEffects.updateHUD();

        // 启动计时器
        this.startTimer();

        this.showScreen(this.elements.examScreen);
        this.showQuestion();

        // 模式分支
        if (this.examMode === 'story') {
            document.body.classList.add('story-mode-active');
            UIEffects.startStoryMode(); // 播放开场剧情
        } else {
            document.body.classList.remove('story-mode-active');
            // 显示考试模式提示
            UIEffects.showToast('考试模式：答题不会立即判分，完成后统一提交', 'info');
        }
    },

    /**
     * 切换答题模式
     */
    toggleExamMode() {
        this.examMode = this.examMode === 'exam' ? 'practice' : 'exam';
        const modeName = this.examMode === 'exam' ? '考试模式' : '练习模式';
        UIEffects.showToast(`已切换为${modeName}`, 'info');
    },

    /**
     * 继续考试
     */
    continueExam() {
        this.isReviewMode = false;
        this.showScreen(this.elements.examScreen);
        this.showQuestion();
    },

    /**
     * 重新开始
     */
    restartExam() {
        this.loadExamData().then(() => {
            this.startExam();
        });
    },

    /**
     * 显示题目
     */
    showQuestion() {
        const q = this.allQuestions[this.currentQuestionIndex];
        if (!q) return;

        // Set current question for AI features (Ask Mia, etc.)
        this.currentQuestion = q;

        // 保存当前进度
        StorageManager.updateGameData({ currentQuestionIndex: this.currentQuestionIndex });

        // Auto-save every 5 questions
        if ((this.currentQuestionIndex + 1) % 5 === 0) {
            this.autoSave();
        }

        // 更新进度显示
        this.elements.currentQ.textContent = this.currentQuestionIndex + 1;

        // Multi-year support: show year badge
        if (q.year && this.selectedYears.length > 1) {
            this.elements.sectionName.textContent = `[${q.year}] ${q.sectionName}`;
        } else {
            this.elements.sectionName.textContent = q.sectionName;
        }

        // 显示文章（或图片）
        if (q.image) {
            // 如果题目包含图片（如图片作文题）
            this.elements.articleContent.innerHTML = `
                <div class="question-image-container">
                    <img src="${q.image}" alt="题目图片" class="question-image" onclick="App.zoomImage(this.src)" />
                    <p style="text-align:center; margin-top:10px; color:#7f8c8d; font-size:0.9rem;">
                        <i class="ph-duotone ph-magnifying-glass-plus"></i> 点击图片放大查看
                    </p>
                </div>
            `;
        } else if (q.article && q.article.length > 0) {
            this.elements.articleContent.innerHTML = q.article
                .map(p => `<p>${this.formatText(p)}</p>`)
                .join('');
        } else {
            this.elements.articleContent.innerHTML =
                '<p style="color:#95a5a6; text-align:center; padding: 50px 20px;">本题无阅读材料</p>';
        }

        // 显示题目
        this.elements.questionText.innerHTML = this.formatText(q.text);

        // 显示选项
        this.renderOptions(q);

        // 显示反馈（如果已答题且已提交或练习模式）
        const answer = StorageManager.getAnswer(q.id);
        if (answer && (this.isSubmitted || this.examMode === 'practice')) {
            this.showFeedback(q, answer.answer);
        } else {
            this.elements.feedback.classList.remove('show');
        }

        // 更新导航按钮
        this.updateNavButtons(q);
        this.updateAnsweredCount();

        // Load drawing for this question
        if (window.DrawingBoard && DrawingBoard.loadDrawingForQuestion) {
            DrawingBoard.loadDrawingForQuestion(q.id);
        }

        // Clear conversation history when switching questions
        if (window.UIEffects && UIEffects.clearConversation) {
            UIEffects.clearConversation();
        }
    },

    /**
     * 渲染选项
     */
    renderOptions(q) {
        this.elements.optionsDiv.innerHTML = '';
        const savedAnswer = StorageManager.getAnswer(q.id);
        const pendingAnswer = StorageManager.getPendingAnswer(q.id);

        // Improved question type detection
        const hasValidOptions = q.options &&
            typeof q.options === 'object' &&
            !Array.isArray(q.options) &&
            Object.keys(q.options).length > 0;

        if (hasValidOptions) {
            // Objective question - render option buttons
            Object.entries(q.options).sort().forEach(([key, value]) => {
                const btn = document.createElement('button');
                btn.className = 'option-btn';
                btn.innerHTML = `<strong>${key}.</strong> ${value}`;
                btn.dataset.key = key;

                // 考试模式且已提交：显示对错
                if (this.isSubmitted && savedAnswer) {
                    btn.disabled = true;
                    if (key === q.correct_answer) {
                        btn.classList.add('correct');
                    } else if (key === savedAnswer.answer) {
                        btn.classList.add('wrong');
                    }
                }
                // 考试模式未提交：显示选中状态
                else if (this.examMode === 'exam' && !this.isSubmitted) {
                    if (pendingAnswer === key) {
                        btn.classList.add('selected');
                    }
                    btn.addEventListener('click', () => this.selectOption(key));
                }
                // 练习模式已答题：显示对错
                else if (savedAnswer) {
                    btn.disabled = true;
                    if (key === q.correct_answer) {
                        btn.classList.add('correct');
                    } else if (key === savedAnswer.answer) {
                        btn.classList.add('wrong');
                    }
                }
                // 练习模式未答题
                else {
                    btn.addEventListener('click', () => this.selectOption(key));
                }

                this.elements.optionsDiv.appendChild(btn);
            });
        } else {
            // 主观题
            console.log(`[App] Rendering subjective question for Q${q.id} - No valid options found`);
            this.renderSubjectiveQuestion(q);
        }
    },

    /**
     * 渲染主观题
     */
    renderSubjectiveQuestion(q) {
        const savedAnswer = StorageManager.getAnswer(q.id);

        this.elements.optionsDiv.innerHTML = `
            <div class="subjective-input">
                <textarea id="subjectiveAnswer" placeholder="请在此输入你的答案..." 
                    rows="6" ${savedAnswer ? 'disabled' : ''}>${savedAnswer?.answer || ''}</textarea>
                ${!savedAnswer ? `
                    <div class="subjective-buttons">
                        <button class="btn-primary" onclick="App.submitSubjective()">
                            提交答案
                        </button>
                        <button class="btn-secondary" onclick="App.showSubjectiveAnswer()">
                            查看参考答案
                        </button>
                    </div>
                ` : ''}
            </div>
        `;

        // 添加样式
        if (!document.getElementById('subjective-styles')) {
            const style = document.createElement('style');
            style.id = 'subjective-styles';
            style.textContent = `
                .subjective-input textarea {
                    width: 100%;
                    padding: 15px;
                    background: rgba(0,0,0,0.2);
                    border: 2px solid #4a6278;
                    border-radius: 10px;
                    color: white;
                    font-size: 1rem;
                    line-height: 1.6;
                    resize: vertical;
                }
                .subjective-input textarea:focus {
                    outline: none;
                    border-color: var(--accent-primary);
                }
                .subjective-buttons {
                    display: flex;
                    gap: 10px;
                    margin-top: 15px;
                }
                .subjective-buttons button {
                    flex: 1;
                    padding: 12px;
                }
            `;
            document.head.appendChild(style);
        }
    },

    /**
     * 提交主观题（AI 批改）
     */
    async submitSubjective() {
        const q = this.allQuestions[this.currentQuestionIndex];
        const textarea = document.getElementById('subjectiveAnswer');
        const userAnswer = textarea?.value.trim();

        if (!userAnswer) {
            UIEffects.showToast('请先输入答案', 'error');
            return;
        }

        // 记录答案
        StorageManager.recordAnswer(q.id, userAnswer, true);
        StorageManager.addExp(15); // 主观题给更多经验
        UIEffects.animateEXPIncrease();
        this.updateAnsweredCount();

        // 检查是否有 AI
        if (GeminiService.isConfigured()) {
            // 显示 AI 批改中
            this.elements.feedback.classList.add('show');
            this.elements.feedback.innerHTML = `
                <div class="feedback-content">
                    <div class="ai-loading">
                        <div class="spinner"></div>
                        <span>AI 正在批改...</span>
                    </div>
                </div>
            `;

            try {
                const referenceAnswer = q.reference_answer || q.analysis_raw || '';
                const result = await GeminiService.scoreTranslation(q.text, referenceAnswer, userAnswer);

                this.elements.feedback.innerHTML = `
                    <div class="feedback-content feedback-correct">
                        <h4>🤖 AI 批改结果</h4>
                        <div style="white-space: pre-wrap;">${UIEffects.renderMarkdown(result)}</div>
                    </div>
                `;
            } catch (error) {
                this.showFeedback(q, userAnswer);
            }
        } else {
            this.showFeedback(q, userAnswer);
        }

        textarea.disabled = true;
        document.querySelector('.subjective-buttons')?.remove();
        this.elements.nextBtn.disabled = false;
    },

    /**
     * 查看主观题答案
     */
    showSubjectiveAnswer() {
        const q = this.allQuestions[this.currentQuestionIndex];
        StorageManager.recordAnswer(q.id, 'VIEWED', true);
        this.updateAnsweredCount();

        this.elements.feedback.classList.add('show');
        this.elements.feedback.innerHTML = `
            <div class="feedback-content feedback-correct">
                <h4>📝 参考答案</h4>
                <p>${q.reference_answer || q.analysis_raw || q.ai_persona_prompt || '暂无参考答案'}</p>
            </div>
        `;

        document.querySelector('.subjective-buttons')?.remove();
        this.elements.nextBtn.disabled = false;
    },

    /**
     * 选择选项
     */
    selectOption(key) {
        const q = this.allQuestions[this.currentQuestionIndex];

        // 考试模式：只记录选择，不判断对错
        if (this.examMode === 'exam' && !this.isSubmitted) {
            // 临时记录答案（不判断对错）
            StorageManager.recordPendingAnswer(q.id, key);

            // 更新按钮状态 - 只显示选中状态
            document.querySelectorAll('.option-btn').forEach(btn => {
                btn.classList.remove('selected');
                if (btn.dataset.key === key) {
                    btn.classList.add('selected');
                }
            });

            // 启用下一题按钮
            this.elements.nextBtn.disabled = false;
            this.updateAnsweredCount();

            // 可以继续修改，不锁定
            return;
        }

        // 练习模式或已提交：立即判断
        const isCorrect = key === q.correct_answer;

        // 记录答案
        StorageManager.recordAnswer(q.id, key, isCorrect);
        this.updateAnsweredCount();

        if (isCorrect) {
            // 答对
            StorageManager.addExp(10);
            UIEffects.onCorrectAnswer();
            UIEffects.animateEXPIncrease();
        } else {
            // 答错
            StorageManager.recordWrong();
            const hp = StorageManager.decreaseHP(10);
            UIEffects.onWrongAnswer();
            UIEffects.animateHPDecrease();

            // 检查游戏结束
            if (hp <= 0) {
                setTimeout(() => {
                    UIEffects.onGameOver();
                }, 500);
            }
        }

        // Live2D 反应 (通用)
        if (typeof Live2DManager !== 'undefined') {
            if (isCorrect) Live2DManager.onCorrect();
            else Live2DManager.onWrong();
        }

        // 更新按钮状态
        document.querySelectorAll('.option-btn').forEach(btn => {
            btn.disabled = true;
            if (btn.dataset.key === q.correct_answer) {
                btn.classList.add('correct');
            } else if (btn.dataset.key === key && !isCorrect) {
                btn.classList.add('wrong');
            }
        });

        // 剧情模式反馈 vs 普通模式反馈
        if (this.examMode === 'story') {
            console.log('[DEBUG] handleStoryFeedback called - currentIndex:', this.currentQuestionIndex, 'questionId:', q.id, 'questionYear:', q.year);
            UIEffects.handleStoryFeedback(isCorrect, q);
            // 剧情模式下，也可以延迟显示常规反馈作为补充，或者不显示
            // 这里选择不显示常规 feedback，完全依赖对话框
            this.elements.feedback.classList.remove('show');

            // CRITICAL FIX: Ensure next button is enabled even if dialog fails
            // This prevents navigation lockup
            setTimeout(() => {
                this.elements.nextBtn.disabled = false;
                this.elements.nextBtn.classList.add('pulse-hint'); // Visual cue
            }, 500);
        } else {
            this.showFeedback(q, key);
        }

        // In non-story modes, enable immediately
        if (this.examMode !== 'story') {
            this.elements.nextBtn.disabled = false;
        }
    },

    /**
     * 显示反馈
     */
    showFeedback(q, userAnswer) {
        const isCorrect = userAnswer === q.correct_answer || userAnswer === 'VIEWED';
        const pdfInfo = this.getPDFPageForQuestion(q.id);

        // 显示解析面板按钮
        let analysisButton = '';
        if (pdfInfo) {
            analysisButton = `
                <button class="btn-show-analysis" onclick="App.showAnalysisPanel(${q.id})">
                    <i class="ph-duotone ph-book-open-text"></i> 查看解析
                </button>
            `;
        }

        this.elements.feedback.classList.add('show');
        this.elements.feedback.innerHTML = `
            <div class="feedback-content ${isCorrect ? 'feedback-correct' : 'feedback-wrong'}">
                <h4>${isCorrect ? '✓ 回答正确！' : '✗ 回答错误'}</h4>
                ${q.correct_answer ? `<p><strong>正确答案:</strong> ${q.correct_answer}</p>` : ''}
                <p><strong>简要解析:</strong> ${q.analysis_raw || '暂无解析'}</p>
                <div class="feedback-actions">
                    ${analysisButton}
                </div>
            </div>
        `;
    },

    /**
     * 显示解析面板
     */
    showAnalysisPanel(questionId) {
        const panel = document.getElementById('analysis-panel');
        const container = document.querySelector('.exam-container');
        const pdfInfo = this.getPDFPageForQuestion(questionId);

        if (!panel || !pdfInfo) return;

        // 显示面板
        panel.style.display = 'flex';
        container.classList.add('with-analysis');

        // 加载 PDF
        const pdfUrl = `assets/pdf/${encodeURIComponent(pdfInfo.pdf)}#page=${pdfInfo.page}`;
        const pdfViewer = document.getElementById('pdf-viewer');
        pdfViewer.src = pdfUrl;

        // 切换到 PDF 标签
        this.switchAnalysisTab('pdf');

        // 重置 AI 解析区域
        document.getElementById('ai-analysis-area').innerHTML = `
            <p class="analysis-placeholder">点击下方按钮获取 AI 详细解析</p>
            <button class="btn-ai-analyze" onclick="App.getAIAnalysis()">
                <i class="ph-duotone ph-robot"></i> 获取 AI 解析
            </button>
        `;
    },

    /**
     * 切换解析标签页
     */
    switchAnalysisTab(tab) {
        // 更新标签状态
        document.querySelectorAll('.analysis-tab').forEach(t => {
            t.classList.toggle('active', t.dataset.tab === tab);
        });

        // 显示对应内容
        document.getElementById('pdf-analysis-content').style.display = tab === 'pdf' ? 'block' : 'none';
        document.getElementById('ai-analysis-content').style.display = tab === 'ai' ? 'block' : 'none';
    },

    /**
     * 关闭解析面板
     */
    toggleAnalysisPanel() {
        const panel = document.getElementById('analysis-panel');
        const container = document.querySelector('.exam-container');

        panel.style.display = 'none';
        container.classList.remove('with-analysis');

        // 清空 PDF viewer
        document.getElementById('pdf-viewer').src = '';
    },

    /**
     * 获取 AI 解析缓存 key
     */
    getAICacheKey(questionId) {
        return `ai_analysis_${this.currentYear}_${questionId}`;
    },

    /**
     * 从缓存获取 AI 解析
     */
    getCachedAIAnalysis(questionId) {
        const key = this.getAICacheKey(questionId);
        const cached = localStorage.getItem(key);
        if (cached) {
            try {
                return JSON.parse(cached);
            } catch (e) {
                return null;
            }
        }
        return null;
    },

    /**
     * 保存 AI 解析到缓存
     */
    saveAIAnalysisToCache(questionId, analysis) {
        const key = this.getAICacheKey(questionId);
        const data = {
            analysis: analysis,
            timestamp: Date.now()
        };
        localStorage.setItem(key, JSON.stringify(data));
    },

    /**
     * 获取 AI 解析
     */
    async getAIAnalysis() {
        const q = this.allQuestions[this.currentQuestionIndex];
        if (!q) return;

        const aiArea = document.getElementById('ai-analysis-area');
        if (!aiArea) return;

        // 先检查缓存
        const cached = this.getCachedAIAnalysis(q.id);
        if (cached) {
            const cacheDate = new Date(cached.timestamp).toLocaleString('zh-CN');
            aiArea.innerHTML = `
                <div class="ai-response">
                    <div class="ai-cache-info">
                        <i class="ph-duotone ph-database"></i> 已缓存 (${cacheDate})
                        <button class="btn-refresh-ai" onclick="App.refreshAIAnalysis()" title="重新生成">
                            <i class="ph-duotone ph-arrow-clockwise"></i>
                        </button>
                    </div>
                    <div class="ai-content">${UIEffects.renderMarkdown(cached.analysis)}</div>
                </div>
            `;
            return;
        }

        // 检查 AI 是否配置
        if (!GeminiService.isConfigured()) {
            aiArea.innerHTML = `
                <div class="ai-response">
                    <p style="color: var(--warning);">⚠️ 请先在设置中配置 Gemini API Key</p>
                </div>
            `;
            return;
        }

        // 显示加载状态
        aiArea.innerHTML = `
            <div class="ai-response loading">
                <div class="spinner"></div>
                <span>AI 正在分析...</span>
            </div>
        `;

        try {
            // 构建提问内容
            const questionContext = q.article?.length > 0
                ? `文章内容:\n${q.article.join('\n')}\n\n题目: ${q.text}`
                : `题目: ${q.text}`;

            const optionsText = q.options
                ? Object.entries(q.options).map(([k, v]) => `${k}. ${v}`).join('\n')
                : '';

            const prompt = `请详细解释这道考研英语题目：

${questionContext}

选项：
${optionsText}

正确答案：${q.correct_answer}

请从以下几个方面分析：
1. 为什么正确答案是对的
2. 其他选项为什么错误
3. 相关的语法/词汇知识点
4. 解题技巧`;

            const response = await GeminiService.askQuestion(prompt);

            // 保存到缓存
            this.saveAIAnalysisToCache(q.id, response);

            const cacheDate = new Date().toLocaleString('zh-CN');
            aiArea.innerHTML = `
                <div class="ai-response">
                    <div class="ai-cache-info">
                        <i class="ph-duotone ph-check-circle"></i> 刚刚生成
                        <button class="btn-refresh-ai" onclick="App.refreshAIAnalysis()" title="重新生成">
                            <i class="ph-duotone ph-arrow-clockwise"></i>
                        </button>
                    </div>
                    <div class="ai-content">${UIEffects.renderMarkdown(response)}</div>
                </div>
            `;
        } catch (error) {
            aiArea.innerHTML = `
                <div class="ai-response error">
                    <p>❌ AI 分析失败: ${error.message}</p>
                    <button class="btn-ai-analyze" onclick="App.getAIAnalysis()" style="margin-top: 10px;">
                        <i class="ph-duotone ph-arrow-clockwise"></i> 重试
                    </button>
                </div>
            `;
        }
    },

    /**
     * 强制刷新 AI 解析（忽略缓存）
     */
    async refreshAIAnalysis() {
        const q = this.allQuestions[this.currentQuestionIndex];
        if (!q) return;

        // 删除缓存
        const key = this.getAICacheKey(q.id);
        localStorage.removeItem(key);

        // 重新获取
        await this.getAIAnalysis();
    },

    // ==================== 题目选择器 ====================

    /**
     * 打开题目选择器
     */
    openQuestionSelector() {
        const overlay = document.getElementById('question-selector-overlay');
        const content = document.getElementById('question-selector-content');

        if (!overlay || !content) return;

        // 按 Section 分组题目
        // When multiple years are selected, group by year + section to avoid merging
        const sections = {};
        this.allQuestions.forEach((q, index) => {
            // Use year prefix when multiple years selected to keep sections separate
            const sectionKey = this.selectedYears.length > 1 && q.year
                ? `${q.year} - ${q.sectionName}`
                : q.sectionName;

            if (!sections[sectionKey]) {
                sections[sectionKey] = [];
            }
            sections[sectionKey].push({ ...q, index });
        });

        // 生成内容
        let html = '';
        const gameData = StorageManager.getGameData();
        const pendingAnswers = StorageManager.getPendingAnswers();

        for (const [sectionName, questions] of Object.entries(sections)) {
            html += `
                <div class="question-selector-section">
                    <h4>${sectionName}</h4>
                    <div class="question-grid">
            `;

            questions.forEach(q => {
                const answer = gameData.answers[q.id];
                const pending = pendingAnswers[q.id];
                const isCurrent = q.index === this.currentQuestionIndex;
                const isAnswered = !!answer;
                const isPending = !!pending;
                const isWrong = answer && !answer.isCorrect;

                let classes = 'question-grid-item';
                if (isCurrent) classes += ' current';
                if (isAnswered) classes += isWrong ? ' wrong' : ' answered';
                else if (isPending) classes += ' pending';

                html += `
                    <button class="${classes}" 
                            onclick="App.jumpToQuestion(${q.index})"
                            title="第 ${q.id} 题">
                        ${q.id}
                    </button>
                `;
            });

            html += `
                    </div>
                </div>
            `;
        }

        content.innerHTML = html;
        overlay.classList.add('show');
    },

    /**
     * 关闭题目选择器
     */
    closeQuestionSelector(event) {
        if (event && event.target !== event.currentTarget) return;

        const overlay = document.getElementById('question-selector-overlay');
        overlay?.classList.remove('show');
    },

    /**
     * 跳转到指定题目
     */
    jumpToQuestion(index) {
        if (index >= 0 && index < this.allQuestions.length) {
            this.currentQuestionIndex = index;
            this.showQuestion();
            this.closeQuestionSelector();
        }
    },

    /**
     * 更新已答题数
     */
    updateAnsweredCount() {
        if (!this.elements.answeredCount) return;
        const pending = StorageManager.getPendingAnswers();
        const gameData = StorageManager.getGameData();
        const answers = gameData ? gameData.answers : {};

        // Count unique answered questions
        const answeredIds = new Set([...Object.keys(pending), ...Object.keys(answers)]);
        this.elements.answeredCount.textContent = answeredIds.size;
    },

    /**
     * 更新导航按钮
     */
    updateNavButtons(q) {
        const savedAnswer = StorageManager.getAnswer(q.id);
        const pendingAnswer = StorageManager.getPendingAnswer(q.id);

        this.elements.prevBtn.disabled = this.currentQuestionIndex === 0;

        // 考试模式：有待提交答案或无选项题目可继续
        // 练习模式：有已保存答案可继续
        const canProceed = this.examMode === 'exam'
            ? (pendingAnswer || !q.options || Object.keys(q.options).length === 0)
            : (savedAnswer || !q.options || Object.keys(q.options).length === 0);

        this.elements.nextBtn.disabled = !canProceed;

        // 最后一题显示"提交"或"完成"
        if (this.currentQuestionIndex === this.allQuestions.length - 1) {
            this.elements.nextBtn.textContent = this.examMode === 'exam' && !this.isSubmitted ? '提交考试' : '完成';
        } else {
            this.elements.nextBtn.textContent = '下一题';
        }
    },

    /**
     * 上一题
     */
    prevQuestion() {
        if (this.currentQuestionIndex > 0) {
            this.currentQuestionIndex--;
            this.showQuestion();
        }
    },

    /**
     * 下一题
     */
    nextQuestion() {
        if (this.currentQuestionIndex < this.allQuestions.length - 1) {
            this.currentQuestionIndex++;
            this.showQuestion();
        } else {
            // 考试模式需要确认提交
            if (this.examMode === 'exam' && !this.isSubmitted) {
                this.confirmSubmitExam();
            } else {
                this.showResult();
            }
        }
    },

    /**
     * 确认提交考试
     */
    confirmSubmitExam() {
        const pendingAnswers = StorageManager.getPendingAnswers();
        const answeredCount = Object.keys(pendingAnswers).length;
        const totalCount = this.allQuestions.filter(q => q.options).length;
        const unansweredCount = totalCount - answeredCount;

        let message = `确定要提交考试吗？\n\n已答：${answeredCount} 题`;
        if (unansweredCount > 0) {
            message += `\n未答：${unansweredCount} 题`;
        }

        if (confirm(message)) {
            this.submitExam();
        }
    },

    /**
     * 提交考试并评分
     */
    submitExam() {
        // 停止计时器
        this.stopTimer();

        this.isSubmitted = true;
        const pendingAnswers = StorageManager.getPendingAnswers();

        let correctCount = 0;
        let wrongCount = 0;

        // 遍历所有题目进行评分
        this.allQuestions.forEach(q => {
            if (!q.options) return; // 跳过主观题

            const userAnswer = pendingAnswers[q.id];
            if (!userAnswer) {
                // 未作答视为错误
                StorageManager.recordAnswer(q.id, null, false);
                wrongCount++;
                return;
            }

            const isCorrect = userAnswer === q.correct_answer;
            StorageManager.recordAnswer(q.id, userAnswer, isCorrect);

            if (isCorrect) {
                correctCount++;
                StorageManager.addExp(10);
            } else {
                wrongCount++;
                StorageManager.recordWrong();
            }
        });

        // 根据正确率扣HP
        const wrongPenalty = Math.min(wrongCount * 5, 50);
        if (wrongPenalty > 0) {
            StorageManager.decreaseHP(wrongPenalty);
        }

        UIEffects.updateHUD();
        UIEffects.showToast(`考试已提交！正确 ${correctCount} 题，错误 ${wrongCount} 题`, 'success');

        // 清空待提交答案
        StorageManager.clearPendingAnswers();

        // 显示结果
        this.showResult();
    },

    /**
     * 显示结果
     */
    showResult() {
        this.showScreen(this.elements.resultScreen);

        const stats = StorageManager.getStats();

        document.getElementById('result-total').textContent = stats.totalCorrect + stats.totalWrong;
        document.getElementById('result-correct').textContent = stats.totalCorrect;
        document.getElementById('result-rate').textContent = stats.accuracy + '%';

        // 根据成绩显示不同的标题
        const resultTitle = document.querySelector('#result-screen h1');
        if (resultTitle) {
            if (stats.accuracy >= 90) {
                resultTitle.textContent = '🏆 太厉害了！';
            } else if (stats.accuracy >= 70) {
                resultTitle.textContent = '🎉 答题完成！';
            } else if (stats.accuracy >= 50) {
                resultTitle.textContent = '💪 继续加油！';
            } else {
                resultTitle.textContent = '📚 需要多练习！';
            }
        }

        UIEffects.showMascotBubble('correct');
    },

    /**
     * 查看错题
     */
    reviewWrongQuestions() {
        const gameData = StorageManager.getGameData();

        if (!gameData.wrongQuestions || gameData.wrongQuestions.length === 0) {
            UIEffects.showToast('恭喜！没有错题！', 'success');
            return;
        }

        // 只显示错题
        this.isReviewMode = true;
        this.allQuestions = this.allQuestions.filter(q =>
            gameData.wrongQuestions.includes(q.id)
        );
        this.currentQuestionIndex = 0;
        this.elements.totalQ.textContent = this.allQuestions.length;

        // 清除这些题的答案记录
        StorageManager.clearAnswers();

        this.showScreen(this.elements.examScreen);
        this.showQuestion();
    },

    // ==================== 工具方法 ====================

    /**
     * 格式化文本
     */
    formatText(text) {
        if (!text) return '';
        return text.replace(/_(\d+)_/g, '<span class="blank">$1</span>');
    },

    /**
     * 键盘处理
     */
    handleKeyboard(e) {
        // Escape 键关闭弹窗
        if (e.key === 'Escape') {
            const questionSelector = document.getElementById('question-selector-overlay');
            if (questionSelector?.classList.contains('show')) {
                this.closeQuestionSelector();
                return;
            }
        }

        if (!this.elements.examScreen?.classList.contains('active')) return;

        // J 键打开题目选择器
        if (e.key.toLowerCase() === 'j') {
            this.openQuestionSelector();
            return;
        }

        const q = this.allQuestions[this.currentQuestionIndex];
        const savedAnswer = StorageManager.getAnswer(q?.id);

        if (!savedAnswer && q?.options) {
            const key = e.key.toUpperCase();
            if (['A', 'B', 'C', 'D'].includes(key) && q.options[key]) {
                this.selectOption(key);
            }
        }

        if (e.key === 'ArrowLeft' && !this.elements.prevBtn.disabled) {
            this.prevQuestion();
        } else if ((e.key === 'ArrowRight' || e.key === 'Enter') && !this.elements.nextBtn.disabled) {
            this.nextQuestion();
        }
    },

    // ==================== 存档功能 ====================

    /**
     * 导出存档
     */
    exportSave() {
        StorageManager.exportSave();
        UIEffects.showToast('存档已导出！', 'success');
    },

    /**
     * 触发导入存档
     */
    triggerImportSave() {
        document.getElementById('importFileInput')?.click();
    },

    /**
     * 导入存档
     */
    async importSave(e) {
        const file = e.target.files[0];
        if (!file) return;

        try {
            const result = await StorageManager.importSave(file);
            if (result.success) {
                UIEffects.showToast(result.message, 'success');
                UIEffects.updateHUD();
                this.restoreProgress();
            }
        } catch (error) {
            UIEffects.showToast(error.message, 'error');
        }

        e.target.value = '';
    },

    // ==================== 计时器功能 ====================

    /**
     * 启动计时器
     */
    startTimer() {
        this.examStartTime = Date.now();
        this.examElapsedSeconds = 0;
        this.updateTimerDisplay();

        // 每秒更新一次
        this.examTimer = setInterval(() => {
            this.examElapsedSeconds = Math.floor((Date.now() - this.examStartTime) / 1000);
            this.updateTimerDisplay();
        }, 1000);
    },

    /**
     * 停止计时器
     */
    stopTimer() {
        if (this.examTimer) {
            clearInterval(this.examTimer);
            this.examTimer = null;
        }
    },

    /**
     * 更新计时器显示
     */
    updateTimerDisplay() {
        const timerEl = document.getElementById('exam-timer');
        if (!timerEl) return;

        const minutes = Math.floor(this.examElapsedSeconds / 60);
        const seconds = this.examElapsedSeconds % 60;
        timerEl.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    },

    // ==================== 图片功能 ====================

    /**
     * 放大图片
     */
    zoomImage(imageSrc) {
        // 创建模态框
        const modal = document.createElement('div');
        modal.className = 'image-modal';
        modal.innerHTML = `
            <img src="${imageSrc}" alt="放大图片" />
        `;

        // 点击关闭
        modal.addEventListener('click', () => {
            modal.remove();
        });

        // ESC 键关闭
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                modal.remove();
                document.removeEventListener('keydown', escHandler);
            }
        };
        document.addEventListener('keydown', escHandler);

        document.body.appendChild(modal);
    },

    // ==================== Save/Load System ====================

    /**
     * Open save/load panel
     */
    async openSavePanel(tab = null) {
        const panel = document.getElementById('save-panel-overlay');
        panel.classList.add('active');
        if (tab) {
            this.switchSaveTab(tab);
        }
        await this.refreshSaveSlots();
    },

    /**
     * Close save panel
     */
    closeSavePanel(event) {
        // Only close if clicking overlay (not the panel itself)
        if (event && event.target.id !== 'save-panel-overlay') return;
        document.getElementById('save-panel-overlay').classList.remove('active');
    },

    /**
     * Switch between save and load tabs
     */
    switchSaveTab(tab) {
        document.querySelectorAll('.save-tab').forEach(t => {
            t.classList.toggle('active', t.dataset.tab === tab);
        });

        // For auto-save slot, disable click in save mode
        const autoSlot = document.querySelector('.save-slot.auto-save');
        if (tab === 'save') {
            autoSlot.style.opacity = '0.5';
            autoSlot.style.pointerEvents = 'none';
        } else {
            autoSlot.style.opacity = '1';
            autoSlot.style.pointerEvents = 'auto';
        }
    },

    /**
     * Refresh all save slot previews
     */
    async refreshSaveSlots() {
        try {
            const saves = await StorageManager.listSaveSlots();

            for (let i = 0; i <= 5; i++) {
                const slot = saves.find(s => s.slotId === i);
                const timeEl = document.getElementById(`slot-${i}-time`);
                const previewEl = document.getElementById(`slot-${i}-preview`);

                if (slot && timeEl && previewEl) {
                    const meta = slot.metadata || {};
                    const date = new Date(slot.timestamp);
                    timeEl.textContent = date.toLocaleString('zh-CN', {
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit'
                    });

                    const modeText = meta.examMode === 'story' ? '剧情模式' :
                        meta.examMode === 'exam' ? '考试模式' : '练习模式';

                    previewEl.innerHTML = `
                        <p><strong>进度:</strong> ${meta.questionProgress || '?'}</p>
                        <p><strong>模式:</strong> ${modeText}</p>
                        <p><strong>等级:</strong> Lv.${meta.level || 1} | HP: ${meta.hp || 100}</p>
                    `;
                } else if (timeEl && previewEl) {
                    timeEl.textContent = '空';
                    previewEl.innerHTML = '<p class="slot-empty">空存档位</p>';
                }
            }
        } catch (e) {
            console.error('[App] Refresh save slots failed:', e);
        }
    },

    /**
     * Handle slot click (save or load based on active tab)
     */
    async handleSlotClick(slotId) {
        const activeTab = document.querySelector('.save-tab.active').dataset.tab;

        // Don't allow saving to auto-save slot manually
        if (activeTab === 'save' && slotId === 0) {
            UIEffects.showToast('自动存档位仅用于自动保存', 'warning');
            return;
        }

        if (activeTab === 'save') {
            // Manual save
            const confirm = window.confirm(`确定要保存到存档 #${slotId} 吗？`);
            if (confirm) {
                const gameData = StorageManager.getGameData();
                gameData.currentQuestionIndex = this.currentQuestionIndex;
                gameData.examMode = this.examMode;
                gameData.currentYear = this.currentYear;
                gameData.selectedYears = this.selectedYears; // Save multi-year selection
                gameData.totalQuestions = this.allQuestions.length;

                const success = await StorageManager.saveToBackend(slotId, gameData);
                if (success) {
                    await this.refreshSaveSlots();
                    UIEffects.showToast(`已保存到存档 #${slotId}`, 'success');
                } else {
                    UIEffects.showToast('保存失败', 'error');
                }
            }
        } else {
            // Load
            const confirm = window.confirm(`确定要读取存档 #${slotId} 吗？当前进度未保存将丢失！`);
            if (confirm) {
                const data = await StorageManager.loadFromBackend(slotId);
                if (data) {
                    this.currentQuestionIndex = data.currentQuestionIndex || 0;
                    this.currentYear = data.currentYear || '2010';
                    this.examMode = data.examMode || 'practice';

                    // Restore multi-year selection
                    if (data.selectedYears && Array.isArray(data.selectedYears)) {
                        this.selectedYears = data.selectedYears;
                    } else {
                        // Fallback for old saves
                        this.selectedYears = [this.currentYear];
                    }

                    // Update checkbox UI
                    document.querySelectorAll('.year-checkbox-item input').forEach(cb => {
                        cb.checked = this.selectedYears.includes(cb.value);
                    });
                    const countSpan = document.getElementById('selected-year-count');
                    if (countSpan) countSpan.textContent = this.selectedYears.length;

                    // Reload year data
                    await this.loadExamData();

                    // Show question or return to start
                    if (this.currentQuestionIndex > 0) {
                        this.showScreen(this.elements.examScreen);
                        this.showQuestion();
                    } else {
                        this.showScreen(this.elements.startScreen);
                    }

                    this.closeSavePanel();
                    UIEffects.showToast(`已读取存档 #${slotId}`, 'success');
                    UIEffects.updateHUD();
                } else {
                    UIEffects.showToast('读取失败：存档不存在', 'error');
                }
            }
        }
    },

    /**
     * Auto-save to slot 0 (called every 5 questions)
     */
    async autoSave() {
        try {
            const gameData = StorageManager.getGameData();
            gameData.currentQuestionIndex = this.currentQuestionIndex;
            gameData.examMode = this.examMode;
            gameData.currentYear = this.currentYear;
            gameData.selectedYears = this.selectedYears; // Save multi-year selection
            gameData.totalQuestions = this.allQuestions.length;

            await StorageManager.saveToBackend(0, gameData);
            console.log('[App] Auto-saved to slot 0');
        } catch (e) {
            console.warn('[App] Auto-save failed:', e);
        }
    },

    /**
     * Return to main menu (preserve progress via auto-save)
     */
    async returnToMainMenu() {
        // Auto-save before leaving
        await this.autoSave();

        // Don't clear answers or reset index
        this.showScreen(this.elements.startScreen);

        // Update continue button
        if (this.currentQuestionIndex > 0 && this.elements.continueBtn) {
            this.elements.continueBtn.style.display = 'inline-block';
        }

        UIEffects.showToast('进度已自动保存', 'success');
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => App.init());

// 导出到全局
window.App = App;
