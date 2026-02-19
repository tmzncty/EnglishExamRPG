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
