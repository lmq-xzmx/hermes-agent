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

<style scoped>
.tour-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 9999;
  pointer-events: none;
}

.tour-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
}

.tour-spotlight {
  position: absolute;
  border: 2px solid var(--primary-color, #238636);
  border-radius: 8px;
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.6);
  transition: all 0.3s ease;
}

.tour-tooltip {
  position: absolute;
  background: var(--bg-secondary, #1a1f26);
  border: 1px solid var(--border, #30363d);
  border-radius: 12px;
  padding: 0;
  max-width: 280px;
  min-width: 200px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  pointer-events: auto;
  z-index: 10000;
}

.tour-content {
  padding: 16px;
}

.tour-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.tour-step-badge {
  font-size: 12px;
  color: var(--text-secondary, #8b949e);
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
}

.tour-close {
  background: none;
  border: none;
  font-size: 18px;
  color: var(--text-secondary, #8b949e);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
}

.tour-close:hover {
  background: rgba(255, 255, 255, 0.1);
}

.tour-text {
  margin: 0;
  font-size: 14px;
  color: var(--text-primary, #e6edf3);
  line-height: 1.5;
}

.tour-footer {
  display: flex;
  gap: 8px;
  margin-top: 16px;
  justify-content: flex-end;
}

.tour-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}

.tour-btn.primary {
  background: var(--primary-color, #238636);
  color: white;
}

.tour-btn.primary:hover {
  background: var(--primary-hover, #2ea043);
}

.tour-btn.secondary {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary, #e6edf3);
}

.tour-btn.secondary:hover {
  background: rgba(255, 255, 255, 0.15);
}

.tour-progress {
  display: flex;
  gap: 6px;
  padding: 12px 16px;
  border-top: 1px solid var(--border, #30363d);
}

.tour-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  transition: all 0.2s;
}

.tour-dot.active {
  background: var(--primary-color, #238636);
}

/* Transitions */
.tour-enter-active,
.tour-leave-active {
  transition: opacity 0.3s ease;
}

.tour-enter-from,
.tour-leave-to {
  opacity: 0;
}
</style>
