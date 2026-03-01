import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import ExamRoom from '../views/ExamRoom.vue'

const routes = [
    {
        path: '/',
        name: 'Dashboard',
        component: Dashboard
    },
    {
        path: '/exam/:paperId',
        name: 'ExamRoom',
        component: ExamRoom
    },
    {
        path: '/garden',
        name: 'VocabGarden',
        component: () => import('../views/VocabGarden.vue') // Lazy load
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
