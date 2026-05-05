<template>
  <div class="card-apple-base">
    <slot />
  </div>
</template>

<script setup>
// Base card component with hairline border
</script>

<style scoped>
.card-apple-base {
  background-color: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}
</style>