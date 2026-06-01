<template>
  <!-- ☀️ Paper Mode: 米白色纸张背景 -->
  <div class="relative w-full min-h-screen bg-[#f5f5f0]">

    <!-- HUD Layer -->
    <GameHUD />

    <!-- Main Content Area -->
    <div class="relative z-10 w-full min-h-full">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </div>

    <!-- Mia 立绘 (可拖拽) — [T1] collapsed 状态由 miaStore 管理 -->
    <MiaStage />

    <!-- Mia Shell 对话框 (可拖拽，自包含聊天) — [T1] collapsed 状态由 miaStore 管理 -->
    <DraggableDialog />

    <!-- ⚰️ DialogBox 已退役，由 DraggableDialog 接管 -->

    <!-- 🧭 Navigation Bar ([T1] 添加收起 Mia 开关) -->
    <div id="global-nav" class="fixed bottom-4 left-1/2 transform -translate-x-1/2 z-50 flex gap-2 bg-white/90 backdrop-blur shadow-lg border border-gray-200 p-1.5 rounded-full tablet:bottom-auto tablet:top-1/2 tablet:left-6 tablet:-translate-y-1/2 tablet:-translate-x-0 tablet:flex-col tablet:gap-1 tablet:p-2 tablet:rounded-2xl" style="margin-bottom: env(safe-area-inset-bottom, 0px);">
        <router-link
            to="/"
            class="px-4 py-2 rounded-full text-sm font-bold text-gray-400 hover:text-gray-800 hover:bg-gray-100 transition-colors flex items-center gap-2 touch-target tablet:px-3 tablet:py-3 tablet:flex-col tablet:text-xs tablet:gap-0.5"
            active-class="bg-rose-50 text-rose-500 shadow-sm"
        >
            <span>📝</span>
            <span class="hidden md:inline tablet:text-[10px]">Dashboard</span>
        </router-link>

        <router-link
            to="/garden"
            class="px-4 py-2 rounded-full text-sm font-bold text-gray-400 hover:text-gray-800 hover:bg-gray-100 transition-colors flex items-center gap-2 touch-target tablet:px-3 tablet:py-3 tablet:flex-col tablet:text-xs tablet:gap-0.5"
            active-class="bg-emerald-50 text-emerald-600 shadow-sm"
        >
            <span>🌱</span>
            <span class="hidden md:inline tablet:text-[10px]">Garden</span>
        </router-link>

        <!-- [T1] 全局 Mia 收起/展开开关 -->
        <button
            @click="miaStore.toggleMiaCollapsed()"
            class="px-4 py-2 rounded-full text-sm font-bold transition-colors flex items-center gap-2 touch-target tablet:px-3 tablet:py-3 tablet:flex-col tablet:text-xs tablet:gap-0.5"
            :class="miaStore.miaCollapsed
              ? 'text-gray-500 hover:text-rose-500 hover:bg-rose-50 bg-gray-50'
              : 'text-rose-500 bg-rose-50 shadow-sm'"
            :title="miaStore.miaCollapsed ? '展开 Mia (立绘+对话框)' : '收起 Mia (立绘+对话框)'"
        >
            <span class="text-base" :class="{ 'opacity-40': miaStore.miaCollapsed }">
              {{ miaStore.miaCollapsed ? '💤' : '👤' }}
            </span>
            <span class="hidden md:inline tablet:text-[10px]">
              {{ miaStore.miaCollapsed ? 'Mia 已收起' : 'Mia' }}
            </span>
        </button>
    </div>

  </div>
</template>

<script setup>
import { watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useWindowSize } from '@vueuse/core'
import GameHUD        from './GameHUD.vue'
import MiaStage       from './MiaStage.vue'
import DraggableDialog from './DraggableDialog.vue'
import { useMiaStore } from '../stores/useMiaStore'

const route = useRoute()
const miaStore = useMiaStore()
const { width: winWidth } = useWindowSize()

const TABLET_BP = 2000

// [T1] 在需要专注的页面（ExamRoom / VocabGarden）自动收起 Mia
// 离开这些页面时自动展开（仅当之前由自动触发）
const FOCUS_ROUTES = ['ExamRoom', 'VocabGarden']

watch(
  () => route.name,
  (newName, oldName) => {
    const isTablet = winWidth.value >= TABLET_BP

    if (isTablet && FOCUS_ROUTES.includes(newName)) {
      // 进入专注页面 → 自动收起
      miaStore.autoCollapseMia()
    } else if (FOCUS_ROUTES.includes(oldName) && !FOCUS_ROUTES.includes(newName)) {
      // 离开专注页面 → 自动展开
      miaStore.autoExpandMia()
    }
  },
  { immediate: true }
)

// [T1] 初始化时检测：如果页面加载时就已经在专注路由上
onMounted(() => {
  if (winWidth.value >= TABLET_BP && FOCUS_ROUTES.includes(route.name)) {
    miaStore.autoCollapseMia()
  }
})
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
