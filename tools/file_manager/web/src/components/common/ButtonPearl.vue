<template>
  <button
    class="button-pearl"
    :class="{ 'button-pearl--icon-only': iconOnly }"
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
   ButtonPearl - Apple Design System
   Based on DESIGN.md button-pearl-capsule
   ============================================ */

.button-pearl {
  /* Surface - Pearl background */
  background: var(--color-surface-pearl);
  color: var(--color-ink-muted-80);

  /* Typography */
  font: var(--text-caption);

  /* Shape - Pearl capsule with soft ring */
  border: 3px solid var(--color-divider-soft);
  border-radius: var(--radius-md);

  /* Spacing */
  padding: 8px 14px;

  /* Interactive */
  cursor: pointer;
  transition: transform 0.1s ease, opacity 0.15s ease;
}

/* Active State */
.button-pearl:active {
  transform: scale(0.95);
}

/* Focus State */
.button-pearl:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

/* Disabled State */
.button-pearl:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.button-pearl:disabled:active {
  transform: none;
}

/* Icon Only - Circular */
.button-pearl--icon-only {
  width: 44px;
  height: 44px;
  padding: 0;
  border-radius: var(--radius-full);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>