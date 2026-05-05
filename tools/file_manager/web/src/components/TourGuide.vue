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
  background: var(--color-overlay-tour);
}

.tour-spotlight {
  position: absolute;
  border: 2px solid var(--color-primary);
  border-radius: var(--radius-md);
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.6);
  transition: all 0.3s ease;
}

.tour-tooltip {
  position: absolute;
  background: var(--color-surface-tile-2);
  border: 1px solid var(--color-border-on-dark);
  border-radius: var(--radius-lg);
  padding: 0;
  max-width: 280px;
  min-width: 200px;
  pointer-events: auto;
  z-index: 10000;
}

.tour-content {
  padding: var(--spacing-md);
}

.tour-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.tour-step-badge {
  font-size: 12px;
  color: var(--color-body-muted);
  background: var(--color-border-on-dark);
  padding: var(--spacing-xxs) var(--spacing-xs);
  border-radius: var(--radius-xs);
}

.tour-close {
  background: none;
  border: none;
  font-size: 18px;
  color: var(--color-body-muted);
  cursor: pointer;
  padding: var(--spacing-xxs);
  border-radius: var(--radius-xs);
}

.tour-close:hover {
  background: var(--color-border-on-dark);
}

.tour-text {
  margin: 0;
  font-size: 14px;
  color: var(--color-body-on-dark);
  line-height: 1.5;
}

.tour-footer {
  display: flex;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-md);
  justify-content: flex-end;
}

.tour-btn {
  padding: var(--spacing-xs) var(--spacing-md);
  border: none;
  border-radius: var(--radius-pill);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.tour-btn.primary {
  background: var(--color-primary);
  color: var(--color-body-on-dark);
}

.tour-btn.primary:hover {
  background: var(--color-primary-focus);
}

.tour-btn.secondary {
  background: var(--color-border-on-dark);
  color: var(--color-body-on-dark);
}

.tour-btn.secondary:hover {
  background: var(--color-border-on-dark-strong);
}

.tour-progress {
  display: flex;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  border-top: 1px solid var(--color-border-on-dark);
}

.tour-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  background: var(--color-border-on-dark-stronger);
  transition: all 0.2s;
}

.tour-dot.active {
  background: var(--color-primary);
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
