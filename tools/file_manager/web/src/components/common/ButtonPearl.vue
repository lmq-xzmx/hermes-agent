<template>
  <button
    class="btn-apple-pearl"
    :class="{ 'btn-icon-only': iconOnly }"
    :disabled="disabled"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
</template>

<script setup>
defineProps({
  /** 图标模式：44x44 触摸目标 */
  iconOnly: {
    type: Boolean,
    default: false
  },
  /** 禁用状态 */
  disabled: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click'])
</script>

<style scoped>
.btn-apple-pearl {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  background-color: var(--color-surface-pearl);
  color: var(--color-ink-muted-80);
  border: 3px solid var(--color-divider-soft);
  border-radius: var(--radius-md);
  padding: 8px 14px;
  font-family: var(--font-family-text);
  font-size: 14px;
  font-weight: 400;
  line-height: 1.43;
  letter-spacing: -0.224px;
  cursor: pointer;
  transition: transform 0.1s ease;
  white-space: nowrap;
}

.btn-apple-pearl:hover {
  background-color: var(--color-canvas);
}

.btn-apple-pearl:active:not(:disabled) {
  transform: scale(0.95);
}

.btn-apple-pearl:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

.btn-apple-pearl:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Icon-only: 44x44 touch target */
.btn-apple-pearl.btn-icon-only {
  padding: 8px;
  width: 44px;
  height: 44px;
}
</style>