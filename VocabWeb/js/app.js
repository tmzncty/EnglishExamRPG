/**
 * 主应用程序
 */

import { db } from './db.js';
import { LearningAlgorithm } from './learning-algorithm.js';
import { aiService, initAIService } from './ai-service.js';
import { notificationManager } from './notification.js';

class VocabApp {
    constructor() {
        this.currentWords = [];
        this.currentIndex = 0;
        this.currentWord = null;
        this.currentSentence = null;
        this.selectedOption = null;
        this.stats = null;
        this.settings = {};
    }

    async init() {
        console.log('初始化应用...');
        
        // 初始化数据库
        await db.init();
        console.log('数据库初始化完成');

        // 加载设置
        await this.loadSettings();

        // 初始化AI服务
        const apiKey = db.getSetting('geminiApiKey');
        if (apiKey) {
            initAIService(apiKey);
        }

        // 加载统计数据
        this.updateStats();

        // 初始化UI
        this.initUI();

        // 请求通知权限
        if (this.settings.notificationEnabled === 'true') {
            await notificationManager.requestPermission();
        }

        // 开始学习
        await this.loadTodayWords();
    }

    async loadSettings() {
        this.settings = {
            dailyGoal: parseInt(db.getSetting('dailyGoal') || '20'),
            sleepTime: db.getSetting('sleepTime') || '23:00',
            notificationEnabled: db.getSetting('notificationEnabled') || 'false',
            notificationTime: db.getSetting('notificationTime') || '20:00',
            geminiApiKey: db.getSetting('geminiApiKey') || ''
        };

        // 更新UI
        document.getElementById('dailyGoal').value = this.settings.dailyGoal;
        document.getElementById('sleepTime').value = this.settings.sleepTime;
        document.getElementById('notificationEnabled').checked = this.settings.notificationEnabled === 'true';
        document.getElementById('notificationTime').value = this.settings.notificationTime;
        if (this.settings.geminiApiKey) {
            document.getElementById('geminiApiKey').value = this.settings.geminiApiKey;
        }
    }

    initUI() {
        // 设置按钮
        document.getElementById('settingsBtn').addEventListener('click', () => {
            document.getElementById('settingsModal').classList.add('active');
        });

        document.getElementById('closeSettings').addEventListener('click', () => {
            document.getElementById('settingsModal').classList.remove('active');
        });

        // 保存设置
        document.getElementById('saveSettings').addEventListener('click', () => {
            this.saveSettings();
        });

        // 导出/导入数据
        document.getElementById('exportData').addEventListener('click', () => {
            db.exportDB();
        });

        document.getElementById('importData').addEventListener('click', () => {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.db';
            input.onchange = async (e) => {
                const file = e.target.files[0];
                if (file) {
                    try {
                        await db.importDB(file);
                        alert('数据导入成功！页面即将刷新。');
                        location.reload();
                    } catch (error) {
                        alert('数据导入失败：' + error.message);
                    }
                }
            };
            input.click();
        });

        // 答题相关
        document.getElementById('showAnswerBtn').addEventListener('click', () => {
            this.showAnswer();
        });

        document.getElementById('explainBtn').addEventListener('click', () => {
            this.showExplanation();
        });

        document.getElementById('nextBtn').addEventListener('click', () => {
            this.handleAnswer();
        });

        document.getElementById('prevBtn')?.addEventListener('click', () => {
            this.showPreviousQuestion();
        });
    }

    async loadTodayWords() {
        console.log('加载今日词汇...');
        const dailyGoal = this.settings.dailyGoal;
        
        // 获取错题（最多占20%）
        const mistakeCount = Math.min(Math.floor(dailyGoal * 0.2), db.getMistakeCount());
        const mistakeWords = db.getMistakeWords(mistakeCount);
        
        // 获取新词和复习词
        const normalWords = db.getTodayWords(dailyGoal - mistakeCount);
        
        // 合并并打乱顺序
        this.currentWords = [...normalWords, ...mistakeWords];
        this.currentWords = this.shuffleArray(this.currentWords);
        
        console.log(`📚 今日学习: ${normalWords.length}个常规词 + ${mistakeWords.length}个错题`);
        
        if (this.currentWords.length === 0) {
            this.showCompletionMessage();
            return;
        }

        this.currentIndex = 0;
        this.showQuestion();
        this.updateProgress();
    }

    shuffleArray(array) {
        const shuffled = [...array];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    }

    showPreviousQuestion() {
        if (this.currentIndex > 0) {
            this.currentIndex--;
            this.showQuestion();
        } else {
            alert('已经是第一题了！');
        }
    }

    showQuestion() {
        if (this.currentIndex >= this.currentWords.length) {
            this.showCompletionMessage();
            return;
        }

        const wordData = this.currentWords[this.currentIndex];
        this.currentWord = wordData;
        this.currentSentence = {
            id: wordData.sentence_id,
            sentence: wordData.sentence,
            translation: wordData.translation,
            year: wordData.sentence_year,
            questionNumber: wordData.sentence_question_number,
            sectionName: wordData.sentence_section_name,
            sectionType: wordData.sentence_section_type,
            examType: wordData.sentence_exam_type,
            questionRange: wordData.sentence_question_range,
            questionLabel: wordData.sentence_question_label,
            sourceLabel: wordData.sentence_source_label,
            questionText: wordData.sentence_question_text
        };

        // 重置UI
        document.getElementById('optionsContainer').innerHTML = '';
        document.getElementById('showAnswerBtn').style.display = 'block';
        document.getElementById('explainBtn').style.display = 'none';
        document.getElementById('resultButtons').style.display = 'none';
        document.getElementById('explanationContainer').style.display = 'none';
        this.selectedOption = null;

        // 显示句子
        document.getElementById('sentenceText').textContent = wordData.sentence;
        document.getElementById('sentenceHint').textContent = this.formatSentenceHint(this.currentSentence);
        document.getElementById('targetWord').textContent = wordData.word;

        // 生成选项
        this.generateOptions(wordData.id, wordData.meaning);

        // 更新题号
        document.getElementById('questionNumber').textContent = 
            `${this.currentIndex + 1}/${this.currentWords.length}`;
    }

    formatSentenceHint(sentenceMeta) {
        if (!sentenceMeta) {
            return '';
        }

        const translation = (sentenceMeta.translation || '').trim();
        const metaParts = [];
        const examPart = [sentenceMeta.year, sentenceMeta.examType].filter(Boolean).join(' ').trim();
        if (examPart) {
            metaParts.push(examPart);
        }
        if (sentenceMeta.sectionName) {
            metaParts.push(sentenceMeta.sectionName);
        }
        if (sentenceMeta.questionLabel) {
            metaParts.push(sentenceMeta.questionLabel);
        } else if (sentenceMeta.questionRange) {
            metaParts.push(sentenceMeta.questionRange);
        }
        if (!metaParts.length && sentenceMeta.sourceLabel) {
            metaParts.push(sentenceMeta.sourceLabel);
        }

        const metaText = metaParts.join(' · ');
        return [translation, metaText].filter(Boolean).join('  |  ');
    }

    generateOptions(correctWordId, correctMeaning) {
        const options = [correctMeaning];
        
        // 随机获取3个错误选项
        const wrongOptions = db.db.exec(`
            SELECT DISTINCT meaning FROM vocabulary 
            WHERE id != ${correctWordId} 
            ORDER BY RANDOM() 
            LIMIT 3
        `);

        if (wrongOptions.length > 0) {
            wrongOptions[0].values.forEach(row => {
                options.push(row[0]);
            });
        }

        // 洗牌
        const shuffled = LearningAlgorithm.shuffleArray(options);

        // 渲染选项
        const container = document.getElementById('optionsContainer');
        shuffled.forEach((option, index) => {
            const button = document.createElement('button');
            button.className = 'option-btn';
            button.textContent = option;
            button.dataset.meaning = option;
            button.dataset.isCorrect = option === correctMeaning;
            
            button.addEventListener('click', () => {
                this.selectOption(button);
            });

            container.appendChild(button);
        });
    }

    selectOption(button) {
        // 清除之前的选择
        document.querySelectorAll('.option-btn').forEach(btn => {
            btn.classList.remove('selected');
        });

        button.classList.add('selected');
        this.selectedOption = button;
    }

    showAnswer() {
        if (!this.selectedOption) {
            alert('请先选择一个答案！');
            return;
        }

        const isCorrect = this.selectedOption.dataset.isCorrect === 'true';
        
        // 显示正确/错误状态
        document.querySelectorAll('.option-btn').forEach(btn => {
            btn.disabled = true;
            if (btn.dataset.isCorrect === 'true') {
                btn.classList.add('correct');
            } else if (btn === this.selectedOption && !isCorrect) {
                btn.classList.add('wrong');
            }
        });

        // 显示控制按钮
        document.getElementById('showAnswerBtn').style.display = 'none';
        document.getElementById('explainBtn').style.display = 'block';
        document.getElementById('resultButtons').style.display = 'flex';

        // 记录是否正确（暂存）
        this.currentWord.userAnswer = isCorrect;
    }

    async showExplanation() {
        const container = document.getElementById('explanationContainer');
        const content = document.getElementById('explanationContent');
        
        container.style.display = 'block';
        content.innerHTML = '<div class="loading"></div> 正在生成讲解...';

        // 检查缓存
        let explanation = db.getExplanation(this.currentWord.id, this.currentSentence.id);

        if (!explanation) {
            // 生成新讲解
            explanation = await aiService.generateExplanation(
                this.currentWord.word,
                this.currentSentence.sentence,
                this.currentWord.meaning,
                this.currentWord.userAnswer
            );

            // 保存到缓存
            if (explanation && !explanation.includes('生成讲解时出错')) {
                db.addExplanation(this.currentWord.id, this.currentSentence.id, explanation);
            }
        } else {
            console.log('✅ 使用缓存的AI讲解');
        }

        content.textContent = explanation;
    }

    handleAnswer() {
        const isKnown = this.currentWord.userAnswer;
        // 计算复习参数
        const quality = LearningAlgorithm.answerToQuality(isKnown);
        
        // 获取之前的学习记录
        const record = db.getLearningRecord(this.currentWord.id, this.currentSentence.id);
        
        const repetition = record?.repetition || 0;
        const easinessFactor = record?.easiness_factor || 2.5;
        const interval = record?.interval || 0;

        // 计算下次复习时间
        const nextReview = LearningAlgorithm.calculateNextReview(
            quality, repetition, easinessFactor, interval
        );

        // 保存学习记录
        if (!record) {
            db.addLearningRecord(this.currentWord.id, this.currentSentence.id, isKnown);
        }
        
        db.updateLearningRecord(
            this.currentWord.id,
            this.currentSentence.id,
            nextReview.repetition,
            nextReview.easinessFactor,
            nextReview.interval,
            nextReview.nextReview,
            isKnown
        );

        // 更新统计
        this.updateStats();

        // 下一题
        this.currentIndex++;
        
        setTimeout(() => {
            this.showQuestion();
            this.updateProgress();
        }, 500);
    }

    showCompletionMessage() {
        const stats = db.getTodayStats();
        const mistakeCount = db.getMistakeCount();
        
        document.getElementById('learningView').innerHTML = `
            <div class="card learning-card" style="text-align: center; padding: 60px 30px;">
                <h1 style="font-size: 3rem; margin-bottom: 20px;">🎉</h1>
                <h2 style="color: var(--primary-color); margin-bottom: 20px;">太棒了！今日学习完成！</h2>
                <div style="font-size: 1.2rem; color: var(--text-secondary); margin-bottom: 30px;">
                    <p>✨ 学习了 <strong>${stats.learnedToday}</strong> 个新词</p>
                    <p>📚 复习了 <strong>${stats.reviewedToday}</strong> 个单词</p>
                    <p>🎯 正确率 <strong>${stats.accuracy}%</strong></p>
                    ${mistakeCount > 0 ? `<p style="color: #ff6b6b;">📋 错题本: <strong>${mistakeCount}</strong> 个待复习</p>` : ''}
                </div>
                <button class="btn btn-primary" onclick="location.reload()">继续学习</button>
            </div>
        `;

        // 发送完成通知
        if (this.settings.notificationEnabled === 'true') {
            notificationManager.sendCompletionNotification(stats);
        }
    }

    updateProgress() {
        const total = this.currentWords.length;
        const current = this.currentIndex;
        document.getElementById('todayProgress').textContent = `${current}/${total}`;
    }

    updateStats() {
        this.stats = db.getTodayStats();
        const totalWords = db.getTotalWords();
        const mistakeCount = db.getMistakeCount();

        document.getElementById('learnedToday').textContent = this.stats.learnedToday;
        document.getElementById('reviewToday').textContent = this.stats.reviewedToday;
        document.getElementById('totalLearned').textContent = this.stats.totalLearned;
        document.getElementById('accuracy').textContent = this.stats.accuracy + '%';
        document.getElementById('totalWords').textContent = totalWords;
        
        // 更新错题数量显示
        const mistakeElement = document.getElementById('mistakeCount');
        if (mistakeElement) {
            mistakeElement.textContent = mistakeCount;
        }
    }

    saveSettings() {
        const dailyGoal = document.getElementById('dailyGoal').value;
        const sleepTime = document.getElementById('sleepTime').value;
        const notificationEnabled = document.getElementById('notificationEnabled').checked;
        const notificationTime = document.getElementById('notificationTime').value;
        const geminiApiKey = document.getElementById('geminiApiKey').value;

        db.setSetting('dailyGoal', dailyGoal);
        db.setSetting('sleepTime', sleepTime);
        db.setSetting('notificationEnabled', notificationEnabled.toString());
        db.setSetting('notificationTime', notificationTime);
        
        if (geminiApiKey) {
            db.setSetting('geminiApiKey', geminiApiKey);
            initAIService(geminiApiKey);
        }

        this.settings = {
            dailyGoal: parseInt(dailyGoal),
            sleepTime,
            notificationEnabled: notificationEnabled.toString(),
            notificationTime,
            geminiApiKey
        };

        document.getElementById('settingsModal').classList.remove('active');
        alert('设置已保存！');

        // 重新设置通知
        if (notificationEnabled) {
            notificationManager.checkDailyReminder(this.settings, this.currentWords.length);
        }
    }
}

// 启动应用
const app = new VocabApp();

// 等待DOM加载完成
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => app.init());
} else {
    app.init();
}

export default app;
