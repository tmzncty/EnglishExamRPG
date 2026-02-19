import { defineStore } from 'pinia'
import request from '../utils/request'

export const useMiaStore = defineStore('mia', {
    state: () => ({
        dialogVisible: true,
        currentText: "你好，绯墨！准备好今天的挑战了吗？",
        isTyping: false,
        history: [],
        conversationId: null,
        conversationList: [],
        showHistoryPanel: false,
    }),

    actions: {
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

                // Prepare Payload
                // console.log("🚀 [Frontend] Sending request with Conversation ID:", this.conversationId);
                const payload = {
                    context_type: contextType,
                    conversation_id: this.conversationId, // Use correct state var name
                    context_data: {
                        ...safeContext,
                        q_id: safeContext.q_id || null,
                        rpg_mode: safeContext.rpg_mode !== undefined ? safeContext.rpg_mode : true,
                        // Fix History Fragmentation: Slice off the last user message to avoid duplication 
                        // (Agent constructs user_prompt separately), AND exclude the ghost bubble we are about to push?
                        // Actually, at this point, ghost bubble is NOT pushed yet.
                        // So we slice(0, -1) to remove the User message defined in 'message'.
                        history: this.history.slice(0, -1)
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
