<template>
  <span
    class="badge"
    :class="[
      `badge--${variant}`,
      `badge--${size}`
    ]"
  >
    <slot />
  </span>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'default' // default/success/warning/danger/info
  },
  size: {
    type: String,
    default: 'md' // sm/md/lg
  }
})
</script>

<style scoped>
/* ============================================
   Badge - Apple Design System
   ============================================ */

.badge {
  /* Layout */
  display: inline-flex;
  align-items: center;

  /* Box Model */
  padding: var(--spacing-xxs) var(--spacing-sm);

  /* Visual */
  border-radius: var(--radius-pill);

  /* Typography */
  font: var(--text-caption);
}

/* Size Variants */
.badge--sm {
  font: var(--text-fine-print);
  padding: 2px 8px;
}

.badge--md {
  font: var(--text-caption);
  padding: var(--spacing-xxs) var(--spacing-sm);
}

.badge--lg {
  font: var(--text-body);
  padding: var(--spacing-xs) var(--spacing-md);
}

/* Variant: default */
.badge--default {
  background: var(--color-canvas-parchment);
  color: var(--color-ink);
}

/* Variant: success */
.badge--success {
  background: var(--color-success-subtle);
  color: var(--color-success);
}

/* Variant: warning */
.badge--warning {
  background: var(--color-warning-subtle);
  color: var(--color-warning-strong);
}

/* Variant: danger */
.badge--danger {
  background: var(--color-danger-subtle);
  color: var(--color-danger-strong);
}

/* Variant: info */
.badge--info {
  background: var(--color-primary-subtle);
  color: var(--color-primary);
}
</style>