<template>
  <div class="min-h-screen bg-gradient-to-b from-emerald-50 to-teal-50 flex flex-col items-center relative overflow-hidden">
    
    <!-- 🌿 [Stage 20.0 / 21.0] Minimal Top Bar -->
    <div class="w-full px-6 py-3 flex justify-between items-center z-20 sticky top-0">
      
      <!-- 📚 [Stage 21.0] Dictionary Button -->
      <button 
        @click="openDictionary"
        class="bg-white/70 backdrop-blur-md px-4 py-2 rounded-xl shadow-sm border border-teal-100 hover:bg-white transition-colors flex items-center gap-2 group cursor-pointer"
      >
        <span class="text-xl group-hover:scale-110 transition-transform">📚</span>
        <span class="text-xs font-bold text-teal-700 hidden sm:inline">我的词库</span>
      </button>

      <div class="text-right bg-white/70 backdrop-blur-md px-4 py-2 rounded-xl shadow-sm border border-teal-100">
         <div class="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Today's Goal</div>
         <div class="text-xl font-wenkai font-bold text-teal-700">
            {{ vocabStore.dailyProgress.reviewed }} / <span class="text-teal-400">{{ userStore.dailyLimit }}</span>
         </div>
      </div>
    </div>

    <!-- 🌸 Main Card Area -->
    <div class="flex-1 flex flex-col justify-center w-full max-w-md px-6 relative z-10 pb-24">
      
      <!-- Loading State -->
      <div v-if="vocabStore.loading" class="text-center text-teal-600 animate-pulse">
        <div class="text-4xl mb-4">🌱</div>
        <p>Connecting to the Garden...</p>
      </div>

      <!-- Finish State -->
      <div v-else-if="!vocabStore.currentWord" class="text-center p-8 bg-white/80 rounded-3xl shadow-xl backdrop-blur">
        <div class="text-6xl mb-4">🎉</div>
        <h2 class="text-2xl font-bold text-teal-800 mb-2">Garden Tended!</h2>
        <p class="text-teal-600 mb-6 font-wenkai">You've watered all your logic plants for today.</p>
        <button 
            @click="router.push('/')"
            class="px-6 py-3 bg-teal-500 text-white rounded-full font-bold shadow-lg hover:bg-teal-600 transition-all transform hover:scale-105 active:scale-95"
        >
            Return to Hall
        </button>
      </div>

      <!-- Active Card -->
      <div v-else class="relative w-full aspect-[3/4] perspective-1000">
        <div 
            class="w-full h-full relative transition-all duration-500 transform-style-3d"
            :class="{ 'rotate-y-180': isRevealed }"
        >
            <!-- FRONT: Question -->
            <div class="absolute inset-0 backface-hidden bg-white rounded-3xl shadow-xl border border-emerald-100 p-8 flex flex-col justify-between">
                <div class="flex-1 flex flex-col justify-center items-center text-center">
                    <h1 class="text-5xl font-black text-gray-800 mb-6 tracking-tight">{{ vocabStore.currentWord.word }}</h1>
                    
                    <!-- Sentence (First one) -->
                    <div v-if="vocabStore.currentWord.sentences && vocabStore.currentWord.sentences.length" class="bg-emerald-50/50 p-4 rounded-xl border border-emerald-50 overflow-y-auto max-h-[50vh] custom-scrollbar">
                        <p class="exam-sentence text-lg font-serif italic text-gray-600 leading-relaxed">
                            "{{ vocabStore.currentWord.sentences[0].sentence }}"
                        </p>
                    </div>
                </div>
                
                <div class="text-center text-gray-400 text-sm font-wenkai">
                    Think about the meaning...
                </div>
            </div>

            <!-- BACK: Answer (Revealed) -->
            <div class="absolute inset-0 backface-hidden rotate-y-180 bg-white rounded-3xl shadow-xl border border-teal-100 flex flex-col overflow-hidden">
                <div class="flex-1 overflow-y-auto custom-scrollbar p-8 pb-4">
                    <div class="text-center border-b border-gray-100 pb-4 mb-4">
                        <h2 class="text-3xl font-bold text-teal-700">{{ vocabStore.currentWord.word }}</h2>
                        <p class="text-gray-400 mt-1 font-mono text-sm">/ {{ vocabStore.currentWord.phonetic || '...' }} /</p>
                    </div>

                    <!-- Meanings -->
                    <div class="mb-6">
                        <h3 class="text-xs font-bold text-gray-400 uppercase mb-2">Meanings</h3>
                        <ul class="space-y-2">
                            <li v-for="(m, idx) in vocabStore.currentWord.meanings" :key="idx" class="text-gray-700 font-medium leading-relaxed">
                                {{ m }}
                            </li>
                        </ul>
                    </div>

                    <!-- Notes & Context -->
                    <div class="mb-2">
                        <h3 class="text-xs font-bold text-gray-400 uppercase mb-2">Notes & Context</h3>
                        <p class="text-sm text-gray-500 leading-relaxed mb-3">
                            Part of Speech: <span class="font-mono bg-gray-100 px-1 rounded">{{ vocabStore.currentWord.pos }}</span>
                        </p>
                        
                        <!-- Show sentence context and translation if available -->
                        <div v-if="vocabStore.currentWord.sentences && vocabStore.currentWord.sentences.length > 0" class="p-4 bg-emerald-50/50 rounded-xl text-sm font-wenkai relative border border-emerald-50 text-gray-700">
                            <p class="exam-sentence mb-2 italic leading-relaxed text-gray-600">"{{ vocabStore.currentWord.sentences[0].sentence }}"</p>
                            <p v-if="vocabStore.currentWord.sentences[0].translation" class="text-teal-800 leading-relaxed">{{ vocabStore.currentWord.sentences[0].translation }}</p>
                            
                            <div class="mt-3 text-right">
                               <button 
                                 @click="goToExam(vocabStore.currentWord.sentences[0])"
                                 class="text-xs font-bold text-teal-600 hover:text-teal-800 underline underline-offset-2 decoration-teal-300 transition-colors bg-white/50 px-2 py-1 rounded"
                               >
                                  [🔗 去原卷看看]
                               </button>
                            </div>
                        </div>
                    </div>

                    <!-- [Stage 23.0] 💡 Global Mia AI Explanation Button -->
                    <div class="mt-4 mb-2">
                        <button
                            @click="callMiaGlobal"
                            class="w-full py-2.5 rounded-xl border border-amber-200 text-amber-600 bg-amber-50 text-sm font-bold hover:bg-amber-100 active:scale-95 transition-all flex items-center justify-center gap-2"
                        >
                            <span>💡</span>
                            <span>呼叫 Mia 详细讲解</span>
                        </button>
                    </div>
                </div>

                <!-- 🎮 Grading Action Bar (Visible when Back) -->
                <div class="p-6 pt-2 bg-gradient-to-t from-white via-white shrink-0 z-10 flex justify-between gap-4">
                    <button 
                        @click="handleAnswer(0)"
                        class="flex-1 py-3 bg-white border-2 border-rose-200 text-rose-500 rounded-xl font-bold shadow-sm hover:bg-rose-50 active:scale-95 transition-all flex items-center justify-center gap-2"
                        :disabled="vocabStore.submitting"
                        :class="{ 'opacity-50 cursor-not-allowed': vocabStore.submitting }"
                    >
                        <span class="text-xl">❌</span>
                        <span>记错了 (Forgot)</span>
                    </button>

                    <button 
                        @click="handleAnswer(5)"
                        class="flex-1 py-3 bg-teal-500 border-2 border-teal-500 text-white rounded-xl font-bold shadow-sm hover:bg-teal-600 active:scale-95 transition-all flex items-center justify-center gap-2"
                        :disabled="vocabStore.submitting"
                        :class="{ 'opacity-50 cursor-not-allowed': vocabStore.submitting }"
                    >
                        <span class="text-xl">✅</span>
                        <span>记对了 (Correct)</span>
                    </button>
                </div>
            </div>
        </div>
      </div>
    </div>

    <!-- 🎮 Action Bar (Only visible when Front) -->
    <div v-if="vocabStore.currentWord && !isRevealed" class="fixed bottom-10 left-0 w-full px-8 flex justify-center z-30">
        <button 
            @click="isRevealed = true"
            class="w-full max-w-sm py-4 bg-teal-500 border-2 border-teal-500 text-white rounded-2xl font-bold shadow-lg hover:bg-teal-600 active:scale-95 transition-all flex flex-col items-center"
        >
            <span class="text-2xl mb-1">👆</span>
            <span>点击查看释义 (Show Answer)</span>
        </button>
    </div>

    <!-- ✨ Reward Popup -->
    <transition name="pop">
        <div v-if="showReward" class="fixed top-1/3 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 pointer-events-none">
            <div class="flex flex-col items-center animate-float-up">
                <span class="text-4xl">✨</span>
                <span class="text-rose-500 font-black text-2xl text-shadow-sm">{{ rewardText.hp }}</span>
                <span class="text-teal-500 font-bold text-lg">{{ rewardText.exp }}</span>
            </div>
        </div>
    </transition>

    <!-- 📚 [Stage 22.0] Dictionary Drawer -->
    <transition name="slide-up">
      <div v-if="showDictionary" class="fixed inset-0 z-[100] flex flex-col bg-white overflow-hidden shadow-2xl">
        <!-- Header -->
        <div class="px-6 py-4 flex flex-col sm:flex-row justify-between items-start sm:items-center border-b border-gray-100 bg-teal-50 shrink-0 gap-4">
          <div class="flex-1 w-full">
            <h2 class="text-2xl font-black text-teal-800 flex justify-between items-center w-full">
              <span>📚 我的词库 (Lv.{{ userStore.level }})</span>
              <button @click="showDictionary = false" class="text-3xl text-gray-400 hover:text-rose-500 transition-colors cursor-pointer sm:hidden">
                &times;
              </button>
            </h2>
            <div v-if="dictStats" class="mt-2 text-sm font-bold text-teal-600">
              掌握词汇: {{ dictStats.learned }} / {{ dictStats.total }} (剩余 {{ dictStats.unlearned }})
            </div>
            <div v-if="dictStats" class="mt-1 text-[11px] text-teal-600 bg-teal-100/50 inline-block px-3 py-1 rounded-full font-bold">
              {{ getETAString(dictStats.total, dictStats.learned, userStore.dailyLimit) }}
            </div>
          </div>
          
          <div class="flex flex-col gap-2 w-full sm:w-auto relative items-end">
              <button @click="showDictionary = false" class="hidden sm:block text-3xl text-gray-400 hover:text-rose-500 transition-colors cursor-pointer mb-2">
                &times;
              </button>
              <!-- Search Bar -->
              <div class="relative w-full sm:w-64">
                <input 
                  type="text" 
                  v-model="searchQuery"
                  placeholder="🔍 搜索单词或释义..." 
                  class="w-full px-4 py-2.5 rounded-xl border border-teal-200 outline-none focus:border-teal-500 focus:ring-2 ring-teal-200/50 transition-all text-sm bg-white"
                />
              </div>
          </div>
        </div>

        <!-- Tabs -->
        <div class="flex gap-4 px-6 py-3 bg-white border-b border-gray-100 shrink-0 overflow-x-auto custom-scrollbar shadow-sm z-10">
            <button v-for="tab in ['All', 'Unlearned', 'Learning', 'Mastered']" :key="tab"
              @click="currentTab = tab; currentPage = 1"
              class="px-5 py-2 rounded-full text-xs font-bold transition-all whitespace-nowrap"
              :class="currentTab === tab ? 'bg-teal-500 text-white shadow-md transform scale-105' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'"
            >
              {{ 
                  tab === 'All' ? '全部 (All)' : 
                  tab === 'Unlearned' ? '未学 (Unlearned)' : 
                  tab === 'Learning' ? '学习中 (Learning)' : '已掌握 (Mastered)' 
              }}
            </button>
        </div>

        <!-- List Content -->
        <div class="flex-1 overflow-y-auto custom-scrollbar p-6 bg-gray-50">
          <div v-if="dictLoading" class="text-center py-20 text-gray-400 animate-pulse font-bold">
            正在加载浩瀚词海...
          </div>
          <div v-else-if="paginatedDictList.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pb-6">
            <div 
              v-for="item in paginatedDictList" :key="item.word"
              class="flex items-center justify-between p-4 bg-white rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-all hover:-translate-y-0.5"
            >
              <div class="flex-1 min-w-0 pr-4">
                 <div class="flex items-baseline gap-2">
                   <span class="font-black text-lg text-gray-800">{{ item.word }}</span>
                   <span class="text-[10px] font-mono text-gray-400 bg-gray-50 px-1 rounded">{{ item.phonetic || '...' }}</span>
                 </div>
                 <div class="text-xs text-gray-500 truncate mt-1" :title="item.meanings.join('; ')">
                   {{ item.meanings.join('; ') }}
                 </div>
              </div>
              
              <!-- Mastery Dots (0-7) -->
              <div class="flex flex-col items-end gap-1 shrink-0">
                 <div class="flex gap-0.5" title="掌握度阶段 (0-7)">
                   <div 
                    v-for="i in 7" :key="i"
                    class="w-1.5 h-1.5 rounded-full transition-colors"
                    :class="[
                      item.mastery_level >= i 
                        ? (i <= 3 ? 'bg-amber-400' : i <= 6 ? 'bg-teal-400' : 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.6)]') 
                        : 'bg-gray-100'
                    ]"
                   ></div>
                 </div>
                 <div v-if="item.status === 'learned'" class="text-[10px] font-bold" :class="item.mastery_level >= 7 ? 'text-rose-500' : 'text-teal-600'">
                   连击 {{ item.success_streak }}
                 </div>
                 <div v-else class="text-[10px] text-gray-300 font-bold">
                   未学习
                 </div>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-20 text-gray-400 font-bold">
              这里空空的，没有找到匹配的单词喵~
          </div>
          
          <!-- Pagination Controls -->
          <div v-if="!dictLoading && totalPages > 1" class="flex justify-center items-center gap-4 mt-6 pb-8">
              <button 
                @click="currentPage > 1 ? currentPage-- : null" 
                :disabled="currentPage === 1"
                class="px-4 py-2 rounded-xl font-bold transition-all"
                :class="currentPage === 1 ? 'bg-gray-100 text-gray-300 cursor-not-allowed' : 'bg-white text-teal-600 shadow-sm hover:shadow hover:bg-teal-50 border border-teal-100 active:scale-95'"
              >
                ← 上一页
              </button>
              <span class="text-sm font-bold text-gray-500 px-2 bg-white rounded-lg border border-gray-100 py-1">
                {{ currentPage }} / {{ totalPages }}
              </span>
              <button 
                @click="currentPage < totalPages ? currentPage++ : null" 
                :disabled="currentPage === totalPages"
                class="px-4 py-2 rounded-xl font-bold transition-all"
                :class="currentPage === totalPages ? 'bg-gray-100 text-gray-300 cursor-not-allowed' : 'bg-white text-teal-600 shadow-sm hover:shadow hover:bg-teal-50 border border-teal-100 active:scale-95'"
              >
                下一页 →
              </button>
          </div>
        </div>
      </div>
    </transition>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useVocabStore } from '../stores/useVocabStore'
import { useUserStore } from '../stores/useUserStore'
import { useMiaStore } from '../stores/useMiaStore'
import request from '../utils/request'

const router = useRouter()
const vocabStore = useVocabStore()
const userStore = useUserStore()
const miaStore = useMiaStore()

const isRevealed = ref(false)
const showReward = ref(false)
const rewardText = ref({ hp: '', exp: '' })

// [Stage 22.0] Dictionary Drawer State
const showDictionary = ref(false)
const dictLoading = ref(false)
const dictList = ref([])
const dictStats = ref(null)

const searchQuery = ref('')
const currentTab = ref('All') // 'All', 'Unlearned', 'Learning', 'Mastered'
const currentPage = ref(1)
const itemsPerPage = 50

watch([searchQuery, currentTab], () => {
    currentPage.value = 1
})

const filteredDictList = computed(() => {
    let list = dictList.value
    
    // 1. Filter by Tab
    if (currentTab.value === 'Unlearned') {
        list = list.filter(item => item.status === 'unlearned')
    } else if (currentTab.value === 'Learning') {
        list = list.filter(item => item.status === 'learned' && item.mastery_level < 7)
    } else if (currentTab.value === 'Mastered') {
        list = list.filter(item => item.status === 'learned' && item.mastery_level >= 7)
    }
    
    // 2. Filter by Search
    const q = searchQuery.value.trim().toLowerCase()
    if (q) {
        list = list.filter(item => item.word.toLowerCase().includes(q) || (item.meanings && item.meanings.join(' ').toLowerCase().includes(q)))
    }
    
    return list
})

const totalPages = computed(() => Math.ceil(filteredDictList.value.length / itemsPerPage) || 1)

const paginatedDictList = computed(() => {
    const start = (currentPage.value - 1) * itemsPerPage
    const end = start + itemsPerPage
    return filteredDictList.value.slice(start, end)
})

const getETAString = (total, learned, dailyLimit) => {
    const limit = dailyLimit || 30
    const remaining = total - Math.max(0, learned || 0)
    if (remaining <= 0) return '💡 全部词汇已背完，太棒了喵！'
    
    const days = Math.ceil(remaining / limit)
    const etaDate = new Date()
    etaDate.setDate(etaDate.getDate() + days)
    
    const yyyy = etaDate.getFullYear()
    const mm = String(etaDate.getMonth() + 1).padStart(2, '0')
    const dd = String(etaDate.getDate()).padStart(2, '0')
    
    return `💡 按每日 ${limit} 词的进度，预计还需 ${days} 天（约 ${yyyy}年${mm}月${dd}日）背完考研词汇，加油喵！`
}

onMounted(async () => {
    // Ensuring user slot is correct
    if (!userStore.currentSlotId) {
        await userStore.init()
    }
    // [Stage 25.0] Only fetch if no active session (prevents resetting currentIndex on tab switch)
    const hasActiveSession = vocabStore.todayTasks.length > 0 &&
                             vocabStore.currentIndex < vocabStore.todayTasks.length
    if (!hasActiveSession) {
        await vocabStore.fetchTodayVocab()
    }
})

const handleAnswer = async (quality) => {
    if (vocabStore.submitting) return;

    // 1. Submit Logic
    const res = await vocabStore.submitReview(quality)
    
    // 2. Visual Feedback
    if (res && res.reward) { // Check if reward exists
       const { hp, exp } = res.reward
       if (hp !== 0 || exp > 0) {
           rewardText.value.hp = hp > 0 ? `+${hp} HP` : `${hp} HP`
           rewardText.value.exp = exp > 0 ? `+${exp} EXP` : ''
           showReward.value = true
           setTimeout(() => showReward.value = false, 1500)
       }
    }

    // 3. Move to next word
    nextWord()
}

// [Stage 21.0] Open Dictionary view
const openDictionary = async () => {
    showDictionary.value = true
    dictLoading.value = true
    try {
        const res = await request.get('/vocab/list', { params: { slot_id: userStore.currentSlotId } })
        if (res && res.items) {
            dictList.value = res.items
            dictStats.value = {
                total: res.total,
                learned: res.learned,
                unlearned: res.unlearned
            }
        }
    } catch (e) {
        console.error("Failed to load dictionary:", e)
    } finally {
        dictLoading.value = false
    }
}

const nextWord = () => {
    isRevealed.value = false
    
    setTimeout(() => {
        vocabStore.nextWord()
    }, 200)
}

// [Stage 23.0] Go to original exam paper
const goToExam = (sentence) => {
    if (!sentence || !sentence.year || !sentence.exam_type) return
    // [Stage 25.0] Match DB paper_id format: {year}-eng{n} (e.g. "2015-eng1")
    let typeSlug = sentence.exam_type.toLowerCase().trim()
    if (typeSlug === 'english i' || typeSlug === 'english 1') typeSlug = 'eng1'
    else if (typeSlug === 'english ii' || typeSlug === 'english 2') typeSlug = 'eng2'
    else typeSlug = typeSlug.replace(/english\s*/i, 'eng').replace(/\s+/g, '')
    
    const slug = `${sentence.year}-${typeSlug}`
    console.log(`[VocabGarden] goToExam: navigating to /exam/${slug}`)
    router.push(`/exam/${slug}`)
}

// [Stage 23.0] Call Mia globally for AI word explanation
const callMiaGlobal = () => {
    const word = vocabStore.currentWord?.word
    if (!word) return
    
    const sentenceEn = vocabStore.currentWord.sentences?.[0]?.sentence || '';
    const prompt = `Mia，请给我详细讲解考研单词【${word}】的词根词缀，特别是它在这个真题例句中的用法和含义："${sentenceEn}"`
    
    miaStore.dialogVisible = true;
    miaStore.interact('vocab_chat', prompt)
}
</script>

<style scoped>
.perspective-1000 {
    perspective: 1000px;
}
.transform-style-3d {
    transform-style: preserve-3d;
}
.backface-hidden {
    backface-visibility: hidden;
}
.rotate-y-180 {
    transform: rotateY(180deg);
}

/* Animations */
.pop-enter-active, .pop-leave-active {
  transition: all 0.5s ease;
}
.pop-enter-from, .pop-leave-to {
  opacity: 0;
  transform: translate(-50%, -40%) scale(0.5);
}

.slide-up-enter-active, .slide-up-leave-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-up-enter-from, .slide-up-leave-to {
  opacity: 0;
  transform: translateY(100px) scale(0.98);
}

@keyframes float-up {
    0% { transform: translateY(0); opacity: 1; }
    100% { transform: translateY(-50px); opacity: 0; }
}
.animate-float-up {
    animation: float-up 1.5s ease-out forwards;
}

.text-shadow-sm {
    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
</style>
