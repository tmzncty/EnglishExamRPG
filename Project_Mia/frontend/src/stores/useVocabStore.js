import { defineStore } from 'pinia'
import request from '../utils/request'
import { useUserStore } from './useUserStore'

// [Stage 35.1] Timezone-agnostic Logical Day Anchor (UTC+8 with 4AM offset)
export const getCurrentLogicalDay = () => {
    const now = new Date()
    // UTC+8 offset (8h) - 4 AM refresh offset (4h) = net +4h from UTC
    const logicalTime = new Date(now.getTime() + 4 * 60 * 60 * 1000)
    const yyyy = logicalTime.getUTCFullYear()
    const mm = String(logicalTime.getUTCMonth() + 1).padStart(2, '0')
    const dd = String(logicalTime.getUTCDate()).padStart(2, '0')
    return `${yyyy}-${mm}-${dd}`
}

export const useVocabStore = defineStore('vocab', {
    state: () => ({
        todayTasks: [],
        currentIndex: 0,
        loading: false,
        submitting: false,
        dailyProgress: {
            reviewed: 0,
            total: 0,
            new_learned: 0,
            to_review: 0
        },
        // [Stage 30.0] Time Engine & Check-in
        dailyStreak: 0,
        todayFocusTime: 0,
        isPaused: false,
        _timerInterval: null,
        _visibilityHandler: null,

        // [Stage 31.0] Session tracking
        sessionId: null,
        wordStartTime: 0,
        wordsLearned: 0,
        wordsReviewed: 0,

        // [Stage 32.0 / 34.0] Global Progress
        globalStats: {
            total: 0,
            mastered: 0
        },

        // [Stage 35.1] Cross-Day Rollover Anchor
        lastActiveLogicalDay: null
    }),

    getters: {
        currentWord: (state) => {
            if (!state.todayTasks.length || state.currentIndex >= state.todayTasks.length) return null
            return state.todayTasks[state.currentIndex]
        },
        isFinished: (state) => {
            return state.todayTasks.length > 0 && state.currentIndex >= state.todayTasks.length
        },
        progressPercent: (state) => {
            if (state.dailyProgress.total === 0) return 0
            return Math.min(100, Math.round((state.dailyProgress.reviewed / state.dailyProgress.total) * 100))
        },
        globalProgressPercent: (state) => {
            if (state.globalStats.total === 0) return 0
            return Math.min(100, Math.round((state.globalStats.mastered / state.globalStats.total) * 100))
        }
    },

    actions: {
        async fetchGlobalStats() {
            const userStore = useUserStore()
            try {
                const res = await request.get('/vocab/global_stats', {
                    params: { slot_id: userStore.currentSlotId }
                })
                if (res) {
                    this.globalStats.total = res.total_words
                    this.globalStats.mastered = res.mastered_words
                }
            } catch (e) {
                console.warn("Failed to fetch global stats:", e)
            }
        },

        async addDailyLimit(amount) {
            const userStore = useUserStore()
            await userStore.updateDailyLimit(userStore.dailyLimit + amount)
            // Re-fetch to pull the extra words into today's queue
            await this.fetchTodayVocab()
        },

        async fetchTodayVocab() {
            const userStore = useUserStore()
            this.loading = true
            try {
                const res = await request.get('/vocab/today', {
                    params: {
                        slot_id: userStore.currentSlotId
                    }
                })
                if (res && res.tasks) {
                    this.todayTasks = res.tasks
                    this.dailyProgress.total = res.total_count
                    this.dailyProgress.reviewed = res.today_reviewed_count || 0
                    this.dailyProgress.new_learned = res.today_learned_count || 0

                    // Task 2: Denominator logic fix.
                    // to_review (denominator) should be "what we already did" + "what is in the queue"
                    this.dailyProgress.to_review = (res.today_reviewed_count || 0) + (res.review_count || 0)
                    // For now assume fresh start or filtered list
                    this.currentIndex = 0

                    // [Stage 30.0 / 35.0] Check-in Sync - Defensive Math.max to prevent rolling back accumulated timer
                    this.dailyStreak = res.daily_streak || 0
                    this.todayFocusTime = Math.max(this.todayFocusTime, res.today_focus_time || 0)

                    // [Stage 35.1] Update Logical Day Anchor
                    this.lastActiveLogicalDay = getCurrentLogicalDay()

                    // [Stage 31.0] Start Session
                    try {
                        const sessRes = await request.post('/vocab/start_session', { slot_id: userStore.currentSlotId })
                        if (sessRes && sessRes.session_id) {
                            this.sessionId = sessRes.session_id
                            this.wordsLearned = 0
                            this.wordsReviewed = 0
                            this.wordStartTime = Date.now()
                        }
                    } catch (e) {
                        console.warn("Failed to start vocab session:", e)
                    }
                }
            } catch (error) {
                console.error("Failed to fetch vocab:", error)
            } finally {
                this.loading = false
            }
        },

        async submitReview(quality) {
            const userStore = useUserStore()
            const word = this.currentWord
            if (!word || this.submitting) return

            this.submitting = true;
            try {
                const res = await request.post('/vocab/review', {
                    slot_id: userStore.currentSlotId,
                    word: word.word,
                    quality: quality
                })

                if (res && res.success) {
                    // [Stage 31.0] Log Word
                    if (this.sessionId) {
                        const timeSpent = Math.floor((Date.now() - this.wordStartTime) / 1000)
                        const action = word.type === 'new' ? 'learn' : 'review'
                        if (action === 'learn') this.wordsLearned++
                        else this.wordsReviewed++

                        request.post('/vocab/log_word', {
                            session_id: this.sessionId,
                            word: word.word,
                            action: action,
                            time_spent: timeSpent,
                            result: quality >= 3 ? 'success' : 'forgot'
                        }).catch(e => console.warn('Vocab log error:', e))
                    }

                    // Reward handling
                    if (res.reward) {
                        const { new_hp, new_exp, leveled_up } = res.reward
                        if (new_hp !== undefined && new_hp !== null) {
                            userStore.hp = new_hp
                        }
                        if (new_exp !== undefined && new_exp !== null) {
                            userStore.exp = new_exp
                        }
                        if (leveled_up) {
                            // Ideally fetch full user to get new level/maxHP correctly
                            await userStore.loadUser(userStore.currentSlotId)
                        }
                    }

                    // Move to next manually
                    // this.currentIndex++ 
                    // this.dailyProgress.reviewed++
                }
                return res // Return for UI handling
            } catch (error) {
                console.error("Review failed:", error)
                return { success: false }
            } finally {
                this.submitting = false;
            }
        },

        nextWord() {
            const word = this.currentWord
            this.currentIndex++
            if (word) {
                if (word.type === 'new') {
                    this.dailyProgress.new_learned++
                } else {
                    this.dailyProgress.reviewed++
                }
            }

            // [Stage 31.0] Reset timing for next word
            this.wordStartTime = Date.now()

            // [Stage 30.0] Sync immediately if we just finished
            if (this.isFinished) {
                this.syncProgress()
                this.finishSession() // [Stage 31.0]
            }
        },

        // [Stage 30.0 / 32.0 / 34.0 / 35.0 / 35.1] True Foreground Polling Timer
        startFocusTimer() {
            if (this._timerInterval) return

            this._timerInterval = setInterval(() => {
                // [Stage 35.1] Cross-Day Rollover Tick!
                const currentDay = getCurrentLogicalDay()
                if (this.lastActiveLogicalDay && this.lastActiveLogicalDay !== currentDay) {
                    console.log(`[VocabStore] Midnight Rollover Detected! ${this.lastActiveLogicalDay} -> ${currentDay}`)

                    // Stop timer and pause
                    this.isPaused = true
                    if (this._timerInterval) {
                        clearInterval(this._timerInterval)
                        this._timerInterval = null
                    }

                    window.alert("🌅 新的一天开始啦！系统正在为您刷新今日任务...")

                    // Stale State Wipe (reset inputs to computed isFinished, not isFinished itself)
                    this.currentIndex = 0
                    this.todayFocusTime = 0
                    this.todayTasks = []
                    this.dailyProgress = { reviewed: 0, total: 0, new_learned: 0, to_review: 0 }
                    this.lastActiveLogicalDay = currentDay

                    // Refetch data
                    this.fetchTodayVocab().then(() => {
                        this.startFocusTimer()
                        this.isPaused = false
                    })
                    return // Abort current tick
                }

                // Check if truly inactive (tab hidden or window blurred unless interacting with iframe)
                const isReallyInactive = document.hidden || (!document.hasFocus() && document.activeElement?.tagName !== 'IFRAME')

                if (isReallyInactive) {
                    this.isPaused = true
                    return // Truly AFK, do not accumulate time!
                }

                this.isPaused = false
                if (!this.isFinished) {
                    this.todayFocusTime++

                    // Sync every 30 seconds to be safe
                    if (this.todayFocusTime > 0 && this.todayFocusTime % 30 === 0) {
                        this.syncProgress()
                    }
                }
            }, 1000)
        },

        stopFocusTimer() {
            if (this._timerInterval) {
                clearInterval(this._timerInterval)
                this._timerInterval = null
            }
            this.syncProgress()
            // Optional: You could finish session here if you want it to behave like exams
            this.finishSession()
        },

        async finishSession() {
            if (!this.sessionId) return
            try {
                await request.post('/vocab/finish_session', {
                    session_id: this.sessionId,
                    total_time: this.todayFocusTime, // Ideally track session specific time
                    words_learned: this.wordsLearned,
                    words_reviewed: this.wordsReviewed
                })
                this.sessionId = null
            } catch (e) {
                console.warn("Fast to finish session", e)
            }
        },

        async syncProgress() {
            const userStore = useUserStore()
            if (!userStore.currentSlotId) return

            try {
                const res = await request.post('/vocab/sync_progress', {
                    slot_id: userStore.currentSlotId,
                    focus_time: this.todayFocusTime,
                    goal_met: this.isFinished
                })
                if (res && res.success) {
                    this.dailyStreak = res.daily_streak
                    this.todayFocusTime = res.today_focus_time
                }
            } catch (e) {
                console.error("Sync progress failed:", e)
            }
        }
    },
    persist: {
        paths: ['todayTasks', 'currentIndex', 'dailyProgress', 'dailyStreak', 'todayFocusTime', 'lastActiveLogicalDay']
    }
})
