<template>
  <Teleport to="body">
    <Transition name="tour">
      <div v-if="visible" class="tour-container" :id="tourId">
        <div class="tour-overlay"></div>
        <div
          class="tour-spotlight"
          :style="spotlightStyle"
        ></div>
        <div
          class="tour-tooltip"
          :style="tooltipStyle"
        >
          <div class="tour-content">
            <div class="tour-header">
              <span class="tour-step-badge">步骤 {{ currentStep + 1 }}/{{ totalSteps }}</span>
              <button class="tour-close" @click="close">×</button>
            </div>
            <p class="tour-text">{{ currentStepData?.content }}</p>
            <div class="tour-footer">
              <button
                v-if="currentStep > 0"
                class="tour-btn secondary"
                @click="prev"
              >
                ← 上一步
              </button>
              <button
                class="tour-btn primary"
                @click="next"
              >
                {{ isLastStep ? '完成' : '下一步' }} →
              </button>
            </div>
          </div>
          <div class="tour-progress">
            <div
              v-for="i in totalSteps"
              :key="i"
              class="tour-dot"
              :class="{ active: i - 1 <= currentStep }"
            ></div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useGuidanceStore } from '@/stores/guidanceStore'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  steps: {
    type: Array,
    default: () => []
  },
  initialStep: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['update:visible', 'complete', 'step-change'])

// 可选：与 guidanceStore 同步状态（当用作全局 Tour 时）
const guidanceStore = useGuidanceStore()

const currentStep = ref(0)
const tooltipStyle = ref({})
const spotlightStyle = ref({})

const totalSteps = computed(() => props.steps.length)
const currentStepData = computed(() => props.steps[currentStep.value])
const isLastStep = computed(() => currentStep.value === totalSteps.value - 1)

const tourId = 'tour-' + Date.now()

function next() {
  if (isLastStep.value) {
    close()
    emit('complete')
    // 标记 Tour 完成（如果正在使用 guidanceStore）
    if (guidanceStore.currentTour) {
      guidanceStore.endTour()
    }
  } else {
    currentStep.value++
    updatePositions()
    emit('step-change', currentStep.value)
    // 同步到 guidanceStore
    if (guidanceStore.currentTour) {
      guidanceStore.tourStepIndex = currentStep.value
    }
  }
}

function prev() {
  if (currentStep.value > 0) {
    currentStep.value--
    updatePositions()
    emit('step-change', currentStep.value)
    // 同步到 guidanceStore
    if (guidanceStore.currentTour) {
      guidanceStore.tourStepIndex = currentStep.value
    }
  }
}

function close() {
  emit('update:visible', false)
}

function updatePositions() {
  if (!currentStepData.value?.target) return

  const targetEl = document.querySelector(currentStepData.value.target)
  if (!targetEl) {
    console.warn(`[Tour] Target not found: ${currentStepData.value.target}`)
    return
  }

  const rect = targetEl.getBoundingClientRect()
  const position = currentStepData.value.position || 'bottom'

  // Calculate spotlight
  const padding = 8
  spotlightStyle.value = {
    top: `${rect.top - padding}px`,
    left: `${rect.left - padding}px`,
    width: `${rect.width + padding * 2}px`,
    height: `${rect.height + padding * 2}px`
  }

  // Calculate tooltip position
  let top, left

  switch (position) {
    case 'bottom':
      top = rect.bottom + 16
      left = rect.left + rect.width / 2
      break
    case 'top':
      top = rect.top - 80
      left = rect.left + rect.width / 2
      break
    case 'left':
      top = rect.top + rect.height / 2 - 40
      left = rect.left - 220
      break
    case 'right':
      top = rect.top + rect.height / 2 - 40
      left = rect.right + 16
      break
    default:
      top = rect.bottom + 16
      left = rect.left + rect.width / 2
  }

  tooltipStyle.value = {
    top: `${top}px`,
    left: `${left}px`,
    transform: 'translateX(-50%)'
  }
}

watch(() => props.visible, (val) => {
  if (val) {
    currentStep.value = props.initialStep
    setTimeout(updatePositions, 100)
    // 同步到 guidanceStore（如果正在使用）
    if (guidanceStore.currentTour) {
      guidanceStore.tourStepIndex = currentStep.value
    }
  }
})

onMounted(() => {
  window.addEventListener('resize', updatePositions)
})

onUnmounted(() => {
  window.removeEventListener('resize', updatePositions)
})
</script>

