<template>
  <button
    class="btn-apple-primary"
    :class="{ 'btn-icon-only': iconOnly, 'btn-sm': size === 'sm', 'btn-lg': size === 'lg' }"
    :disabled="disabled"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
</template>

<script setup>
defineProps({
  /** 图标模式：44x44 圆形/方形 */
  iconOnly: {
    type: Boolean,
    default: false
  },
  /** 尺寸: sm / md / lg */
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v)
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
.btn-apple-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background-color: var(--color-primary);
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

.btn-apple-primary:hover {
  background-color: var(--color-primary-focus);
}

.btn-apple-primary:active:not(:disabled) {
  transform: scale(0.95);
}

.btn-apple-primary:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

.btn-apple-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Icon-only: 44x44 touch target */
.btn-apple-primary.btn-icon-only {
  padding: 11px;
  width: 44px;
  height: 44px;
}

/* Sizes */
.btn-apple-primary.btn-sm {
  padding: 6px 14px;
  font-size: 14px;
}

.btn-apple-primary.btn-sm.btn-icon-only {
  padding: 6px;
  width: 32px;
  height: 32px;
}

.btn-apple-primary.btn-lg {
  padding: 14px 28px;
  font-size: 18px;
  font-weight: 300;
}
</style>