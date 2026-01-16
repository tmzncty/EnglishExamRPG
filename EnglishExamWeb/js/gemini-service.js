/**
 * Gemini Service - AI 服务模块
 * 处理 Google Gemini API 调用，包括划词解释、翻译批改、写作评分
 */

/**
 * AI Service - 通用 AI 服务模块
 * 支持 Google Gemini API 和 OpenAI 兼容接口 (如 DeepSeek, ChatGPT 等)
 */

const AIService = {
    // 默认配置
    defaultConfig: {
        provider: 'gemini', // 'gemini' | 'openai'
        baseUrl: 'https://generativelanguage.googleapis.com/v1beta/models', // Gemini Default
        model: 'gemini-2.0-flash',
        apiKey: '',
        openaiBaseUrl: 'https://api.openai.com/v1', // OpenAI Default
        openaiModel: 'gpt-3.5-turbo'
    },

    // Prompt 模板
    PROMPTS: {
        wordExplanation: (selectedText, context) => `你是一位专门辅导中国学生的考研英语老师。请解释以下选中的文本：\n选中内容："${selectedText}"\n上下文段落：\n"${context}"\n请用中文回答，包含：1. 词汇/短语的含义 2. 语法结构分析（如果是句子） 3. 在此语境下的具体含义 4. 相关考研高频词汇或搭配。\n回答要简洁明了。`,
        translationScoring: (originalText, referenceAnswer, userAnswer) => `请评估以下翻译题的学生答案：\n原文：${originalText}\n参考答案：${referenceAnswer}\n学生答案：${userAnswer}\n请用中文给出评分（X/10），列出优缺点和改进建议。`,
        essayReview: (essayText, topic) => `请批改以下考研英语作文：\n题目：${topic || '无'}\n学生作文：${essayText}\n请给出评分（X/20），从内容、语言、词汇、语法四个维度打分评价，并给出修改建议。`,
        sentenceAnalysis: (sentence) => `请分析以下考研英语长难句：\n"${sentence}"\n请包含：1. 句子主干 2. 结构分析 3. 关键词解释 4. 参考翻译。`,
        test: () => 'Hello, are you online? Reply with "OK".'
    },

    /**
     * 获取当前配置
     */
    getConfig() {
        // Read from localStorage
        const saved = StorageManager.getAISettings?.() || {};
        const legacyKey = StorageManager.getApiKey();

        // Legacy compatibility: if no saved provider but has legacy key, use Gemini
        if (!saved.apiKey && legacyKey) {
            saved.apiKey = legacyKey;
            saved.provider = 'gemini';
        }

        // PRIORITY LOGIC: If both OpenAI and Gemini keys exist, prefer OpenAI
        const aiSettings = JSON.parse(localStorage.getItem('ai_settings') || '{}');
        const hasOpenAIKey = aiSettings.provider === 'openai' && aiSettings.apiKey;
        const hasGeminiKey = (aiSettings.provider === 'gemini' && aiSettings.apiKey) || legacyKey;

        // If user has configured OpenAI, use it (higher priority)
        if (hasOpenAIKey) {
            return {
                ...this.defaultConfig,
                provider: 'openai',
                apiKey: aiSettings.apiKey,
                openaiBaseUrl: aiSettings.openaiBaseUrl || this.defaultConfig.openaiBaseUrl,
                openaiModel: aiSettings.openaiModel || this.defaultConfig.openaiModel
            };
        }

        // Fallback to saved config or default
        return { ...this.defaultConfig, ...saved };
    },

    isConfigured() {
        const config = this.getConfig();
        return !!config.apiKey;
    },

    /**
     * 统一 API 调用入口
     * @param {string|array} prompt - 字符串prompt或消息数组 [{role, content}, ...]
     * @param {boolean} useConversation - 是否使用对话模式（传入消息数组）
     * @param {function} onStream - 流式回调
     */
    async callAPI(prompt, useConversation = false, onStream = null) {
        const config = this.getConfig();
        if (!config.apiKey) throw new Error('请先在设置中配置 API Key');

        // For conversation mode, don't cache
        const isConversation = useConversation && Array.isArray(prompt);

        // 尝试读取缓存 (仅针对非流式调用，或者是流式但我们想优化？目前仅缓存非流式)
        if (!onStream && !isConversation) {
            const cacheKey = typeof prompt === 'string' ? prompt : JSON.stringify(prompt);
            try {
                const cacheRes = await fetch('/api/get_cached_ai', {
                    method: 'POST',
                    body: JSON.stringify({ prompt: cacheKey })
                });
                const cacheData = await cacheRes.json();
                if (cacheData.success && cacheData.cached) {
                    console.log('[AI Cache] Hit!');
                    return cacheData.response;
                }
            } catch (e) { console.warn('Cache check failed', e); }
        }

        let responseText;
        if (config.provider === 'openai') {
            responseText = await this.callOpenAI(config, prompt, isConversation, onStream);
        } else {
            responseText = await this.callGemini(config, prompt, isConversation, onStream);
        }

        // 写入缓存 (仅主要成功的文本，且非流式，或者我们让流式返回全文本)
        // 注意：callOpenAI 和 callGemini 在 stream 模式下返回的是 fullText (promise resolves to full string)
        // 所以我们可以统一缓存
        if (responseText && typeof responseText === 'string' && !isConversation) {
            const cacheKey = typeof prompt === 'string' ? prompt : JSON.stringify(prompt);
            try {
                fetch('/api/cache_ai', {
                    method: 'POST',
                    body: JSON.stringify({
                        prompt: cacheKey,
                        response: responseText,
                        provider: config.provider,
                        model: config.model || config.openaiModel
                    })
                });
            } catch (e) { console.warn('Cache write failed', e); }
        }

        return responseText;
    },

    // ========== Gemini 实现 ==========
    async callGemini(config, prompt, isConversation, onStream) {
        const method = onStream ? 'streamGenerateContent' : 'generateContent';
        let baseUrl = config.baseUrl || this.defaultConfig.baseUrl;
        if (baseUrl.endsWith('/')) baseUrl = baseUrl.slice(0, -1);

        const model = config.model || this.defaultConfig.model;
        const url = `${baseUrl}/${model}:${method}?key=${config.apiKey}`;

        // Build request body based on conversation mode
        let requestBody;
        if (isConversation && Array.isArray(prompt)) {
            // Convert to Gemini format
            const contents = prompt.map(msg => ({
                role: msg.role === 'assistant' ? 'model' : 'user',
                parts: [{ text: msg.content }]
            }));
            requestBody = {
                contents: contents,
                generationConfig: { temperature: 0.7 }
            };
        } else {
            // Single prompt
            const textPrompt = typeof prompt === 'string' ? prompt : prompt[0]?.content || '';
            requestBody = {
                contents: [{ parts: [{ text: textPrompt }] }],
                generationConfig: { temperature: 0.7 }
            };
        }

        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) this.handleError(response);

        if (onStream) {
            return await this.handleGeminiStream(response, onStream);
        } else {
            const data = await response.json();
            return data.candidates?.[0]?.content?.parts?.[0]?.text || '无响应内容';
        }
    },

    async handleGeminiStream(response, onStream) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let fullText = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const regex = /"text":\s*"((?:[^"\\]|\\.)*)"/g;
            let match;
            let currentTotalText = '';
            while ((match = regex.exec(buffer)) !== null) {
                try {
                    const text = JSON.parse(`"${match[1]}"`);
                    currentTotalText += text;
                } catch (e) { }
            }
            if (currentTotalText.length > fullText.length) {
                const newText = currentTotalText.substring(fullText.length);
                fullText = currentTotalText;
                onStream(newText);
            }
        }
        return fullText;
    },

    // ========== OpenAI 兼容实现 ==========
    async callOpenAI(config, prompt, isConversation, onStream) {
        let baseUrl = config.openaiBaseUrl || this.defaultConfig.openaiBaseUrl;
        if (baseUrl.endsWith('/')) baseUrl = baseUrl.slice(0, -1);
        if (!baseUrl.endsWith('/chat/completions')) {
            baseUrl = `${baseUrl}/chat/completions`;
        }

        // Build messages array
        let messages;
        if (isConversation && Array.isArray(prompt)) {
            // Already in message format
            messages = prompt;
        } else {
            // Single prompt - wrap as user message
            const textPrompt = typeof prompt === 'string' ? prompt : prompt[0]?.content || '';
            messages = [{ role: 'user', content: textPrompt }];
        }

        const response = await fetch(baseUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${config.apiKey}`
            },
            body: JSON.stringify({
                model: config.openaiModel || 'gpt-3.5-turbo',
                messages: messages,
                stream: !!onStream,
                temperature: 0.7
            })
        });

        if (!response.ok) this.handleError(response);

        if (onStream) {
            return await this.handleOpenAIStream(response, onStream);
        } else {
            const data = await response.json();
            return data.choices?.[0]?.message?.content || '无响应内容';
        }
    },

    async handleOpenAIStream(response, onStream) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullText = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            for (const line of lines) {
                if (line.startsWith('data: ') && line !== 'data: [DONE]') {
                    try {
                        const data = JSON.parse(line.slice(6));
                        const content = data.choices[0]?.delta?.content || '';
                        if (content) {
                            fullText += content;
                            onStream(content);
                        }
                    } catch (e) { }
                }
            }
        }
        return fullText;
    },

    async handleError(response) {
        let msg = `API Error: ${response.status}`;
        try {
            const err = await response.json();
            msg = err.error?.message || msg;
        } catch (e) { }
        throw new Error(msg);
    },

    // ========== 业务封装 ==========
    async explainText(text, context) {
        return await this.callAPI(this.PROMPTS.wordExplanation(text, context));
    },
    async scoreTranslation(o, r, u) {
        return await this.callAPI(this.PROMPTS.translationScoring(o, r, u));
    },
    async reviewEssay(e, t) {
        return await this.callAPI(this.PROMPTS.essayReview(e, t));
    },
    async analyzeSentence(s) {
        return await this.callAPI(this.PROMPTS.sentenceAnalysis(s));
    },
    async testConnection(config) {
        // 使用临时配置进行测试
        const originalGet = this.getConfig;
        this.getConfig = () => config; // Mock getConfig
        try {
            const res = await this.callAPI(this.PROMPTS.test());
            this.getConfig = originalGet; // Restore
            return { success: true, message: `连接成功！回复: ${res.substring(0, 20)}...` };
        } catch (e) {
            this.getConfig = originalGet; // Restore
            return { success: false, message: e.message };
        }
    },

    /**
     * 验证 Gemini API Key
     */
    async validateApiKey(key) {
        try {
            // Simple validation by listing models or small generation
            const url = `https://generativelanguage.googleapis.com/v1beta/models?key=${key}`;
            const response = await fetch(url);
            const data = await response.json();

            if (!response.ok) {
                return { valid: false, message: data.error?.message || '验证失败' };
            }

            // Check if user's configured model is in the list (Optional, just return success)
            return { valid: true, model: 'gemini-2.0-flash (Default)', message: '验证成功' };
        } catch (e) {
            return { valid: false, message: '网络错误: ' + e.message };
        }
    },

    /**
     * 验证 OpenAI 配置
     */
    async validateOpenAI(config) {
        try {
            let baseUrl = config.openaiBaseUrl;
            if (baseUrl.endsWith('/')) baseUrl = baseUrl.slice(0, -1);
            if (!baseUrl.endsWith('/chat/completions')) {
                baseUrl = `${baseUrl}/chat/completions`;
            }

            console.log('[GeminiService] Validating OpenAI:', baseUrl, config.openaiModel);

            const response = await fetch(baseUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${config.openaiApiKey}`
                },
                body: JSON.stringify({
                    model: config.openaiModel,
                    messages: [{ role: 'user', content: 'Hi' }],
                    max_tokens: 5,
                    stream: false
                })
            });

            if (!response.ok) {
                let msg = `Error ${response.status}`;
                try {
                    const err = await response.json();
                    msg = err.error?.message || JSON.stringify(err);
                } catch (e) {
                    try { msg = await response.text(); } catch (z) { }
                }
                // Check for gateway errors
                if (msg.includes('received empty response') || msg.includes('request id')) {
                    return { valid: false, message: `服务商返回错误 (Upstream Error): ${msg}` };
                }
                return { valid: false, message: msg };
            }

            const data = await response.json();
            const returnedModel = data.model || config.openaiModel;

            return {
                valid: true,
                model: returnedModel,
                message: `验证成功！模型: ${returnedModel}`
            };
        } catch (e) {
            return { valid: false, message: '本地请求失败 (Network Error): ' + e.message };
        }
    }
};

// 保持向下兼容
window.GeminiService = AIService;
window.AIService = AIService;
