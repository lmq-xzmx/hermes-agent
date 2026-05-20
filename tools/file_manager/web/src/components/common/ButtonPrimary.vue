<template>
  <button
    class="button-primary"
    :class="{
      'button-primary--icon-only': iconOnly,
      'button-primary--sm': size === 'sm',
      'button-primary--lg': size === 'lg'
    }"
    :disabled="disabled"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
</template>

<script setup>
defineProps({
  iconOnly: {
    type: Boolean,
    default: false
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v)
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click'])
</script>

<style scoped>
/* ============================================
   ButtonPrimary - Apple Design System
   Based on DESIGN.md button-primary component
   ============================================ */

.button-primary {
  /* Brand & Accent */
  background: var(--color-primary);
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

/* Active State - Apple micro-interaction */
.button-primary:active {
  transform: scale(0.95);
}

/* Focus State - Apple focus ring */
.button-primary:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

/* Disabled State */
.button-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.button-primary:disabled:active {
  transform: none;
}

/* Size Variants */
.button-primary--sm {
  font: var(--text-caption);
  padding: var(--spacing-xxs) var(--spacing-sm);
}

.button-primary--lg {
  font: var(--text-button-large);
  padding: 14px 28px;
}

/* Icon Only - Circular */
.button-primary--icon-only {
  width: 44px;
  height: 44px;
  padding: 0;
  border-radius: var(--radius-full);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>