<template>
  <div class="min-h-screen bg-[#f5f5f0] text-gray-900 p-4 sm:p-6 lg:p-8 pb-[env(safe-area-inset-bottom,2rem)] overflow-y-auto custom-scrollbar">

    <!-- Header -->
    <header class="mb-10 flex items-end justify-between">
      <div>
        <h1 class="text-4xl font-bold text-gray-900 mb-1">Project <span class="text-mia-pink-dark">Mia</span></h1>
        <p class="text-gray-400 text-sm">选择试卷，开始今天的修炼</p>
      </div>
      <div class="text-right bg-white/80 border border-gray-100 shadow-sm px-4 py-2 rounded-xl">
        <div class="text-xl font-bold text-mia-pink-dark">LV.{{ userStore.level }}</div>
        <div class="text-xs text-gray-400">EXP: {{ userStore.exp }}</div>
      </div>
    </header>

    <!-- Loading -->
    <div v-if="examStore.loading" class="text-center text-gray-400 py-24">
      <div class="text-4xl mb-3">⏳</div>
      <p>正在加载试卷列表…</p>
    </div>

    <!-- Empty / Error -->
    <div v-else-if="!examStore.examList.length" class="text-center text-gray-400 py-24">
      <div class="text-4xl mb-3">📄</div>
      <p>列表为空或加载失败。请检查后端运行状态。</p>
    </div>

    <!-- Paper Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <div
        v-for="paper in examStore.examList"
        :key="paper.paper_id"
        @click="goToPaper(paper.paper_id)"
        class="group relative bg-white rounded-2xl p-6 border border-gray-200 shadow-sm hover:shadow-md hover:border-rose-200 transition-all duration-200 cursor-pointer overflow-hidden"
      >
        <!-- Subtle pink tint on hover -->
        <div class="absolute inset-0 bg-rose-50 opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl pointer-events-none"></div>

        <div class="relative z-10 flex justify-between items-start mb-3">
          <span class="text-3xl font-bold font-mono text-gray-200 group-hover:text-rose-200 transition-colors">
            {{ paper.year }}
          </span>
          <span class="px-2 py-0.5 bg-rose-50 border border-rose-100 rounded-full text-xs text-mia-pink-dark font-medium">
            {{ paper.exam_type || '英语一' }}
          </span>
        </div>

        <h3 class="relative z-10 text-base font-semibold text-gray-800 mb-3 group-hover:text-gray-900 transition-colors">
          {{ paper.title }}
        </h3>

        <!-- Progress Bar & Actions — [T4] 接入真实进度数据 -->
        <div class="relative z-10 mt-auto pt-3">
          <div class="h-1.5 bg-gray-100 rounded-full overflow-hidden mb-2">
            <div class="h-full bg-mia-pink rounded-full transition-all duration-700" :style="{ width: (paperProgress[paper.paper_id] || 0) + '%' }"></div>
          </div>
          <div class="flex justify-between items-center text-xs text-gray-400 mt-1">
            <span>{{ paperProgress[paper.paper_id] || 0 }}% 完成</span>
            <div class="flex items-center gap-2">
                <button 
                  @click.stop="goToReport(paper.paper_id)" 
                  class="px-2 py-1 bg-gray-50 hover:bg-gray-100 text-gray-500 rounded border border-gray-100 transition-colors z-20 tooltip"
                  title="查看历史批次记录"
                >
                  <span class="mr-1">📚</span>历史
                </button>
                <span class="group-hover:translate-x-1 transition-transform inline-block font-semibold">开始 →</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useExamStore } from '../stores/useExamStore'
import { useUserStore } from '../stores/useUserStore'
import request from '../utils/request'

const router    = useRouter()
const examStore = useExamStore()
const userStore = useUserStore()

// [T4] Paper progress map: { paperId: percentage }
const paperProgress = ref({})

onMounted(async () => {
  await examStore.fetchExams()
  // [T4] Fetch progress for all papers
  await fetchAllProgress()
})

// [T4] Batch fetch progress for all papers
const fetchAllProgress = async () => {
  const papers = examStore.examList
  if (!papers.length) return
  try {
    const results = await Promise.allSettled(
      papers.map(p =>
        request.get(`/exam/${p.paper_id}/progress`, {
          params: { slot_id: userStore.currentSlotId }
        })
      )
    )
    results.forEach((r, i) => {
      if (r.status === 'fulfilled' && r.value) {
        paperProgress.value[papers[i].paper_id] = r.value.percentage || 0
      }
    })
  } catch (e) {
    console.error('Progress fetch error:', e)
  }
}

const goToPaper = (id) => {
  router.push(`/exam/${id}`)
}

const goToReport = (id) => {
  router.push(`/report/${id}`)
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: #f0f0ec; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #d1d1cc; border-radius: 3px; }
</style>
