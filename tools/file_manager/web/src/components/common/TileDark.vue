<template>
  <section class="tile-apple-dark" :class="{ 'tile-2': variant === '2', 'tile-3': variant === '3' }">
    <slot />
  </section>
</template>

<script setup>
defineProps({
  /** Tile 变体: 1 (默认) / 2 (略浅) / 3 (略深) */
  variant: {
    type: String,
    default: '1',
    validator: (v) => ['1', '2', '3'].includes(v)
  }
})
</script>

<style scoped>
.tile-apple-dark {
  background-color: var(--color-surface-tile-1);
  color: var(--color-body-on-dark);
  padding: var(--spacing-section) var(--spacing-lg);
  width: 100%;
}

.tile-apple-dark.tile-2 {
  background-color: var(--color-surface-tile-2);
}

.tile-apple-dark.tile-3 {
  background-color: var(--color-surface-tile-3);
}

@media (max-width: 640px) {
  .tile-apple-dark {
    padding: var(--spacing-xxl) var(--spacing-md);
  }
}
</style>