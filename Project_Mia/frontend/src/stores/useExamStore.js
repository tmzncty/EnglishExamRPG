import { defineStore } from 'pinia'
import request from '../utils/request'
import { useUserStore } from './useUserStore'

export const useExamStore = defineStore('exam', {
    state: () => ({
        paperId: null,
        currentPaper: null, // 试卷详情
        examList: [], // 试卷列表
        loading: false,
        lastError: null, // [Stage 25.0] User-facing error message

        // [Stage 28.1] Exam Shield (Per-Paper HP)
        paperHp: 100,
        maxPaperHp: 100,

        // Annotations: { [paperId]: { [sectionId]: base64 } }
        annotations: {},

        // Active Question Tracking for Context Injection
        activeQuestionId: null,

        // [Stage 14.0] 用户答题历史回显 { q_id: { user_answer, score, is_correct, ai_feedback } }
        answerHistory: {},

        // ── [Stage 31.0] Attempt & Dual-Track Timer ──────────────
        attemptId: null,
        attemptNumber: 1,

        // 双轨计时
        totalExamTime: 0,       // 总耗时 (秒)
        currentQuestionTime: 0, // 当前题目耗时 (秒)
        questionTimes: {},      // { q_id: seconds } 累计表

        isPaused: false,
        _timerInterval: null,
        _heartbeatInterval: null,
        _visibilityHandler: null,
        _blurHandler: null,
        _focusHandler: null,
    }),

    actions: {
        // ── [Stage 31.0] Attempt 生命周期 ──────────────────────────
        async startAttempt(paperId) {
            try {
                const userStore = useUserStore()
                const res = await request.post('/exam/start_attempt', {
                    paper_id: paperId,
                    slot_id: userStore.currentSlotId
                })
                if (res) {
                    this.attemptId = res.attempt_id
                    this.attemptNumber = res.attempt_number

                    // 恢复持久化的时间
                    const restored = res.restored_time || {}
                    this.totalExamTime = restored.total_time || 0
                    this.questionTimes = restored.question_times || {}
                    this.currentQuestionTime = 0

                    console.log(`[ExamStore] Attempt ${this.attemptId} (第${this.attemptNumber}刷), restored ${this.totalExamTime}s`)
                }
            } catch (e) {
                console.error('[ExamStore] startAttempt failed:', e)
            }
        },

        async finishAttempt() {
            if (!this.attemptId) return
            try {
                // 最后一次心跳同步
                await this._syncTimeNow()
                await request.post('/exam/finish_attempt', {
                    attempt_id: this.attemptId
                })
                console.log(`[ExamStore] Attempt ${this.attemptId} finished`)
            } catch (e) {
                console.error('[ExamStore] finishAttempt failed:', e)
            }
        },

        // ── 切题逻辑 (累加旧题耗时 → 恢复新题耗时) ─────────────
        setActiveQuestion(qId) {
            const oldQId = this.activeQuestionId
            if (oldQId === qId) return

            // 累加旧题的耗时到 map
            if (oldQId) {
                this.questionTimes[oldQId] = (this.questionTimes[oldQId] || 0) + this.currentQuestionTime
            }

            // 恢复新题的已有耗时 (如果之前做过)
            this.currentQuestionTime = 0  // 从 0 开始追加
            this.activeQuestionId = qId

            // 切题时触发一次心跳同步
            this._syncTimeNow()
        },

        // ── [Stage 14.0] 拉取答题历史 ──────────────────────────
        async fetchAnswerHistory() {
            try {
                const userStore = useUserStore()
                const params = { slot_id: userStore.currentSlotId }
                if (this.attemptId) params.attempt_id = this.attemptId
                const res = await request.get('/exam/history', { params })
                if (res) {
                    this.answerHistory = res
                }
            } catch (e) {
                console.error("Failed to fetch answer history:", e)
            }
        },

        // 获取试卷列表
        async fetchExams() {
            this.loading = true
            try {
                const res = await request.get('/exams')
                this.examList = res
            } catch (e) {
                console.error(e)
            } finally {
                this.loading = false
            }
        },

        async fetchPaper(id) {
            this.loading = true
            this.lastError = null
            try {
                const res = await request.get(`/exam/${id}`)
                this.currentPaper = res

                // [Stage 28.2] Initialize fresh shield unconditionally
                this.paperHp = 100
                this.maxPaperHp = 100

                this.paperId = id

                // [Stage 31.0] 启动 Attempt (会恢复时间或创建新 attempt)
                await this.startAttempt(id)

                // 加载答题历史
                await this.fetchAnswerHistory()

                return res
            } catch (e) {
                console.error(e)
                this.lastError = `未找到对应试卷 (${id})`
                this.currentPaper = null
                return null
            } finally {
                this.loading = false
            }
        },

        // 保存笔迹
        saveAnnotation(paperId, sectionId, data) {
            try {
                if (!this.annotations[paperId]) this.annotations[paperId] = {}
                this.annotations[paperId][sectionId] = data

                localStorage.setItem(`mia_notes_${paperId}`, JSON.stringify(this.annotations[paperId]))
            } catch (e) {
                if (e.name === 'QuotaExceededError') {
                    alert('存储空间已满！请清理旧的笔记或导出备份。')
                } else {
                    console.error('Storage Error:', e)
                }
            }
        },

        // 加载笔迹
        loadAnnotation(paperId, sectionId) {
            if (this.annotations[paperId]?.[sectionId]) {
                return this.annotations[paperId][sectionId]
            }
            const saved = localStorage.getItem(`mia_notes_${paperId}`)
            if (saved) {
                try {
                    const parsed = JSON.parse(saved)
                    if (!this.annotations[paperId]) this.annotations[paperId] = parsed
                    else Object.assign(this.annotations[paperId], parsed)

                    return parsed[sectionId]
                } catch {
                    return null
                }
            }
            return null
        },

        // 清除笔迹
        clearAnnotation(paperId) {
            if (this.annotations[paperId]) delete this.annotations[paperId]
            localStorage.removeItem(`mia_notes_${paperId}`)
        },

        // [Stage 28.1] 考场专属护盾扣血 (不再直接扣全局 HP)
        animateHpChange(changeAmount) {
            if (!changeAmount || changeAmount === 0) return;

            this.paperHp += changeAmount;

            // 强制血量边界
            if (this.paperHp > this.maxPaperHp) this.paperHp = this.maxPaperHp;
            if (this.paperHp < 0) this.paperHp = 0;
        },

        // ══════════════════════════════════════════════════════════
        // [Stage 31.0 / 35.0] Strict Foreground Dual-Track Timer (Polling Tick)
        // ══════════════════════════════════════════════════════════

        startExamTimer() {
            if (this._timerInterval) return

            // ── 每秒递增计时器 + 严格轮询 ──────────────────────────────────
            this._timerInterval = setInterval(() => {
                const isReallyInactive = document.hidden || (!document.hasFocus() && document.activeElement?.tagName !== 'IFRAME')

                if (isReallyInactive) {
                    this.isPaused = true
                    return // 挂机时不计入时间！
                }

                this.isPaused = false
                this.totalExamTime++
                if (this.activeQuestionId) {
                    this.currentQuestionTime++
                }
            }, 1000)

            // ── 心跳持久化 (每 10 秒静默同步) ────────────────────
            this._startHeartbeat()
        },

        stopExamTimer() {
            if (this._timerInterval) {
                clearInterval(this._timerInterval)
                this._timerInterval = null
            }
            if (this._heartbeatInterval) {
                clearInterval(this._heartbeatInterval)
                this._heartbeatInterval = null
            }

            // 最后一次同步
            this._syncTimeNow()
        },

        // ── 心跳引擎 (Silent — 不触发 Loading) ──────────────────
        _startHeartbeat() {
            if (this._heartbeatInterval) return
            this._heartbeatInterval = setInterval(() => {
                this._syncTimeNow()
            }, 10000) // 每 10 秒
        },

        async _syncTimeNow() {
            if (!this.attemptId) return

            // 构建当前完整的 questionTimes 快照
            const snapshot = { ...this.questionTimes }
            // 加上当前正在做的题的 live 时间
            if (this.activeQuestionId) {
                snapshot[this.activeQuestionId] = (snapshot[this.activeQuestionId] || 0) + this.currentQuestionTime
            }

            try {
                // 静默请求 — 不走全局 interceptor 的 loading
                await request.post('/exam/sync_time', {
                    attempt_id: this.attemptId,
                    total_time: this.totalExamTime,
                    question_times: snapshot
                })
            } catch (e) {
                // 心跳失败不应该中断用户体验
                console.warn('[ExamStore] Heartbeat sync failed (silent):', e.message)
            }
        }
    }
})
