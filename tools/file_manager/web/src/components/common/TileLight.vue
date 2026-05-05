<template>
  <section class="tile-apple-light">
    <slot />
  </section>
</template>

<script setup>
// Full-bleed light tile section
// Used for alternating light sections in page rhythm
</script>

<style scoped>
.tile-apple-light {
  background-color: var(--color-canvas);
  padding: var(--spacing-section) var(--spacing-lg);
  width: 100%;
}

@media (max-width: 640px) {
  .tile-apple-light {
    padding: 48px var(--spacing-md);
  }
}
</style>