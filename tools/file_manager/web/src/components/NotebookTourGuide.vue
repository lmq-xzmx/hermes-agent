<template>
  <div class="notebook-tour-wrapper">
    <TourGuide
      v-if="tourVisible"
      :visible="tourVisible"
      :steps="steps"
      :initial-step="0"
      @update:visible="handleClose"
      @complete="onComplete"
      @step-change="onStepChange"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import TourGuide from './TourGuide.vue'

const emit = defineEmits(['complete'])

const tourVisible = ref(false)
const currentStep = ref(0)
const STORAGE_KEY = 'notebook_tour_completed'

// Tour steps for notebook creation
const steps = [
  {
    target: '#nb_name',
    position: 'bottom',
    content: '📓 输入笔记本名称，如"项目需求文档"或"会议纪要"'
  },
  {
    target: '#nb_tags',
    position: 'bottom',
    content: '🏷 添加标签方便分类管理，如"项目"、"会议"、"教程"'
  },
  {
    target: '#nb_content',
    position: 'top',
    content: '✍️ 使用 Markdown 编写内容，支持标题、列表、代码高亮'
  },
  {
    target: '#nb_shared',
    position: 'right',
    content: '👥 勾选"团队共享"可以让空间成员协作编辑'
  }
]

function isCompleted() {
  return localStorage.getItem(STORAGE_KEY) === 'true'
}

function startTour() {
  if (isCompleted()) return
  tourVisible.value = true
}

function handleClose(val) {
  tourVisible.value = val
}

function onComplete() {
  localStorage.setItem(STORAGE_KEY, 'true')
  emit('complete')
  tourVisible.value = false
}

function onStepChange(step) {
  currentStep.value = step
}

// 监听引导触发事件
function handleGuidanceTrigger(e) {
  const { event, context } = e.detail || {}
  if (event === 'CREATE_NOTEBOOK' || event === 'FIRST_NOTEBOOK_CREATED') {
    startTour()
  }
}

// 监听 notebook:created 事件
function handleNotebookCreated(e) {
  console.log('[NotebookTour] notebook:created event received')
  startTour()
}

onMounted(() => {
  window.addEventListener('guidance:trigger', handleGuidanceTrigger)
  window.addEventListener('notebook:created', handleNotebookCreated)
  window.addEventListener('guidance:notebook-tour', () => {
    startTour()
  })
})

onUnmounted(() => {
  window.removeEventListener('guidance:trigger', handleGuidanceTrigger)
  window.removeEventListener('notebook:created', handleNotebookCreated)
  window.removeEventListener('guidance:notebook-tour', startTour)
})

defineExpose({ startTour })
</script>

<style scoped>
.notebook-tour-wrapper {
  /* Wrapper for scoped styles if needed */
}
</style>
