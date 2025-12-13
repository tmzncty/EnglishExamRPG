/**
 * 遗忘曲线算法 - SuperMemo 2 算法实现
 */

export class LearningAlgorithm {
    /**
     * 计算下次复习时间
     * @param {number} quality - 回答质量 (0-5)
     *   5 - 完美记忆
     *   4 - 犹豫后正确
     *   3 - 困难但正确
     *   2 - 错误但想起来了
     *   1 - 错误且难想起
     *   0 - 完全不记得
     * @param {number} repetition - 已复习次数
     * @param {number} easinessFactor - 容易度因子 (1.3-2.5)
     * @param {number} interval - 上次间隔天数
     * @returns {Object} 包含新的重复次数、容易度因子、间隔和下次复习日期
     */
    static calculateNextReview(quality, repetition, easinessFactor, interval) {
        let newRepetition = repetition;
        let newEasinessFactor = easinessFactor;
        let newInterval = interval;

        // 更新容易度因子
        newEasinessFactor = Math.max(
            1.3,
            easinessFactor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        );

        // 如果质量低于3，重置学习进度
        if (quality < 3) {
            newRepetition = 0;
            newInterval = 0;
        } else {
            newRepetition = repetition + 1;
            
            // 计算新间隔
            if (newRepetition === 1) {
                newInterval = 1;
            } else if (newRepetition === 2) {
                newInterval = 6;
            } else {
                newInterval = Math.round(interval * newEasinessFactor);
            }
        }

        // 计算下次复习日期
        const nextReviewDate = new Date();
        nextReviewDate.setDate(nextReviewDate.getDate() + newInterval);

        return {
            repetition: newRepetition,
            easinessFactor: newEasinessFactor,
            interval: newInterval,
            nextReview: nextReviewDate.toISOString()
        };
    }

    /**
     * 将用户回答转换为质量分数
     * @param {boolean} isCorrect - 是否正确
     * @param {boolean} isEasy - 是否容易（用户反馈）
     * @returns {number} 质量分数
     */
    static answerToQuality(isCorrect, isEasy = null) {
        if (!isCorrect) {
            return 1; // 不认识/错误
        }
        
        if (isEasy === true) {
            return 5; // 认识且容易
        } else if (isEasy === false) {
            return 3; // 认识但有些困难
        } else {
            return 4; // 认识（默认）
        }
    }

    /**
     * 生成今日学习计划
     * @param {Array} words - 词汇列表
     * @param {number} dailyGoal - 每日目标数量
     * @returns {Object} 包含新词和复习词的学习计划
     */
    static generateDailyPlan(words, dailyGoal) {
        const today = new Date().toISOString().split('T')[0];
        
        // 分类词汇
        const reviewWords = [];
        const newWords = [];

        words.forEach(word => {
            if (word.next_review && word.next_review <= today) {
                reviewWords.push(word);
            } else if (!word.next_review) {
                newWords.push(word);
            }
        });

        // 优先复习旧词
        let plan = [...reviewWords];
        
        // 添加新词直到达到目标
        const remaining = dailyGoal - plan.length;
        if (remaining > 0) {
            plan = plan.concat(newWords.slice(0, remaining));
        }

        return {
            reviewWords: reviewWords.length,
            newWords: Math.min(remaining, newWords.length),
            totalWords: plan.length,
            words: this.shuffleArray(plan)
        };
    }

    /**
     * 洗牌算法 - Fisher-Yates
     */
    static shuffleArray(array) {
        const shuffled = [...array];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    }

    /**
     * 检查是否应该结束今日学习
     * @param {string} sleepTime - 睡眠时间 (HH:MM)
     * @returns {boolean} 是否已过睡眠时间
     */
    static shouldEndDay(sleepTime) {
        const now = new Date();
        const [hours, minutes] = sleepTime.split(':').map(Number);
        const sleepDateTime = new Date();
        sleepDateTime.setHours(hours, minutes, 0, 0);

        return now >= sleepDateTime;
    }

    /**
     * 计算学习统计
     * @param {Array} records - 学习记录
     * @returns {Object} 统计数据
     */
    static calculateStats(records) {
        if (records.length === 0) {
            return {
                totalReviews: 0,
                correctRate: 0,
                averageInterval: 0,
                masteredWords: 0
            };
        }

        const totalReviews = records.length;
        const correctCount = records.filter(r => r.is_correct).length;
        const correctRate = (correctCount / totalReviews * 100).toFixed(1);
        
        const intervals = records.filter(r => r.interval > 0).map(r => r.interval);
        const averageInterval = intervals.length > 0
            ? (intervals.reduce((a, b) => a + b, 0) / intervals.length).toFixed(1)
            : 0;
        
        const masteredWords = records.filter(r => r.repetition >= 3 && r.interval >= 21).length;

        return {
            totalReviews,
            correctRate: parseFloat(correctRate),
            averageInterval: parseFloat(averageInterval),
            masteredWords
        };
    }

    /**
     * 获取下一批需要复习的词汇
     * @param {Array} allWords - 所有词汇
     * @param {number} batchSize - 批次大小
     * @returns {Array} 下一批词汇
     */
    static getNextBatch(allWords, batchSize = 10) {
        const today = new Date().toISOString().split('T')[0];
        
        // 过滤出今天需要复习的
        const dueWords = allWords.filter(word => {
            if (!word.next_review) return true; // 新词
            return word.next_review <= today; // 到期的复习词
        });

        // 按优先级排序：最早到期的优先
        dueWords.sort((a, b) => {
            if (!a.next_review) return 1;
            if (!b.next_review) return -1;
            return new Date(a.next_review) - new Date(b.next_review);
        });

        return dueWords.slice(0, batchSize);
    }
}
