<template>
  <button
    class="button-secondary"
    :class="[
      `button-secondary--${size}`,
      { 'button-secondary--icon-only': iconOnly }
    ]"
    :disabled="disabled"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
</template>

<script setup>
/**
 * ButtonSecondary - 次要操作按钮 (Ghost Pill)
 *
 * @see DESIGN.md - button-secondary-pill
 * @example
 * <ButtonSecondary @click="handleClick">取消</ButtonSecondary>
 * <ButtonSecondary size="sm">小按钮</ButtonSecondary>
 */
defineProps({
  iconOnly: Boolean,
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md'].includes(v)
  },
  disabled: Boolean
})

defineEmits(['click'])
</script>

<style scoped>
/* ============================================
   ButtonSecondary - Apple Design System
   Based on DESIGN.md button-secondary-pill
   ============================================ */

.button-secondary {
  /* Surface - transparent background */
  background: transparent;

  /* Primary color for text and border */
  color: var(--color-primary);

  /* Typography */
  font: var(--text-body);

  /* Shape - Ghost pill */
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-pill);

  /* Spacing */
  padding: var(--spacing-sm) var(--spacing-md);

  /* Interactive */
  cursor: pointer;
  transition: transform 0.1s ease, background 0.15s ease;
}

/* Active State */
.button-secondary:active {
  transform: scale(0.95);
}

/* Focus State */
.button-secondary:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

/* Hover State - Parchment background */
.button-secondary:hover {
  background: var(--color-canvas-parchment);
}

/* Disabled State */
.button-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.button-secondary:disabled:active {
  transform: none;
}

/* Size Variants */
.button-secondary--sm {
  font: var(--text-caption);
  padding: var(--spacing-xxs) var(--spacing-sm);
}

.button-secondary--md {
  font: var(--text-body);
  padding: var(--spacing-sm) var(--spacing-md);
}

/* Icon Only - Circular */
.button-secondary--icon-only {
  width: 44px;
  height: 44px;
  padding: 0;
  border-radius: var(--radius-full);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>