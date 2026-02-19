import { defineStore } from 'pinia'
import request from '../utils/request'

export const useExamStore = defineStore('exam', {
    state: () => ({
        paperId: null,
        currentPaper: null, // 试卷详情
        examList: [], // 试卷列表
        loading: false,

        // Annotations: { [paperId]: { [sectionId]: base64 } }
        annotations: {},

        // Active Question Tracking for Context Injection
        activeQuestionId: null,
    }),

    actions: {
        setActiveQuestion(qId) {
            this.activeQuestionId = qId
            this.activeQuestionId = qId
            // console.log("[ExamStore] Active question set to:", qId)
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

        // 获取试卷详情
        async fetchPaper(id) {
            this.loading = true
            try {
                const res = await request.get(`/exam/${id}`)
                this.currentPaper = res
                this.paperId = id
                return res
            } catch (e) {
                console.error(e)
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
        }
    }
})
