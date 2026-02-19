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
          <!-- HP Fill — must have explicit bg color to be visible -->
          <div
            class="h-full rounded-full bg-gradient-to-r from-rose-400 to-mia-pink transition-all duration-700 ease-out"
            :style="{ width: userStore.hpPercentage + '%' }"
          ></div>
          <span class="absolute inset-0 flex items-center justify-center text-[9px] font-bold text-gray-700 drop-shadow-sm">
            HP {{ userStore.hp }} / {{ userStore.maxHp }}
          </span>
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

const userStore = useUserStore()
const hudRef    = ref(null)

const { style } = useDraggable(hudRef, {
  initialValue: { x: 20, y: 72 },
})
</script>
