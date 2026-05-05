/**
 * Tour composable - reusable tour logic for guided workflows
 *
 * Usage:
 * const { startTour, endTour, isActive, currentStep } = useTour({
 *   storageKey: 'my_tour_completed',
 *   steps: [
 *     { target: '.btn-create', content: 'Click to create', position: 'bottom' },
 *     { target: '.name-input', content: 'Enter name', position: 'right' },
 *   ]
 * })
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'

export function useTour(options = {}) {
  const {
    storageKey = 'tour_completed',
    steps = [],
    autoStart = false,
    delay = 100
  } = options

  const visible = ref(false)
  const currentStep = ref(0)
  const totalSteps = computed(() => steps.length)
  const isLastStep = computed(() => currentStep.value === totalSteps.value - 1)
  const isFirstStep = computed(() => currentStep.value === 0)
  const currentStepData = computed(() => steps[currentStep.value])
  const isCompleted = computed(() => localStorage.getItem(storageKey) === 'true')

  function startTour() {
    if (isCompleted.value) {
      console.log(`[useTour] Tour already completed: ${storageKey}`)
      return false
    }
    currentStep.value = 0
    visible.value = true
    return true
  }

  function endTour(completed = false) {
    visible.value = false
    if (completed) {
      localStorage.setItem(storageKey, 'true')
    }
  }

  function next() {
    if (isLastStep.value) {
      endTour(true)
      return 'complete'
    }
    currentStep.value++
    return 'continue'
  }

  function prev() {
    if (isFirstStep.value) return
    currentStep.value--
  }

  function goToStep(index) {
    if (index >= 0 && index < totalSteps.value) {
      currentStep.value = index
    }
  }

  function resetTour() {
    localStorage.removeItem(storageKey)
    currentStep.value = 0
  }

  function getStepPosition(stepIndex) {
    const step = steps[stepIndex]
    if (!step) return { top: 0, left: 0 }

    const targetEl = document.querySelector(step.target)
    if (!targetEl) return { top: 0, left: 0 }

    const rect = targetEl.getBoundingClientRect()
    const padding = 8

    let top, left
    const position = step.position || 'bottom'

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

    return { top, left }
  }

  // Auto-start if enabled and not completed
  onMounted(() => {
    if (autoStart && !isCompleted.value) {
      setTimeout(startTour, delay)
    }
  })

  return {
    visible,
    currentStep,
    totalSteps,
    isLastStep,
    isFirstStep,
    isCompleted,
    currentStepData,
    startTour,
    endTour,
    next,
    prev,
    goToStep,
    resetTour,
    getStepPosition
  }
}

/**
 * TourHighlight component - standalone highlight overlay
 *
 * Usage:
 * <TourHighlight :target="'.my-element'" :padding="8" />
 */
export const TourHighlight = {
  name: 'TourHighlight',
  props: {
    target: { type: String, required: true },
    padding: { type: Number, default: 8 }
  },
  setup(props) {
    const style = ref({})

    function updatePosition() {
      const el = document.querySelector(props.target)
      if (!el) {
        style.value = { display: 'none' }
        return
      }

      const rect = el.getBoundingClientRect()
      style.value = {
        top: `${rect.top - props.padding}px`,
        left: `${rect.left - props.padding}px`,
        width: `${rect.width + props.padding * 2}px`,
        height: `${rect.height + props.padding * 2}px`
      }
    }

    onMounted(() => {
      updatePosition()
      window.addEventListener('resize', updatePosition)
    })

    onUnmounted(() => {
      window.removeEventListener('resize', updatePosition)
    })

    return { style }
  },
  template: `
    <div class="tour-highlight" :style="style"></div>
  `
}

/**
 * TourProgress - step indicator dots
 *
 * Usage:
 * <TourProgress :current="2" :total="5" />
 */
export const TourProgress = {
  name: 'TourProgress',
  props: {
    current: { type: Number, default: 0 },
    total: { type: Number, default: 0 },
    activeColor: { type: String, default: 'var(--color-success, #34c759)' }
  },
  computed: {
    dots() {
      return Array.from({ length: this.total }, (_, i) => ({
        index: i,
        active: i <= this.current
      }))
    }
  },
  template: `
    <div class="tour-progress">
      <span
        v-for="dot in dots"
        :key="dot.index"
        class="tour-progress-dot"
        :class="{ active: dot.active }"
        :style="dot.active ? { background: activeColor } : {}"
      ></span>
    </div>
  `
}
