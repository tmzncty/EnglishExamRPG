<template>
  <div class="h-screen bg-[#f5f5f0] text-gray-900 flex font-sans overflow-hidden">
    <!-- Sidebar: Attempts List -->
    <div class="w-80 bg-white border-r border-gray-200 flex flex-col h-full shrink-0 shadow-sm relative z-10">
      <div class="p-6 border-b border-gray-100 flex items-center justify-between sticky top-0 bg-white bg-opacity-90 backdrop-blur">
        <h2 class="text-xl font-bold font-wenkai text-gray-800 flex items-center gap-2">
          <button @click="router.push('/')" class="text-gray-400 hover:text-rose-400 transition-colors">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
          </button>
          历史批次
        </h2>
      </div>
      
      <div class="flex-1 overflow-y-auto custom-scrollbar p-4 flex flex-col gap-3">
        <div v-if="loadingAttempts" class="text-center text-sm text-gray-400 py-10">加载中...</div>
        <div v-else-if="!attempts.length" class="text-center text-sm text-gray-400 py-10">
          暂无作答记录
        </div>
        
        <button
          v-for="att in attempts"
          :key="att.attempt_id"
          @click="selectAttempt(att)"
          class="text-left w-full p-4 rounded-xl border transition-all duration-200 group"
          :class="selectedAttemptId === att.attempt_id ? 'bg-rose-50 border-rose-300 shadow-sm' : 'bg-white border-gray-100 hover:border-rose-200 hover:shadow-sm'"
        >
          <div class="flex justify-between items-center mb-2">
            <span class="font-bold text-gray-800 text-sm">Attempt #{{ att.attempt_number }}</span>
            <span 
              class="text-xs px-2 py-0.5 rounded-full font-medium"
              :class="att.status === 'finished' ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'"
            >
              {{ att.status === 'finished' ? '已完成' : '进行中' }}
            </span>
          </div>
          <div class="text-xs text-gray-500 font-mono mb-2">
            {{ formatTimeLong(att.started_at) }}
          </div>
          <div class="flex justify-between text-xs font-semibold">
            <span class="text-gray-600">耗时: {{ Math.floor(att.total_time / 60) }}分{{ att.total_time % 60 }}秒</span>
            <span v-if="att.status === 'finished'" class="text-rose-500">得分: {{ att.total_score }}</span>
          </div>
        </button>
      </div>
    </div>

    <!-- Main Content: Attempt Detail -->
    <div class="flex-1 flex flex-col h-full bg-[#fdfdfc] overflow-y-auto custom-scrollbar relative">
      <div v-if="!selectedAttemptId" class="m-auto text-gray-400 flex flex-col items-center gap-4">
        <span class="text-5xl opacity-40">🗂️</span>
        <span class="font-wenkai text-lg">请在左侧选择一次作答记录</span>
      </div>

      <div v-else-if="loadingDetail" class="m-auto text-rose-400 animate-pulse font-wenkai">
        正在解压缩记忆档案...
      </div>

      <div v-else class="max-w-4xl mx-auto w-full p-8 md:p-12 pb-32">
        <header class="mb-10 text-center">
            <h1 class="text-3xl font-bold font-wenkai text-gray-800 mb-4">
              Attempt #{{ attemptDetail?.attempt?.attempt_number }}
            </h1>
            <div class="flex justify-center gap-6 text-sm text-gray-500 font-mono">
                <span class="bg-gray-100 px-3 py-1 rounded-lg">耗时: {{ formatDuration(attemptDetail?.attempt?.total_time) }}</span>
                <span class="bg-gray-100 px-3 py-1 rounded-lg">得分: <span class="text-rose-500 font-bold">{{ attemptDetail?.attempt?.total_score }}</span></span>
            </div>
        </header>

        <!-- Question List -->
        <div class="space-y-6">
            <h2 class="text-xl font-bold font-wenkai text-gray-800 border-b pb-2">📂 答题明细</h2>
            
            <div v-if="!attemptDetail?.answers || Object.keys(attemptDetail.answers).length === 0" class="text-center py-16">
                <div class="text-5xl mb-4 opacity-60">📋</div>
                <p class="text-gray-400 font-wenkai text-lg mb-2">此档案为空</p>
                <p class="text-gray-300 text-sm">该批次尚未提交任何答题记录</p>
            </div>
            
            <div 
              v-for="(ans, qId) in attemptDetail?.answers" 
              :key="qId"
              class="bg-white border rounded-xl p-5 shadow-sm"
              :class="ans.is_correct ? 'border-emerald-100' : 'border-rose-100'"
            >
                <div class="flex justify-between items-center mb-4">
                    <span class="font-mono font-bold text-gray-700 bg-gray-100 px-2.5 py-1 rounded text-sm">Q{{ Object.keys(attemptDetail.answers).indexOf(qId) + 1 }}</span>
                    <span class="text-xs font-mono px-2 py-1 rounded bg-gray-50 text-gray-500 border">
                        🕐 {{ getQuestionTime(qId) }}秒
                    </span>
                </div>
                
                <!-- Display the actual question content -->
                <div v-if="getQuestionData(qId)" class="mb-5 bg-[#fafafa] p-4 rounded-lg border border-gray-100">
                    <!-- Passage or Prompt -->
                    <div class="font-wenkai text-gray-800 leading-relaxed whitespace-pre-wrap mb-4" style="font-size: 15px;">
                        <span v-if="getQuestionData(qId).sectionPassage" class="block mb-2 text-gray-500 text-sm border-l-2 border-gray-300 pl-2">
                            [Context] {{ getQuestionData(qId).sectionPassage.substring(0, 80) }}...
                        </span>
                        <span>{{ getQuestionData(qId).prompt || getQuestionData(qId).passage || '（无题干）' }}</span>
                    </div>

                    <!-- Options (if objective) -->
                    <div v-if="getQuestionData(qId).options" class="flex flex-col gap-2 mb-2">
                        <div 
                           v-for="(optText, optKey) in getQuestionData(qId).options" 
                           :key="optKey"
                           class="flex items-start gap-3 p-2 rounded text-sm font-wenkai border transition-colors"
                           :class="[
                               optKey === getQuestionData(qId).answer ? 'bg-emerald-50 border-emerald-200 text-emerald-800 font-bold' : '',
                               optKey === ans.user_answer && optKey !== getQuestionData(qId).answer ? 'bg-rose-50 border-rose-200 text-rose-800' : '',
                               optKey !== getQuestionData(qId).answer && optKey !== ans.user_answer ? 'border-transparent text-gray-600' : ''
                           ]"
                        >
                            <span class="shrink-0 mt-0.5 font-mono w-5 rounded-full flex items-center justify-center text-xs"
                                  :class="optKey === getQuestionData(qId).answer ? 'bg-emerald-500 text-white' : (optKey === ans.user_answer ? 'bg-rose-500 text-white' : 'bg-gray-200 text-gray-600')">
                                {{ optKey }}
                            </span>
                            <span class="leading-relaxed">{{ optText }}</span>
                        </div>
                    </div>
                </div>
                
                <div class="flex items-center gap-4 text-sm font-wenkai mb-3 mt-4">
                    <div class="flex-1 p-3 bg-gray-50 rounded-lg flex items-center justify-between">
                        <div>
                            <span class="text-gray-400 block mb-1 text-xs uppercase tracking-wider">Your Answer</span>
                            <span class="font-bold text-gray-800 text-base">{{ ans.user_answer || '（空）' }}</span>
                        </div>
                        <div v-if="getQuestionData(qId)?.answer && ans.user_answer !== getQuestionData(qId).answer" class="text-right">
                           <span class="text-gray-400 block mb-1 text-xs uppercase tracking-wider">Correct Answer</span>
                           <span class="font-bold text-emerald-600 text-base">{{ getQuestionData(qId).answer }}</span>
                        </div>
                    </div>
                    
                    <div class="px-4 py-3 rounded-lg flex flex-col items-center justify-center min-w-[100px]" :class="ans.is_correct ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'">
                        <span class="text-xl mb-1">
                            {{ ans.is_correct ? '💯' : '💥' }}
                        </span>
                        <span class="font-bold text-xs uppercase tracking-wider">
                            {{ ans.is_correct ? 'Correct' : 'Missed' }}
                        </span>
                    </div>
                </div>
                
                <div v-if="ans.ai_feedback && ans.ai_feedback !== '[]' && ans.ai_feedback !== '{}'" class="mt-4 p-4 bg-gradient-to-r from-[#fff0f3] to-white rounded-lg text-sm text-gray-700 border border-rose-50 border-l-4 border-l-rose-300 shadow-sm relative overflow-hidden">
                    <div class="absolute -right-4 -top-4 text-6xl opacity-5">💭</div>
                    <div class="flex items-center gap-2 mb-2">
                       <span class="text-rose-500 text-lg">✨</span>
                       <span class="font-bold text-rose-600 font-wenkai">Mia 短评</span>
                    </div>
                    <div class="font-wenkai leading-relaxed relative z-10">{{ ans.ai_feedback }}</div>
                </div>

                <!-- Attached MIA Conversations for this specific question -->
                <div v-if="getQuestionConversations(qId).length > 0" class="mt-4 border border-gray-200 rounded-lg overflow-hidden">
                    <details class="group">
                        <summary class="flex items-center justify-between p-3 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors list-none">
                            <div class="flex items-center gap-2">
                                <span class="text-base">💬</span>
                                <span class="text-sm font-bold text-gray-700 font-wenkai">查看此题的 AI 探讨记录 ({{ getQuestionConversations(qId).length }} 次)</span>
                            </div>
                            <span class="transform transition-transform group-open:rotate-180 text-gray-400">▼</span>
                        </summary>
                        <div class="p-4 bg-white space-y-4">
                            <div v-for="conv in getQuestionConversations(qId)" :key="conv.id" class="text-sm font-wenkai bg-gray-50 rounded p-3 border border-gray-100">
                                <div class="text-xs text-gray-400 mb-2 border-b border-gray-200 pb-1">{{ conv.created_at }}</div>
                                <div class="space-y-3">
                                  <div v-for="(msg, idx) in conv.messages" :key="idx" class="flex gap-2">
                                      <span :class="msg.role === 'user' ? 'text-blue-600 font-bold' : 'text-rose-600 font-bold shrink-0'">{{ msg.role === 'user' ? '我：' : 'Mia：' }}</span>
                                      <span :class="msg.role === 'user' ? 'text-gray-800' : 'text-gray-900 bg-rose-50 p-2 rounded'">{{ msg.content }}</span>
                                  </div>
                                </div>
                            </div>
                        </div>
                    </details>
                </div>
            </div>
        </div>

        <!-- General AI Conversations (Unbound to specific questions) -->
        <div v-if="getGeneralConversations().length" class="space-y-6 mt-12">
            <h2 class="text-xl font-bold font-wenkai text-gray-800 border-b pb-2">💬 考场全局 AI 讨论</h2>
            
            <div 
              v-for="conv in getGeneralConversations()" 
              :key="conv.id"
              class="bg-white border border-gray-200 rounded-xl p-5 shadow-sm"
            >
                <div class="text-xs font-mono text-gray-400 mb-3 border-b pb-2 flex justify-between">
                  <span>{{ conv.created_at }}</span>
                </div>
                <div class="space-y-4">
                  <div v-for="(msg, idx) in conv.messages" :key="idx" class="text-sm font-wenkai">
                      <div v-if="msg.role === 'user'" class="flex gap-2">
                          <span class="font-bold text-gray-800 shrink-0">我：</span>
                          <span class="text-gray-700">{{ msg.content }}</span>
                      </div>
                      <div v-else class="flex gap-2 text-rose-600 bg-rose-50 p-3 rounded-lg">
                          <span class="font-bold shrink-0">Mia：</span>
                          <span>{{ msg.content }}</span>
                      </div>
                  </div>
                </div>
            </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/useUserStore'
import { useExamStore } from '../stores/useExamStore'
import request from '../utils/request'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const examStore = useExamStore()

const paperId = route.params.paperId
const attempts = ref([])
const loadingAttempts = ref(true)

const selectedAttemptId = ref(null)
const attemptDetail = ref(null)
const loadingDetail = ref(false)

onMounted(async () => {
    try {
        // Load the paper structure to map q_ids to texts
        await examStore.fetchPaper(paperId)

        const res = await request.get(`/exam/attempts/${paperId}`, {
            params: { slot_id: userStore.currentSlotId }
        })
        attempts.value = res || []
    } catch (e) {
        console.error('Failed to load attempts or paper', e)
    } finally {
        loadingAttempts.value = false
    }
})

const selectAttempt = async (att) => {
    selectedAttemptId.value = att.attempt_id
    loadingDetail.value = true
    attemptDetail.value = null
    try {
        const res = await request.get(`/exam/attempt/${att.attempt_id}`)
        attemptDetail.value = res
    } catch (e) {
        console.error('Failed to load attempt detail', e)
    } finally {
        loadingDetail.value = false
    }
}

const formatTimeLong = (dateStr) => {
    if (!dateStr) return '-'
    const d = new Date(dateStr)
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

const formatDuration = (secs) => {
    if (!secs) return '0分0秒'
    const m = Math.floor(secs / 60)
    const s = secs % 60
    return `${m}分${s}秒`
}

const getQuestionTime = (qId) => {
    if (!attemptDetail.value || !attemptDetail.value.question_times) return 0
    return attemptDetail.value.question_times[qId] || 0
}

const getQuestionData = (qId) => {
    if (!examStore.currentPaper || !examStore.currentPaper.sections) return null
    for (const section of examStore.currentPaper.sections) {
        if (section.questions) {
            const q = section.questions.find(x => x.q_id === qId)
            if (q) return { ...q, sectionPassage: section.passage }
        }
    }
    return null
}

const getQuestionConversations = (qId) => {
    if (!attemptDetail.value || !attemptDetail.value.conversations) return []
    return attemptDetail.value.conversations.filter(c => c.bound_q_id === qId)
}

const getGeneralConversations = () => {
    if (!attemptDetail.value || !attemptDetail.value.conversations) return []
    return attemptDetail.value.conversations.filter(c => !c.bound_q_id)
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 3px; }
.custom-scrollbar:hover::-webkit-scrollbar-thumb { background: #d1d5db; }
</style>
