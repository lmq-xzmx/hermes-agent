<template>
  <div class="card-apple-utility" :class="{ 'card-clickable': clickable }">
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
.card-apple-utility {
  background-color: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.card-apple-utility img {
  border-radius: var(--radius-md);
}

.card-apple-utility.card-clickable {
  cursor: pointer;
}

.card-apple-utility.card-clickable:hover {
  border-color: var(--color-primary);
}
</style>