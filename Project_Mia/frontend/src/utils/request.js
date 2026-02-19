import axios from 'axios'
import { useUserStore } from '../stores/useUserStore'

// 创建 Axios 实例
const service = axios.create({
    baseURL: '/api', // Vite 代理转发
    timeout: 60000,
})

// 响应拦截器
service.interceptors.response.use(
    (response) => {
        const res = response.data
        const userStore = useUserStore()

        // 1. 自动处理 HP 变更 (headears 或 body)
        // 假设后端在 response body 返回了 user_status 或 hp_change
        // 我们的 API 设计: MiaInteractResult 返回 hp, max_hp, current_mood

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
