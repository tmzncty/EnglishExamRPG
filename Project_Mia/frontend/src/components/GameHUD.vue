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

        <!-- Temporary Heal Button -->
        <div class="flex items-center gap-2 mt-1 ml-1">
            <button 
              @click="userStore.animateHpChange(20)"
              class="px-2 py-0.5 bg-emerald-50 text-emerald-600 text-[10px] rounded hover:bg-emerald-100 transition-colors cursor-pointer border border-emerald-200 w-fit"
              title="临时休整：恢复 20 HP"
            >
              💊 休息
            </button>
            
            <!-- [Stage 15.0] 多存档切换 -->
            <select 
                v-model="userStore.currentSlotId" 
                @change="handleSlotChange"
                class="text-[10px] bg-white border border-gray-300 rounded px-1 py-0.5 outline-none text-gray-600 hover:border-rose-300 focus:border-rose-400 transition-colors cursor-pointer"
            >
                <option :value="0">Slot 0 (Main)</option>
                <!-- Dynamic slots will be populated via userStore.slots list if available, but for now fixed -->
                <!-- Ideally should iterate userStore.availableSlots -->
                <option v-for="slot in userStore.availableSlots" :key="slot.slot_id" :value="slot.slot_id">
                    {{ slot.summary }}
                </option>
            </select>
            
            <!-- [Stage 16.0] Create New Slot -->
             <button 
              @click="createNewSlot"
              class="px-2 py-0.5 bg-sky-50 text-sky-600 text-[10px] rounded hover:bg-sky-100 transition-colors cursor-pointer border border-sky-200 w-fit font-bold"
              title="新建存档"
            >
              +
            </button>
        </div>

        <!-- EXP Track -->
        <div class="h-1.5 bg-gray-100 rounded-full w-4/5 ml-1 border border-gray-200 overflow-hidden">
          <div class="h-full rounded-full bg-sky-400 transition-all duration-700" style="width: 33%"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useDraggable } from '@vueuse/core'
import { useUserStore } from '../stores/useUserStore'
import { useExamStore } from '../stores/useExamStore'

const userStore = useUserStore()
const examStore = useExamStore()
const hudRef    = ref(null)

const { style } = useDraggable(hudRef, {
  initialValue: { x: 20, y: 72 },
})

const handleSlotChange = async () => {
    // 切换存档后，立即重载用户状态 + 答题记录
    // console.log(`[GameHUD] Switching to Slot ${userStore.currentSlotId}...`)
    await userStore.loadUser(userStore.currentSlotId)
    await examStore.fetchAnswerHistory()
}

const createNewSlot = async () => {
    if(!confirm("Create a new save slot?")) return;
    try {
        await userStore.createSlot() 
    } catch(e) {
        alert("Failed to create slot: " + e.message)
    }
}
</script>
