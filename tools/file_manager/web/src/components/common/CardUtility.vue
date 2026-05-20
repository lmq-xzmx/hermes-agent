<template>
  <div class="card-utility" :class="{ 'card-clickable': clickable }">
    <slot />
  </div>
</template>

<script setup>
defineProps({
  /** 是否可点击（hover 效果） */
  clickable: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.card-utility {
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.card-clickable {
  cursor: pointer;
  transition: box-shadow var(--transition-fast);
}

.card-clickable:hover {
  box-shadow: var(--shadow-md);
}
</style>

