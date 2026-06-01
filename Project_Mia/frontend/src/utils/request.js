import axios from 'axios'
import { useUserStore } from '../stores/useUserStore'

// 创建 Axios 实例
// AI 批改(非流式)最慢约 35s，给足 2 分钟避免超时
const service = axios.create({
    baseURL: '/api', // Vite 代理转发
    timeout: 120000,
})

// 响应拦截器
service.interceptors.response.use(
    (response) => {
        const res = response.data
        const userStore = useUserStore()

        // 1. 自动处理 HP 变更 (headers 或 body)
        if (res.hp !== undefined) {
            userStore.updateStatus({
                hp: res.hp,
                maxHp: res.max_hp
            })
        }

        // 2. 自动处理 Mood 变更
        if (res.current_mood) {
            userStore.setMood(res.current_mood)
        }

        return res
    },
    (error) => {
        console.error('API Error:', error)
        return Promise.reject(error)
    }
)

export default service
