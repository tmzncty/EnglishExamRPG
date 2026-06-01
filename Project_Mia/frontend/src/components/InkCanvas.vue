<template>
  <div class="absolute inset-0 z-10 overflow-hidden pointer-events-none">
    <canvas 
      ref="canvasRef"
      class="block touch-none"
      :class="{ 'pointer-events-auto': mode === 'draw' || mode === 'erase' }"
      @pointerdown="startDrawing"
      @pointermove="draw"
      @pointerup="stopDrawing"
      @pointerleave="stopDrawing"
      @pointercancel="stopDrawing"
    ></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { useResizeObserver } from '@vueuse/core'

const props = defineProps({
  color: { type: String, default: '#ff3b30' },
  width: { type: Number, default: 2 },
  mode: { type: String, default: 'read' }, // 'read' | 'draw' | 'erase'
  initialData: { type: String, default: '' }
})

const emit = defineEmits(['update:data'])

const canvasRef = ref(null)
const ctx = ref(null)
const isDrawing = ref(false)
const lastX = ref(0)
const lastY = ref(0)
const lastPressure = ref(0.5)

// ── Undo Stack ──
const MAX_UNDO = 30
const undoStack = ref([])

const pushUndo = () => {
  const data = canvasRef.value?.toDataURL('image/png')
  if (data) {
    undoStack.value.push(data)
    if (undoStack.value.length > MAX_UNDO) undoStack.value.shift()
  }
}

const undo = () => {
  if (undoStack.value.length === 0) return
  const data = undoStack.value.pop()
  const canvas = canvasRef.value
  const parent = canvas.parentElement
  ctx.value.clearRect(0, 0, canvas.width, canvas.height)
  const img = new Image()
  img.onload = () => {
    ctx.value.drawImage(img, 0, 0, parent.clientWidth, parent.clientHeight)
    save()
  }
  img.src = data
}

// 初始化 Canvas
const initCanvas = () => {
  const canvas = canvasRef.value
  const parent = canvas.parentElement
  if (!canvas || !parent) return

  const dpr = window.devicePixelRatio || 1
  canvas.width = parent.clientWidth * dpr
  canvas.height = parent.clientHeight * dpr
  
  canvas.style.width = `${parent.clientWidth}px`
  canvas.style.height = `${parent.clientHeight}px`

  ctx.value = canvas.getContext('2d')
  ctx.value.scale(dpr, dpr)
  ctx.value.lineCap = 'round'
  ctx.value.lineJoin = 'round'
  
  if (props.initialData) {
    const img = new Image()
    img.onload = () => {
      ctx.value.drawImage(img, 0, 0, parent.clientWidth, parent.clientHeight)
    }
    img.src = props.initialData
  }
}

onMounted(() => {
  const parent = canvasRef.value?.parentElement
  if (parent) {
      useResizeObserver(parent, (entries) => {
        const entry = entries[0]
        const { width, height } = entry.contentRect
        if (width && height) {
           initCanvas()
        }
      })
      initCanvas()
  }
})

// ── Pointer Events (统一处理鼠标+触摸+笔) ──
const getPos = (e) => {
  const canvas = canvasRef.value
  const rect = canvas.getBoundingClientRect()
  return {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top,
    pressure: e.pressure || 0.5  // 鼠标默认 0.5
  }
}

const startDrawing = (e) => {
  if (props.mode === 'read') return
  // 笔输入时捕获指针防止浏览器手势干扰
  if (e.pointerType === 'pen') canvasRef.value?.setPointerCapture(e.pointerId)
  isDrawing.value = true
  const { x, y, pressure } = getPos(e)
  lastX.value = x
  lastY.value = y
  lastPressure.value = pressure
  pushUndo()  // 每个 stroke 开始前保存状态
}

const draw = (e) => {
  if (!isDrawing.value || props.mode === 'read') return
  
  const { x, y, pressure } = getPos(e)
  const context = ctx.value
  
  context.beginPath()
  context.lineWidth = props.width * (1 + pressure * 2)  // 压感: 1x~3x 粗细
  
  if (props.mode === 'erase') {
    context.globalCompositeOperation = 'destination-out'
    context.lineWidth = props.width * (3 + pressure * 4)  // 橡皮擦更大
    context.strokeStyle = 'rgba(0,0,0,1)'
  } else {
    context.globalCompositeOperation = 'source-over'
    context.strokeStyle = props.color
  }
  
  context.moveTo(lastX.value, lastY.value)
  context.lineTo(x, y)
  context.stroke()
  
  lastX.value = x
  lastY.value = y
  lastPressure.value = pressure
}

const stopDrawing = (e) => {
  if (isDrawing.value) {
    isDrawing.value = false
    // 重置合成模式
    ctx.value.globalCompositeOperation = 'source-over'
    save()
  }
}

// 监听初始数据
watch(() => props.initialData, (newVal) => {
  if (ctx.value && canvasRef.value) {
      const canvas = canvasRef.value
      const parent = canvas.parentElement
      ctx.value.clearRect(0, 0, canvas.width, canvas.height) 
      if (newVal) {
          const img = new Image()
          img.onload = () => {
             ctx.value.drawImage(img, 0, 0, parent.clientWidth, parent.clientHeight)
          }
          img.src = newVal
      }
      isDrawing.value = false
      undoStack.value = []  // 换题时清空撤销栈
  }
})

const save = () => {
  const data = canvasRef.value.toDataURL('image/png')
  emit('update:data', data)
}

const clear = () => {
  pushUndo()  // 清除前保存状态，可撤销
  const canvas = canvasRef.value
  ctx.value.clearRect(0, 0, canvas.width, canvas.height)
  save()
}

defineExpose({ clear, save, undo })
</script>
