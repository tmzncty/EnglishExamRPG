<template>
  <div class="h-screen w-full flex flex-col bg-[#f5f5f0] text-gray-900">
    <!-- 1. Toolbar -->
    <div class="h-12 border-b border-gray-200 bg-white flex items-center px-4 gap-6 shrink-0 z-20 shadow-sm">
      <button @click="$router.push('/')" class="text-gray-400 hover:text-gray-800 transition-colors">
          ← Home
      </button>
      <div class="text-mia-pink font-bold text-lg mr-4">
          {{ examStore.currentPaper?.title || 'Loading...' }}
      </div>
      
      <!-- Font Size Slider -->
      <div class="flex items-center gap-2">
        <span class="text-xs">A-</span>
        <input 
          type="range" 
          min="14" max="24" 
          v-model="fontSize"
          class="w-24 h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer accent-mia-pink"
        >
        <span class="text-xs">A+</span>
      </div>

      <div class="w-px h-6 bg-gray-700 mx-2"></div>

      <!-- Pen Controls -->
      <div class="flex items-center gap-2 bg-gray-800 p-1 rounded-full border border-gray-700">
        <button 
          @click="setMode('read')"
          :class="['p-1.5 rounded-full transition-all', mode === 'read' ? 'bg-mia-pink text-black' : 'hover:bg-gray-700']"
          title="阅读模式"
        >
          👆
        </button>
        <button 
          @click="setMode('draw')"
          :class="['p-1.5 rounded-full transition-all', mode === 'draw' ? 'bg-mia-pink text-black' : 'hover:bg-gray-700']"
          title="标注模式"
        >
          ✏️
        </button>
      </div>

      <!-- Colors -->
      <div v-show="mode === 'draw'" class="flex items-center gap-2 animate-fade-in-left">
        <button @click="penColor = '#ff3b30'" class="w-5 h-5 rounded-full bg-red-500 border border-white" :class="{'ring-2 ring-mia-pink': penColor === '#ff3b30'}"></button>
        <button @click="penColor = '#ffcc00'" class="w-5 h-5 rounded-full bg-yellow-400 border border-white" :class="{'ring-2 ring-mia-pink': penColor === '#ffcc00'}"></button>
        <button @click="penColor = '#34c759'" class="w-5 h-5 rounded-full bg-green-500 border border-white" :class="{'ring-2 ring-mia-pink': penColor === '#34c759'}"></button>
      </div>
      
      <div class="flex-1"></div>
      <button @click="clearInk" class="text-xs hover:text-red-400">Clear Ink</button>
    </div>

    <!-- 2. Main Layout (Sidebar + Content) -->
    <div class="flex-1 flex overflow-hidden relative">
      
      <!-- Sidebar Navigation -->
      <div class="w-48 bg-white border-r border-gray-200 flex flex-col overflow-y-auto shrink-0 custom-scrollbar">
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

      <!-- Content Split Screen -->
      <div class="flex-1 flex overflow-hidden" v-if="currentData">
          <!-- Left: Passage Panel -->
          <div class="flex-1 border-r border-gray-200 bg-white relative overflow-auto custom-scrollbar">
             <div class="relative min-h-full">
                <!-- Article Text -->
                <div 
                  class="p-8 font-wenkai leading-loose text-justify text-gray-900 selection:bg-mia-pink selection:text-black transition-all"
                  :class="{ 'select-none': mode === 'draw' }"
                  :style="{ fontSize: fontSize + 'px' }"
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
                  :width="3"
                  :initial-data="initialAnnotation"
                />
             </div>
          </div>

          <!-- Right: Questions Panel -->
          <div class="w-[450px] flex flex-col bg-[#fafafa] z-10 shadow-[-4px_0_12px_rgba(0,0,0,0.06)] border-l border-gray-200">
             <div class="p-4 border-b border-gray-200 font-semibold text-gray-600 text-sm tracking-wide">习题</div>
             <div class="flex-1 overflow-auto p-4 pb-48 custom-scrollbar bg-[#fafafa]">
                 
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
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useExamStore } from '../stores/useExamStore'
import { useMiaStore } from '../stores/useMiaStore'
import InkCanvas from '../components/InkCanvas.vue'
import SingleChoice from '../components/exam/SingleChoice.vue'
import EssayBox from '../components/exam/EssayBox.vue'
import SubjectiveInput from '../components/exam/SubjectiveInput.vue'

const route = useRoute()
const examStore = useExamStore()
const miaStore = useMiaStore()

// State
const fontSize = ref(18)
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
    await examStore.fetchPaper(route.params.paperId)
    console.log('Paper Loaded:', examStore.currentPaper)
    
    // Select first item
    if (navItems.value.length > 0) {
        switchSection(navItems.value[0])
    } else {
        console.warn('No nav items found! Check backend response sections.')
    }
})

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

// Helpers
const setMode = (m) => mode.value = m
const clearInk = () => {
    if(confirm('Clear current notes?')) inkCanvasRef.value?.clear()
}

</script>
