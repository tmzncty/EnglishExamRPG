<template>
  <!-- Mia 立绘：可拖拽，右下角为初始位置 -->
  <div
    ref="el"
    :style="dragStyle"
    class="fixed z-30 pointer-events-auto cursor-grab active:cursor-grabbing select-none"
    style="touch-action: none;"
  >
    <img
      :src="currentImage"
      class="block mix-blend-multiply object-contain transition-opacity duration-300 w-auto drop-shadow-sm"
      style="max-height: 40vh; max-width: 260px;"
      alt="Mia"
      draggable="false"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useDraggable } from '@vueuse/core'
import { useUserStore } from '../stores/useUserStore'
import { ASSETS } from '../config/assets'

const userStore = useUserStore()

const currentImage = computed(() => {
  return ASSETS.mia[userStore.mood] ?? ASSETS.mia.default
})

const el = ref(null)

// 初始位置：右下角留 24px 边距
const initialX = window.innerWidth - 280
const initialY = window.innerHeight - window.innerHeight * 0.42

const { style: dragStyle } = useDraggable(el, {
  initialValue: { x: initialX, y: initialY },
})
</script>
