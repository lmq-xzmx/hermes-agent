<template>
  <span class="badge" :class="variant" :style="customStyle">
    <slot />
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'default' // default/success/warning/danger/info
  },
  size: {
    type: String,
    default: 'md' // sm/md/lg
  }
})

const customStyle = computed(() => ({
  fontSize: props.size === 'sm' ? '11px' : props.size === 'lg' ? '14px' : '12px',
  padding: props.size === 'sm' ? '2px 8px' : props.size === 'lg' ? '6px 14px' : '4px 10px',
  fontFamily: 'var(--font-family-text)'
}))
</script>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  border-radius: var(--radius-pill);
  font-family: var(--font-family-text);
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
}

.badge.default {
  background: var(--color-surface-pearl);
  color: var(--color-ink-muted-80);
}

.badge.success {
  background: var(--color-success-subtle);
  color: var(--color-success);
}

.badge.warning {
  background: var(--color-warning-subtle);
  color: var(--color-warning);
}

.badge.danger {
  background: var(--color-danger-subtle);
  color: var(--color-danger);
}

.badge.info {
  background: var(--color-primary-hover);
  color: var(--color-primary);
}

.badge.primary {
  background: var(--color-primary-hover);
  color: var(--color-primary);
}
</style>
