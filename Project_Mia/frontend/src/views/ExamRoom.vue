<template>
  <div class="min-h-screen w-full flex flex-col bg-[#f5f5f0] text-gray-900">
    <!-- 1. Toolbar -->
    <div class="border-b border-gray-200 bg-white flex items-center px-4 gap-3 lg:gap-6 shrink-0 z-20 shadow-sm flex-wrap py-2">
      <button @click="$router.push('/')" class="text-gray-400 hover:text-gray-800 transition-colors">
          ← Home
      </button>
      <div class="text-mia-pink font-bold text-lg mr-4">
          {{ examStore.currentPaper?.title || 'Loading...' }}
      </div>

      <!-- [Stage 28.1] Exam Shield Visual Tracker -->
      <div class="flex items-center gap-2 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 px-3 py-1.5 rounded-full shadow-inner tooltip-container group cursor-help transition-all hover:scale-105">
          <span class="text-lg animate-pulse" :class="examStore.paperHp < 50 ? 'text-red-500' : 'text-blue-500'">🛡️</span>
          <div class="flex flex-col min-w-[60px]">
             <span class="text-[9px] font-black text-blue-400 leading-none uppercase tracking-widest">Exam Shield</span>
             <span class="text-sm font-bold leading-tight" :class="examStore.paperHp < 50 ? 'text-red-600' : 'text-blue-700'">{{ examStore.paperHp }} <span class="text-blue-300 text-[10px]">/ {{ examStore.maxPaperHp }}</span></span>
          </div>
          <!-- Tooltip -->
          <div class="absolute top-[120%] left-1/2 -translate-x-1/2 bg-gray-800 text-white text-xs px-3 py-2 rounded shadow-xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none w-48 z-50">
             这是当前考卷的专属“精神护盾”。答错题会消耗它，别让主观情绪干扰了全局学习状态！
          </div>
      </div>
      
      <!-- [Stage 30.0] Time Engine Dashboard -->
      <div class="flex items-center gap-3 bg-white border border-gray-200 px-3 py-1 rounded-full shadow-sm ml-2">
         <div class="flex flex-col items-center min-w-[50px]">
            <span class="text-[9px] font-black text-gray-400 uppercase tracking-widest leading-none mb-0.5">Total</span>
            <span class="text-sm font-mono font-bold leading-none" :class="examStore.isPaused ? 'text-rose-400' : 'text-gray-700'">
               {{ examStore.isPaused ? '[暂停]' : formatTime(examStore.totalExamTime) }}
            </span>
         </div>
         <div class="w-px h-6 bg-gray-200"></div>
         <div class="flex flex-col items-center min-w-[50px]">
            <span class="text-[9px] font-black text-teal-400 uppercase tracking-widest leading-none mb-0.5">Task</span>
            <span class="text-sm font-mono font-bold leading-none" :class="examStore.isPaused ? 'text-gray-300' : 'text-teal-600'">
               {{ formatTime(examStore.currentQuestionTime) }}
            </span>
         </div>
      </div>

      <!-- [Stage 17.0] Progress Bar + Reset Button -->
      <div class="flex items-center gap-2">
        <div class="flex flex-col min-w-[120px]">
          <div class="flex justify-between text-[10px] text-gray-400 mb-0.5">
            <span>{{ progress.answered }}/{{ progress.total }}</span>
            <span>{{ progress.percentage }}%</span>
          </div>
          <div class="h-1.5 w-32 bg-gray-100 rounded-full overflow-hidden">
            <div
              class="h-full bg-emerald-400 rounded-full transition-all duration-500"
              :style="{ width: progress.percentage + '%' }"
            ></div>
          </div>
        </div>
        <button
          @click="resetPaper"
          class="text-[11px] px-2 py-1 bg-white border border-gray-200 rounded text-gray-400 hover:text-rose-500 hover:border-rose-300 transition-all"
          title="清空重做本卷"
        >🔄 二刷</button>
      </div>
      
      <!-- Font Size Slider -->
      <div class="flex items-center gap-2">
        <span class="text-xs">A-</span>
        <input 
          type="range" 
          min="0.9" max="1.8" step="0.05"
          v-model="fontSize"
          class="w-24 h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer accent-mia-pink"
        >
        <span class="text-xs">A+</span>
      </div>

      <div class="w-px h-6 bg-gray-700 mx-2"></div>

      <!-- Mode Switch: Read / Draw / Erase -->
      <div class="flex items-center gap-1 bg-gray-800 p-1 rounded-full border border-gray-700">
        <button 
          @click="setMode('read')"
          :class="['p-1.5 rounded-full transition-all text-sm', mode === 'read' ? 'bg-mia-pink text-black' : 'hover:bg-gray-700 text-gray-300']"
          title="阅读模式"
        >👆</button>
        <button 
          @click="setMode('draw')"
          :class="['p-1.5 rounded-full transition-all text-sm', mode === 'draw' ? 'bg-mia-pink text-black' : 'hover:bg-gray-700 text-gray-300']"
          title="画笔标注"
        >✏️</button>
        <button 
          @click="setMode('erase')"
          :class="['p-1.5 rounded-full transition-all text-sm', mode === 'erase' ? 'bg-mia-pink text-black' : 'hover:bg-gray-700 text-gray-300']"
          title="橡皮擦"
        >🧹</button>
      </div>

      <!-- Colors (draw/erase mode) -->
      <div v-show="mode === 'draw' || mode === 'erase'" class="flex items-center gap-2 animate-fade-in-left">
        <button @click="penColor = '#ff3b30'" class="w-6 h-6 lg:w-7 lg:h-7 rounded-full bg-red-500 border border-white touch-target" :class="{'ring-2 ring-mia-pink': penColor === '#ff3b30'}"></button>
        <button @click="penColor = '#ffcc00'" class="w-6 h-6 lg:w-7 lg:h-7 rounded-full bg-yellow-400 border border-white touch-target" :class="{'ring-2 ring-mia-pink': penColor === '#ffcc00'}"></button>
        <button @click="penColor = '#34c759'" class="w-6 h-6 lg:w-7 lg:h-7 rounded-full bg-green-500 border border-white touch-target" :class="{'ring-2 ring-mia-pink': penColor === '#34c759'}"></button>
        <div class="w-px h-5 bg-gray-600 mx-1"></div>
        <!-- Pen width -->
        <button @click="penWidth = Math.max(1, penWidth - 1)" class="w-6 h-6 flex items-center justify-center text-xs text-gray-300 hover:text-white rounded-full hover:bg-gray-700 transition-colors" title="细笔">−</button>
        <span class="text-[10px] text-gray-400 w-4 text-center">{{ penWidth }}</span>
        <button @click="penWidth = Math.min(8, penWidth + 1)" class="w-6 h-6 flex items-center justify-center text-xs text-gray-300 hover:text-white rounded-full hover:bg-gray-700 transition-colors" title="粗笔">+</button>
      </div>
      
      <div class="flex-1"></div>

      <!-- Undo + Clear -->
      <div v-show="mode === 'draw' || mode === 'erase'" class="flex items-center gap-1">
        <button @click="undoInk" class="px-2 py-1 text-[10px] text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors" title="撤销 (Ctrl+Z)">↩ 撤销</button>
        <button @click="clearInk" class="px-2 py-1 text-[10px] text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded transition-colors" title="清除全部">Clear</button>
      </div>
    </div>

    <!-- 2. Main Layout (Sidebar + Content) -->
    <div class="flex-1 flex overflow-hidden relative">
      
      <!-- Sidebar Navigation -->
      <div class="w-48 tablet:w-[clamp(192px,8vw,280px)] bg-white border-r border-gray-200 flex flex-col overflow-y-auto shrink-0 custom-scrollbar">
          <div v-if="loading" class="p-4 text-center text-gray-400 text-sm">Loading...</div>
          <template v-else>
              <div v-for="(item, idx) in navItems" :key="idx">
                  <button 
                    @click="switchSection(item)"
                    class="w-full text-left px-4 py-3 text-sm border-l-4 transition-all hover:bg-rose-50"
                    :class="currentNavId === item.id ? 'border-mia-pink-dark bg-rose-50 text-mia-pink-dark font-bold' : 'border-transparent text-gray-500'"
                  >
                      {{ item.label }}
                  </button>
              </div>
          </template>
      </div>

      <!-- Content Split Screen — [T3] 可拖拽分隔线 -->
      <div class="flex-1 flex overflow-hidden" v-if="currentData">
          <!-- Left: Passage Panel -->
          <div
            class="overflow-y-auto overflow-x-hidden custom-scrollbar pb-16 tablet:pb-12 bg-white relative"
            :style="{ width: (1 - splitRatio) * 100 + '%' }"
          >
             <div class="relative">
                <!-- Article Text -->
                <div 
                  class="p-6 lg:p-8 tablet:p-10 font-wenkai leading-loose text-justify text-gray-900 selection:bg-mia-pink selection:text-black transition-all"
                  :class="{ 'select-none': mode === 'draw' }"
                  :style="{ fontSize: fontSize + 'rem' }"
                >
                  <h2 class="text-xl font-bold mb-6 text-mia-pink">{{ currentData.label }}</h2>
                  
                  <!-- Writing B: base64 图片 prompt (Priority over passage) -->
                  <div v-if="currentData.type === 'writing_b'">
                    <div v-if="currentData.image && currentData.image.length > 100" class="flex flex-col items-center gap-3">
                      <img
                        :src="currentData.image.startsWith('data:') ? currentData.image : `data:image/png;base64,${currentData.image}`"
                        class="max-w-full h-auto max-h-[400px] object-contain border border-gray-200 rounded-xl shadow-md mx-auto"
                        alt="Writing Task Image"
                        @error="imgError = true"
                      />
                      <p class="text-xs text-gray-400">（试题图示）</p>
                    </div>
                    <div v-else class="w-full h-48 bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg flex flex-col items-center justify-center text-gray-400 mb-4">
                      <span class="text-3xl mb-2">🖼️</span>
                      <span class="text-sm">暂无图片数据</span>
                      <span class="text-xs mt-1">（年份：{{ examStore.currentPaper?.year }}）</span>
                    </div>
                    <div v-if="currentData.passage" class="whitespace-pre-wrap mb-4">{{ currentData.passage }}</div>
                    <div v-else-if="currentData.prompt" class="mt-4 font-wenkai leading-relaxed text-gray-700">{{ currentData.prompt }}</div>
                  </div>

                  <!-- Writing A: 只有文字 prompt -->
                  <div v-else-if="currentData.type === 'writing_a'">
                    <div v-if="currentData.passage" class="whitespace-pre-wrap">{{ currentData.passage }}</div>
                    <div v-else class="font-wenkai leading-relaxed text-gray-700">{{ currentData.prompt }}</div>
                  </div>

                  <!-- Dynamic Content: Passage (Fallback for Reading/Translation) -->
                  <div v-else-if="currentData.passage" class="whitespace-pre-wrap">{{ currentData.passage }}</div>

                  <div v-else class="text-gray-500 italic">[No passage content]</div>
                </div>

                <!-- Ink Overlay -->
                <!-- Keybinding to section ID ensures component re-creation or just data update? -->
                <!-- If we use same component, we rely on watcher. -->
                <InkCanvas 
                  ref="inkCanvasRef"
                  v-model:data="canvasData"
                  :mode="mode"
                  :color="penColor"
                  :width="penWidth"
                  :initial-data="initialAnnotation"
                />
             </div>
          </div>

          <!-- [T3] 可拖拽分隔线 -->
          <div
            ref="dividerRef"
            class="w-1.5 bg-gray-200 hover:bg-rose-300 cursor-col-resize shrink-0 transition-colors relative group"
            @mousedown="startDrag"
            @touchstart.prevent="startDragTouch"
          >
            <div class="absolute inset-y-0 -left-1 -right-1"></div>
            <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-5 h-10 rounded-full bg-white border border-gray-300 shadow-sm flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
              <span class="text-gray-400 text-xs">⋮</span>
            </div>
          </div>

          <!-- Right: Questions Panel — [T3] 动态宽度 -->
          <div
            class="flex flex-col bg-[#fafafa] z-10 shadow-[-4px_0_12px_rgba(0,0,0,0.06)] border-l border-gray-200"
            :style="{ width: splitRatio * 100 + '%', minWidth: '280px' }"
          >
             <div class="p-4 border-b border-gray-200 font-semibold text-gray-600 text-sm tracking-wide">习题</div>
             <div class="flex-1 overflow-y-auto overflow-x-hidden p-4 pb-32 tablet:pb-16 custom-scrollbar bg-[#fafafa]">
                 
                 <!-- 客观题：完形 / 阅读 -->
                 <template v-if="currentData.questions && currentData.questions.length > 0
                                 && !currentData.type.includes('translation')
                                 && !currentData.type.startsWith('writing')">
                     <SingleChoice
                        v-for="q in currentData.questions"
                        :key="q.q_id"
                        :question="q"
                     />
                 </template>

                 <!-- 翻译题：每句一个 SubjectiveInput -->
                 <template v-else-if="currentData.type === 'translation'">
                   <div class="space-y-6">
                     <div
                       v-for="(q, idx) in currentData.questions"
                       :key="q.q_id"
                       class="bg-white rounded-2xl p-4 shadow-sm border border-gray-100"
                     >
                       <div class="flex items-center gap-2 mb-3">
                         <span class="w-6 h-6 rounded-full bg-rose-100 text-rose-500 text-xs font-bold flex items-center justify-center">{{ idx + 1 }}</span>
                         <span class="text-xs text-gray-400">{{ q.score }} 分</span>
                       </div>
                       <SubjectiveInput
                         :q-id="q.q_id"
                         :content="q.content"
                         :rows="4"
                         :max-score="q.score || 10"
                         section-type="translation"
                         placeholder="输入译文…"
                       />
                     </div>
                   </div>
                 </template>

                 <!-- 写作题 A / B: SubjectiveInput -->
                 <template v-else-if="currentData.type === 'writing_a' || currentData.type === 'writing_b'">
                   <div class="bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
                     <SubjectiveInput
                       :key="currentData.q_id || currentData.type"
                       :q-id="currentData.q_id || currentData.type"
                       :rows="currentData.type === 'writing_b' ? 16 : 10"
                       :max-score="currentData.type === 'writing_b' ? 20 : 10"
                       :max-words="currentData.type === 'writing_b' ? 200 : 100"
                       :section-type="currentData.type"
                       placeholder="在此写你的作文…"
                     />
                   </div>
                 </template>
                 
             </div>
          </div>
      </div>
    </div>
    


  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useWindowSize } from '@vueuse/core'
import { useExamStore } from '../stores/useExamStore'
import { useMiaStore } from '../stores/useMiaStore'
import { useUserStore } from '../stores/useUserStore'
import request from '../utils/request'
import InkCanvas from '../components/InkCanvas.vue'
import SingleChoice from '../components/exam/SingleChoice.vue'
import EssayBox from '../components/exam/EssayBox.vue'
import SubjectiveInput from '../components/exam/SubjectiveInput.vue'

const route = useRoute()
const examStore = useExamStore()
const miaStore = useMiaStore()
const userStore = useUserStore()

// [Stage 17.0] Progress state
const progress = ref({ answered: 0, total: 0, percentage: 0 })

const fetchProgress = async () => {
    const paperId = route.params.paperId
    try {
        const res = await request.get(`/exam/${paperId}/progress`, {
            params: { slot_id: userStore.currentSlotId }
        })
        if (res) progress.value = res
    } catch(e) {
        console.error('Progress fetch failed:', e)
    }
}

const resetPaper = async () => {
    const paperId = route.params.paperId
    if (!confirm('确定要清空本卷的当前作答记录开启二刷吗？历史轨迹将被保留。')) return
    try {
        await request.delete(`/exam/${paperId}/reset`, {
            params: { slot_id: userStore.currentSlotId }
        })
        // Refresh answer state and progress
        await examStore.fetchAnswerHistory()
        await fetchProgress()
    } catch(e) {
        alert('重置失败：' + e.message)
    }
}

// State
// [T3] 平板检测
const { width: winWidth } = useWindowSize()
const isTablet = computed(() => winWidth.value >= 2000)

// [T3] 可拖拽分栏比例 (right panel ratio, default 0.35 desktop / 0.40 tablet)
const splitRatio = ref(isTablet.value ? 0.40 : 0.35)
const dividerRef = ref(null)
const isDragging = ref(false)

const fontSize = ref(isTablet.value ? 1.25 : 1.1)
const mode = ref('read')
const penColor = ref('#ff3b30')
const canvasData = ref('')
const initialAnnotation = ref('')
const inkCanvasRef = ref(null)

const loading = computed(() => examStore.loading)
const miaMessage = computed(() => miaStore.currentText || '认真审题哦，这次不要再粗心了！')

// Navigation Logic
const navItems = computed(() => {
    const s = examStore.currentPaper?.sections
    if (!s) return []
    
    const list = []
    
    if (s.use_of_english) {
        list.push({ id: 'cloze', label: 'Use of English', type: 'use_of_english', data: s.use_of_english })
    }
    
    // Reading A (Array)
    if (s.reading_a) {
        s.reading_a.forEach((g, idx) => {
            list.push({ id: `rea_${idx}`, label: `Reading A - ${g.group_name}`, type: 'reading_a', data: g })
        })
    }
    
    // Reading B (Array)
    if (s.reading_b) {
         s.reading_b.forEach((g, idx) => {
            list.push({ id: `reb_${idx}`, label: `Reading B - ${g.group_name}`, type: 'reading_b', data: g })
        })
    }
    
    if (s.translation) {
        list.push({ id: 'trans', label: 'Translation', type: 'translation', data: s.translation })
    }
    
    if (s.writing_a) {
        list.push({ id: 'wra', label: 'Writing A', type: 'writing_a', data: s.writing_a })
    }
    
     if (s.writing_b) {
        list.push({ id: 'wrb', label: 'Writing B', type: 'writing_b', data: s.writing_b })
    }
    
    return list
})

const currentNavId = ref(null)
const currentData = computed(() => {
    const item = navItems.value.find(i => i.id === currentNavId.value)
    if (!item) return null
    // Merge label/type into data for template usage
    return { ...item.data, label: item.label, type: item.type }
})

// Lifecycle
onMounted(async () => {
    console.log('ExamRoom Mounted. Fetching paper:', route.params.paperId)
    const result = await examStore.fetchPaper(route.params.paperId)
    
    // [Stage 25.0] If paper not found, toast and redirect
    if (!result || examStore.lastError) {
        alert(examStore.lastError || '未找到对应试卷')
        // Navigate back after a moment
        setTimeout(() => {
            import('vue-router').then(() => {
                // Already have route, use router from import
            })
        }, 0)
        return
    }
    
    console.log('Paper Loaded:', examStore.currentPaper)
    
    // [Stage 17.0] Fetch progress
    await fetchProgress()
    
    // Select first item
    if (navItems.value.length > 0) {
        switchSection(navItems.value[0])
    } else {
        console.warn('No nav items found! Check backend response sections.')
    }
    
    // [Stage 30.0] Start Time Engine
    examStore.startExamTimer()
})

onBeforeUnmount(() => {
    examStore.stopExamTimer()
})

// [Stage 30.0] Time Engine formatter
const formatTime = (seconds) => {
    if (!seconds) return '00:00'
    const m = Math.floor(seconds / 60).toString().padStart(2, '0')
    const s = (seconds % 60).toString().padStart(2, '0')
    if (seconds >= 3600) {
        const h = Math.floor(seconds / 3600).toString()
        return `${h}:${m}:${s}`
    }
    return `${m}:${s}`
}

// Switching Sections
// CRITICAL: Manage InkCanvas State
const switchSection = (item) => {
    if (currentNavId.value === item.id) return
    
    // 1. Save current
    if (currentNavId.value && canvasData.value) {
        examStore.saveAnnotation(route.params.paperId, currentNavId.value, canvasData.value)
    }
    
    // 2. Switch
    currentNavId.value = item.id
    
    // 3. Reset Canvas triggers
    // We update initialAnnotation to trigger watch in InkCanvas
    const saved = examStore.loadAnnotation(route.params.paperId, item.id)
    initialAnnotation.value = saved || '' 
    canvasData.value = '' // Clear current v-model binding
    
    // Note: If saved is empty, we must ensure InkCanvas is cleared visually.
    // Logic inside InkCanvas watcher handles "if (newVal) ... else ?".
    // I should check InkCanvas watcher logic.
    // If newVal is empty, it does nothing?
    // We need to FORCE clear if new section has no data.
    // I will call clear() explicitly via ref next tick.
    setTimeout(() => {
        if (!saved && inkCanvasRef.value) {
             inkCanvasRef.value.clear()
        }
    }, 50)
}

// Watchers
watch(fontSize, () => {
    inkCanvasRef.value?.clear()
    miaStore.speak('字体变化了喵！笔记已经帮你清理掉了，重新记一下吧~')
})

// Auto Save (Debounced?)
// For now save on change is heavy if too frequent, but usually `save` logic is just updating local state.
// Writing to localStorage is sync.
// Only save if section is set.
watch(canvasData, (val) => {
    if (currentNavId.value && val) {
        examStore.saveAnnotation(route.params.paperId, currentNavId.value, val)
    }
})

// [T3] 可拖拽分隔线 handlers
let _dragContainer = null

const startDrag = (e) => {
  e.preventDefault()
  isDragging.value = true
  _dragContainer = dividerRef.value?.parentElement
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}
const startDragTouch = (e) => {
  e.preventDefault()
  isDragging.value = true
  _dragContainer = dividerRef.value?.parentElement
  document.addEventListener('touchmove', onDragTouch)
  document.addEventListener('touchend', stopDragTouch)
}
const onDrag = (e) => {
  if (!isDragging.value || !_dragContainer) return
  const rect = _dragContainer.getBoundingClientRect()
  const ratio = 1 - (e.clientX - rect.left) / rect.width
  splitRatio.value = Math.max(0.2, Math.min(0.6, ratio))
}
const onDragTouch = (e) => {
  if (!isDragging.value || !_dragContainer) return
  const rect = _dragContainer.getBoundingClientRect()
  const ratio = 1 - (e.touches[0].clientX - rect.left) / rect.width
  splitRatio.value = Math.max(0.2, Math.min(0.6, ratio))
}
const stopDrag = () => {
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}
const stopDragTouch = () => {
  isDragging.value = false
  document.removeEventListener('touchmove', onDragTouch)
  document.removeEventListener('touchend', stopDragTouch)
}

// [T3] Cleanup drag listeners on unmount
onBeforeUnmount(() => {
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', onDragTouch)
  document.removeEventListener('touchend', stopDragTouch)
})

// Helpers
const setMode = (m) => mode.value = m
const penWidth = ref(2)

const undoInk = () => {
  inkCanvasRef.value?.undo()
}

const clearInk = () => {
    if(confirm('Clear current notes?')) inkCanvasRef.value?.clear()
}

</script>
