<template>
  <div class="mb-6">
      <div class="text-white mb-2 font-bold">{{ title }}</div>
      
      <!-- Prompt / Image -->
      <div v-if="image" class="mb-4">
          <img :src="image" class="max-w-full rounded border border-gray-700" alt="Writing Prompt" />
      </div>
      <div v-if="prompt" class="mb-4 text-gray-300 text-sm whitespace-pre-wrap leading-relaxed bg-gray-900/50 p-3 rounded">{{ prompt }}</div>
      
      <!-- Input Area -->
      <div class="relative">
          <textarea 
            v-model="content"
            rows="12"
            class="w-full bg-[#1e1e1e] border border-gray-700 rounded p-4 text-gray-300 focus:border-mia-pink focus:outline-none transition-colors resize-none font-mono"
            placeholder="Start writing here..."
          ></textarea>
          <div class="absolute bottom-3 right-3 text-xs text-gray-500">
              {{ wordCount }} words
          </div>
      </div>
      
      <div class="mt-4 flex justify-end">
          <button class="px-6 py-2 bg-mia-pink text-black font-bold rounded hover:bg-pink-400 transition-colors">
              Submit for AI Grading
          </button>
      </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
    title: String,
    prompt: String,
    image: String
})

const content = ref('')

const wordCount = computed(() => {
    return content.value.trim().split(/\s+/).filter(Boolean).length
})
</script>
