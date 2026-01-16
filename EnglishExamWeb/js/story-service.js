/**
 * Story Service - 从JSON/API获取预生成的剧情
 * 优先级：JSON文件 > API > Static fallback
 */

const StoryService = {
    storiesData: null,  // 缓存JSON数据

    /**
     * 加载预生成的剧情JSON
     */
    /**
     * 加载预生成的剧情JSON
     */
    async loadStoriesJSON() {
        // Skip JSON loading to avoid 404s, prefer API directly
        return null;

        /* 
        if (this.storiesData) return this.storiesData;

        try {
            const response = await fetch('/data/stories.json');
            if (response.ok) {
                this.storiesData = await response.json();
                console.log('[StoryService] Loaded pregenerated stories:', Object.keys(this.storiesData).length);
                return this.storiesData;
            }
        } catch (e) {
            console.log('[StoryService] JSON not available, will use API/fallback');
        }
        return null;
        */
    },

    /**
     * 获取题目剧情（优先JSON）
     * @param {number} qId - 题目ID
     * @param {number} year - 年份
     * @param {boolean} isCorrect - 是否答对
     * @param {string} lang - 语言 'cn', 'en', 或 'both'
     */
    async getStory(qId, year, isCorrect, lang = 'both') {
        // 1. 尝试从JSON加载
        await this.loadStoriesJSON();

        if (this.storiesData) {
            const key = `${year}_${qId}`;
            const story = this.storiesData[key];

            if (story) {
                const storyText = isCorrect ? story.correct : story.wrong;

                // 返回双语或单语
                if (lang === 'both') {
                    return {
                        cn: storyText.cn,
                        en: storyText.en,
                        bilingual: true
                    };
                } else {
                    return storyText[lang];
                }
            }
        }

        // 2. 尝试从API获取
        try {
            const response = await fetch('/api/get_story', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    q_id: qId,
                    year: year,
                    is_correct: isCorrect,
                    lang: lang // Pass 'both' or 'cn'/'en' directly
                })
            });

            const data = await response.json();
            if (data.success && data.story) {
                return data.story;
            }
        } catch (e) {
            console.error('[StoryService] API error:', e);
        }

        // 3. Fallback到静态
        return null;
    },

    /**
     * 显示剧情对话框（支持双语）
     */
    showStory(story, mood = 'normal') {
        if (!story) return;

        let displayText = '';

        // 如果是双语对象
        if (story.bilingual && story.cn && story.en) {
            displayText = `${story.cn}\n\n---\n\n${story.en}`;
        } else if (typeof story === 'string') {
            displayText = story;
        } else {
            displayText = story.cn || story.en || '';
        }

        // 使用现有的UIEffects剧情系统
        if (window.UIEffects && UIEffects.showStoryDialog) {
            UIEffects.showStoryDialog(displayText, mood, () => { });
        }
    }
};

window.StoryService = StoryService;
