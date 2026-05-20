<template>
  <button
    class="button-icon"
    :disabled="disabled"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
</template>

<script setup>
defineProps({
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
   ButtonIcon - Apple Design System
   Based on DESIGN.md button-icon-circular
   ============================================ */

.button-icon {
  /* Surface - Translucent chip over photography */
  background: var(--color-surface-chip-translucent-bg);
  color: var(--color-ink);

  /* Shape - Circular */
  border: none;
  border-radius: var(--radius-full);

  /* Size - 44x44 touch target */
  width: 44px;
  height: 44px;
  padding: 0;

  /* Layout - Center content */
  display: inline-flex;
  align-items: center;
  justify-content: center;

  /* Interactive */
  cursor: pointer;
  transition: transform 0.1s ease, opacity 0.15s ease;
}

/* Active State */
.button-icon:active {
  transform: scale(0.95);
}

/* Focus State */
.button-icon:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

/* Disabled State */
.button-icon:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.button-icon:disabled:active {
  transform: none;
}
</style>