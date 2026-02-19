<template>
  <div class="flex flex-col gap-3 font-wenkai">
    <!-- Question Content -->
    <div
      v-if="content"
      class="text-sm text-gray-600 bg-amber-50 border border-amber-200 rounded-lg p-3 leading-relaxed"
    >
      {{ content }}
    </div>

    <!-- Text Input Area -->
    <div class="relative">
      <textarea
        v-model="userAnswer"
        :placeholder="placeholder || '在此输入你的答案…'"
        :rows="rows"
        :disabled="isSubmitting || submitted"
        class="w-full border border-gray-200 rounded-xl p-4 text-gray-800 text-sm leading-relaxed
               bg-white focus:border-rose-300 focus:ring-2 focus:ring-rose-100 focus:outline-none
               transition-all resize-y disabled:opacity-60 disabled:cursor-not-allowed font-wenkai"
      ></textarea>

      <!-- Word count -->
      <div class="absolute bottom-2 right-3 text-[11px] text-gray-400 pointer-events-none">
        {{ wordCount }}
        <span v-if="maxWords" :class="wordCount > maxWords ? 'text-rose-500 font-bold' : ''">/ {{ maxWords }}</span>
        词
      </div>
    </div>

    <!-- Submit Row -->
    <div class="flex items-center gap-3">
      <button
        @click="submitForGrading"
        :disabled="isSubmitting"
        class="flex items-center gap-2 px-5 py-2 rounded-xl text-sm font-semibold transition-all
               bg-rose-400 hover:bg-rose-500 text-white disabled:opacity-40 disabled:cursor-not-allowed
               shadow-sm hover:shadow-md active:scale-95"
      >
        <span v-if="isSubmitting" class="flex items-center gap-2">
          <span class="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
          Mia 正在阅卷…
        </span>
        <span v-else-if="submitted">✓ 已提交</span>
        <span v-else>📝 提交批改</span>
      </button>

      <span v-if="aiFeedback && score !== null" class="text-sm text-gray-500">
        得分：<span class="font-bold text-rose-500">{{ score }}</span> / {{ maxScore }}
      </span>
    </div>

    <!-- Mia Feedback Card -->
    <transition name="slide-in">
      <div
        v-if="aiFeedback"
        class="bg-white border border-rose-100 rounded-2xl p-4 shadow-sm flex gap-3 items-start"
      >
        <div class="w-10 h-10 rounded-full overflow-hidden shrink-0 border-2 border-rose-200">
          <img :src="miaAvatar" class="w-full h-full object-cover" alt="Mia" />
        </div>
        <div>
          <div class="text-xs font-bold text-rose-400 mb-1">Mia 点评</div>
          <div class="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{{ aiFeedback }}</div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import request from '../../utils/request'
import { useUserStore } from '../../stores/useUserStore'
import { useMiaStore } from '../../stores/useMiaStore'
import { useExamStore } from '../../stores/useExamStore'
import { ASSETS } from '../../config/assets'

const props = defineProps({
  qId:         { type: String, required: true },
  content:     { type: String, default: '' },        // 题目正文 / 句子
  placeholder: { type: String, default: '' },
  rows:        { type: Number, default: 6 },
  maxWords:    { type: Number, default: 0 },
  maxScore:    { type: Number, default: 10 },
  sectionType: { type: String, default: 'translation' },  // 'translation' | 'writing_a' | 'writing_b'
})

// Listen for qId changes to reset local state
watch(() => props.qId, (newVal) => {
  // console.log(`[SubjectiveInput] Question changed to ${newVal}, resetting state.`)
  userAnswer.value = ''
  score.value      = null
  aiFeedback.value = ''
  submitted.value  = false
  isSubmitting.value = false
})

const userStore = useUserStore()
const miaStore  = useMiaStore()
const examStore = useExamStore()

const miaAvatar  = ASSETS.mia.avatar
const userAnswer = ref('')
const isSubmitting = ref(false)
const submitted    = ref(false)
const aiFeedback   = ref('')
const score        = ref(null)

const wordCount = computed(() =>
  userAnswer.value.trim().split(/[\s\n]+/).filter(Boolean).length
)

const canSubmit = computed(() =>
  !isSubmitting.value && !submitted.value && userAnswer.value.trim().length > 3
)

const submitForGrading = async () => {
  if (!userAnswer.value || userAnswer.value.trim() === '') return;
  isSubmitting.value = true

  try {
    const res = await request.post('/exam/submit_subjective', {
      q_id:         props.qId,
      answer:       userAnswer.value,
      section_type: props.sectionType,
    })

    // 分数和评语
    score.value      = res.score      ?? null
    aiFeedback.value = res.mia_feedback ?? res.feedback ?? '（暂无评语）'
    submitted.value  = true

    // HP 扣减（主观题写了就扣消耗，答得好少扣）
    const hpDelta = res.hp_change ?? -3
    userStore.animateHpChange(hpDelta)

    // Mia 说话
    await miaStore.speak(aiFeedback.value)

  } catch (err) {
    // console.error('[SubjectiveInput] submit error:', err)
    // 离线 Mock
    score.value      = props.maxScore * 0.6
    aiFeedback.value = '（离线模式）Mia 暂时连不上服务器，不过你写得很认真哦！等网络恢复后再重新提交吧～'
    submitted.value  = true
    userStore.animateHpChange(-2)
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.slide-in-enter-active {
  transition: all 0.35s ease;
}
.slide-in-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
</style>
