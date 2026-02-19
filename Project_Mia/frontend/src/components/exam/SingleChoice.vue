<template>
  <div 
    @click="setFocus"
    class="mb-5 rounded-xl border border-gray-200 bg-white hover:border-rose-200 hover:shadow-sm transition-all"
  >
     <!-- Question Number Badge -->
     <div class="px-4 pt-3 pb-2 border-b border-gray-100 flex items-center gap-2">
       <span class="text-xs font-bold bg-rose-50 text-mia-pink-dark px-2 py-0.5 rounded-full border border-rose-100">
         Q{{ question.question_number }}
       </span>
     </div>

     <!-- 题干 -->
     <div class="px-4 pt-3 pb-2 text-gray-800 text-sm leading-relaxed font-wenkai" v-if="question.content">
       {{ question.content }}
     </div>
     
     <!-- 选项 -->
     <div class="px-4 pb-4 flex flex-col gap-2">
         <template v-if="question.options">
             <label 
               v-for="(text, key) in question.options" 
               :key="key"
               class="flex items-center gap-3 p-2.5 rounded-lg cursor-pointer border transition-all text-sm"
               :class="getOptionClass(key)"
             >
                <input 
                  type="radio" 
                  :name="'q'+question.q_id" 
                  :value="key"
                  v-model="selected"
                  @change="submit"
                  :disabled="submitted"
                  class="hidden" 
                >
                <!-- Custom Radio UI -->
                <div class="w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 transition-colors"
                     :class="selected === key ? 'border-rose-400 bg-rose-50' : 'border-gray-300'"
                >
                    <div v-if="selected === key" class="w-2 h-2 rounded-full bg-rose-400"></div>
                </div>
                <span class="text-gray-700">
                  <span class="font-semibold text-gray-400 mr-1">{{ key }}.</span>{{ text }}
                </span>
             </label>
         </template>
     </div>
     
     <!-- Feedback -->
     <div v-if="submitted" class="px-4 pb-3 text-sm font-semibold flex items-center gap-2 border-t border-gray-50 pt-2">
         <span v-if="isCorrect" class="text-emerald-600">✓ 正确！太棒了 🎉</span>
         <span v-else class="text-red-500">✗ 错了，正确答案是 <span class="font-bold underline">{{ correctAnswer }}</span></span>
     </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import request from '../../utils/request'
import { useUserStore } from '../../stores/useUserStore'
import { useMiaStore } from '../../stores/useMiaStore'
import { useExamStore } from '../../stores/useExamStore'

const props = defineProps({ question: Object })

const userStore = useUserStore()
const miaStore  = useMiaStore()
const examStore = useExamStore()

const selected      = ref(null)
const submitted     = ref(false)
const isCorrect     = ref(false)
const correctAnswer = ref(null)

const setFocus = () => {
    examStore.setActiveQuestion(props.question.q_id)
}

const getOptionClass = (key) => {
    if (!submitted.value) {
        return selected.value === key
          ? 'bg-rose-50 border-rose-300 text-gray-800'
          : 'hover:bg-gray-50 border-gray-100 text-gray-700'
    }
    if (key === correctAnswer.value) return 'bg-emerald-50 border-emerald-400'
    if (key === selected.value && !isCorrect.value) return 'bg-red-50 border-red-400'
    return 'opacity-50 border-gray-100'
}

const submit = async () => {
    if (submitted.value) return
    submitted.value = true
    
    // Set focus on submit as well
    setFocus()
    
    // console.log(`[SingleChoice] Q${props.question.question_number} 提交答案:`, selected.value)

    try {
        const res = await request.post('/exam/submit_objective', {
            q_id: props.question.q_id,
            answer: selected.value
        })
        // console.log('[SingleChoice] API 响应:', res)

        isCorrect.value     = res.correct
        correctAnswer.value = res.correct_answer

        // ── 交互链路：HP 扣减 + Mia 反馈 ──
        if (res.correct) {
            userStore.animateHpChange(0)  // 答对不扣血
            miaStore.history.push({ role: 'assistant', content: '答对了！你真棒 ✨ 继续保持！' })
        } else {
            userStore.animateHpChange(-10) // 答错扣 10 血
            userStore.setMood('worried')
            miaStore.history.push({
                role: 'assistant',
                content: `答错了，正确答案是 ${res.correct_answer}。别气馁，下次一定！`
            })
        }
        // console.log('[UserStore] HP 现在:', userStore.hp)

    } catch (e) {
        // ── API 不可用时的 Mock 反馈（保证前端闭环）──
        console.warn('[SingleChoice] API 调用失败，使用 Mock 反馈:', e.message)

        // Mock: 假设选 A 为正确答案
        const mockCorrect = selected.value === 'A'
        isCorrect.value     = mockCorrect
        correctAnswer.value = 'A'

        if (mockCorrect) {
            miaStore.history.push({ role: 'assistant', content: '（Mock）答对了！✨' })
        } else {
            userStore.animateHpChange(-10)
            userStore.setMood('worried')
            miaStore.history.push({ role: 'assistant', content: `（Mock）答错了，正确是 A。` })
        }
        // console.log('[Mock] HP 现在:', userStore.hp)
    }
}
</script>
