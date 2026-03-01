<template>
  <Layout />
</template>

<script setup>
import { onMounted } from 'vue'
import Layout from './components/Layout.vue'
import { useUserStore } from '@/stores/useUserStore'

const userStore = useUserStore()

onMounted(async () => {
    console.log("🎮 [System] Initializing RPG Save Data...")
    await userStore.init()
})
</script>
