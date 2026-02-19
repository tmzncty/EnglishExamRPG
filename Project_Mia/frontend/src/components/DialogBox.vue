<template>
  <div 
    v-if="miaStore.dialogVisible"
    class="fixed bottom-8 left-1/2 transform -translate-x-1/2 w-[800px] h-48 z-40
           bg-black/80 border-2 border-mia-pink/50 rounded-xl backdrop-blur-sm
           shadow-[0_0_20px_rgba(255,182,193,0.2)] p-6 flex flex-col justify-between
           transition-all duration-300"
  >
    <!-- Header -->
    <div class="flex items-center gap-2 mb-2">
      <span class="text-mia-pink font-bold text-lg select-none">Mia</span>
      <span v-if="miaStore.isTyping" class="text-xs text-gray-400 animate-pulse">正在输入...</span>
    </div>

    <!-- Content -->
    <div class="flex-1 text-white text-lg leading-relaxed font-sans overflow-y-auto custom-scrollbar">
      {{ miaStore.currentText }}
      <span v-if="miaStore.isTyping" class="inline-block w-2 h-4 bg-mia-pink ml-1 animate-blink"></span>
    </div>

    <!-- Triangle Indicator -->
    <div v-if="!miaStore.isTyping" class="absolute bottom-4 right-4 text-mia-pink animate-bounce select-none">
      ▼
    </div>
  </div>
</template>

<script setup>
import { useMiaStore } from '../stores/useMiaStore'
const miaStore = useMiaStore()
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.animate-blink {
  animation: blink 1s step-end infinite;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
</style>
