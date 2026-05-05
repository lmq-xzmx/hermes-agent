<template>
  <span class="chip" :class="{ selected }">
    <slot />
    <button v-if="closable" class="chip-close" @click.stop="$emit('close')" aria-label="关闭">
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
        <path d="M9 3L3 9M3 3L9 9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
    </button>
  </span>
</template>

<script setup>
defineProps({
  selected: { type: Boolean, default: false },
  closable: { type: Boolean, default: false }
})

defineEmits(['close'])
</script>

<style scoped>
.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  font-family: var(--font-body);
  font-size: 14px;
  line-height: 1.43;
  letter-spacing: -0.224px;
  color: var(--color-ink);
  cursor: pointer;
  transition: all 0.15s ease;
}

.chip:hover {
  border-color: var(--color-ink-muted-48);
}

.chip.selected {
  background: var(--color-primary-hover);
  border-color: var(--color-primary-focus);
  color: var(--color-primary);
}

.chip-close {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  padding: 2px;
  margin-right: -4px;
  opacity: 0.6;
  transition: opacity 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chip-close:hover {
  opacity: 1;
}

.chip-close:active {
  transform: scale(0.9);
}
</style>
