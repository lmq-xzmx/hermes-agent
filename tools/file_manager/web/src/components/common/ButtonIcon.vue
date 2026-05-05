<template>
  <button
    class="btn-apple-icon"
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
.btn-apple-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  background-color: var(--color-surface-chip-translucent-bg);
  color: var(--color-ink);
  border: none;
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: transform 0.1s ease;
}

.btn-apple-icon:hover {
  background-color: var(--color-surface-chip-hover);
}

.btn-apple-icon:active:not(:disabled) {
  transform: scale(0.95);
}

.btn-apple-icon:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

.btn-apple-icon:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>