<template>
  <button
    class="button-danger"
    :class="{
      'button-danger--sm': size === 'sm',
      'button-danger--icon-only': iconOnly
    }"
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
/* ============================================
   ButtonDanger - Apple Design System
   ============================================ */

.button-danger {
  /* Brand & Accent - Danger */
  background: var(--color-danger);
  color: var(--color-on-primary);

  /* Typography */
  font: var(--text-body);

  /* Shape */
  border: none;
  border-radius: var(--radius-pill);

  /* Spacing */
  padding: var(--spacing-sm) var(--spacing-md);

  /* Interactive */
  cursor: pointer;
  transition: transform 0.1s ease, opacity 0.15s ease;
}

/* Active State */
.button-danger:active {
  transform: scale(0.95);
}

/* Focus State */
.button-danger:focus {
  outline: 2px solid var(--color-danger-strong);
  outline-offset: 2px;
}

/* Disabled State */
.button-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.button-danger:disabled:active {
  transform: none;
}

/* Size Variants */
.button-danger--sm {
  font: var(--text-caption);
  padding: var(--spacing-xxs) var(--spacing-sm);
}

/* Icon Only - Circular */
.button-danger--icon-only {
  width: 44px;
  height: 44px;
  padding: 0;
  border-radius: var(--radius-full);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>