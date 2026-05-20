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

