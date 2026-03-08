<template>
  <div
    ref="hudRef"
    :style="style"
    class="fixed z-40 flex flex-col gap-2 cursor-move select-none"
    style="touch-action: none;"
  >
    <div class="flex items-center gap-3 bg-white/90 backdrop-blur-sm px-3 py-2 rounded-xl shadow-sm border border-gray-100">
      <!-- Level Badge -->
      <div class="w-10 h-10 rounded-full bg-white border-2 border-mia-pink flex items-center justify-center text-mia-pink-dark font-bold text-xs shadow-sm shrink-0">
        Lv.{{ userStore.level }}
      </div>
      
      <div class="flex flex-col gap-1 w-48">
        <template v-if="!isExamRoute">
            <!-- HP Track -->
        <div class="h-3 bg-gray-100 rounded-full overflow-hidden border border-gray-200 relative">
          <!-- HP Fill — Dynamic Width & Color -->
          <div
            class="h-full rounded-full transition-all duration-500 ease-out"
            :class="{
              'bg-sky-400': userStore.hpPercentage > 40,
              'bg-amber-400': userStore.hpPercentage > 15 && userStore.hpPercentage <= 40,
              'bg-rose-500 animate-pulse': userStore.hpPercentage <= 15
            }"
            :style="{ width: userStore.hpPercentage + '%' }"
          ></div>
          <span class="absolute inset-0 flex items-center justify-center text-[9px] font-bold text-gray-700 drop-shadow-sm">
            HP {{ userStore.hp }} / {{ userStore.maxHp }}
          </span>
        </div>

        <!-- Temporary Heal Button + Slot Selector -->
        <div class="flex items-center gap-2 mt-1 ml-1">
            <button 
              @click="userStore.animateHpChange(20)"
              class="px-2 py-0.5 bg-emerald-50 text-emerald-600 text-[10px] rounded hover:bg-emerald-100 transition-colors cursor-pointer border border-emerald-200 w-fit"
              title="临时休整：恢复 20 HP"
            >
              💊 休息
            </button>
            
            <!-- [Stage 20.0 / 21.0] Dynamic Slot Selector -->
            <select 
                v-model="userStore.currentSlotId" 
                @change="handleSlotChange"
                class="text-[10px] bg-white border border-gray-300 rounded px-1 py-0.5 outline-none text-gray-600 hover:border-rose-300 focus:border-rose-400 transition-colors cursor-pointer max-w-[90px] truncate"
            >
                <option v-for="slot in userStore.availableSlots" :key="slot.slot_id" :value="slot.slot_id">
                    {{ slot.slot_name }}
                </option>
            </select>
            
            <!-- [Stage 20.0] ⚙️ Settings Modal Trigger -->
             <button 
              @click="showSettingsModal = true"
              class="px-1.5 py-0.5 bg-gray-50 text-gray-500 text-[10px] rounded hover:bg-gray-100 transition-colors cursor-pointer border border-gray-200 w-fit"
              title="存档管理"
            >
              ⚙️
            </button>
        </div>

        <!-- EXP Track [Stage 20.0 Fix: dynamic width + label] -->
        <div class="h-3 bg-gray-100 rounded-full w-4/5 ml-1 border border-gray-200 overflow-hidden relative">
          <div class="h-full rounded-full bg-indigo-400 transition-all duration-700" :style="{ width: expPercentage + '%' }"></div>
          <span class="absolute inset-0 flex items-center justify-center text-xs font-bold text-sky-900 drop-shadow-sm">
            EXP {{ userStore.exp }} / {{ nextLevelExp }}
          </span>
        </div>
        </template>
        <!-- Exam Mode Visual -->
        <div v-else class="h-8 bg-blue-50 border border-blue-100 rounded-lg flex items-center justify-center pointer-events-none">
            <span class="text-xs font-bold text-blue-600 tracking-widest flex items-center gap-2">
               <span>🛡️</span> Immersed in Exam
            </span>
        </div>
      </div>
    </div>

    <!-- ⚙️ [Stage 20.0] Settings Modal -->
    <Teleport to="body">
      <div v-if="showSettingsModal" class="fixed inset-0 z-[999] flex items-center justify-center" @click.self="showSettingsModal = false">
        <!-- Overlay -->
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm"></div>
        
        <!-- Modal Content -->
        <div class="relative bg-white rounded-2xl shadow-2xl w-[360px] max-h-[80vh] overflow-y-auto p-6 z-10">
          <h3 class="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            ⚙️ 存档管理
          </h3>

          <!-- Current Slot Settings -->
          <div class="space-y-3 mb-6">
            <div class="text-xs font-bold text-gray-400 uppercase tracking-wider">当前存档设置</div>

            <div>
              <label class="text-xs text-gray-500 mb-1 block">存档名称</label>
              <input 
                v-model="editSlotName" 
                class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-rose-300 transition-colors"
                placeholder="输入存档名称"
              />
            </div>

            <div>
              <label class="text-xs text-gray-500 mb-1 block">每日新词上限</label>
              <input 
                v-model.number="editDailyLimit" 
                type="number" 
                min="1" max="200"
                class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-rose-300 transition-colors"
              />
            </div>

            <div>
              <label class="text-xs text-gray-500 mb-1 block">每日刷新时间 (HH:MM)</label>
              <input 
                v-model="editResetTime" 
                type="time"
                class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-rose-300 transition-colors"
              />
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="flex gap-2 mb-4">
            <button 
              @click="saveSlotSettings"
              class="flex-1 py-2 bg-rose-500 text-white rounded-lg text-sm font-bold hover:bg-rose-600 active:scale-95 transition-all"
            >
              💾 保存设置
            </button>
            <button 
              @click="showSettingsModal = false"
              class="flex-1 py-2 bg-gray-100 text-gray-600 rounded-lg text-sm font-bold hover:bg-gray-200 active:scale-95 transition-all"
            >
              取消
            </button>
          </div>

          <hr class="my-4 border-gray-100" />

          <!-- Slot Management -->
          <div class="space-y-2">
            <div class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">所有存档</div>
            
            <div 
              v-for="slot in userStore.availableSlots" :key="slot.slot_id"
              class="flex items-center justify-between p-2 rounded-lg border border-gray-100 hover:bg-gray-50 transition-colors"
            >
              <div class="flex-1 min-w-0">
                <div class="text-sm font-bold text-gray-700 truncate">{{ slot.slot_name }}</div>
                <div class="text-[10px] text-gray-400">{{ slot.summary }} · 每日{{ slot.daily_new_words_limit || 30 }}词 · {{ slot.daily_reset_time || '04:00' }}刷新</div>
              </div>
              <button 
                v-if="slot.slot_id !== 0"
                @click="deleteSlot(slot.slot_id, slot.slot_name)"
                class="ml-2 px-2 py-1 text-rose-400 text-xs hover:bg-rose-50 rounded transition-colors shrink-0"
                title="删除存档"
              >
                🗑️
              </button>
            </div>

            <button 
              @click="createNewSlotFromModal"
              class="w-full py-2 border-2 border-dashed border-gray-200 text-gray-400 rounded-lg text-sm font-bold hover:border-rose-300 hover:text-rose-400 active:scale-95 transition-all"
            >
              + 新建存档
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useDraggable } from '@vueuse/core'
import { useUserStore } from '../stores/useUserStore'
import { useExamStore } from '../stores/useExamStore'
import request from '../utils/request'

const route = useRoute()
const userStore = useUserStore()
const examStore = useExamStore()
const hudRef    = ref(null)

const isExamRoute = computed(() => {
    return route.path.startsWith('/exam/')
})

const { style } = useDraggable(hudRef, {
  initialValue: { x: 20, y: 72 },
})

// --- EXP computation ---
const nextLevelExp = computed(() => userStore.level * 100)
const expPercentage = computed(() => {
    const needed = nextLevelExp.value
    if (needed <= 0) return 0
    return Math.min(100, Math.max(0, (userStore.exp / needed) * 100))
})

// --- Slot switching ---
const handleSlotChange = async () => {
    await userStore.loadUser(userStore.currentSlotId)
    await examStore.fetchAnswerHistory()
}

// --- [Stage 20.0] Settings Modal ---
const showSettingsModal = ref(false)
const editSlotName = ref('')
const editDailyLimit = ref(30)
const editResetTime = ref('04:00')

// When modal opens, populate fields with current slot info
watch(showSettingsModal, (isOpen) => {
    if (isOpen) {
        const current = userStore.availableSlots.find(s => s.slot_id === userStore.currentSlotId)
        if (current) {
            editSlotName.value = current.slot_name
            editDailyLimit.value = current.daily_new_words_limit || 30
            editResetTime.value = current.daily_reset_time || '04:00'
        }
    }
})

const saveSlotSettings = async () => {
    try {
        await request.put(`/user/slots/${userStore.currentSlotId}`, {
            slot_name: editSlotName.value,
            daily_new_words_limit: editDailyLimit.value,
            daily_reset_time: editResetTime.value,
        })
        await userStore.fetchSlots()
        showSettingsModal.value = false
    } catch (e) {
        alert('保存失败: ' + e.message)
    }
}

const createNewSlotFromModal = async () => {
    const name = prompt('请输入新存档名称:', `Save ${userStore.availableSlots.length}`)
    if (!name) return
    try {
        await userStore.createSlot(name)
    } catch (e) {
        alert('创建失败: ' + e.message)
    }
}

const deleteSlot = async (slotId, slotName) => {
    if (!confirm(`确定要删除存档「${slotName || slotId}」吗？此操作不可撤销！`)) return
    try {
        await request.delete(`/user/slots/${slotId}`)
        await userStore.fetchSlots()
        // If deleted current slot, switch to slot 0
        if (userStore.currentSlotId === slotId) {
            userStore.currentSlotId = 0
            await userStore.loadUser(0)
        }
    } catch (e) {
        alert('删除失败: ' + e.message)
    }
}
</script>
