<template>
  <button
    class="button-dark-utility"
    :class="{ 'button-dark-utility--icon-only': iconOnly }"
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
/* ============================================
   ButtonDarkUtility - Apple Design System
   Based on DESIGN.md button-dark-utility
   ============================================ */

.button-dark-utility {
  /* Surface - Ink background */
  background: var(--color-ink);
  color: var(--color-on-dark);

  /* Typography */
  font: var(--text-button-utility);

  /* Shape */
  border: none;
  border-radius: var(--radius-sm);

  /* Spacing */
  padding: 8px 15px;

  /* Interactive */
  cursor: pointer;
  transition: transform 0.1s ease, opacity 0.15s ease;
}

/* Active State */
.button-dark-utility:active {
  transform: scale(0.95);
}

/* Focus State */
.button-dark-utility:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

/* Disabled State */
.button-dark-utility:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.button-dark-utility:disabled:active {
  transform: none;
}

/* Icon Only - Circular */
.button-dark-utility--icon-only {
  width: 44px;
  height: 44px;
  padding: 0;
  border-radius: var(--radius-full);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>