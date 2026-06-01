<template>
  <!-- Mia 立绘：可拖拽，右下角初始位置。支持收起/展开 -->
  <transition name="mia-stage">
    <div
      v-show="!miaStore.miaCollapsed"
      ref="el"
      :style="dragStyle"
      class="fixed z-30 pointer-events-auto select-none mia-stage-wrapper"
      style="touch-action: none;"
    >
      <!-- [T1] 最小化按钮 -->
      <button
        @click="miaStore.toggleMiaCollapsed()"
        class="absolute -top-2 -right-2 w-7 h-7 rounded-full bg-white/90 border border-gray-200 shadow-md text-gray-400 hover:text-rose-500 hover:border-rose-200 flex items-center justify-center text-xs transition-all z-10 opacity-0 group-hover:opacity-100 mia-minimize-btn cursor-pointer"
        title="收起 Mia 立绘"
      >
        ✕
      </button>

      <img
        :src="currentImage"
        class="block mix-blend-multiply object-contain transition-opacity duration-300 w-auto drop-shadow-sm max-w-[clamp(180px,12vw,400px)] max-h-[clamp(30dvh,35dvh,50dvh)]"
        alt="Mia"
        draggable="false"
      />
    </div>
  </transition>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useDraggable } from '@vueuse/core'
import { useUserStore } from '../stores/useUserStore'
import { useMiaStore } from '../stores/useMiaStore'
import { ASSETS } from '../config/assets'

const userStore = useUserStore()
const miaStore = useMiaStore()

const currentImage = computed(() => {
  return ASSETS.mia[userStore.mood] ?? ASSETS.mia.default
})

const el = ref(null)

const initialX = window.innerWidth - 280
const initialY = window.innerHeight - window.innerHeight * 0.42

const { style: dragStyle } = useDraggable(el, {
  initialValue: { x: initialX, y: initialY },
})
</script>

<style scoped>
/* [T1] 收起/展开过渡动画 */
.mia-stage-enter-active {
  transition: opacity 0.4s ease, transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.mia-stage-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease-in;
}
.mia-stage-enter-from {
  opacity: 0;
  transform: scale(0.7) translateY(20px);
}
.mia-stage-leave-to {
  opacity: 0;
  transform: scale(0.5) translateY(40px);
}

/* [T1] 在 wrapper 上 hover 显示最小化按钮 */
.mia-stage-wrapper:hover .mia-minimize-btn {
  opacity: 1;
}
.mia-minimize-btn {
  transition: opacity 0.2s ease, color 0.2s ease, border-color 0.2s ease;
}
</style>
