<template>
  <div class="workflow-tour-wrapper">
    <TourGuide
      v-if="tourVisible"
      :visible="tourVisible"
      :steps="tourSteps"
      @update:visible="handleTourClose"
      @complete="handleTourComplete"
      @step-change="handleStepChange"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import TourGuide from '../TourGuide.vue'

const props = defineProps({
  spaceId: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['complete', 'select-template'])

const tourVisible = ref(false)
const currentStep = ref(0)
const templates = ref([])
const templatesLoading = ref(false)

const STORAGE_KEY = 'workflow_tour_completed'

const tourSteps = computed(() => [
  {
    target: '[data-tour="workflow-create-btn"]',
    position: 'bottom',
    content: '点击「+ 新建工作流」按钮开始创建工作流'
  },
  {
    target: '[data-tour="workflow-template-list"]',
    position: 'right',
    content: templatesLoading.value
      ? '正在加载模板...'
      : '从模板列表中选择「文件归档流程」模板，或选择空白工作流开始'
  },
  {
    target: '[data-tour="workflow-share-btn"]',
    position: 'top',
    content: '配置完成后，点击「分享」将工作流分享给团队成员'
  }
])

const isCompleted = computed(() => {
  return localStorage.getItem(STORAGE_KEY) === 'true'
})

// 启动 tour
function startTour() {
  if (isCompleted.value) return
  loadTemplates()
  tourVisible.value = true
}

// 监听引导触发事件（来自 Vanilla JS 系统）
function handleGuidanceTrigger(e) {
  const { event, context } = e.detail || {}
  if (event === 'CREATE_WORKFLOW' || event === 'WORKFLOW_EXECUTED') {
    startTour()
  }
}

onMounted(() => {
  // 监听来自引导系统的触发事件
  window.addEventListener('guidance:trigger', handleGuidanceTrigger)

  // 监听 workflow:created 事件
  window.addEventListener('workflow:created', (e) => {
    console.log('[WorkflowTour] workflow:created event received')
    startTour()
  })

  // 监听来自 guidanceStore 的事件
  window.addEventListener('guidance:workflow-tour', () => {
    startTour()
  })
})

onUnmounted(() => {
  window.removeEventListener('guidance:trigger', handleGuidanceTrigger)
  window.removeEventListener('workflow:created', startTour)
  window.removeEventListener('guidance:workflow-tour', startTour)
})

async function loadTemplates() {
  if (!props.spaceId) return

  templatesLoading.value = true
  try {
    const resp = await fetch(`/api/v1/spaces/${props.spaceId}/workflows`)
    if (resp.ok) {
      const data = await resp.json()
      templates.value = data.workflows || []
    }
  } catch (e) {
    console.warn('[WorkflowTour] Failed to load templates:', e)
    templates.value = []
  } finally {
    templatesLoading.value = false
  }
}

function handleTourClose(val) {
  tourVisible.value = val
}

function handleTourComplete() {
  localStorage.setItem(STORAGE_KEY, 'true')
  emit('complete')
  tourVisible.value = false
}

function handleStepChange(step) {
  currentStep.value = step
}

function resetTour() {
  localStorage.removeItem(STORAGE_KEY)
  currentStep.value = 0
}

// 暴露 startTour 供外部调用
defineExpose({ startTour, resetTour })
</script>

