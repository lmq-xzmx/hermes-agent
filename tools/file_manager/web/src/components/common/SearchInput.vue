<template>
  <div class="search-input">
    <span class="search-input__icon">
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M10.5 10.5L14 14M7 2C4.79086 2 3 3.79086 3 6C3 8.20914 4.79086 10 7 10C9.20914 10 11 8.20914 11 6C11 3.79086 9.20914 2 7 2Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </span>
    <input
      type="text"
      class="search-input__field"
      :value="modelValue"
      :placeholder="placeholder"
      @input="$emit('update:modelValue', $event.target.value)"
      @keydown.enter="$emit('search', modelValue)"
    >
    <button
      v-if="modelValue"
      class="search-input__clear"
      type="button"
      @click="$emit('update:modelValue', ''); $emit('clear')"
      aria-label="清除搜索"
    >
      <svg width="12" height="12" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
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
/* ============================================
   SearchInput - Apple Design System
   Based on DESIGN.md search-input component
   ============================================ */

.search-input {
  /* Layout */
  position: relative;
  display: inline-flex;
  align-items: center;
  width: 100%;
  max-width: 320px;

  /* Box Model */
  height: 44px;

  /* Visual */
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);

  /* Animation */
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.search-input:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-faint);
}

/* ============================================
   Element: search-input__field
   ============================================ */
.search-input__field {
  /* Box Model */
  width: 100%;
  height: 100%;
  padding: var(--spacing-sm) 20px var(--spacing-sm) 40px;
  border: none;
  border-radius: inherit;
  box-sizing: border-box;

  /* Typography */
  font: var(--text-body);
  color: var(--color-ink);

  /* Visual */
  background: transparent;
  outline: none;
  cursor: text;
}

.search-input__field::placeholder {
  color: var(--color-ink-muted-48);
}

/* ============================================
   Element: search-input__icon
   ============================================ */
.search-input__icon {
  /* Layout */
  position: absolute;
  left: var(--spacing-sm);
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;

  /* Visual */
  color: var(--color-ink-muted-48);
  pointer-events: none;
}

/* ============================================
   Element: search-input__clear
   ============================================ */
.search-input__clear {
  /* Layout */
  position: absolute;
  right: var(--spacing-xs);
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;

  /* Box Model */
  width: 28px;
  height: 28px;

  /* Visual */
  background: var(--color-surface-pearl);
  border: none;
  border-radius: var(--radius-full);
  color: var(--color-ink-muted-48);
  cursor: pointer;

  /* Animation */
  transition: background-color 0.15s ease, color 0.15s ease, transform 0.1s ease;
}

.search-input__clear:hover {
  background: var(--color-hairline);
  color: var(--color-ink);
}

.search-input__clear:active {
  transform: translateY(-50%) scale(0.95);
}
</style>