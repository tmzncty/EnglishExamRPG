<template>
  <div class="absolute inset-0 z-10 overflow-hidden pointer-events-none">
    <canvas 
      ref="canvasRef"
      class="block touch-none"
      :class="{ 'pointer-events-auto cursor-crosshair': mode === 'draw' }"
      @mousedown="startDrawing"
      @mousemove="draw"
      @mouseup="stopDrawing"
      @mouseleave="stopDrawing"
      @touchstart.prevent="startDrawing"
      @touchmove.prevent="draw"
      @touchend.prevent="stopDrawing"
    ></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { useResizeObserver } from '@vueuse/core'

const props = defineProps({
  color: { type: String, default: '#ff0000' },
  width: { type: Number, default: 2 },
  mode: { type: String, default: 'read' }, // 'read' or 'draw'
  initialData: { type: String, default: '' } // Base64 data
})

const emit = defineEmits(['update:data'])

const canvasRef = ref(null)
const ctx = ref(null)
const isDrawing = ref(false)
const lastX = ref(0)
const lastY = ref(0)

// 初始化 Canvas
const initCanvas = () => {
  const canvas = canvasRef.value
  const parent = canvas.parentElement
  if (!canvas || !parent) return

  // 设置物理像素大小 (解决模糊问题)
  const dpr = window.devicePixelRatio || 1
  canvas.width = parent.clientWidth * dpr
  canvas.height = parent.clientHeight * dpr
  
  // 设置 CSS 样式大小
  canvas.style.width = `${parent.clientWidth}px`
  canvas.style.height = `${parent.clientHeight}px`

  ctx.value = canvas.getContext('2d')
  ctx.value.scale(dpr, dpr)
  ctx.value.lineCap = 'round'
  ctx.value.lineJoin = 'round'
  
  // 恢复数据
  if (props.initialData) {
    const img = new Image()
    img.onload = () => {
      ctx.value.drawImage(img, 0, 0, parent.clientWidth, parent.clientHeight)
    }
    img.src = props.initialData
  }
}

// 监听父容器大小变化 (Project Note: 必须跟随文本区域高度变化)
useResizeObserver(document.body, () => {
   // Placeholder for body resize, but we want parent resize.
})

onMounted(() => {
  const parent = canvasRef.value?.parentElement
  if (parent) {
      // 使用 VueUse 的 useResizeObserver 监听父元素
      useResizeObserver(parent, (entries) => {
        const entry = entries[0]
        const { width, height } = entry.contentRect
        // 只有当尺寸发生确切变化时才重置，避免初始化闪烁
        // 注意：contentRect不包含padding? 
        // 为了安全起见，我们重新调用 initCanvas 获取 clientWidth/Height
        // 或者直接使用 clientWidth (which includes padding but not border/scroll)
        // initCanvas 会重置画布内容，符合 Reflow Trap 的处理逻辑 (Text Reflow -> Ink Clear)
        if (width && height) {
           initCanvas()
        }
      })
      initCanvas()
  }
})

// 绘图逻辑
const getPos = (e) => {
  const canvas = canvasRef.value
  const rect = canvas.getBoundingClientRect()
  
  let clientX, clientY
  if (e.touches) {
    clientX = e.touches[0].clientX
    clientY = e.touches[0].clientY
  } else {
    clientX = e.clientX
    clientY = e.clientY
  }
  
  return {
    x: clientX - rect.left,
    y: clientY - rect.top
  }
}

const startDrawing = (e) => {
  if (props.mode !== 'draw') return
  isDrawing.value = true
  const { x, y } = getPos(e)
  lastX.value = x
  lastY.value = y
}

const draw = (e) => {
  if (!isDrawing.value || props.mode !== 'draw') return
  
  const { x, y } = getPos(e)
  const context = ctx.value
  
  context.beginPath()
  context.strokeStyle = props.color
  context.lineWidth = props.width
  context.moveTo(lastX.value, lastY.value)
  context.lineTo(x, y)
  context.stroke()
  
  lastX.value = x
  lastY.value = y
}

const stopDrawing = () => {
  if (isDrawing.value) {
    isDrawing.value = false
    save()
  }
}

// 监听外部传入的初始数据 (支持异步加载/切换试题)
watch(() => props.initialData, (newVal) => {
  if (ctx.value && canvasRef.value) {
      // 1. 无论是否有新数据，先清空当前画布 (防止上一题笔记残留)
      const canvas = canvasRef.value
      const parent = canvas.parentElement
      
      // 清除物理像素区域 (覆盖整个Canvas)
      ctx.value.clearRect(0, 0, canvas.width, canvas.height) 
      
      // 2. 如果有数据，则绘制
      if (newVal) {
          const img = new Image()
          img.onload = () => {
             // 确保绘制时 Context 状态正确
             ctx.value.drawImage(img, 0, 0, parent.clientWidth, parent.clientHeight)
          }
          img.src = newVal
      }
      
      // 3. 重置内部状态? 
      // isDrawing should be false.
      isDrawing.value = false
  }
})

const save = () => {
  // 导出数据
  const data = canvasRef.value.toDataURL('image/png')
  emit('update:data', data)
}

const clear = () => {
  const canvas = canvasRef.value
  ctx.value.clearRect(0, 0, canvas.width, canvas.height)
  save()
}

// 暴露方法给父组件
defineExpose({ clear, save })

</script>
