import { defineStore } from 'pinia'
import request from '../utils/request'

// [T1] Persistent collapsed state helper
const STORAGE_KEY = 'mia_collapsed'

function loadCollapsed() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) ?? false }
    catch { return false }
}

function saveCollapsed(val) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(val))
}

export const useMiaStore = defineStore('mia', {
    state: () => ({
        dialogVisible: true,
        currentText: "你好，绯墨！准备好今天的挑战了吗？",
        isTyping: false,
        history: [],
        conversationId: null,
        conversationList: [],
        showHistoryPanel: false,
        // [T1] 平板/考试模式下收起 Mia (立绘 + 对话框)
        miaCollapsed: loadCollapsed(),
        // [T1] 是否由自动收起触发 (若用户手动展开则不再自动收起)
        autoCollapsed: false,
    }),

    actions: {
        // [T1] 切换 Mia 立绘+对话框 的收起/展开
        toggleMiaCollapsed() {
            this.miaCollapsed = !this.miaCollapsed
            this.autoCollapsed = false // 手动操作，取消自动标记
            saveCollapsed(this.miaCollapsed)
        },
        // [T1] 自动收起 (仅当未被手动展开)
        autoCollapseMia() {
            if (!this.miaCollapsed) {
                this.miaCollapsed = true
                this.autoCollapsed = true
                saveCollapsed(true)
            }
        },
        // [T1] 自动展开 (仅当之前由自动收起触发)
        autoExpandMia() {
            if (this.autoCollapsed) {
                this.miaCollapsed = false
                this.autoCollapsed = false
                saveCollapsed(false)
            }
        },

        async speak(text) {
            this.dialogVisible = true
            this.isTyping = true
            this.currentText = ''
            const speed = 20
            for (let i = 0; i < text.length; i++) {
                this.currentText += text[i]
                if (i % 3 === 0) await new Promise(r => setTimeout(r, speed))
            }
            this.isTyping = false
            this.history.push({ role: 'assistant', content: text })
        },

        startNewChat() {
            this.conversationId = null
            this.history = []
            this.currentText = "让我们开始新的话题吧！"
            this.showHistoryPanel = false
        },

        async fetchHistory() {
            try {
                const res = await request.get('/mia/conversations')
                this.conversationList = res || []
                this.showHistoryPanel = true
            } catch (e) {
                console.error("Failed to fetch history", e)
            }
        },

        async loadConversation(id) {
            try {
                this.isTyping = true
                const res = await request.get(`/mia/conversations/${id}`)
                if (res) {
                    this.conversationId = res.id
                    this.history = (res.messages || []).map(m => ({
                        role: m.role === 'user' ? 'user' : 'assistant',
                        content: m.content
                    }))

                    const lastMia = [...this.history].reverse().find(m => m.role === 'assistant')
                    if (lastMia) this.currentText = lastMia.content
                }
                this.showHistoryPanel = false
            } catch (e) {
                console.error("Failed to load conversation", e)
            } finally {
                this.isTyping = false
            }
        },

        // --- Stream-Based Interact ---
        async interact(contextType, contextData) {
            try {
                this.isTyping = true
                this.currentText = "..."

                const safeContext = (typeof contextData === 'string')
                    ? { message: contextData }
                    : (contextData || {})

                // [Stage 31.0] 动态获取 attempt_id 和 word_id
                let attemptId = null
                let wordId = null
                if (contextType === 'exam') {
                    const { useExamStore } = await import('./useExamStore')
                    attemptId = useExamStore().attemptId
                } else if (contextType === 'vocab') {
                    const { useVocabStore } = await import('./useVocabStore')
                    const wordObj = useVocabStore().currentWord
                    if (wordObj) wordId = wordObj.word
                }

                // Prepare Payload
                // 历史窗口：最多保留最近 8 条 (4轮对话)，避免 token 爆炸导致超时
                // slice(0, -1) 去掉「当前用户消息」（后端从 message 字段单独拿），
                // 再 slice(-8) 只取最后 8 条，足够上下文又不至于过重
                const MAX_HISTORY = 8
                const trimmedHistory = this.history.slice(0, -1).slice(-MAX_HISTORY)

                const payload = {
                    context_type: contextType,
                    conversation_id: this.conversationId,
                    context_data: {
                        ...safeContext,
                        q_id: safeContext.q_id || null,
                        attempt_id: attemptId,  // [Stage 31.0]
                        word_id: wordId,        // [Stage 31.0]
                        rpg_mode: safeContext.rpg_mode !== undefined ? safeContext.rpg_mode : true,
                        history: trimmedHistory
                    }
                }

                // Push empty placeholder (The Ghost Bubble)
                this.history.push({ role: 'assistant', content: '' })
                const lastIndex = this.history.length - 1

                // Use native fetch for streaming
                // Force relative path to use Vite proxy (avoids CORS/Port issues)
                const response = await fetch('/api/mia/interact', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                })

                if (!response.ok) throw new Error(response.statusText)

                // Read Headers for State Updates (Conversation ID, HP, Mood)
                const newConvId = response.headers.get("X-Conversation-Id")
                if (newConvId && !this.conversationId) this.conversationId = parseInt(newConvId)

                const newHp = response.headers.get("X-User-Hp")
                const newMood = response.headers.get("X-Mia-Mood")

                if (newHp || newMood) {
                    const { useUserStore } = await import('./useUserStore')
                    const userStore = useUserStore()
                    if (newHp) userStore.hp = parseInt(newHp) // Direct sync or animate? Let's direct sync for now or calc delta
                    // If animate needed: userStore.animateHpChange(parseInt(newHp) - userStore.hp)
                    // But simplest is update.
                    if (newMood) userStore.setMood(newMood)
                }

                const reader = response.body.getReader()
                const decoder = new TextDecoder("utf-8")
                let buffer = ''

                while (true) {
                    const { done, value } = await reader.read()
                    if (done) break

                    buffer += decoder.decode(value, { stream: true })
                    const lines = buffer.split('\n\n')
                    buffer = lines.pop()

                    for (const line of lines) {
                        const trimmedLine = line.trim()
                        if (!trimmedLine.startsWith('data: ')) continue

                        const jsonStr = trimmedLine.substring(6).trim()
                        if (jsonStr === '[DONE]') break

                        try {
                            const data = JSON.parse(jsonStr)

                            // Handle Metadata updates (if sent in first chunk)
                            if (data.conversation_id) {
                                this.conversationId = data.conversation_id
                                // console.log("💾 [Frontend] Saved Conversation ID from stream:", this.conversationId);
                            }
                            if (data.hp !== undefined) {
                                const { useUserStore } = await import('./useUserStore')
                                const userStore = useUserStore()
                                userStore.animateHpChange(data.hp - userStore.hp) // Simplified sync
                            }
                            if (data.current_mood) {
                                const { useUserStore } = await import('./useUserStore')
                                const userStore = useUserStore()
                                userStore.setMood(data.current_mood)
                            }

                            // Handle Text Content
                            if (data.mia_reply) {
                                this.history[lastIndex].content += data.mia_reply
                                this.currentText = this.history[lastIndex].content
                            }
                        } catch (e) {
                            console.error("Stream JSON parse error:", e, jsonStr)
                        }
                    }
                }

            } catch (error) {
                console.error('[MiaStore] interact error:', error)
                const errMsg = " [Mia 掉线了…]"
                // If last message was empty, replace it, else append
                const lastMsg = this.history[this.history.length - 1]
                if (lastMsg && lastMsg.role === 'assistant') {
                    lastMsg.content += errMsg
                } else {
                    this.history.push({ role: 'assistant', content: errMsg })
                }
            } finally {
                this.isTyping = false
            }
        }
    }
})
