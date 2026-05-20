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

