import { defineStore } from 'pinia'
import request from '../utils/request'

export const useUserStore = defineStore('user', {
    state: () => ({
        hp: 100,
        maxHp: 100,
        level: 1,
        exp: 0,
        mood: 'focused', // focused, happy, worried, exhausted
        token: null,     // JWT token (Phase 5)
        currentSlotId: 0, // [Stage 15.0] 当前存档槽位
        availableSlots: [], // [Stage 16.0] 可用存档列表
        dailyLimit: 30,  // [Stage 20.0] 当前存档的每日新词上限
    }),

    getters: {
        hpPercentage: (state) => {
            if (state.maxHp <= 0) return 0
            return Math.min(100, Math.max(0, (state.hp / state.maxHp) * 100))
        }
    },

    actions: {
        // 初始化或全量更新状态
        updateStatus(status) {
            if (status.hp !== undefined) this.hp = status.hp
            if (status.maxHp !== undefined) this.maxHp = status.maxHp
            if (status.level !== undefined) this.level = status.level
            if (status.exp !== undefined) this.exp = status.exp
            if (status.mood !== undefined) this.mood = status.mood
        },

        // 手动设置心情 (用于测试或动画)
        setMood(newMood) {
            this.mood = newMood
        },

        // 根据当前HP更新心情
        updateMood() {
            const percentage = this.hpPercentage
            if (percentage > 80) {
                this.mood = 'happy'
            } else if (percentage > 40) {
                this.mood = 'focused'
            } else if (percentage > 10) {
                this.mood = 'worried'
            } else {
                this.mood = 'exhausted'
            }
        },

        // 从后端加载用户进度
        async loadUser(slotId = null) {
            if (slotId !== null) this.currentSlotId = slotId

            try {
                // GET /api/user/load?slot_id=...
                const res = await request.get('/user/load', {
                    params: { slot_id: this.currentSlotId }
                })
                if (res) {
                    this.hp = res.hp
                    this.maxHp = res.max_hp
                    this.level = res.level
                    this.exp = res.exp
                    // Sync mood based on HP
                    this.updateMood()
                }
            } catch (error) {
                console.error("Failed to load user progress:", error)
            }

            // [Stage 20.0] Sync dailyLimit from current slot info
            this._syncDailyLimit()
        },

        // [Stage 20.0] Sync dailyLimit from availableSlots
        _syncDailyLimit() {
            const current = this.availableSlots.find(s => s.slot_id === this.currentSlotId)
            if (current) {
                this.dailyLimit = current.daily_new_words_limit || 30
            }
        },

        // 保存用户进度到后端
        async saveUser() {
            try {
                // POST /api/user/save
                await request.post('/user/save', {
                    slot_id: this.currentSlotId,
                    hp: this.hp,
                    max_hp: this.maxHp,
                    level: this.level,
                    exp: this.exp,
                    completed_questions: [] // TODO: Track completed questions in store
                })
            } catch (error) {
                console.error("Failed to save user progress:", error)
            }
        },

        // 更新HP并自动保存
        updateHp(change) {
            const newHp = Math.max(0, Math.min(this.maxHp, this.hp + change))
            this.hp = newHp
            this.updateMood()

            // Auto-save on HP change
            this.saveUser()
        },

        // [Stage 10.1 Hotfix] 恢复丢失的动画动作，由 SubjectiveInput 组件调用
        animateHpChange(changeAmount) {
            if (!changeAmount || changeAmount === 0) return;

            this.hp += changeAmount;

            // 强制血量边界
            if (this.hp > this.maxHp) this.hp = this.maxHp;
            if (this.hp < 0) this.hp = 0;

            this.updateMood();

            // 状态改变后，静默触发自动存档
            this.saveUser();
        },

        // 从后端拉取最新状态 (保留兼容)
        async fetchStatus() {
            await this.loadUser()
        },

        // [Stage 34.1] 更新每日新词上限
        async updateDailyLimit(newLimit) {
            this.dailyLimit = newLimit
            try {
                await request.put(`/user/slots/${this.currentSlotId}`, {
                    daily_new_words_limit: newLimit
                })
                // 同时更新 availableSlots，防崩溃
                const current = this.availableSlots.find(s => s.slot_id === this.currentSlotId)
                if (current) current.daily_new_words_limit = newLimit
            } catch (error) {
                console.error("Failed to update daily limit:", error)
            }
        },

        // 初始化用户状态
        async init() {
            await this.fetchSlots()
            await this.loadUser()
        },

        // [Stage 16.0 / 21.0] Fetch available slots
        async fetchSlots() {
            try {
                const res = await request.get('/user/slots')
                if (res) {
                    // Apply explicit naming rules for Phase 21.0
                    this.availableSlots = res.map(slot => {
                        let displayName = slot.slot_name
                        if (slot.slot_id === 0) {
                            displayName = "主存档 (Main Save)"
                        } else if (!displayName || displayName === "Auto Save" || displayName.startsWith("Save ")) {
                            displayName = `Custom Save #${slot.slot_id}`
                        }
                        return { ...slot, slot_name: displayName }
                    })
                    this._syncDailyLimit()
                }
            } catch (e) {
                console.error("Failed to fetch slots:", e)
            }
        },

        // [Stage 16.0 / 20.0] Create new slot (with optional name)
        async createSlot(slotName = null) {
            try {
                const payload = slotName ? { slot_name: slotName } : {}
                const res = await request.post('/user/slots/new', payload)
                if (res && res.success) {
                    await this.fetchSlots()
                    // Switch to new slot
                    this.currentSlotId = res.slot_id
                    await this.loadUser(res.slot_id)
                } else {
                    throw new Error(res.error || "Unknown error")
                }
            } catch (e) {
                console.error("Failed to create slot:", e)
                throw e
            }
        }
    }
})
