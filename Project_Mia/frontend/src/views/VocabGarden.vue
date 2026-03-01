<template>
  <div class="min-h-screen bg-gradient-to-b from-emerald-50 to-teal-50 flex flex-col items-center relative overflow-hidden">
    
    <!-- 🌿 Top Status Bar -->
    <div class="w-full px-6 py-4 flex justify-between items-center z-20 bg-white/60 backdrop-blur-md sticky top-0 shadow-sm">
      <div class="flex items-center gap-3">
        <!-- HP -->
        <div class="flex flex-col">
          <div class="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Health</div>
          <div class="flex items-center gap-1">
            <div class="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div 
                class="h-full bg-rose-400 transition-all duration-500"
                :style="{ width: userStore.hpPercentage + '%' }"
              ></div>
            </div>
            <span class="text-xs font-bold text-rose-500">{{ userStore.hp }}</span>
          </div>
        </div>
        
        <!-- Level -->
        <div class="flex flex-col ml-2">
            <div class="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Level</div>
            <span class="text-sm font-black text-teal-600">Lv.{{ userStore.level }}</span>
        </div>
      </div>

      <!-- Progress -->
      <div class="text-right">
         <div class="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Today's Goal</div>
         <div class="text-xl font-wenkai font-bold text-teal-700">
            {{ vocabStore.currentIndex }} / <span class="text-teal-400">{{ vocabStore.todayTasks.length }}</span>
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
                    <div v-if="vocabStore.currentWord.sentences && vocabStore.currentWord.sentences.length" class="bg-emerald-50/50 p-4 rounded-xl border border-emerald-50">
                        <p class="text-lg font-serif italic text-gray-600 leading-relaxed">
                            "{{ vocabStore.currentWord.sentences[0].sentence }}"
                        </p>
                    </div>
                </div>
                
                <div class="text-center text-gray-400 text-sm font-wenkai">
                    Think about the meaning...
                </div>
            </div>

            <!-- BACK: Answer (Revealed) -->
            <div class="absolute inset-0 backface-hidden rotate-y-180 bg-white rounded-3xl shadow-xl border border-teal-100 p-8 flex flex-col overflow-y-auto custom-scrollbar">
                <div class="text-center border-b border-gray-100 pb-4 mb-4">
                    <h2 class="text-3xl font-bold text-teal-700">{{ vocabStore.currentWord.word }}</h2>
                    <p class="text-gray-400 mt-1 font-mono text-sm">/ {{ vocabStore.currentWord.phonetic || '...' }} /</p>
                </div>

                <!-- Meanings -->
                <div class="mb-6">
                    <h3 class="text-xs font-bold text-gray-400 uppercase mb-2">Meanings</h3>
                    <ul class="space-y-2">
                        <li v-for="(m, idx) in vocabStore.currentWord.meanings" :key="idx" class="text-gray-700 font-medium">
                            {{ m }}
                        </li>
                    </ul>
                </div>

                <!-- Explanation / AI (Simulated for now, or from JSON) -->
                <!-- Assuming 'pos' is available -->
                <div class="flex-1">
                    <h3 class="text-xs font-bold text-gray-400 uppercase mb-2">Notes</h3>
                    <p class="text-sm text-gray-500 leading-relaxed">
                        Part of Speech: <span class="font-mono bg-gray-100 px-1 rounded">{{ vocabStore.currentWord.pos }}</span>
                    </p>
                    <!-- Show translation of sentence if available -->
                    <div v-if="vocabStore.currentWord.sentences && vocabStore.currentWord.sentences.length > 0 && vocabStore.currentWord.sentences[0].translation" class="mt-4 p-3 bg-gray-50 rounded-lg text-sm text-gray-600">
                        {{ vocabStore.currentWord.sentences[0].translation }}
                    </div>
                </div>

                <!-- [Stage 17.0] 💡 Mia AI Explanation Button -->
                <div class="mt-3">
                    <button
                        @click="callMiaExplain"
                        :disabled="explainLoading"
                        class="w-full py-2.5 rounded-xl border border-amber-200 text-amber-600 bg-amber-50 text-sm font-bold hover:bg-amber-100 active:scale-95 transition-all flex items-center justify-center gap-2"
                    >
                        <span v-if="explainLoading" class="animate-spin">⏳</span>
                        <span v-else>💡</span>
                        <span>{{ explainLoading ? 'Mia 正在思考...' : '呼叫 Mia 讲解' }}</span>
                    </button>

                    <!-- Mia's Speech Bubble -->
                    <transition name="bubble">
                        <div v-if="miaSays" class="mt-3 p-4 bg-gradient-to-br from-rose-50 to-pink-50 border border-rose-100 rounded-2xl relative">
                            <div class="absolute -top-2 left-6 w-4 h-4 bg-rose-50 border-l border-t border-rose-100 rotate-45"></div>
                            <p class="text-sm text-rose-800 leading-relaxed font-wenkai whitespace-pre-wrap">{{ miaSays }}</p>
                        </div>
                    </transition>
                </div>

                <!-- Next Button -->
                <button 
                    @click="nextWord"
                    class="mt-4 w-full py-3 bg-teal-500 text-white rounded-xl font-bold shadow-md hover:bg-teal-600 active:scale-95 transition-all"
                >
                    Next Word →
                </button>
            </div>
        </div>
      </div>
    </div>

    <!-- 🎮 Action Bar (Only visible when Front) -->
    <div v-if="vocabStore.currentWord && !isRevealed" class="fixed bottom-10 left-0 w-full px-8 flex justify-between gap-6 z-30">
        <button 
            @click="handleAnswer(0)"
            class="flex-1 py-4 bg-white border-2 border-rose-100 text-rose-500 rounded-2xl font-bold shadow-lg hover:bg-rose-50 active:scale-95 transition-all flex flex-col items-center"
        >
            <span class="text-2xl mb-1">❌</span>
            <span>Forget</span>
        </button>

        <button 
            @click="handleAnswer(5)"
            class="flex-1 py-4 bg-teal-500 border-2 border-teal-500 text-white rounded-2xl font-bold shadow-lg hover:bg-teal-600 active:scale-95 transition-all flex flex-col items-center"
        >
            <span class="text-2xl mb-1">✅</span>
            <span>Know</span>
        </button>
    </div>

    <!-- ✨ Reward Popup -->
    <transition name="pop">
        <div v-if="showReward" class="fixed top-1/3 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 pointer-events-none">
            <div class="flex flex-col items-center animate-float-up">
                <span class="text-4xl">✨</span>
                <span class="text-rose-500 font-black text-2xl text-shadow-sm">+0.5 HP</span>
                <span class="text-teal-500 font-bold text-lg">+2 EXP</span>
            </div>
        </div>
    </transition>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useVocabStore } from '../stores/useVocabStore'
import { useUserStore } from '../stores/useUserStore'
import request from '../utils/request'

const router = useRouter()
const vocabStore = useVocabStore()
const userStore = useUserStore()

const isRevealed = ref(false)
const showReward = ref(false)
// [Stage 17.0] Mia Explanation State
const explainLoading = ref(false)
const miaSays = ref('')

onMounted(async () => {
    // Ensuring user slot is correct
    if (!userStore.currentSlotId) {
        await userStore.init()
    }
    await vocabStore.fetchTodayVocab()
})

const handleAnswer = async (quality) => {
    // 1. Submit Logic
    const res = await vocabStore.submitReview(quality)
    
    // 2. Visual Feedback
    if (res && res.reward) { // Check if reward exists
       const { hp, exp } = res.reward
       if (hp > 0 || exp > 0) {
           showReward.value = true
           setTimeout(() => showReward.value = false, 1500)
       }
    }

    // 3. Reveal Card
    isRevealed.value = true
}

const nextWord = () => {
    isRevealed.value = false
    miaSays.value = ''  // Clear explanation for next word
    explainLoading.value = false
    
    setTimeout(() => {
        vocabStore.nextWord()
    }, 200)
}

// [Stage 17.0] Call Mia for AI word explanation
const callMiaExplain = async () => {
    const word = vocabStore.currentWord?.word
    if (!word || explainLoading.value) return
    
    explainLoading.value = true
    miaSays.value = ''
    try {
        const res = await request.post('/vocab/explain', { word })
        if (res && res.success) {
            miaSays.value = res.explanation
        } else {
            miaSays.value = 'Mia 暂时想不出来了，稍后再试喵...'
        }
    } catch (e) {
        miaSays.value = '网络出错了喵 (>_<)'
    } finally {
        explainLoading.value = false
    }
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
