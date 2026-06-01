<template>
  <!-- [T1] 对话框收起过渡 -->
  <transition name="mia-dialog">
    <div
      v-show="!miaStore.miaCollapsed"
      ref="hudRef"
      :style="[style, dialogSizeStyle]"
      class="fixed z-50 flex flex-col rounded-2xl overflow-hidden shadow-[0_8px_32px_rgba(0,0,0,0.12)] border border-gray-200 bg-white/95 backdrop-blur-sm transition-all duration-300 touch-none-important resize-dialog"
    >
    <!-- ── 标题栏 / 拖拽区 ── -->
    <div
      ref="handle"
      class="flex items-center justify-between px-3 py-2 bg-white border-b border-gray-100 select-none shrink-0" :class="isFullscreen ? 'cursor-default' : 'cursor-move'"
    >
      <div class="flex items-center gap-2.5">
        <!-- 头像：w-14 h-14 = 56px -->
        <div class="w-14 h-14 rounded-full overflow-hidden border-2 border-rose-200 shrink-0 shadow-sm">
          <img :src="ASSETS.mia.avatar" class="w-full h-full object-cover rounded-full" alt="Mia" />
        </div>
        <div>
          <div class="text-sm font-bold text-gray-800 leading-none">Mia</div>
          <div class="text-[11px] text-gray-400 leading-none mt-1">
            <span v-if="miaStore.isTyping" class="text-mia-pink animate-pulse">正在输入…</span>
            <span v-else class="text-emerald-500">● 在线</span>
          </div>
        </div>
      </div>
      <div class="flex items-center gap-1">
        <button
            @click="miaStore.startNewChat()"
            class="w-7 h-7 rounded-full text-gray-400 hover:text-mia-pink hover:bg-rose-50 transition-all flex items-center justify-center text-xs"
            title="新建对话"
        >
            ➕
        </button>
        <button
            @click="toggleHistory"
            class="w-7 h-7 rounded-full text-gray-400 hover:text-mia-pink hover:bg-rose-50 transition-all flex items-center justify-center text-xs"
            title="历史记录"
        >
            📜
        </button>
        <button
            @click="isCollapsed = !isCollapsed"
            class="w-7 h-7 rounded-full text-gray-400 hover:text-mia-pink hover:bg-rose-50 transition-all flex items-center justify-center text-xs"
        >
            {{ isCollapsed ? '▲' : '▼' }}
        </button>
        <button
            @click="isFullscreen = !isFullscreen"
            class="w-7 h-7 rounded-full text-gray-400 hover:text-mia-pink hover:bg-rose-50 transition-all flex items-center justify-center text-xs"
            title="全屏 / 退出全屏"
        >
            {{ isFullscreen ? '🔲' : '⬜' }}
        </button>
      </div>
    </div>

    <!-- ── 对话历史 ── -->
    <div
      v-show="!isCollapsed"
      ref="chatContainer"
      class="flex-1 overflow-y-auto p-3 space-y-4 custom-scrollbar bg-gray-50/60"
    >
      <!-- History Panel Overlay -->
      <div v-if="miaStore.showHistoryPanel" class="absolute inset-0 top-[60px] bottom-[50px] bg-white/95 z-20 overflow-y-auto p-2 backdrop-blur-sm">
          <div class="flex justify-between items-center px-2 mb-2">
              <span class="text-xs font-bold text-gray-500">历史记录</span>
              <button @click="miaStore.showHistoryPanel = false" class="text-xs text-rose-400">关闭</button>
          </div>
          <div v-if="miaStore.conversationList.length === 0" class="text-center text-xs text-gray-400 py-4">无历史记录</div>
          <div 
            v-for="c in miaStore.conversationList" 
            :key="c.id"
            @click="miaStore.loadConversation(c.id)"
            class="p-2 hover:bg-rose-50 rounded-lg cursor-pointer text-xs mb-1 border border-transparent hover:border-rose-100 transition-all"
          >
              <div class="font-bold text-gray-700 truncate">{{ c.title }}</div>
              <div class="text-[10px] text-gray-400 flex justify-between mt-1">
                  <span>{{ c.updated_at.split(' ')[0] }}</span>
                  <span class="truncate max-w-[100px]">{{ c.last_message }}</span>
              </div>
          </div>
      </div>
      <div v-if="!miaStore.history.length" class="text-center text-gray-300 text-xs py-6">
        💬 和 Mia 打个招呼吧
      </div>

      <div
        v-for="(msg, index) in miaStore.history"
        :key="index"
        class="flex flex-col gap-1 w-full"
        :class="msg.role === 'user' ? 'items-end' : 'items-start'"
      >
        <span class="text-[10px] font-semibold px-1"
              :class="msg.role === 'user' ? 'text-gray-400' : 'text-rose-400'">
          {{ msg.role === 'user' ? '绯墨' : 'Mia' }}
        </span>
        
        <!-- 消息气泡 (Markdown渲染) -->
        <div
          class="px-3 py-2 rounded-2xl text-sm leading-relaxed max-w-[92%] shadow-sm overflow-hidden"
          :class="msg.role === 'user'
            ? 'bg-gray-200 text-gray-800 rounded-tr-none'
            : 'bg-white border border-pink-100 text-gray-700 rounded-tl-none prose prose-sm prose-pink max-w-none'"
        >
          <div v-if="msg.role === 'user'" class="whitespace-pre-wrap">{{ msg.content }}</div>
          <div v-else v-html="renderMarkdown(msg.content)"></div>
        </div>
      </div>

      <!-- 打字动画 -->
      <div v-if="miaStore.isTyping" class="flex items-start gap-1 pl-1">
        <div class="bg-white border border-pink-100 rounded-xl rounded-tl-none px-3 py-2 flex gap-1 shadow-sm">
          <span class="w-1.5 h-1.5 bg-rose-400 rounded-full animate-bounce" style="animation-delay:0ms"></span>
          <span class="w-1.5 h-1.5 bg-rose-400 rounded-full animate-bounce" style="animation-delay:150ms"></span>
          <span class="w-1.5 h-1.5 bg-rose-400 rounded-full animate-bounce" style="animation-delay:300ms"></span>
        </div>
      </div>
    </div>

    <!-- ── 功能开关栏 ── -->
    <div v-show="!isCollapsed" class="px-3 py-1.5 bg-white border-t border-gray-50 flex flex-col gap-1 text-[10px] text-gray-400 select-none">
        <div class="flex gap-3">
            <label class="flex items-center gap-1.5 cursor-pointer hover:text-rose-400 transition-colors py-1 touch-target">
                <input type="checkbox" v-model="attachContext" class="accent-rose-400 rounded-sm w-4 h-4" />
                <span>携带题目上下文</span>
            </label>
            <label class="flex items-center gap-1.5 cursor-pointer hover:text-rose-400 transition-colors py-1 touch-target">
                <input type="checkbox" v-model="rpgMode" class="accent-rose-400 rounded-sm w-4 h-4" />
                <span>启用扣血机制</span>
            </label>
        </div>
        <!-- 勾选时显示绑定的题目，没有 activeQuestionId 则橙色警告 -->
        <transition name="ctx-fade">
            <div v-if="attachContext" class="flex items-center gap-1 pl-0.5 leading-none">
                <template v-if="activeQLabel">
                    <span class="text-emerald-400">📎</span>
                    <span class="text-emerald-600 font-medium">{{ activeQLabel }}</span>
                </template>
                <template v-else>
                    <span class="text-amber-400">⚠</span>
                    <span class="text-amber-500">未选中题目 — 请先点击一道题</span>
                </template>
            </div>
        </transition>
    </div>

    <!-- ── 输入栏 (Textarea) ── -->
    <div v-show="!isCollapsed" class="flex gap-2 px-3 py-2 border-t border-gray-100 bg-white shrink-0 items-end">
      <textarea
        ref="textareaRef"
        v-model="inputText"
        @keydown.enter="handleEnter"
        placeholder="和 Mia 说点什么… (Shift+Enter换行)"
        rows="1"
        class="flex-1 text-sm bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 outline-none focus:border-rose-300 focus:ring-1 focus:ring-rose-100 text-gray-700 placeholder:text-gray-300 transition-all resize-none custom-scrollbar max-h-32"
        style="min-height: 38px;"
      ></textarea>
      
      <button
        @click="sendMessage"
        :disabled="!inputText.trim() || miaStore.isTyping"
        class="mb-0.5 px-3 py-2 rounded-lg bg-rose-400 hover:bg-rose-500 text-white text-xs font-semibold disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-sm active:scale-95 whitespace-nowrap"
      >
        发送
      </button>
    </div>
  </div>
  </transition>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue'
import { useDraggable, useWindowSize } from '@vueuse/core'
import { ASSETS } from '../config/assets'
import { useMiaStore } from '../stores/useMiaStore'
import { useExamStore } from '../stores/useExamStore'
import { marked, parse } from 'marked'

const miaStore = useMiaStore()
const examStore = useExamStore()

const hudRef        = ref(null)
const handle        = ref(null)
const chatContainer = ref(null)
const textareaRef   = ref(null)
const isCollapsed   = ref(false)
const inputText     = ref('')
const isFullscreen  = ref(false)

// 响应式窗口尺寸（适配平板高分屏）
const { width: winWidth } = useWindowSize()
const isTablet = computed(() => winWidth.value >= 2000)

const dialogSizeStyle = computed(() => {
  if (isFullscreen.value) {
    return { width: '100vw', height: '100dvh', top: 0, left: 0 }
  }
  if (isTablet.value) {
    return {
      minWidth: '380px',
      width: 'clamp(380px, 15vw, 640px)',
      height: 'clamp(550px, 45vh, 850px)'
    }
  }
  return {
    minWidth: '320px',
    width: 'clamp(320px, 18vw, 480px)',
    height: 'clamp(500px, 55vh, 700px)'
  }
})

// Toggles
const attachContext = ref(false)
const rpgMode       = ref(false)

// 题目类型短名映射
const SECTION_SHORT = {
    'translation':    '翻译',
    'writing_a':      '写作A',
    'writing_b':      '写作B',
    'use_of_english': '完形填空',
    'reading':        '阅读理解',
}

// "2025-eng1-translation-q46" → "2025 · 翻译 · 第46题"
const activeQLabel = computed(() => {
    const qid = examStore.activeQuestionId
    if (!qid) return null
    const parts = qid.split('-')
    const year  = parts[0]
    const qNum  = (parts[parts.length - 1] || '').replace('q', '')
    // section 是去掉 year / eng1 / qN 之后的中间段
    const sectionRaw = parts.slice(2, parts.length - 1).join('_')
    const name  = SECTION_SHORT[sectionRaw] || sectionRaw
    return `${year} · ${name} · 第${qNum}题`
})

const { style } = useDraggable(hudRef, {
  initialValue: { x: 24, y: window.innerHeight - 500 },
  handle: handle,
})

// Auto-resize textarea
watch(inputText, async () => {
    await nextTick()
    if (textareaRef.value) {
        textareaRef.value.style.height = 'auto'
        textareaRef.value.style.height = textareaRef.value.scrollHeight + 'px'
    }
})

// Markdown Renderer
const renderMarkdown = (text) => {
    if (!text) return ''
    try {
        let result;
        if (typeof marked?.parse === 'function') {
            result = marked.parse(text);
        } else if (typeof parse === 'function') {
            result = parse(text);
        } else if (typeof marked === 'function') {
            result = marked(text);
        } else {
            console.error("Marked instance missing parse method:", marked);
            return text; // Fallback raw
        }
        
        if (result instanceof Promise) {
            console.error("Marked unexpectedly returned a Promise. Using raw text fallback.");
            return text; // Fallback raw if marked is running in async mode
        }
        return result || text;
    } catch (e) {
        console.error("Markdown parse error:", e)
        return text; // Fallback raw text if crash occurs
    }
}

// 新消息时自动滚到底
watch(
  () => miaStore.history.length,
  async () => {
    await nextTick()
    if (chatContainer.value) {
        chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  }
)

const handleEnter = (e) => {
    if (e.shiftKey) return // Allow default newline
    e.preventDefault()
    sendMessage()
}

const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text || miaStore.isTyping) return
  
  inputText.value = ''
  // Reset height
  if (textareaRef.value) textareaRef.value.style.height = 'auto'
  
  miaStore.history.push({ role: 'user', content: text })
  
  // Construct context data with toggles
  const ctxData = {
      message: text,
      attach_context: attachContext.value,
      rpg_mode: rpgMode.value,
      q_id: attachContext.value ? examStore.activeQuestionId : null
  }
  
  await miaStore.interact('chat', ctxData)
}

const toggleHistory = () => {
    if (miaStore.showHistoryPanel) {
        miaStore.showHistoryPanel = false
    } else {
        miaStore.fetchHistory()
    }
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 3px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #ffb6c1; border-radius: 2px; }

/* 上下文绑定提示的淡入淡出 */
.ctx-fade-enter-active, .ctx-fade-leave-active { transition: opacity 0.2s, transform 0.2s; }
.ctx-fade-enter-from, .ctx-fade-leave-to { opacity: 0; transform: translateY(-3px); }

/* 平板可拖拽调整尺寸 */
.resize-dialog { resize: both; }

/* [T1] 对话框收起/展开过渡 */
.mia-dialog-enter-active {
  transition: opacity 0.35s ease, transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.mia-dialog-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease-in;
}
.mia-dialog-enter-from {
  opacity: 0;
  transform: scale(0.85) translateY(20px);
}
.mia-dialog-leave-to {
  opacity: 0;
  transform: scale(0.8) translateY(30px);
}
</style>
