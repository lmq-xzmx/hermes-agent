<template>
  <div class="search-input-wrapper">
    <span class="search-icon">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M10.5 10.5L14 14M7 2C4.79086 2 3 3.79086 3 6C3 8.20914 4.79086 10 7 10C9.20914 10 11 8.20914 11 6C11 3.79086 9.20914 2 7 2Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </span>
    <input
      type="text"
      class="apple-search-input"
      :value="modelValue"
      :placeholder="placeholder"
      @input="$emit('update:modelValue', $event.target.value)"
      @keydown.enter="$emit('search', modelValue)"
    >
    <button
      v-if="modelValue"
      class="clear-btn"
      type="button"
      @click="$emit('update:modelValue', ''); $emit('clear')"
      aria-label="清除搜索"
    >
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M10.5 3.5L3.5 10.5M3.5 3.5L10.5 10.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
    </button>
  </div>
</template>

<script setup>
defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '搜索'
  }
})

defineEmits(['update:modelValue', 'search', 'clear'])
</script>

<style scoped>
.search-input-wrapper {
  position: relative;
  display: inline-flex;
  align-items: center;
  width: 100%;
  max-width: 320px;
}

.apple-search-input {
  width: 100%;
  height: 44px;
  padding: 12px 40px 12px 40px;
  background-color: var(--color-canvas);
  color: var(--color-ink);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  font-family: var(--font-family-text);
  font-size: 17px;
  font-weight: 400;
  line-height: 1.47;
  letter-spacing: -0.374px;
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.apple-search-input::placeholder {
  color: var(--color-ink-muted-48);
}

.apple-search-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-hover);
}

.search-icon {
  position: absolute;
  left: 14px;
  color: var(--color-ink-muted-48);
  display: flex;
  align-items: center;
  pointer-events: none;
}

.clear-btn {
  position: absolute;
  right: 8px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface-pearl);
  border: none;
  border-radius: 50%;
  color: var(--color-ink-muted-48);
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.clear-btn:hover {
  background-color: var(--color-hairline);
  color: var(--color-ink);
}

.clear-btn:active {
  transform: scale(0.95);
}
</style>
