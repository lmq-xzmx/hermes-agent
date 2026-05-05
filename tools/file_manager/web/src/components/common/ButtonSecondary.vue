<template>
  <button
    class="btn-apple-secondary"
    :class="{ 'btn-icon-only': iconOnly, 'btn-sm': size === 'sm' }"
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
  /** 尺寸: sm / md */
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md'].includes(v)
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
.btn-apple-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background-color: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-pill);
  padding: 11px 22px;
  font-family: var(--font-family-text);
  font-size: 17px;
  font-weight: 400;
  line-height: 1.47;
  letter-spacing: -0.374px;
  cursor: pointer;
  transition: transform 0.1s ease;
  white-space: nowrap;
}

.btn-apple-secondary:hover {
  background-color: var(--color-primary);
  color: var(--color-body-on-dark);
}

.btn-apple-secondary:active:not(:disabled) {
  transform: scale(0.95);
}

.btn-apple-secondary:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

.btn-apple-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Icon-only: 44x44 touch target */
.btn-apple-secondary.btn-icon-only {
  padding: 11px;
  width: 44px;
  height: 44px;
}

/* Sizes */
.btn-apple-secondary.btn-sm {
  padding: var(--space-xxs) var(--space-sm);
  font-size: 14px;
}

.btn-apple-secondary.btn-sm.btn-icon-only {
  padding: var(--space-xxs);
  width: 32px;
  height: 32px;
}
</style>