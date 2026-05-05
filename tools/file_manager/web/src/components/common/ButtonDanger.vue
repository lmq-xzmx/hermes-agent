<template>
  <button
    class="btn-apple-danger"
    :class="{ 'btn-sm': size === 'sm', 'btn-icon-only': iconOnly }"
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
.btn-apple-danger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background-color: var(--color-danger);
  color: var(--color-body-on-dark);
  border: none;
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

.btn-apple-danger:hover {
  background-color: #e6352b;
}

.btn-apple-danger:active:not(:disabled) {
  transform: scale(0.95);
}

.btn-apple-danger:focus {
  outline: 2px solid var(--color-danger);
  outline-offset: 2px;
}

.btn-apple-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Icon-only: 44x44 touch target */
.btn-apple-danger.btn-icon-only {
  padding: 11px;
  width: 44px;
  height: 44px;
}

/* Sizes */
.btn-apple-danger.btn-sm {
  padding: 6px 14px;
  font-size: 14px;
}

.btn-apple-danger.btn-sm.btn-icon-only {
  padding: 6px;
  width: 32px;
  height: 32px;
}
</style>
