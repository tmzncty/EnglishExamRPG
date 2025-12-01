/**
 * Gemini Service - AI 服务模块
 * 处理 Google Gemini API 调用，包括划词解释、翻译批改、写作评分
 */

const GeminiService = {
    // API 配置
    API_BASE: 'https://generativelanguage.googleapis.com/v1beta/models',
    MODEL: 'gemini-2.0-flash',

    // Prompt 模板
    PROMPTS: {
        // 划词解释
        wordExplanation: (selectedText, context) => `你是一位专门辅导中国学生的考研英语老师。请解释以下选中的文本：

选中内容："${selectedText}"

上下文段落：
"${context}"

请用中文回答，包含：
1. 词汇/短语的含义
2. 语法结构分析（如果是句子）
3. 在此语境下的具体含义
4. 相关考研高频词汇或搭配（如有）

回答要简洁明了，适合考研学生理解。`,

        // 翻译打分
        translationScoring: (originalText, referenceAnswer, userAnswer) => `请评估以下翻译题的学生答案：

原文（英语）：
"${originalText}"

参考答案：
"${referenceAnswer}"

学生答案：
"${userAnswer}"

请用中文给出评价，格式如下：
📊 得分：X/10

✅ 优点：
（列出翻译中的亮点）

❌ 不足：
（指出翻译中的问题）

📝 改进建议：
（提供具体的修改建议）

🔄 参考改进版：
（给出一个改进后的翻译版本）`,

        // 写作批改
        essayReview: (essayText, topic) => `请批改以下考研英语作文：

${topic ? `题目：${topic}\n` : ''}
学生作文：
"${essayText}"

请用中文给出详细评价，格式如下：
📊 总分：X/20

📋 评分细则：
- 内容与结构：X/5
- 语言表达：X/5  
- 词汇丰富度：X/5
- 语法准确性：X/5

✅ 亮点：
（列出作文中的优秀之处）

❌ 问题与修改：
（指出具体的语法错误、用词不当等，并给出修改建议）

💡 高级表达建议：
（提供可替换的高级词汇和句型）

📝 总体评语：
（总结性建议）`,

        // 长难句分析
        sentenceAnalysis: (sentence) => `请分析以下考研英语长难句：

"${sentence}"

请用中文回答，包含：
1. 🔍 句子主干（主谓宾）
2. 📐 句子结构分析（各从句/修饰成分）
3. 🔑 关键词汇解释
4. 🇨🇳 参考翻译
5. 💡 类似句型的考研真题示例（如有）`
    },

    /**
     * 检查是否配置了 API Key
     */
    isConfigured() {
        return StorageManager.hasApiKey();
    },

    /**
     * 调用 Gemini API
     * @param {string} prompt 提示词
     * @param {function} onStream 流式输出回调 (text) => void
     */
    async callAPI(prompt, onStream = null) {
        const apiKey = StorageManager.getApiKey();
        
        if (!apiKey) {
            throw new Error('请先在设置中配置 Gemini API Key');
        }

        const method = onStream ? 'streamGenerateContent' : 'generateContent';
        const url = `${this.API_BASE}/${this.MODEL}:${method}?key=${apiKey}`;

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    contents: [{
                        parts: [{
                            text: prompt
                        }]
                    }],
                    generationConfig: {
                        temperature: 0.7,
                        maxOutputTokens: 2048
                    }
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                if (response.status === 400) {
                    throw new Error('API Key 无效，请检查设置');
                } else if (response.status === 429) {
                    throw new Error('API 调用频率过高，请稍后再试');
                } else {
                    throw new Error(errorData.error?.message || `API 错误: ${response.status}`);
                }
            }

            if (onStream) {
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';
                let fullText = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    
                    // 简单的流式解析：查找 "text": "..." 模式
                    const regex = /"text":\s*"((?:[^"\\]|\\.)*)"/g;
                    let match;
                    
                    let currentTotalText = '';
                    while ((match = regex.exec(buffer)) !== null) {
                        try {
                            // 反转义 JSON 字符串
                            const text = JSON.parse(`"${match[1]}"`);
                            currentTotalText += text;
                        } catch (e) {
                            // 忽略解析错误
                        }
                    }
                    
                    if (currentTotalText.length > fullText.length) {
                        const newText = currentTotalText.substring(fullText.length);
                        fullText = currentTotalText;
                        onStream(newText);
                    }
                }
                return fullText;
            } else {
                const data = await response.json();
                if (data.candidates && data.candidates[0]?.content?.parts?.[0]?.text) {
                    return data.candidates[0].content.parts[0].text;
                } else {
                    throw new Error('API 返回数据格式异常');
                }
            }
        } catch (error) {
            console.error('[GeminiService] API 调用失败:', error);
            throw error;
        }
    },

    /**
     * 划词解释
     */
    async explainText(selectedText, context = '') {
        const prompt = this.PROMPTS.wordExplanation(selectedText, context);
        return await this.callAPI(prompt);
    },

    /**
     * 翻译题评分
     */
    async scoreTranslation(originalText, referenceAnswer, userAnswer) {
        const prompt = this.PROMPTS.translationScoring(originalText, referenceAnswer, userAnswer);
        return await this.callAPI(prompt);
    },

    /**
     * 写作批改
     */
    async reviewEssay(essayText, topic = '') {
        const prompt = this.PROMPTS.essayReview(essayText, topic);
        return await this.callAPI(prompt);
    },

    /**
     * 长难句分析
     */
    async analyzeSentence(sentence) {
        const prompt = this.PROMPTS.sentenceAnalysis(sentence);
        return await this.callAPI(prompt);
    },

    /**
     * 自定义提问
     */
    async askQuestion(question, context = '') {
        const prompt = context 
            ? `上下文：\n${context}\n\n问题：${question}\n\n请用中文回答。`
            : `${question}\n\n请用中文回答。`;
        return await this.callAPI(prompt);
    },

    /**
     * 单词讲解（结合句子语境）
     */
    async explainWord(word, sentence = '', onStream = null) {
        let prompt = `请详细讲解英语单词 "${word}"：

1. **音标**：给出英式和美式音标
2. **词性与释义**：列出常见词性和对应的中文释义
3. **词根词缀**：分析词根词缀帮助记忆
4. **常见搭配**：给出3-5个常用搭配
5. **例句**：给出2-3个考研真题级别的例句（附中文翻译）
6. **易混词辨析**：如果有容易混淆的词，请对比说明
7. **记忆技巧**：给出一个便于记忆的方法`;

        if (sentence) {
            prompt += `\n\n**语境分析**：请特别分析该单词在以下句子中的用法和含义：
"${sentence}"`;
        }

        prompt += '\n\n请用中文回答，格式清晰。';
        
        return await this.callAPI(prompt, onStream);
    },

    /**
     * 验证 API Key
     */
    async validateApiKey(key) {
        const originalKey = StorageManager.getApiKey();
        
        try {
            // 临时保存新 key 用于测试
            StorageManager.saveApiKey(key);
            
            // 发送测试请求
            await this.callAPI('请回复"OK"');
            
            return { valid: true, message: 'API Key 验证成功！' };
        } catch (error) {
            // 恢复原来的 key
            if (originalKey) {
                StorageManager.saveApiKey(originalKey);
            } else {
                StorageManager.removeApiKey();
            }
            
            return { valid: false, message: error.message };
        }
    }
};

// 导出
window.GeminiService = GeminiService;
