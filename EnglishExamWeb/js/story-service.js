/**
 * Story Service - 从服务器获取预生成的剧情
 */

const StoryService = {
    /**
     * 获取题目剧情
     * @param {number} qId - 题目ID
     * @param {number} year - 年份
     * @param {boolean} isCorrect - 是否答对
     * @param {string} lang - 语言 'cn' 或 'en'
     */
    async getStory(qId, year, isCorrect, lang = 'cn') {
        try {
            const response = await fetch('/api/get_story', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    q_id: qId,
                    year: year,
                    is_correct: isCorrect,
                    lang: lang
                })
            });

            const data = await response.json();
            if (data.success && data.story) {
                return data.story;
            }
            return null;
        } catch (e) {
            console.error('[StoryService] Error fetching story:', e);
            return null;
        }
    },

    /**
     * 显示剧情对话框
     */
    showStory(story, mood = 'normal') {
        if (!story) return;

        // 使用现有的UIEffects剧情系统
        if (window.UIEffects && UIEffects.showStoryDialog) {
            UIEffects.showStoryDialog(story, mood, () => { });
        }
    }
};

window.StoryService = StoryService;
