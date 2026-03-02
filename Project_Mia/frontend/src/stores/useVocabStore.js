import { defineStore } from 'pinia'
import request from '../utils/request'
import { useUserStore } from './useUserStore'

export const useVocabStore = defineStore('vocab', {
    state: () => ({
        todayTasks: [],
        currentIndex: 0,
        loading: false,
        submitting: false,
        dailyProgress: {
            reviewed: 0,
            total: 0
        }
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
            return Math.round((state.dailyProgress.reviewed / state.dailyProgress.total) * 100)
        }
    },

    actions: {
        async fetchTodayVocab() {
            const userStore = useUserStore()
            this.loading = true
            try {
                const res = await request.get('/vocab/today', {
                    params: { slot_id: userStore.currentSlotId }
                })
                if (res && res.tasks) {
                    this.todayTasks = res.tasks
                    this.dailyProgress.total = res.total_count
                    this.dailyProgress.reviewed = 0 // Reset or Calculate if partial? 
                    // For now assume fresh start or filtered list
                    this.currentIndex = 0
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
                    // Reward handling
                    if (res.reward) {
                        const { hp, exp, leveled_up } = res.reward
                        if (hp !== 0 || exp > 0) {
                            // Update User Store locally to reflect change instantly
                            // Ensure HP doesn't go below 0 visually
                            userStore.hp = Math.min(userStore.maxHp, Math.max(0, userStore.hp + hp))
                            userStore.exp += exp
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
            this.currentIndex++
            this.dailyProgress.reviewed++
        }
    },
    persist: true
})
