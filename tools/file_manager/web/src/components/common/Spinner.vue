<template>
  <div class="spinner" :class="sizeClass" role="status" :aria-label="label">
    <svg class="spinner-svg" viewBox="0 0 24 24" fill="none">
      <circle
        class="spinner-track"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        stroke-width="2"
      />
      <circle
        class="spinner-indicator"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        :stroke-dasharray="dashArray"
        :stroke-dashoffset="dashOffset"
      />
    </svg>
    <span v-if="label" class="spinner-label">{{ label }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  size: { type: String, default: 'md' }, // sm/md/lg
  label: { type: String, default: '' }
})

const sizeClass = computed(() => `spinner-${props.size}`)

const dashArray = computed(() => {
  const circumference = 2 * Math.PI * 10
  return `${circumference * 0.75} ${circumference * 0.25}`
})

const dashOffset = computed(() => {
  return 0
})
</script>

<style scoped>
.spinner {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: var(--color-primary);
}

.spinner-sm { font-size: 12px; }
.spinner-md { font-size: 16px; }
.spinner-lg { font-size: 24px; }

.spinner-svg {
  animation: spinner-rotate 1s linear infinite;
}

.spinner-sm .spinner-svg { width: 16px; height: 16px; }
.spinner-md .spinner-svg { width: 24px; height: 24px; }
.spinner-lg .spinner-svg { width: 40px; height: 40px; }

.spinner-track {
  opacity: 0.2;
}

.spinner-indicator {
  animation: spinner-dash 1.5s ease-in-out infinite;
}

.spinner-label {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-ink-muted-48);
}

@keyframes spinner-rotate {
  100% {
    transform: rotate(360deg);
  }
}

@keyframes spinner-dash {
  0% {
    stroke-dasharray: 1, 150;
    stroke-dashoffset: 0;
  }
  50% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -35;
  }
  100% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -124;
  }
}
</style>
