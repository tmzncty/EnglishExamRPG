<template>
  <!-- ☀️ Paper Mode: 米白色纸张背景 -->
  <div class="relative w-full h-screen bg-[#f5f5f0] overflow-hidden">

    <!-- HUD Layer -->
    <GameHUD />

    <!-- Main Content Area -->
    <div class="relative z-10 w-full h-full">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </div>

    <!-- Mia 立绘 (可拖拽) -->
    <MiaStage />

    <!-- Mia Shell 对话框 (可拖拽，自包含聊天) -->
    <DraggableDialog />

    <!-- ⚰️ DialogBox 已退役，由 DraggableDialog 接管 -->
    
    <!-- 🧭 Navigation Bar (New in Phase 16.1) -->
    <!-- Fixed Bottom on Mobile, or you can choose another placement. -->
    <!-- Let's put it Top-Right fixed for Desktop, and Bottom Fixed for Mobile? 
         Or just a simple floating pill at bottom center? -->
    <div class="fixed bottom-4 left-1/2 transform -translate-x-1/2 z-50 flex gap-2 bg-white/90 backdrop-blur shadow-lg border border-gray-200 p-1.5 rounded-full">
        <router-link 
            to="/" 
            class="px-4 py-2 rounded-full text-sm font-bold text-gray-400 hover:text-gray-800 hover:bg-gray-100 transition-colors flex items-center gap-2"
            active-class="bg-rose-50 text-rose-500 shadow-sm"
        >
            <span>📝</span>
            <span class="hidden md:inline">Dashboard</span>
        </router-link>
        
        <router-link 
            to="/garden" 
            class="px-4 py-2 rounded-full text-sm font-bold text-gray-400 hover:text-gray-800 hover:bg-gray-100 transition-colors flex items-center gap-2"
            active-class="bg-emerald-50 text-emerald-600 shadow-sm"
        >
            <span>🌱</span>
            <span class="hidden md:inline">Garden</span>
        </router-link>
    </div>

  </div>
</template>

<script setup>
import GameHUD        from './GameHUD.vue'
import MiaStage       from './MiaStage.vue'
import DraggableDialog from './DraggableDialog.vue'
// DialogBox 不再引入
</script>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
