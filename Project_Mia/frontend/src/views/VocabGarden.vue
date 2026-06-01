<template>
  <div class="min-h-screen bg-gradient-to-b from-emerald-50 to-teal-50 flex flex-col items-center relative">
    
    <!-- 🌿 [Stage 20.0 / 21.0] Minimal Top Bar -->
    <div class="w-full px-4 sm:px-6 lg:px-8 py-3 lg:py-4 flex justify-between items-center z-20 sticky top-0">
      
      <!-- 📚 [Stage 21.0] Dictionary Button -->
      <div class="flex gap-2">
        <button 
          @click="openDictionary"
          class="bg-white/70 backdrop-blur-md px-4 py-2 rounded-xl shadow-sm border border-teal-100 hover:bg-white transition-colors flex items-center gap-2 group cursor-pointer"
        >
          <span class="text-xl group-hover:scale-110 transition-transform">📚</span>
          <span class="text-xs font-bold text-teal-700 hidden sm:inline">我的词库</span>
        </button>

        <!-- 🔄 [Stage 35.7] Force Sync Button -->
        <button 
          @click="forceSync"
          class="bg-white/70 backdrop-blur-md px-3 py-2 rounded-xl shadow-sm border border-amber-100 hover:bg-white transition-colors flex items-center gap-2 group cursor-pointer bg-gradient-to-r from-amber-50 to-orange-50"
          title="强制打破缓存，同步服务器最新队列"
        >
          <span class="text-lg group-active:rotate-180 transition-transform duration-500">🔄</span>
          <span class="text-xs font-bold text-amber-700 hidden sm:inline">同步</span>
        </button>
      </div>

      <!-- 📊 [Stage 29.0] Glassmorphism Progress Dashboard -->
      <div v-if="vocabStore.dailyProgress" class="w-44 sm:w-56 lg:w-64 xl:w-72 tablet:w-80 bg-white/60 backdrop-blur-xl border border-white/30 shadow-lg rounded-2xl p-2.5 sm:p-3 lg:p-4 flex flex-col gap-1.5 sm:gap-2" id="progress-dashboard">
         <!-- Row 1: Date & Time Engine -->
         <div class="flex items-center justify-between">
            <div class="flex items-center gap-1 font-bold text-teal-700 text-[9px] sm:text-[10px]">
               <span>📅 {{ new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) }}</span>
            </div>
            <div class="flex items-center gap-1.5">
               <!-- Check-in Streak -->
               <div v-if="vocabStore.dailyStreak > 0" class="flex items-center gap-0.5 font-bold text-[9px] sm:text-[10px]" :class="vocabStore.isFinished ? 'text-rose-500 drop-shadow-[0_0_2px_rgba(244,63,94,0.5)]' : 'text-amber-500/80'">
                  <span>🔥</span> <span class="hidden sm:inline">连续</span> {{ vocabStore.dailyStreak }} 天
               </div>
               <!-- Focus Timer -->
               <div class="flex items-center gap-1 font-mono font-bold text-[10px] sm:text-xs px-1.5 py-0.5 rounded" :class="vocabStore.isPaused ? 'bg-gray-100/50 text-gray-500' : 'bg-teal-50 text-teal-600 shadow-[inset_0_1px_2px_rgba(0,0,0,0.05)]'">
                  <span>⏱️</span>
                  <span>{{ formatTime(vocabStore.todayFocusTime) }}</span>
                  <span v-if="vocabStore.isPaused" class="text-[8px] tracking-tighter font-wenkai font-normal">[⏸️暂停中]</span>
               </div>
            </div>
         </div>
         <!-- Row 2: New Words Progress -->
         <div class="flex flex-col gap-0.5">
            <div class="flex items-center justify-between text-[9px] sm:text-[10px] font-bold">
               <span class="text-teal-600 flex items-center gap-1"><span class="text-xs">🆕</span> New</span>
               <span class="text-teal-500 font-mono">{{ vocabStore.dailyProgress.new_learned || 0 }}/{{ userStore.dailyLimit || 30 }}</span>
            </div>
            <div class="h-1.5 sm:h-2 bg-teal-100/60 rounded-full overflow-hidden">
               <div class="h-full bg-gradient-to-r from-teal-400 to-emerald-400 rounded-full transition-all duration-700 ease-out" :style="{ width: Math.min(100, ((vocabStore.dailyProgress.new_learned || 0) / (userStore.dailyLimit || 30)) * 100) + '%' }"></div>
            </div>
         </div>
         <!-- Row 3: Review Progress -->
         <div class="flex flex-col gap-0.5 mb-1 border-b border-gray-100/50 pb-1.5">
            <div class="flex items-center justify-between text-[9px] sm:text-[10px] font-bold">
               <span class="text-amber-600 flex items-center gap-1"><span class="text-xs">🔄</span> Review</span>
               <span class="text-amber-500 font-mono">{{ vocabStore.dailyProgress.reviewed || 0 }}/{{ vocabStore.dailyProgress.to_review || 0 }}</span>
            </div>
            <div class="h-1.5 sm:h-2 bg-amber-100/60 rounded-full overflow-hidden">
               <div class="h-full bg-gradient-to-r from-amber-400 to-orange-400 rounded-full transition-all duration-700 ease-out" :style="{ width: vocabStore.dailyProgress.to_review ? Math.min(100, ((vocabStore.dailyProgress.reviewed || 0) / vocabStore.dailyProgress.to_review) * 100) + '%' : '0%' }"></div>
            </div>
         </div>
         <!-- Row 4: Global Mastery (Phase 32.0) -->
         <div class="flex flex-col gap-0.5 mt-0.5">
            <div class="flex items-center justify-between text-[9px] sm:text-[10px] font-bold">
               <span class="text-indigo-600 flex items-center gap-1"><span class="text-[10px]">🏆</span> Mastery</span>
               <span class="text-indigo-500 font-mono">{{ vocabStore.globalStats.mastered }}/{{ vocabStore.globalStats.total }}</span>
            </div>
            <div class="h-1 sm:h-1.5 bg-indigo-100/50 rounded-full overflow-hidden">
               <div class="h-full bg-gradient-to-r from-indigo-400 to-purple-400 rounded-full transition-all duration-1000 ease-out" :style="{ width: vocabStore.globalProgressPercent + '%' }"></div>
            </div>
         </div>
      </div>
    </div>

    <!-- 🌸 [v2] Mode-Switch Card Area -->

    <div class="flex-1 flex flex-col justify-center w-full max-w-md lg:max-w-lg tablet:max-w-xl px-6 relative z-10 pb-[env(safe-area-inset-bottom,2rem)] tablet:pb-[env(safe-area-inset-bottom,1.5rem)]">

      <!-- ⏳ Loading -->
      <div v-if="pageLoading" class="text-center text-teal-600 animate-pulse">
        <div class="text-4xl mb-4">🌱</div>
        <p>Loading Garden...</p>
      </div>

      <!-- ── 🏠 DASHBOARD MODE ── -->
      <div v-else-if="gardenMode === 'dashboard'" class="w-full max-w-lg mx-auto">

        <!-- Stats Card -->
        <div class="bg-white/90 rounded-3xl shadow-xl border border-teal-100 p-8 mb-6">
          <h2 class="text-2xl font-black text-teal-800 mb-6 flex items-center gap-2">
            <span>🌱</span> 词汇花园
          </h2>

          <!-- Key stats grid -->
          <div class="grid grid-cols-2 gap-3 mb-6">
            <div class="bg-teal-50 rounded-xl p-3 text-center">
              <div class="text-3xl font-black text-teal-600">{{ progressStats.mastered || 0 }}</div>
              <div class="text-[10px] text-teal-500 font-bold">📊 总进度 {{ ((progressStats.learned||0)/(progressStats.total_words||1)*100).toFixed(1) }}%</div>
            </div>
            <div class="bg-amber-50 rounded-xl p-3 text-center">
              <div class="text-3xl font-black text-amber-600">{{ progressStats.days_until_exam || '?' }}</div>
              <div class="text-[10px] text-amber-500 font-bold">⏰ 距考研 (天)</div>
            </div>
            <div class="bg-indigo-50 rounded-xl p-3 text-center">
              <div class="text-3xl font-black text-indigo-500">{{ progressStats.graduated || 0 }}</div>
              <div class="text-[10px] text-indigo-400 font-bold">🎓 已毕业</div>
            </div>
            <div class="bg-rose-50 rounded-xl p-3 text-center">
              <div class="text-3xl font-black text-rose-400">{{ progressStats.mistake_book || 0 }}</div>
              <div class="text-[10px] text-rose-400 font-bold">📌 顽固词</div>
            </div>
          </div>

          <!-- Progress bar -->
          <div class="mb-2">
            <div class="flex justify-between text-[10px] font-bold text-gray-500 mb-1">
              <span>{{ progressStats.learned || 0 }} / {{ progressStats.total_words || 0 }} 已学</span>
              <span>{{ ((progressStats.learned||0)/(progressStats.total_words||1)*100).toFixed(1) }}%</span>
            </div>
            <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div class="h-full bg-gradient-to-r from-teal-400 to-emerald-500 rounded-full transition-all duration-1000"
                :style="{ width: ((progressStats.learned||0)/(progressStats.total_words||1)*100) + '%' }"></div>
            </div>
          </div>
          <div v-if="progressStats.daily_needed > 0" class="text-[10px] text-gray-400 text-center mt-1">
            💡 每天需学 {{ progressStats.daily_needed }} 词才能在考前学完全部
          </div>

          <!-- Action stats -->
          <div class="flex gap-4 mt-5 text-center border-t border-gray-100 pt-4">
            <div class="flex-1 bg-emerald-50/70 rounded-xl p-2.5">
              <div class="font-black text-emerald-600 text-lg">{{ vocabStore.dailyProgress.to_review || 0 }}</div>
              <div class="text-[10px] text-emerald-500 font-bold">🔄 待复习</div>
            </div>
            <div class="flex-1 bg-blue-50/70 rounded-xl p-2.5">
              <div class="font-black text-blue-500 text-lg">{{ progressStats.unseen || 0 }}</div>
              <div class="text-[10px] text-blue-400 font-bold">🆕 未学词</div>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex flex-col gap-2.5">
          <button @click="startScreening"
            class="w-full py-3.5 bg-gradient-to-r from-indigo-400 to-purple-500 text-white rounded-2xl font-bold shadow-md shadow-indigo-200 hover:shadow-lg active:scale-95 transition-all flex items-center justify-center gap-2">
            <span class="text-lg">⚡</span>
            <span>快速筛选 — 批量浏览，会的直接跳过</span>
          </button>
          <button @click="startLearning"
            class="w-full py-3.5 bg-gradient-to-r from-teal-400 to-emerald-500 text-white rounded-2xl font-bold shadow-md shadow-teal-200 hover:shadow-lg active:scale-95 transition-all flex items-center justify-center gap-2">
            <span class="text-lg">📖</span>
            <span>开始学习 — 混合新词+复习（每日 {{ userStore.dailyLimit || 30 }} 词）</span>
          </button>
          <button @click="startReviewOnly"
            class="w-full py-3.5 bg-gradient-to-r from-amber-400 to-orange-500 text-white rounded-2xl font-bold shadow-md shadow-amber-200 hover:shadow-lg active:scale-95 transition-all flex items-center justify-center gap-2"
            :class="{ 'opacity-50': (vocabStore.dailyProgress.to_review || 0) === 0 }">
            <span class="text-lg">🔄</span>
            <span>只复习 — 清掉到期复习（{{ vocabStore.dailyProgress.to_review || 0 }} 词待复习）</span>
          </button>
        </div>
      </div>

      <!-- ── 📖 LEARNING MODE (original card flow) ── -->
      <template v-else-if="gardenMode === 'learning'">
        <!-- Finish State -->
        <div v-if="!vocabStore.currentWord" class="relative w-full aspect-[3/4] flex items-center justify-center p-6">
          <div class="w-full bg-white/90 rounded-3xl shadow-xl backdrop-blur-md border border-teal-100 p-8 flex flex-col items-center text-center transform transition-all">
            <div class="text-6xl mb-4 drop-shadow-md">🎉</div>
            <h2 class="text-2xl font-black text-teal-800 mb-2">今日任务完成！</h2>
            <p class="text-teal-600 mb-6 font-wenkai text-sm leading-relaxed">今天的词汇已全部完成。学有余力？继续追加吧！</p>
            <div class="flex flex-col gap-3 w-full">
              <button @click="continueLearning(10)"
                class="w-full py-3 bg-gradient-to-r from-orange-400 to-rose-500 text-white rounded-xl font-bold shadow-md shadow-rose-200 hover:shadow-lg active:scale-95 transition-all flex items-center justify-center gap-2">
                <span class="text-lg">🔥</span> <span>再来 10 个</span>
              </button>
              <button @click="continueLearning(20)"
                class="w-full py-3 bg-gradient-to-r from-amber-400 to-orange-500 text-white rounded-xl font-bold shadow-md shadow-amber-200 hover:shadow-lg active:scale-95 transition-all flex items-center justify-center gap-2">
                <span class="text-lg">🚀</span> <span>再来 20 个</span>
              </button>
              <button @click="gardenMode = 'dashboard'; refreshProgress()"
                class="w-full py-3 bg-teal-50 text-teal-700 rounded-xl font-bold border border-teal-200 hover:bg-teal-100 transition-all active:scale-95">
                🏠 今天够了，回去
              </button>
            </div>
          </div>
        </div>

        <!-- Active Card (original) -->
        <div v-else class="relative w-full aspect-[3/4] max-h-[calc(100dvh-16rem)] tablet:max-h-[calc(100dvh-14rem)] perspective-1000">
          <div class="w-full h-full relative transition-all duration-500 transform-style-3d"
            :class="{ 'rotate-y-180': isRevealed }"
            :style="cardStyle"
            @touchstart="handleTouchStart"
            @touchmove="handleTouchMove"
            @touchend="handleTouchEnd">
            <!-- FRONT -->
            <div class="absolute inset-0 backface-hidden bg-white rounded-3xl shadow-xl border border-emerald-100 p-8 flex flex-col justify-between">
              <div class="flex-1 flex flex-col justify-center items-center text-center">
                <h1 class="text-5xl tablet:text-6xl font-black text-gray-800 mb-2 tracking-tight">{{ vocabStore.currentWord.word }}</h1>
                <p class="text-gray-400 mb-6 font-mono text-lg tablet:text-xl">/ {{ vocabStore.currentWord.phonetic || '...' }} /</p>
                <div v-if="vocabStore.currentWord.sentences && vocabStore.currentWord.sentences.length" class="bg-emerald-50/50 p-5 rounded-xl border border-emerald-50 overflow-y-auto max-h-[40vh] custom-scrollbar w-full">
                  <p class="exam-sentence text-lg font-serif italic text-gray-600 leading-relaxed">"{{ vocabStore.currentWord.sentences[0].sentence }}"</p>
                </div>
              </div>
              <div class="text-center text-gray-400 text-sm font-wenkai flex flex-col items-center gap-1">
                <span>Space / 点击下方按钮 查看释义</span>
                <span class="text-[10px] text-gray-300 tablet:hidden">← 翻面后左右滑动评分 →</span>
              </div>
            </div>
            <!-- BACK -->
            <div class="absolute inset-0 backface-hidden rotate-y-180 bg-white rounded-3xl shadow-xl border border-teal-100 flex flex-col overflow-hidden">
              <div class="flex-1 overflow-y-auto custom-scrollbar p-8 pb-4">
                <div class="text-center border-b border-gray-100 pb-4 mb-4">
                  <h2 class="text-4xl tablet:text-5xl font-bold text-teal-700">{{ vocabStore.currentWord.word }}</h2>
                  <p class="text-gray-400 mt-1 font-mono text-base tablet:text-lg">/ {{ vocabStore.currentWord.phonetic || '...' }} /</p>
                  <p v-if="vocabStore.currentWord.pos" class="text-xs text-gray-400 mt-1"><span class="font-mono bg-gray-100 px-2 py-0.5 rounded-full">{{ vocabStore.currentWord.pos }}</span></p>
                </div>
                <div class="mb-5">
                  <h3 class="text-xs font-bold text-gray-400 uppercase mb-3 tracking-wide">释义 Meanings</h3>
                  <ul class="space-y-2.5">
                    <li v-for="(m, idx) in vocabStore.currentWord.meanings" :key="idx" class="text-gray-700 font-medium leading-relaxed text-base tablet:text-lg pl-4 border-l-2 border-teal-200">{{ m }}</li>
                  </ul>
                </div>
                <div v-if="vocabStore.currentWord.sentences && vocabStore.currentWord.sentences.length > 0" class="p-5 bg-emerald-50/50 rounded-xl text-sm font-wenkai relative border border-emerald-50 text-gray-700 mb-4">
                  <p class="exam-sentence mb-2 italic leading-relaxed text-gray-600">"{{ vocabStore.currentWord.sentences[0].sentence }}"</p>
                  <p v-if="vocabStore.currentWord.sentences[0].translation" class="text-teal-800 leading-relaxed">{{ vocabStore.currentWord.sentences[0].translation }}</p>
                  <div class="mt-3 text-right">
                    <button @click="goToExam(vocabStore.currentWord.sentences[0])" class="text-xs font-bold text-teal-600 hover:text-teal-800 underline underline-offset-2 decoration-teal-300 transition-colors bg-white/50 px-2 py-1 rounded">[🔗 去原卷看看]</button>
                  </div>
                </div>
                <div class="mt-2 mb-2">
                  <button @click="callMiaGlobal" class="w-full py-2.5 rounded-xl border border-amber-200 text-amber-600 bg-amber-50 text-sm font-bold hover:bg-amber-100 active:scale-95 transition-all flex items-center justify-center gap-2">
                    <span>💡</span> <span>呼叫 Mia 详细讲解</span>
                  </button>
                </div>
              </div>
              <div class="p-6 pt-2 bg-gradient-to-t from-white via-white shrink-0 z-10 flex justify-between gap-4">
                <button id="btn-forgot" @click="handleAnswer(0)"
                  class="flex-1 py-3 lg:py-4 bg-white border-2 border-rose-200 text-rose-500 rounded-xl font-bold shadow-sm hover:bg-rose-50 active:scale-95 transition-all flex items-center justify-center gap-2 touch-target"
                  :disabled="vocabStore.submitting" :class="{ 'opacity-50 cursor-not-allowed': vocabStore.submitting }">
                  <span class="text-xl">❌</span>
                  <span class="flex flex-col items-start leading-tight"><span>记错了</span><span class="text-[10px] font-normal text-rose-300">← 左滑 / 按 1</span></span>
                </button>
                <button id="btn-correct" @click="handleAnswer(5)"
                  class="flex-1 py-3 lg:py-4 bg-teal-500 border-2 border-teal-500 text-white rounded-xl font-bold shadow-md hover:bg-teal-600 active:scale-95 transition-all flex items-center justify-center gap-2 touch-target"
                  :disabled="vocabStore.submitting" :class="{ 'opacity-50 cursor-not-allowed': vocabStore.submitting }">
                  <span class="flex flex-col items-end leading-tight"><span>记对了</span><span class="text-[10px] font-normal text-teal-200">右滑 → / 按 2</span></span>
                  <span class="text-xl">✅</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- ── ⚡ SCREENING MODE ── -->
      <template v-else-if="gardenMode === 'screening'">
        <!-- Done -->
        <div v-if="screeningDone" class="w-full max-w-lg mx-auto">
          <div class="bg-white/90 rounded-3xl shadow-xl border border-indigo-100 p-8 flex flex-col items-center text-center">
            <div class="text-6xl mb-4">⚡</div>
            <h2 class="text-2xl font-black text-indigo-700 mb-2">筛选完成！</h2>
            <p class="text-indigo-500 mb-2 font-bold">{{ screeningSkipped }} 词已标记为已会</p>
            <p class="text-gray-400 mb-6 font-wenkai text-sm">还剩 {{ screeningWords.length }} 词等待学习</p>
            <div class="flex flex-col gap-3 w-full">
              <button @click="gardenMode = 'dashboard'; refreshProgress()"
                class="w-full py-3 bg-gradient-to-r from-teal-400 to-emerald-500 text-white rounded-xl font-bold shadow-md active:scale-95 transition-all">
                📖 开始学习这些词
              </button>
              <button @click="gardenMode = 'dashboard'; refreshProgress()"
                class="w-full py-3 bg-teal-50 text-teal-700 rounded-xl font-bold border border-teal-200 hover:bg-teal-100 transition-all active:scale-95">
                🏠 返回花园
              </button>
            </div>
          </div>
        </div>

        <!-- Screening Card -->
        <div v-else class="relative w-full aspect-[3/4] max-h-[calc(100dvh-16rem)] tablet:max-h-[calc(100dvh-14rem)] perspective-1000">
          <div class="w-full h-full relative transition-all duration-500"
            :style="screeningCardStyle"
            @touchstart="handleScreeningTouchStart"
            @touchmove="handleScreeningTouchMove"
            @touchend="handleScreeningTouchEnd">
            <div class="absolute inset-0 bg-white rounded-3xl shadow-xl border border-indigo-100 p-8 flex flex-col justify-between">
              <div class="flex-1 flex flex-col justify-center items-center text-center">
                <div class="text-[10px] font-bold text-indigo-400 mb-2">{{ screeningIndex + 1 }} / {{ screeningWords.length }}</div>
                <h1 class="text-5xl tablet:text-6xl font-black text-gray-800 mb-2 tracking-tight">{{ currentScreeningWord?.word }}</h1>
                <p class="text-gray-400 mb-6 font-mono text-lg tablet:text-xl">/ {{ currentScreeningWord?.phonetic || '...' }} /</p>
                <p v-if="currentScreeningWord?.meanings?.length" class="text-sm text-gray-500 font-wenkai leading-relaxed max-w-[80%]">
                  {{ currentScreeningWord.meanings.slice(0, 2).join('；') }}
                </p>
              </div>
              <div class="flex justify-between gap-4">
                <button @click="screeningSkip"
                  class="flex-1 py-3 bg-white border-2 border-emerald-200 text-emerald-500 rounded-xl font-bold shadow-sm hover:bg-emerald-50 active:scale-95 transition-all flex items-center justify-center gap-2 touch-target">
                  <span>✅</span> <span>认识了</span>
                </button>
                <button @click="screeningKeep"
                  class="flex-1 py-3 bg-white border-2 border-amber-200 text-amber-500 rounded-xl font-bold shadow-sm hover:bg-amber-50 active:scale-95 transition-all flex items-center justify-center gap-2 touch-target">
                  <span>📌</span> <span>需要学</span>
                </button>
              </div>
            </div>
          </div>
          <!-- Screening progress -->
          <div class="mt-4 w-full">
            <div class="flex justify-between text-[10px] text-gray-400 mb-1">
              <span>筛选进度</span><span>{{ screeningIndex }} / {{ screeningWords.length }}</span>
            </div>
            <div class="h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div class="h-full bg-indigo-400 rounded-full transition-all duration-300"
                :style="{ width: (screeningIndex / Math.max(1, screeningWords.length) * 100) + '%' }"></div>
            </div>
          </div>
        </div>
      </template>

      <!-- ── 🤷 Fallback -->
      <div v-else class="text-center text-gray-400 py-12">
        <div class="text-4xl mb-3">🌿</div>
        <p>加载中…</p>
      </div>
    </div>


    <!-- 🎮 [v2] Action Bar — only in Learning mode when Front card showing -->
    <div v-if="gardenMode === 'learning' && vocabStore.currentWord && !isRevealed" class="fixed bottom-20 left-0 w-full px-8 flex justify-center z-30">
        <button
            id="btn-show-answer"
            @click="isRevealed = true"
            class="w-full max-w-sm tablet:max-w-md py-4 tablet:py-5 bg-teal-500 border-2 border-teal-500 text-white rounded-2xl font-bold shadow-lg hover:bg-teal-600 active:scale-95 transition-all flex flex-col items-center"
        >
            <span class="text-2xl mb-1">👆</span>
            <span>点击查看释义</span>
            <span class="text-[10px] font-normal text-teal-200 mt-0.5">或按空格键 Space</span>
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
              <button @click="closeDictionary" class="text-3xl text-gray-400 hover:text-rose-500 transition-colors cursor-pointer sm:hidden">
                &times;
              </button>
            </h2>
            <div v-if="dictStats" class="mt-2 text-sm font-bold text-teal-600">
              掌握词汇: {{ dictStats.mastered }} / {{ dictStats.total }} (剩余 {{ dictStats.unlearned }})
            </div>
            <div v-if="dictStats" class="mt-1 text-[11px] text-teal-600 bg-teal-100/50 inline-block px-3 py-1 rounded-full font-bold transition-all">
              {{ getETAString(dictStats.total, dictStats.learned, localDailyLimit) }}
            </div>
            
            <!-- [Stage 34.1] 🎚️ Dynamic Daily Goal Slider -->
            <div class="mt-4 flex flex-col gap-1 w-full max-w-sm">
               <div class="flex justify-between items-center text-xs font-bold text-teal-700">
                  <span>🎯 今日学习强度 (词/天)</span>
                  <span class="text-orange-500 bg-orange-100 px-2 py-0.5 rounded-md">🔥 {{ localDailyLimit }} </span>
               </div>
               <input 
                  type="range" 
                  min="10" 
                  max="300" 
                  step="10" 
                  v-model.number="localDailyLimit"
                  @input="handleSliderInput"
                  class="w-full accent-teal-500 h-2 bg-teal-200 rounded-lg appearance-none cursor-pointer"
               />
            </div>
          </div>
          
          <div class="flex flex-col gap-2 w-full sm:w-auto relative items-end">
              <button @click="closeDictionary" class="hidden sm:block text-3xl text-gray-400 hover:text-rose-500 transition-colors cursor-pointer mb-2">
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
          <div v-else-if="paginatedDictList.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 tablet:grid-cols-5 gap-4 pb-6">
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
                        ? (i <= 3 ? 'bg-amber-400' : 'bg-teal-400 shadow-[0_0_8px_rgba(45,212,191,0.6)]') 
                        : 'bg-gray-100'
                    ]"
                   ></div>
                 </div>
                 <div v-if="item.status === 'learned'" class="text-[10px] font-bold" :class="item.mastery_level >= 4 ? 'text-teal-500' : 'text-amber-600'">
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
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useVocabStore, getCurrentLogicalDay } from '../stores/useVocabStore'
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

// ── [v2] Garden Mode & Screening State ──
const gardenMode = ref('dashboard')   // 'dashboard' | 'learning' | 'screening'
const pageLoading = ref(false)
const progressStats = ref({
  total_words: 0, learned: 0, mastered: 0, graduated: 0,
  mistake_book: 0, unseen: 0, days_until_exam: 0, daily_needed: 0
})

// Screening state
const screeningWords = ref([])
const screeningIndex = ref(0)
const screeningSkipped = ref(0)
const screeningDone = ref(false)
const screeningSkipBatch = ref([])  // words to batch-mark
let _screenBatchTimer = null

const screeningTouchStartX = ref(null)
const screeningTouchCurrentX = ref(null)
const screeningSwipeOffset = computed(() => {
  if (screeningTouchStartX.value === null || screeningTouchCurrentX.value === null) return 0
  return screeningTouchCurrentX.value - screeningTouchStartX.value
})
const screeningCardStyle = computed(() => {
  const offset = screeningSwipeOffset.value
  if (offset === 0) return {}
  const clamped = Math.max(-100, Math.min(100, offset))
  const rotate = clamped * 0.1
  const intensity = Math.abs(clamped) / 100
  const shadowColor = clamped > 0 ? `rgba(16, 185, 129, ${intensity * 0.5})` : `rgba(245, 158, 11, ${intensity * 0.5})`
  return {
    transform: `translateX(${clamped}px) rotate(${rotate}deg)`,
    boxShadow: `0 ${Math.abs(clamped) / 4}px ${Math.abs(clamped) / 2}px ${shadowColor}`,
    transition: screeningTouchStartX.value ? 'none' : 'transform 0.5s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s ease'
  }
})
const currentScreeningWord = computed(() => {
  if (!screeningWords.value.length || screeningIndex.value >= screeningWords.value.length) return null
  return screeningWords.value[screeningIndex.value]
})

// [Stage 28.1] Swipe & Keyboard State
const touchStartX = ref(null)
const touchCurrentX = ref(null)
const swipeOffset = computed(() => {
    if (touchStartX.value === null || touchCurrentX.value === null) return 0
    return touchCurrentX.value - touchStartX.value
})
const cardStyle = computed(() => {
    if (swipeOffset.value === 0) return {}
    // Limits visual translation to a reasonable visual dragging area
    const offset = Math.max(-100, Math.min(100, swipeOffset.value))
    // Adds a slight rotation for flair when dragging
    const rotate = offset * 0.1
    // [T2] 滑动方向颜色反馈
    const intensity = Math.abs(offset) / 100
    const shadowColor = offset > 0
      ? `rgba(20, 184, 166, ${intensity * 0.5})`  // teal for correct (right)
      : `rgba(244, 63, 94, ${intensity * 0.5})`    // rose for forgot (left)
    return {
        transform: `translateX(${offset}px) rotate(${rotate}deg)`,
        boxShadow: `0 ${Math.abs(offset) / 4}px ${Math.abs(offset) / 2}px ${shadowColor}`,
        transition: touchStartX.value ? 'none' : 'transform 0.5s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s ease'
        // Note: transition is none while dragging, smooth when released
    }
})

// [Stage 22.0] Dictionary Drawer State
const showDictionary = ref(false)
const dictLoading = ref(false)
const dictList = ref([])
const dictStats = ref(null)

const localDailyLimit = ref(30) // [Stage 34.1] Local reactive state for slider

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
        list = list.filter(item => item.status === 'learned' && item.mastery_level < 4)
    } else if (currentTab.value === 'Mastered') {
        list = list.filter(item => item.status === 'learned' && item.mastery_level >= 4)
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
    
    return `💡 按每日 ${limit} 词进度，还需 ${days} 天（约 ${yyyy}-${mm}-${dd} 考研上岸）`
}

// [Stage 34.1] Debounce Logic for Goal Slider
let sliderDebounceTimeout = null
const handleSliderInput = () => {
    if (sliderDebounceTimeout) clearTimeout(sliderDebounceTimeout)
    sliderDebounceTimeout = setTimeout(async () => {
        // [Stage 34.1] 防抖执行 (500ms 不再拖动后)
        console.log(`[VocabGarden] Slider Debounced: updating daily limit to ${localDailyLimit.value}`)
        await userStore.updateDailyLimit(localDailyLimit.value)
        // 瞬间重设 Vocab Queue 兵力
        await vocabStore.fetchTodayVocab()
    }, 500)
}

// ── [v2] Init: Load stats first, show dashboard ──
onMounted(async () => {
    if (!userStore.currentSlotId) await userStore.init()
    localDailyLimit.value = userStore.dailyLimit || 30

    // Fetch global stats and progress stats in parallel
    pageLoading.value = true
    try {
        await Promise.all([
            vocabStore.fetchGlobalStats(),
            refreshProgress()
        ])
        // Also fetch today's vocab silently so to_review is populated in dashboard
        await vocabStore.fetchTodayVocab()
        gardenMode.value = 'dashboard'
    } catch (e) {
        console.error('VocabGarden init error:', e)
    } finally {
        pageLoading.value = false
    }

    vocabStore.startFocusTimer()
    window.addEventListener('keydown', handleGlobalKeydown)
    document.activeElement?.blur()
})

onBeforeUnmount(() => {
    window.removeEventListener('keydown', handleGlobalKeydown)
    vocabStore.stopFocusTimer() // [Stage 30.0]
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

// [Stage 28.2 / 34.3 / 34.5] Define handleGlobalKeydown BEFORE using it in lifecycles
const handleGlobalKeydown = (e) => {
    // [Stage 34.3] Debug log - FIRST LINE, before any returns
    console.log('[Keydown Debug] Key pressed:', e.key, e.code,
        '| e.target:', e.target?.tagName, e.target?.type || '',
        '| activeEl:', document.activeElement?.tagName, document.activeElement?.type || '',
        '| currentWord:', !!vocabStore.currentWord, '| isRevealed:', isRevealed.value, '| showDict:', showDictionary.value)

    // [Stage 34.5] Guard: use document.activeElement (NOT e.target) for accurate focus detection
    const active = document.activeElement
    if (active && active.tagName === 'INPUT' && (active.type === 'text' || active.type === 'search')) return;
    if (active && active.tagName === 'TEXTAREA') return;
    
    // Only block shortcuts when the fullscreen dictionary overlay is open
    if (showDictionary.value) return;
    
    // If no current word yet (still loading), prevent Space from scrolling but don't swallow
    if (!vocabStore || !vocabStore.currentWord) {
        if (e.code === 'Space' || e.key === ' ') e.preventDefault()
        return;
    }

    if (!isRevealed.value) {
        console.log('[Keydown Debug] PRE-SPACE CHECK: code===', JSON.stringify(e.code), 'key===', JSON.stringify(e.key), 'match?', e.code === 'Space' || e.key === ' ')
        if (e.code === 'Space' || e.key === ' ') {
            e.preventDefault()
            console.log('[Keydown Debug] >>> SPACE BRANCH HIT! Flipping card.')
            isRevealed.value = true
        }
    } else {
        if (!vocabStore.submitting) {
            if (e.key === '1' || e.code === 'ArrowLeft') {
                e.preventDefault()
                handleAnswer(0)
            } else if (e.key === '2' || e.code === 'ArrowRight') {
                e.preventDefault()
                handleAnswer(5)
            } else if (e.code === 'Space' || e.key === ' ') {
                e.preventDefault()
                // Auto Know if hitting space again
                handleAnswer(5)
            }
        }
    }
}

// [Stage 28.1] Touch Handlers for Swiping
const SWIPE_THRESHOLD = 50

const handleTouchStart = (e) => {
    if (!vocabStore || !vocabStore.currentWord) return;
    if (!isRevealed.value || vocabStore.submitting) return;
    touchStartX.value = e.touches[0].clientX
    touchCurrentX.value = e.touches[0].clientX
}

const handleTouchMove = (e) => {
    if (!vocabStore || !vocabStore.currentWord) return;
    if (touchStartX.value === null) return;
    touchCurrentX.value = e.touches[0].clientX
}

const handleTouchEnd = () => {
    if (!vocabStore || !vocabStore.currentWord) return;
    if (touchStartX.value === null || touchCurrentX.value === null) return;
    
    if (swipeOffset.value < -SWIPE_THRESHOLD) {
        // Swiped Left -> Forgot
        handleAnswer(0)
    } else if (swipeOffset.value > SWIPE_THRESHOLD) {
        // Swiped Right -> Know
        handleAnswer(5)
    }

    touchStartX.value = null
    touchCurrentX.value = null
}

const handleAnswer = async (quality) => {
    if (!vocabStore || !vocabStore.currentWord) return;
    if (vocabStore.submitting) return;

    // 1. Submit Logic
    const res = await vocabStore.submitReview(quality)
    
    // 2. Visual Feedback
    // Use the correct keys from the backend response: new_hp, new_exp, hp, exp
    if (res && res.reward) { 
       const { new_hp, new_exp, hp: hp_change, exp: exp_change } = res.reward
       
       // Fallback fix: If undefined, default to 0 to prevent UI string "undefined HP"
       const safe_hp_change = hp_change || 0;
       const safe_exp_change = exp_change || 0;
       
       // Show delta if we have it
       if (safe_hp_change !== 0 || safe_exp_change > 0) {
           rewardText.value.hp = safe_hp_change > 0 ? `+${safe_hp_change} HP` : `${safe_hp_change} HP`
           if (safe_exp_change > 0) {
               rewardText.value.exp = `+${safe_exp_change} EXP`
           } else {
               rewardText.value.exp = ''
           }
           showReward.value = true
           setTimeout(() => { showReward.value = false }, 1500)
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
                mastered: res.mastered,
                unlearned: res.unlearned
            }
        }
    } catch (e) {
        console.error("Failed to load dictionary:", e)
    } finally {
        dictLoading.value = false
    }
}

// [Stage 34.2] Close Dictionary with focus release
const closeDictionary = () => {
    showDictionary.value = false
    // Force blur to prevent slider or input fields from hijacking global keyboard focus
    if (document.activeElement && document.activeElement.blur) {
        document.activeElement.blur()
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
    
    // [Stage 35.9] Fix: Emulate user input correctly
    miaStore.history.push({ role: 'user', content: prompt })
    miaStore.dialogVisible = true;
    
    // Provide an object context matching what interact expects
    miaStore.interact('vocab_chat', { message: prompt, rpg_mode: false })
}


// ── [v2] Garden Mode Functions ──

// Fetch progress stats for dashboard
const refreshProgress = async () => {
    try {
        const res = await request.get('/vocab/progress_stats', {
            params: { slot_id: userStore.currentSlotId }
        })
        if (res) {
            progressStats.value = {
                total_words: res.total_words || 0,
                learned: res.learned || 0,
                mastered: res.mastered || 0,
                graduated: res.graduated || 0,
                mistake_book: res.mistake_book || 0,
                unseen: res.unseen || 0,
                days_until_exam: res.days_until_exam || 0,
                daily_needed: res.daily_needed || 0,
            }
        }
    } catch (e) {
        console.error('progress_stats error:', e)
    }
}

// ── Screening Mode ──
const startScreening = async () => {
    pageLoading.value = true
    try {
        const res = await request.get('/vocab/screening', {
            params: { slot_id: userStore.currentSlotId, limit: 50 }
        })
        if (res && res.words) {
            screeningWords.value = res.words
            screeningIndex.value = 0
            screeningSkipped.value = 0
            screeningDone.value = false
            screeningSkipBatch.value = []
            gardenMode.value = 'screening'
        }
    } catch (e) {
        console.error('screening error:', e)
    } finally {
        pageLoading.value = false
    }
}

const _flushScreeningBatch = async () => {
    if (!screeningSkipBatch.value.length) return
    const batch = [...screeningSkipBatch.value]
    screeningSkipBatch.value = []
    try {
        await request.post('/vocab/batch_mark', {
            slot_id: userStore.currentSlotId,
            words: batch,
            action: 'skip'
        })
    } catch (e) {
        console.error('batch_mark error:', e)
    }
}

const screeningSkip = () => {
    const word = currentScreeningWord.value
    if (!word) return
    screeningSkipBatch.value.push(word.word)
    screeningSkipped.value++
    screeningIndex.value++
    if (screeningIndex.value >= screeningWords.value.length) {
        _flushScreeningBatch().then(() => { screeningDone.value = true })
    } else if (screeningSkipBatch.value.length >= 10) {
        _flushScreeningBatch()
    }
}

const screeningKeep = () => {
    screeningIndex.value++
    if (screeningIndex.value >= screeningWords.value.length) {
        _flushScreeningBatch().then(() => { screeningDone.value = true })
    }
}

// Screening touch handlers
const handleScreeningTouchStart = (e) => {
    if (!currentScreeningWord.value || screeningDone.value) return
    screeningTouchStartX.value = e.touches[0].clientX
    screeningTouchCurrentX.value = e.touches[0].clientX
}
const handleScreeningTouchMove = (e) => {
    if (screeningTouchStartX.value === null) return
    screeningTouchCurrentX.value = e.touches[0].clientX
}
const handleScreeningTouchEnd = () => {
    if (screeningTouchStartX.value === null) return
    const SWIPE_S = 50
    if (screeningSwipeOffset.value < -SWIPE_S) screeningSkip()
    else if (screeningSwipeOffset.value > SWIPE_S) screeningKeep()
    screeningTouchStartX.value = null
    screeningTouchCurrentX.value = null
}

// ── Learning Mode ──
const startLearning = async () => {
    pageLoading.value = true
    try {
        vocabStore.currentIndex = 0
        await vocabStore.fetchTodayVocab()
        gardenMode.value = 'learning'
    } finally {
        pageLoading.value = false
    }
}

const startReviewOnly = () => {
    startLearning()
}

const continueLearning = async (count) => {
    pageLoading.value = true
    try {
        await vocabStore.addDailyLimit(count)
        isRevealed.value = false
        if (!vocabStore.currentWord) vocabStore.currentIndex = 0
    } catch (e) {
        console.error('continueLearning error:', e)
    } finally {
        pageLoading.value = false
    }
}

// Keep backward compat
const handleEndlessMode = async () => {
    await continueLearning(10)
}

const forceSync = async () => {
    await vocabStore.fetchTodayVocab()
    await refreshProgress()
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
