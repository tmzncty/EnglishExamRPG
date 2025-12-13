/**
 * AI服务 - Gemini API集成
 */

export class AIService {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.baseUrl = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent';
    }

    /**
     * 生成词汇讲解
     * @param {string} word - 单词
     * @param {string} sentence - 例句
     * @param {string} correctMeaning - 正确释义
     * @param {boolean} isCorrect - 用户是否答对
     */
    async generateExplanation(word, sentence, correctMeaning, isCorrect) {
        if (!this.apiKey) {
            return '请先在设置中配置 Gemini API Key。';
        }

        const prompt = this.buildPrompt(word, sentence, correctMeaning, isCorrect);

        try {
            const response = await fetch(this.baseUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-goog-api-key': this.apiKey,
                },
                body: JSON.stringify({
                    contents: [{
                        parts: [{
                            text: prompt
                        }]
                    }],
                    generationConfig: {
                        temperature: 0.7,
                        maxOutputTokens: 800,
                    }
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(`API请求失败: ${response.status} - ${errorData.error?.message || response.statusText}`);
            }

            const data = await response.json();
            const explanation = data.candidates[0].content.parts[0].text;
            
            return this.formatExplanation(explanation);
        } catch (error) {
            console.error('AI讲解生成失败:', error);
            return `生成讲解时出错：${error.message}\n\n基础释义：${correctMeaning}`;
        }
    }

    /**
     * 构建提示词
     */
    buildPrompt(word, sentence, correctMeaning, isCorrect) {
        const userStatus = isCorrect ? '答对了' : '答错了';
        
        return `你是一个英语学习助手，请用简洁、有趣的方式讲解以下单词。

**单词**: ${word}
**正确释义**: ${correctMeaning}
**例句**: ${sentence}
**学生状态**: ${userStatus}

请提供：
1. 📖 **基础释义**：简单明了的中文解释
2. 🎯 **在例句中的用法**：解释这个词在例句中的含义和作用
3. 💡 **记忆技巧**：提供一个有趣的记忆方法（联想、词根、谐音等）
4. 📝 **常见搭配**：2-3个常用短语或搭配

${!isCorrect ? '5. ⚠️ **易错提示**：为什么这个词容易混淆，如何避免错误' : ''}

请用轻松、鼓励的语气，像朋友一样讲解。内容控制在200字以内。`;
    }

    /**
     * 格式化讲解内容
     */
    formatExplanation(rawText) {
        // 清理markdown格式，保留emoji和基本结构
        let formatted = rawText.trim();
        
        // 移除过多的markdown标记
        formatted = formatted.replace(/\*\*\*/g, '');
        formatted = formatted.replace(/\*\*/g, '');
        
        return formatted;
    }

    /**
     * 批量生成讲解（带缓存）
     */
    async batchGenerateExplanations(wordSentencePairs, db) {
        const results = [];
        
        for (const pair of wordSentencePairs) {
            const { wordId, sentenceId, word, sentence, meaning } = pair;
            
            // 检查缓存
            const cached = db.getExplanation(wordId, sentenceId);
            if (cached) {
                results.push({ wordId, sentenceId, explanation: cached, fromCache: true });
                continue;
            }

            // 生成新讲解
            const explanation = await this.generateExplanation(word, sentence, meaning, true);
            
            // 保存到缓存
            db.addExplanation(wordId, sentenceId, explanation);
            
            results.push({ wordId, sentenceId, explanation, fromCache: false });
            
            // 避免API限流
            await this.delay(1000);
        }

        return results;
    }

    /**
     * 延迟函数
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * 更新API Key
     */
    updateApiKey(newKey) {
        this.apiKey = newKey;
    }

    /**
     * 验证API Key
     */
    async validateApiKey() {
        if (!this.apiKey) return false;

        try {
            const response = await fetch(`${this.baseUrl}?key=${this.apiKey}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    contents: [{
                        parts: [{
                            text: 'Hello'
                        }]
                    }]
                })
            });

            return response.ok;
        } catch (error) {
            console.error('API Key验证失败:', error);
            return false;
        }
    }
}

export let aiService = new AIService(null);

export function initAIService(apiKey) {
    aiService = new AIService(apiKey);
    return aiService;
}
