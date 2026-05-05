<template>
  <button
    class="btn-apple-dark-utility"
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
.btn-apple-dark-utility {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  background-color: var(--color-ink);
  color: var(--color-body-on-dark);
  border: none;
  border-radius: var(--radius-sm);
  padding: 8px 15px;
  font-family: var(--font-family-text);
  font-size: 14px;
  font-weight: 400;
  line-height: 1.29;
  letter-spacing: -0.224px;
  cursor: pointer;
  transition: transform 0.1s ease;
  white-space: nowrap;
}

.btn-apple-dark-utility:hover {
  background-color: var(--color-ink-muted-80);
}

.btn-apple-dark-utility:active:not(:disabled) {
  transform: scale(0.95);
}

.btn-apple-dark-utility:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

.btn-apple-dark-utility:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Icon-only: 44x44 touch target */
.btn-apple-dark-utility.btn-icon-only {
  padding: 8px;
  width: 44px;
  height: 44px;
}
</style>